#!/usr/bin/env python3
"""Project bronze-zone dumps into a candidate feed.

This is a BUILD STEP. Its output is derived and disposable: delete
data/serveable/api/candidates/ and re-run, and you get the same bytes back.
Nothing here is hand-edited. That property is the whole point -- the existing
serveable zone lost it, which is why manifest.json has said 28 events while
all_events.json said 1194 since 2025-12-24.

What it does, in order:
  1. Load the latest dump per source (or an explicit dump via --dump).
  2. Drop tombstoned records (see "Privacy" below).
  3. Screen for possible privacy concerns; flag, never silently delete.
  4. Score salience within kind and year; derive an importance tier.
  5. Stamp review_status; nothing is game-facing until a human flips it.
  6. Emit the feed plus a LINEAGE.json accounting for every input record.

Every record that enters and does not leave is accounted for in LINEAGE.json.
There is no silent truncation anywhere in this file.

Privacy
-------
Raw dumps are immutable, with exactly one exception: content that should not
have been ingested (private individuals, personal circumstances, anything
identifying that serves no analytic purpose). Removal is by tombstone --
data/raw/_tombstones/<source_id>.jsonl records the id, the date, the reason
CATEGORY, and who decided. It never records the content. The audit trail
survives the erasure.

Usage:
    python scripts/build/project_candidates.py
    python scripts/build/project_candidates.py --dry-run
"""

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "adapters"))

import _base  # noqa: E402

BUILD_VERSION = "0.1.0"
RAW_ROOT = os.path.join(REPO_ROOT, "data", "raw")
OUT_ROOT = os.path.join(REPO_ROOT, "data", "serveable", "api", "candidates")
TOMBSTONE_ROOT = os.path.join(RAW_ROOT, "_tombstones")

# Sources this build consumes. Deliberately explicit: a new adapter does not
# silently enter the feed just by existing.
SOURCES = ["epoch_ai", "forum_lesswrong", "forum_eaforum"]

# Tier bands are QUANTILES of the final salience distribution, not absolute
# cut points. Absolute thresholds against a percentile-derived score pile
# almost everything into the bottom band, which makes the review queue useless.
# These sizes are chosen for a human reader: a short A band worth full
# attention, a B band worth skimming, and the rest available but not urgent.
TIER_QUANTILES = [("A", 0.05), ("B", 0.20), ("C", 0.50)]

# Shrinkage constant: a group needs roughly this many members before its
# internal percentile is trusted at full strength.
SHRINKAGE_K = 12

# Terms marking a record as topically relevant to AI safety. Matched on WORD
# BOUNDARIES: plain substring matching makes "ai" hit "training", "domain",
# and "explain", which turns this signal into noise.
# Non-matching records are KEPT (per the data-lake posture) but scored down,
# so they sink in the review queue rather than vanishing from it.
AI_TAG_PATTERNS = [
    r"\bai\b", r"\bagi\b", r"\ba\.i\.", r"\balignment\b", r"\baligned\b",
    r"\binterpretability\b", r"\bmachine learning\b", r"\bml\b",
    r"\blanguage model", r"\bllms?\b", r"\bexistential risk\b", r"\bx-risk\b",
    r"\bcompute\b", r"\bscaling\b", r"\bgovernance\b", r"\bsafety\b",
    r"\bforecasting\b", r"\btakeoff\b", r"\bmesa-?optimi", r"\bdeceptive\b",
    r"\beval(uation)?s?\b", r"\brobustness\b", r"\bsuperintelligence\b",
    r"\btransformer\b", r"\bneural\b", r"\bfrontier model\b", r"\bagent(ic)?\b",
    r"\bdoom\b", r"\bcatastroph", r"\bextinction\b", r"\banthropic\b",
    r"\bopenai\b", r"\bdeepmind\b", r"\bgpt\b", r"\bclaude\b", r"\bllama\b",
]
AI_TAG_RE = re.compile("|".join(AI_TAG_PATTERNS), re.IGNORECASE)

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
                if not line:
                    continue
                entry = json.loads(line)
                tombstones[entry["id"]] = entry
    return tombstones


