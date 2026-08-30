#!/usr/bin/env python3
"""Project bronze-zone dumps into a candidate feed.

This is a BUILD STEP. Its output is derived and disposable: delete
data/serveable/api/candidates/ and re-run to reproduce it. The feed is byte
identical across rebuilds; LINEAGE.json differs only in its built_at wall
clock stamp. Run with --check to assert exactly that, which is the intended
CI gate. Nothing here is hand-edited. That property is the whole point -- the existing
serveable zone lost it, which is why manifest.json has said 28 events while
all_events.json said 1194 since 2025-12-24.

What it does, in order:
  1. Load the latest dump per source.
  2. Drop tombstoned records (see "Privacy" below).
  3. Resolve source-level facts from config/sources.json.
  4. Score salience under EVERY profile in config/salience_profiles/.
  5. Merge attributed human reviews from data/curated/human_review/.
  6. Screen for possible privacy concerns; flag, never silently delete.
  7. Emit the feed plus a LINEAGE.json accounting for every input record.

FACTS VERSUS OPINIONS
---------------------
Every field in an emitted record is one or the other, and they are kept
structurally distinct so a consumer can take the facts and ignore the
opinions, or inherit the opinions deliberately.

  Facts    title, the four clocks, actors, source_urls, signals, license
  Opinions salience_by_profile (a weighting choice, named and versioned)
           reviews (attributed to a named reviewer, never anonymous)

There is deliberately no bare `salience` field and no `game_facing` flag.
A bare number reads as a property of the record; an unattributed verdict
makes one person's taste indistinguishable from a source-derived fact. Both
would force a disagreeing consumer to fork rather than ignore.

Privacy
-------
Raw dumps are immutable, with exactly one exception: content that should not
have been ingested. Removal is by tombstone -- data/raw/_tombstones/ records
the id, date and reason CATEGORY, never the content. Downstream consumers
must honour tombstones; this is the one obligation that is not optional.

Usage:
    python scripts/build/project_candidates.py
    python scripts/build/project_candidates.py --dry-run
    python scripts/build/project_candidates.py --check   # CI gate
"""

import argparse
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "adapters"))

import _base  # noqa: E402

BUILD_VERSION = "0.2.0"
RAW_ROOT = os.path.join(REPO_ROOT, "data", "raw")
OUT_ROOT = os.path.join(REPO_ROOT, "data", "serveable", "api", "candidates")
TOMBSTONE_ROOT = os.path.join(RAW_ROOT, "_tombstones")
REVIEW_ROOT = os.path.join(REPO_ROOT, "data", "curated", "human_review")
ID_MIGRATIONS = os.path.join(REPO_ROOT, "data", "curated", "id_migrations.json")
AIRR_TAG_ROOT = os.path.join(REPO_ROOT, "data", "enrichment", "airr_tags")

# Source-level facts (notably source_available_at) are resolved here at build
# time rather than stamped by adapters. They are properties of the SOURCE, not
# of any particular fetch, so correcting one must not require re-downloading a
# dump. This supersedes the "adapter stamps it" wording in ADAPTER_SPEC v0.1.
SOURCE_REGISTRY_PATH = os.path.join(REPO_ROOT, "config", "sources.json")
PROFILE_DIR = os.path.join(REPO_ROOT, "config", "salience_profiles")

# Sources this build consumes. Deliberately explicit: a new adapter does not
# silently enter the feed just by existing.
SOURCES = ["epoch_ai", "forum_lesswrong", "forum_eaforum"]

# Heuristic privacy screen. Deliberately over-inclusive: a false flag costs a
# reviewer ten seconds, a miss can publish something about a real person who
# never asked to be in a game. Flags only; never auto-deletes.
PRIVACY_PATTERNS = [
    r"\bhas passed away\b", r"\bpassed away\b", r"\bin memoriam\b",
    r"\bobituary\b", r"\bmemorial\b", r"\brest in peace\b", r"\bRIP\b",
    r"\bdied\b", r"\bdeath of\b", r"\bsuicide\b", r"\bmental health\b",
    r"\bmy diagnosis\b", r"\bmy illness\b", r"\bcancer\b",
    r"\bharassment\b", r"\bmisconduct\b", r"\babuse\b", r"\ballegations\b",
    r"\brestraining order\b", r"\bcourt case\b", r"\bdivorce\b",
]
PRIVACY_RE = re.compile("|".join(PRIVACY_PATTERNS), re.IGNORECASE)


def latest_dump(source_id):
    dumps_dir = os.path.join(RAW_ROOT, source_id, "dumps")
    if not os.path.isdir(dumps_dir):
        return None
    stamps = sorted(
        d for d in os.listdir(dumps_dir)
        if os.path.isfile(os.path.join(dumps_dir, d, "data.jsonl"))
    )
    return os.path.join(dumps_dir, stamps[-1]) if stamps else None


def load_tombstones():
    """id -> tombstone record. Content is never stored in a tombstone."""
    tombstones = {}
    if not os.path.isdir(TOMBSTONE_ROOT):
        return tombstones
    for name in sorted(os.listdir(TOMBSTONE_ROOT)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(TOMBSTONE_ROOT, name), encoding="ascii") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    tombstones[entry["id"]] = entry
    return tombstones


def load_source_registry():
    if not os.path.isfile(SOURCE_REGISTRY_PATH):
        return {}
    with open(SOURCE_REGISTRY_PATH, encoding="ascii") as handle:
        return json.load(handle)


def load_profiles():
    """Every profile in config/salience_profiles/ is applied.

    Adding a profile file is how a consumer expresses a different weighting
    without forking records or arguing with anyone else's.
    """
    profiles = []
    for path in sorted(glob.glob(os.path.join(PROFILE_DIR, "*.json"))):
        with open(path, encoding="ascii") as handle:
            profile = json.load(handle)
        rel = profile.get("relevance", {})
        terms = rel.get("terms", [])
        profile["_relevance_re"] = (
            re.compile("|".join(r"\b(?:%s)\b" % t for t in terms), re.IGNORECASE)
            if terms else None
        )
        profiles.append(profile)
    return profiles


def load_id_migrations():
    """old_id -> new_id, for records whose identity moved between dumps.

    An id is a slug of a title, so repairing a title moves the id and every
    verdict recorded against the old one stops matching. That is not a
    hypothetical: it orphaned two of Pip's accepts on 2026-08-22 and the only
    visible symptom was a reviewed count falling 518 -> 516. Migrations are
    curated, evidenced and dated -- see data/curated/id_migrations.json.
    """
    if not os.path.isfile(ID_MIGRATIONS):
        return {}
    with open(ID_MIGRATIONS, encoding="ascii") as handle:
        payload = json.load(handle)
    mapping = {}
    for entry in payload.get("migrations") or []:
        old_id, new_id = entry.get("old_id"), entry.get("new_id")
        if not old_id or not new_id:
            continue
        if old_id in mapping and mapping[old_id] != new_id:
            raise ValueError(
                "id_migrations.json sends %s to two different ids (%s and %s). "
                "An identity claim cannot be ambiguous."
                % (old_id, mapping[old_id], new_id))
        mapping[old_id] = new_id
    return mapping


def load_reviews():
    """id -> list of attributed review entries.

    Reviews are opinions with an author. Storing them unattributed would make
    one person's taste indistinguishable from a source-derived property, and
    a disagreeing consumer would have to fork rather than filter.

    Ids are rewritten through load_id_migrations() on the way in. The curated
    file keeps the id the verdict was ACTUALLY recorded against -- rewriting it
    in place would destroy the record of what was in front of the reviewer --
    and the mapping stays a separate, evidenced, arguable artifact.
    """
    reviews = defaultdict(list)
    layers = []
    if not os.path.isdir(REVIEW_ROOT):
        return reviews, layers
    migrations = load_id_migrations()
    for path in sorted(glob.glob(os.path.join(REVIEW_ROOT, "*.json"))):
        with open(path, encoding="ascii") as handle:
            payload = json.load(handle)
        meta = payload.get("_metadata", {})
        reviewer = meta.get("reviewer") or "unknown"
        count = 0
        for record_id, entry in (payload.get("records") or {}).items():
            if not entry.get("verdict") and not entry.get("tier_override") \
                    and not entry.get("note"):
                continue
            record_id = migrations.get(record_id, record_id)
            reviews[record_id].append({
                "reviewer": entry.get("reviewer") or reviewer,
                "verdict": entry.get("verdict"),
                "tier_override": entry.get("tier_override"),
                "note": entry.get("note"),
                "at": entry.get("at") or entry.get("reviewed_at"),
                "layer": os.path.basename(path),
            })
            count += 1
        layers.append({
            "file": os.path.basename(path),
            "reviewer": reviewer,
            "records": count,
        })
    return reviews, layers