def topical_relevance(record):
    """0.0 to 1.0. Transparent and separate from salience, not folded into it."""
    # Some sources are AI-by-construction: every row in an AI-models database
    # is on-topic regardless of whether the model's NAME happens to contain a
    # matching word. Keyword scoring only makes sense where topicality is
    # genuinely uncertain, which for now means general-interest forums.
    if record.get("kind") == "model_release":
        return 1.0
    haystack = " ".join(
        [record.get("title", "")]
        + list(record.get("extra", {}).get("forum_tags", []) or [])
        + [record.get("extra", {}).get("notability_criteria") or ""]
    ).lower()
    hits = len(set(match.group(0).lower() for match in AI_TAG_RE.finditer(haystack)))
    if hits >= 2:
        return 1.0
    if hits == 1:
        return 0.75
    return 0.25


def raw_salience_score(record):
    """A within-kind comparable number. Higher is more salient.

    Returns (score, method) so the provenance envelope can say how it was
    derived rather than presenting a bare number as fact.
    """
    kind = record.get("kind")
    signals = record.get("signals") or {}

    def latest(name):
        series = signals.get(name)
        if not series:
            return None
        return series[-1].get("value")

    if kind == "model_release":
        compute = latest("training_compute_flop")
        if compute and compute > 0:
            score = math.log10(compute)
            if str(record.get("extra", {}).get("frontier_model", "")).lower() in (
                "true", "yes", "1"
            ):
                score += 1.0
            return score, "log10_training_compute_plus_frontier_flag"
        citations = latest("citations")
        if citations is not None:
            return math.log10(citations + 1.0), "log_citations_fallback"
        return 0.0, "no_signal_available"

    if kind == "forum_post":
        karma = latest("karma")
        if karma is not None:
            return float(karma), "karma"
        return 0.0, "no_signal_available"

    if kind == "publication":
        citations = latest("citations")
        if citations is not None:
            return math.log10(citations + 1.0), "log_citations"
        return 0.0, "no_signal_available"

    return 0.0, "unscored_kind"


def percentile_within_group(values):
    """Map each value to its percentile rank in [0,1]. Ties share a rank."""
    ordered = sorted(set(values))
    if len(ordered) <= 1:
        return {value: 0.5 for value in values}
    lookup = {}
    for index, value in enumerate(ordered):
        lookup[value] = index / float(len(ordered) - 1)
    return lookup


def assign_tiers(records):
    """Assign A/B/C/D by quantile of the realised salience distribution.

    Returns the cut points so LINEAGE.json can record exactly where the bands
    fell for this build. Tier membership is therefore reproducible and
    explainable rather than a magic constant.
    """
    if not records:
        return {}
    ordered = sorted(records, key=lambda r: -r["salience"])
    total = len(ordered)
    cuts = {}
    start = 0
    for name, fraction in TIER_QUANTILES:
        end = min(total, start + max(1, int(round(fraction * total))))
        for record in ordered[start:end]:
            record["salience_tier"] = name
        if end > start:
            cuts[name] = {
                "count": end - start,
                "salience_max": ordered[start]["salience"],
                "salience_min": ordered[end - 1]["salience"],
            }
        start = end
    for record in ordered[start:]:
        record["salience_tier"] = "D"
    if start < total:
        cuts["D"] = {
            "count": total - start,
            "salience_max": ordered[start]["salience"],
            "salience_min": ordered[total - 1]["salience"],
        }
    return cuts