def load_airr_tags():
    """layer_id -> {record_id: tag}. Machine tags are opinions, not facts.

    Kept in their own namespace so a human tagging pass can sit alongside at
    higher precedence without either overwriting the other.
    """
    layers = {}
    meta = []
    if not os.path.isdir(AIRR_TAG_ROOT):
        return layers, meta
    for path in sorted(glob.glob(os.path.join(AIRR_TAG_ROOT, "*.json"))):
        with open(path, encoding="ascii") as handle:
            payload = json.load(handle)
        info = payload.get("_metadata", {})
        layer_id = info.get("layer_id") or os.path.basename(path)
        layers[layer_id] = payload.get("tags") or {}
        meta.append({
            "layer_id": layer_id,
            "file": os.path.basename(path),
            "nature": info.get("nature"),
            "tagged_count": info.get("tagged_count"),
            "evaluation": info.get("evaluation"),
        })
    return layers, meta


def apply_source_registry(record, registry):
    """Stamp source-level facts, recording where each came from."""
    source_id = str(record.get("id", "")).split(":", 1)[0]
    entry = registry.get(source_id)
    if not entry:
        record["_provenance"]["source_available_at"] = {
            "layer": "registry", "method": "source_not_in_registry",
            "confidence": "low",
        }
        return
    available = entry.get("source_available_at")
    record["source_available_at"] = available
    record["_provenance"]["source_available_at"] = {
        "layer": "registry",
        "method": "config/sources.json",
        "confidence": entry.get("confidence", "low") if available else "low",
        "evidence_count": len(entry.get("evidence") or []),
    }


def normalise_urls(record):
    """Rewrite source_urls and archive_urls in place. Returns True if changed.

    The parse itself is _base.split_url_cell, shared with the adapter so the
    two cannot drift. This function is only the in-place application of it.
    """
    changed = False
    for field in ("source_urls", "archive_urls"):
        original = record.get(field) or []
        rebuilt = []
        for element in original:
            rebuilt.extend(_base.split_url_cell(element))
        if rebuilt != original:
            record[field] = rebuilt
            changed = True
    return changed


def apply_source_fallback(record, registry):
    """Give a sourceless record the dataset URL it actually came from.

    Six of 3,434 candidates carried no source at all, for three different
    reasons: four are blank in Epoch AI's own CSV, one lost a schemeless URL to
    the adapter, and one has an author list where the URL should be. A consumer
    could not check any of them against anything.

    The fallback is NOT invented. `config/sources.json` records the dataset the
    record was ingested from, and `license.citation` on every one of these
    records already names that same page in words -- "Epoch AI. Data on Notable
    AI Models. Retrieved from https://epoch.ai/data/notable-ai-models". This
    puts the URL where a consumer can follow it.

    It is a WEAKER source than the others and must not be mistaken for them:
    the other 3,428 records point at a primary paper or announcement, and this
    points at an aggregator. That is why a `_provenance` entry is written for
    `source_urls` naming the method. Presence of that entry is the signal --
    no other record carries one, so a consumer can tell the two apart today
    without waiting for a `source_kind` field to be designed.

    Applied AFTER normalise_urls, so a record whose only URL-shaped value turns
    out to be prose falls back rather than being left empty.
    """
    if record.get("source_urls"):
        return False
    source_id = str(record.get("id", "")).split(":", 1)[0]
    entry = registry.get(source_id) or {}
    url = entry.get("url")
    if not url:
        return False
    record["source_urls"] = [url]
    record["_provenance"]["source_urls"] = {
        "layer": "registry",
        "method": "aggregator_fallback",
        "confidence": "low",
    }
    return True


def topical_relevance(record, profile):
    rel = profile.get("relevance", {})
    if record.get("kind") in (rel.get("kinds_always_relevant") or []):
        return 1.0
    pattern = profile.get("_relevance_re")
    if pattern is None:
        return 1.0
    haystack = " ".join(
        [record.get("title", "") or ""]
        + list((record.get("extra") or {}).get("forum_tags") or [])
        + [(record.get("extra") or {}).get("notability_criteria") or ""]
    ).lower()
    hits = len(set(m.group(0).lower() for m in pattern.finditer(haystack)))
    weights = rel.get("weights", {})
    if hits >= 2:
        return float(weights.get("two_or_more_hits", 1.0))
    if hits == 1:
        return float(weights.get("one_hit", 0.75))
    return float(weights.get("no_hits", 0.25))


def apply_transform(value, name):
    if value is None:
        return None
    if name == "log10":
        return math.log10(value) if value > 0 else None
    if name == "log10_plus1":
        return math.log10(value + 1.0) if value >= 0 else None
    return float(value)


def raw_salience_score(record, profile):
    """Return (score, method) so provenance can say how it was derived."""
    spec = (profile.get("kind_scoring") or {}).get(record.get("kind"))
    if not spec:
        return 0.0, "kind_not_scored_by_profile"

    signals = record.get("signals") or {}

    def latest(name):
        series = signals.get(name) if name else None
        return series[-1].get("value") if series else None

    primary = apply_transform(latest(spec.get("primary_signal")),
                              spec.get("transform", "identity"))
    if primary is not None:
        method = "%s:%s" % (spec.get("primary_signal"), spec.get("transform"))
        bonus_field = spec.get("bonus_field")
        if bonus_field:
            raw = str((record.get("extra") or {}).get(bonus_field, "")).lower()
            if raw in [str(v).lower() for v in (spec.get("bonus_values") or [])]:
                primary += float(spec.get("bonus", 0.0))
                method += "+" + bonus_field
        return primary, method

    fallback = apply_transform(latest(spec.get("fallback_signal")),
                               spec.get("fallback_transform", "identity"))
    if fallback is not None:
        return fallback, "fallback:%s" % spec.get("fallback_signal")

    return 0.0, "no_signal_available"


def percentile_within_group(values):
    """Map each value to its percentile rank in [0,1]. Ties share a rank."""
    ordered = sorted(set(values))
    if len(ordered) <= 1:
        return {value: 0.5 for value in values}
    return {value: index / float(len(ordered) - 1)
            for index, value in enumerate(ordered)}


def score_profile(kept, profile):
    """Compute this profile's salience and tiers. Returns the tier cut points."""
    pid = profile["profile_id"]
    shrinkage_k = float(profile.get("shrinkage_k", 0))

    groups = defaultdict(list)
    for record in kept:
        year = (record.get("published_at") or "____")[:4]
        groups[(record.get("kind"), year)].append(record)

    scored = {}
    for (kind, year), members in groups.items():
        raws = {}
        for record in members:
            score, method = raw_salience_score(record, profile)
            raws[record["id"]] = (score, method)
        lookup = percentile_within_group([v[0] for v in raws.values()])
        shrink = len(members) / float(len(members) + shrinkage_k) if shrinkage_k \
            else 1.0
        for record in members:
            score, method = raws[record["id"]]
            shrunk = 0.5 + (lookup[score] - 0.5) * shrink
            relevance = topical_relevance(record, profile)
            scored[record["id"]] = {
                "salience": round(shrunk * relevance, 4),
                "topical_relevance": relevance,
                "method": method,
                "raw_score": round(score, 4),
                "group": "kind=%s,year=%s" % (kind, year),
                "group_size": len(members),
                "shrinkage": round(shrink, 3),
            }

    ordered = sorted(kept, key=lambda r: -scored[r["id"]]["salience"])
    cuts = {}
    start = 0
    total = len(ordered)
    for name, fraction in profile.get("tier_quantiles", []):
        end = min(total, start + max(1, int(round(fraction * total))))
        for record in ordered[start:end]:
            scored[record["id"]]["tier"] = name
        if end > start:
            cuts[name] = {
                "count": end - start,
                "salience_max": scored[ordered[start]["id"]]["salience"],
                "salience_min": scored[ordered[end - 1]["id"]]["salience"],
            }
        start = end
    for record in ordered[start:]:
        scored[record["id"]]["tier"] = "D"
    if start < total:
        cuts["D"] = {
            "count": total - start,
            "salience_max": scored[ordered[start]["id"]]["salience"],
            "salience_min": scored[ordered[total - 1]["id"]]["salience"],
        }

    for record in kept:
        entry = scored[record["id"]]
        record.setdefault("salience_by_profile", {})[pid] = entry["salience"]
        record.setdefault("salience_tier_by_profile", {})[pid] = entry["tier"]
        record.setdefault("salience_basis_by_profile", {})[pid] = {
            "profile_version": profile.get("version"),
            "method": entry["method"],
            "raw_score": entry["raw_score"],
            "topical_relevance": entry["topical_relevance"],
            "percentile_within": entry["group"],
            "group_size": entry["group_size"],
            "shrinkage": entry["shrinkage"],
            "note": (
                "A weighting choice under profile '%s', not a property of the "
                "record. Add your own profile rather than forking." % pid
            ),
        }
    return cuts