def project(records, tombstones):
    """Returns (kept, dropped) where dropped explains every exclusion."""
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

    # Salience is relative, so it must be computed per (kind, year) group
    # rather than globally: a 2016 model and a 2026 model are not competing.
    groups = defaultdict(list)
    for record in kept:
        year = (record.get("published_at") or "____")[:4]
        groups[(record.get("kind"), year)].append(record)

    for (kind, year), members in groups.items():
        scores = []
        for record in members:
            score, method = raw_salience_score(record)
            record["_salience_raw"] = score
            record["_salience_method"] = method
            scores.append(score)
        lookup = percentile_within_group(scores)
        # Shrink toward 0.5 when the group is small. Without this, the top
        # member of a 2-record group scores a perfect 1.0 on the strength of
        # one comparison, and a 2001 decision-tree model outranks Alignment
        # Faking. Standard regularisation: trust the observed percentile in
        # proportion to how much evidence produced it.
        shrink = len(members) / float(len(members) + SHRINKAGE_K)
        for record in members:
            percentile = lookup[record["_salience_raw"]]
            shrunk = 0.5 + (percentile - 0.5) * shrink
            relevance = topical_relevance(record)
            record["salience"] = round(shrunk * relevance, 4)
            record["topical_relevance"] = relevance
            record["salience_shrinkage"] = round(shrink, 3)
            record["salience_basis"] = {
                "method": record.pop("_salience_method"),
                "raw_score": round(record.pop("_salience_raw"), 4),
                "percentile_within": "kind=%s,year=%s" % (kind, year),
                "group_size": len(members),
                "note": (
                    "salience = percentile * topical_relevance. This measures "
                    "estimated importance, NOT source quality. It is a "
                    "candidate-ordering signal, not an editorial verdict."
                ),
            }

    tier_cuts = assign_tiers(kept)

    for record in kept:
        flagged = bool(PRIVACY_RE.search(record.get("title", "") or ""))
        record["privacy_review_required"] = flagged
        record["review_status"] = "needs_privacy_review" if flagged else "unreviewed"
        record["game_facing"] = False

    return kept, dropped, tier_cuts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tombstones = load_tombstones()
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

    kept, dropped, tier_cuts = project(records, tombstones)

    tier_counts = defaultdict(int)
    for record in kept:
        tier_counts[record["salience_tier"]] += 1
    flagged = sum(1 for r in kept if r["privacy_review_required"])

    print("---")
    print("input records      : %d" % len(records))
    print("dropped            : %d" % len(dropped))
    print("kept               : %d" % len(kept))
    print("privacy-flagged    : %d" % flagged)
    print("tiers              : %s" % dict(sorted(tier_counts.items())))
    print("game-facing        : 0 (nothing promotes without human review)")

    if args.dry_run:
        print("dry run; nothing written")
        return 0

    os.makedirs(OUT_ROOT, exist_ok=True)
    kept.sort(key=lambda r: (-(r["salience"]), r["id"]))

    feed_path = os.path.join(OUT_ROOT, "all_candidates.jsonl")
    with open(feed_path, "w", encoding="ascii", newline="\n") as handle:
        for record in kept:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")

    by_year = defaultdict(list)
    for record in kept:
        by_year[(record.get("published_at") or "unknown")[:4]].append(record["id"])

    lineage = {
        "build_version": BUILD_VERSION,
        "built_at": _base.utc_now_iso(),
        "adapter_framework_version": _base.ADAPTER_FRAMEWORK_VERSION,
        "inputs": inputs,
        "counts": {
            "input_records": len(records),
            "dropped": len(dropped),
            "kept": len(kept),
            "privacy_flagged": flagged,
            "game_facing": 0,
            "by_tier": dict(sorted(tier_counts.items())),
            "tier_cut_points": tier_cuts,
            "by_year": {y: len(ids) for y, ids in sorted(by_year.items())},
        },
        "dropped_records": dropped,
        "policy": {
            "salience": (
                "percentile within (kind, year) times topical_relevance; "
                "measures estimated importance, not source quality"
            ),
            "review": (
                "every record is review_status=unreviewed or "
                "needs_privacy_review; game_facing is false for all records "
                "and only a human review pass may flip it"
            ),
            "privacy": (
                "raw dumps are immutable except by tombstone; tombstones "
                "record id, date, and reason category, never content"
            ),
            "truncation": "none; every input record is either kept or listed in dropped_records",
        },
    }
    lineage_path = os.path.join(OUT_ROOT, "LINEAGE.json")
    with open(lineage_path, "w", encoding="ascii", newline="\n") as handle:
        json.dump(lineage, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")

    print("wrote %s" % os.path.relpath(feed_path, REPO_ROOT))
    print("wrote %s" % os.path.relpath(lineage_path, REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