def project(records, tombstones, registry, profiles, reviews, airr_layers):
    """Returns (kept, dropped, cuts_by_profile). Every exclusion is explained."""
    kept = []
    dropped = []

    for record in records:
        if record["id"] in tombstones:
            entry = tombstones[record["id"]]
            dropped.append({
                "id": record["id"],
                "reason": "tombstoned",
                "category": entry.get("category"),
                "tombstoned_at": entry.get("tombstoned_at"),
            })
            continue
        kept.append(dict(record))

    for record in kept:
        apply_source_registry(record, registry)
        normalise_urls(record)
        apply_source_fallback(record, registry)

    cuts_by_profile = {}
    for profile in profiles:
        cuts_by_profile[profile["profile_id"]] = score_profile(kept, profile)

    for record in kept:
        by_layer = {}
        for layer_id, mapping in airr_layers.items():
            hit = mapping.get(record["id"])
            if hit:
                by_layer[layer_id] = hit
        if by_layer:
            record["airr_tags_by_layer"] = by_layer
        record.pop("airr_tags", None)   # empty adapter placeholder
        record["reviews"] = reviews.get(record["id"], [])
        flagged = bool(PRIVACY_RE.search(record.get("title", "") or ""))
        record["privacy_review_required"] = flagged
        if record["reviews"]:
            record["review_status"] = "reviewed"
        elif flagged:
            record["review_status"] = "needs_privacy_review"
        else:
            record["review_status"] = "unreviewed"

    return kept, dropped, cuts_by_profile


VOLATILE_LINEAGE_KEYS = ("built_at",)


def check_against_disk(feed_path, feed_text, lineage_path, lineage_text):
    """Compare a fresh build against committed output. Returns an exit code.

    The feed must match byte for byte. LINEAGE.json is compared with the
    genuinely volatile keys removed -- built_at is a wall-clock stamp and
    changes on every run by design, so demanding equality there would make
    this gate permanently red and therefore ignored.
    """
    problems = []

    if not os.path.isfile(feed_path):
        problems.append("missing %s" % feed_path)
    else:
        on_disk = open(feed_path, encoding="ascii", newline="").read()
        if on_disk != feed_text:
            problems.append(
                "feed differs: %d bytes on disk vs %d rebuilt"
                % (len(on_disk), len(feed_text)))

    if not os.path.isfile(lineage_path):
        problems.append("missing %s" % lineage_path)
    else:
        def strip(text):
            data = json.loads(text)
            for key in VOLATILE_LINEAGE_KEYS:
                data.pop(key, None)
            return json.dumps(data, sort_keys=True)
        if strip(open(lineage_path, encoding="ascii").read()) != strip(lineage_text):
            problems.append("lineage differs (ignoring %s)"
                            % ", ".join(VOLATILE_LINEAGE_KEYS))

    if problems:
        print("CHECK FAILED:")
        for problem in problems:
            print("  - %s" % problem)
        print("Committed output does not match a fresh build. Re-run without "
              "--check and commit the result.")
        return 1
    print("CHECK OK: committed output matches a fresh build "
          "(feed byte-identical; lineage identical ignoring %s)"
          % ", ".join(VOLATILE_LINEAGE_KEYS))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="rebuild and compare against what is on disk; "
                             "exit 1 on drift. Intended as a CI gate.")
    args = parser.parse_args()

    tombstones = load_tombstones()
    registry = load_source_registry()
    profiles = load_profiles()
    reviews, review_layers = load_reviews()
    airr_layers, airr_meta = load_airr_tags()

    if not profiles:
        print("ERROR: no salience profiles in %s" % PROFILE_DIR)
        return 1

    inputs = []
    records = []
    for source_id in SOURCES:
        dump_dir = latest_dump(source_id)
        if dump_dir is None:
            print("SKIP %s: no dump found" % source_id)
            inputs.append({"source_id": source_id, "dump": None, "records": 0})
            continue
        path = os.path.join(dump_dir, "data.jsonl")
        loaded = [json.loads(line) for line in open(path, encoding="ascii")]
        records.extend(loaded)
        inputs.append({
            "source_id": source_id,
            "dump": os.path.relpath(dump_dir, REPO_ROOT).replace("\\", "/"),
            "dump_data_sha256": _base.sha256_file(path),
            "records": len(loaded),
        })
        print("loaded %-18s %5d records" % (source_id, len(loaded)))

    kept, dropped, cuts = project(records, tombstones, registry, profiles,
                                  reviews, airr_layers)

    flagged = sum(1 for r in kept if r["privacy_review_required"])
    reviewed = sum(1 for r in kept if r["reviews"])
    print("---")
    print("input records      : %d" % len(records))
    print("dropped (tombstone): %d" % len(dropped))
    print("kept               : %d" % len(kept))
    print("privacy-flagged    : %d" % flagged)
    print("with human reviews : %d (from %d layer file(s))"
          % (reviewed, len(review_layers)))
    for profile in profiles:
        pid = profile["profile_id"]
        counts = defaultdict(int)
        for record in kept:
            counts[record["salience_tier_by_profile"][pid]] += 1
        print("profile %-12s : %s" % (pid, dict(sorted(counts.items()))))

    if args.dry_run:
        print("dry run; nothing written")
        return 0

    primary = profiles[0]["profile_id"]
    kept.sort(key=lambda r: (-r["salience_by_profile"][primary], r["id"]))

    feed_path = os.path.join(OUT_ROOT, "all_candidates.jsonl")
    feed_text = "".join(
        json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n"
        for record in kept
    )

    by_year = defaultdict(int)
    for record in kept:
        by_year[(record.get("published_at") or "unknown")[:4]] += 1

    lineage = {
        "build_version": BUILD_VERSION,
        "built_at": _base.utc_now_iso(),
        "adapter_framework_version": _base.ADAPTER_FRAMEWORK_VERSION,
        "inputs": inputs,
        "source_registry": {"path": "config/sources.json"},
        "salience_profiles": [
            {"profile_id": p["profile_id"], "version": p.get("version"),
             "status": p.get("status")} for p in profiles
        ],
        "human_review_layers": review_layers,
        "airr_tag_layers": airr_meta,
        "ordering": "file is sorted by profile '%s'; this is presentation only"
                    % primary,
        "counts": {
            "input_records": len(records),
            "dropped": len(dropped),
            "kept": len(kept),
            "privacy_flagged": flagged,
            "with_human_reviews": reviewed,
            "by_year": dict(sorted(by_year.items())),
            "tier_cut_points_by_profile": cuts,
        },
        "dropped_records": dropped,
        "policy": {
            "facts_vs_opinions": (
                "Facts: title, clocks, actors, source_urls, signals, license. "
                "Opinions: salience_by_profile (named weighting) and reviews "
                "(attributed to a named reviewer). No bare salience field and "
                "no game_facing flag, so a disagreeing consumer can ignore "
                "rather than fork."
            ),
            "review": (
                "Reviews are attributed opinions. Consumers may inherit a "
                "reviewer's judgement, filter to reviewers they trust, or "
                "ignore reviews entirely."
            ),
            "privacy": (
                "Raw dumps are immutable except by tombstone; tombstones "
                "record id, date and reason category, never content. "
                "Downstream consumers must honour tombstones."
            ),
            "truncation": (
                "None. Every input record is either kept or listed in "
                "dropped_records with a reason."
            ),
        },
    }
    lineage_path = os.path.join(OUT_ROOT, "LINEAGE.json")
    lineage_text = json.dumps(
        lineage, ensure_ascii=True, indent=2, sort_keys=True) + "\n"

    if args.check:
        return check_against_disk(feed_path, feed_text, lineage_path, lineage_text)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(feed_path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(feed_text)
    with open(lineage_path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(lineage_text)

    print("wrote %s" % os.path.relpath(feed_path, REPO_ROOT))
    print("wrote %s" % os.path.relpath(lineage_path, REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
