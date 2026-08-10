#!/usr/bin/env python3
"""Assert the properties this repo claims about itself.

Every check here exists because something actually went wrong once. This file
is the session's lessons in executable form: prose in a README decays quietly,
an assertion fails loudly.

    python scripts/validation/check_invariants.py

Exits 1 if any invariant is violated. Safe to run anywhere, writes nothing.
Intended as a CI gate once the workflows are repaired -- see the note in
docs/SESSION_2026-07-26_FORWARD_FILL.md about why that is not yet done.
"""

import glob
import hashlib
import json
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FEED = os.path.join(REPO_ROOT, "data", "serveable", "api", "candidates",
                    "all_candidates.jsonl")
TOMBSTONE_ROOT = os.path.join(REPO_ROOT, "data", "raw", "_tombstones")

# Paths added by the forward-fill work, which are ASCII-clean and must stay so.
ASCII_GUARDED = [
    "scripts/adapters", "scripts/build", "scripts/enrichment",
    "scripts/validation/check_invariants.py",
    "config/sources.json", "config/salience_profiles",
    "docs/ADAPTER_SPEC.md", "docs/CONSUMER_GUIDE.md",
    "docs/PDOOM1_INTEGRATION_BRIEF.md", "tools/review_queue.html",
]

failures = []
notes = []


def check(condition, message):
    if condition:
        return True
    failures.append(message)
    return False


def load_feed():
    if not os.path.isfile(FEED):
        notes.append("no candidate feed present; feed checks skipped")
        return []
    return [json.loads(line) for line in open(FEED, encoding="ascii")]


def check_ids_unique(records):
    """Cost of getting this wrong: PointNet++ and PointNet shared an id, so a
    consumer keying by id silently lost one, and an attributed review would
    have landed on the wrong record."""
    seen = {}
    dupes = []
    for record in records:
        rid = record.get("id")
        if rid in seen:
            dupes.append(rid)
        seen[rid] = True
    check(not dupes, "duplicate ids in feed: %r" % dupes[:5])


def check_licences(records):
    """No record may travel without its terms, and ShareAlike is excluded by
    repo policy rather than by anyone remembering to check."""
    missing = [r["id"] for r in records if not (r.get("license") or {}).get("spdx")]
    check(not missing, "records with no licence spdx: %r" % missing[:5])
    sa = [r["id"] for r in records
          if "-SA" in str((r.get("license") or {}).get("spdx", "")).upper()]
    check(not sa, "ShareAlike records present, excluded by policy: %r" % sa[:5])


def check_opinions_namespaced(records):
    """A bare `salience` reads as a property of the record rather than as one
    weighting among many, and would force a disagreeing consumer to fork."""
    bare = [r["id"] for r in records if "salience" in r or "salience_tier" in r]
    check(not bare, "bare salience field found (must be by-profile): %r" % bare[:5])
    gf = [r["id"] for r in records if "game_facing" in r]
    check(not gf, "game_facing flag found; promotion is the consumer's call: %r"
          % gf[:5])


def check_reviews_attributed(records):
    """An unattributed verdict makes one person's taste indistinguishable from
    a source-derived fact."""
    bad = []
    for record in records:
        for review in record.get("reviews") or []:
            if not review.get("reviewer"):
                bad.append(record["id"])
    check(not bad, "unattributed reviews: %r" % bad[:5])


def check_clocks(records):
    """Absent is different from null. Null means ungated and known-unknown; a
    missing key means nobody thought about it."""
    for clock in ("occurred_at", "published_at", "source_available_at"):
        missing = [r["id"] for r in records if clock not in r]
        check(not missing, "records missing clock %s: %r" % (clock, missing[:3]))


def check_tombstones_honoured(records):
    """The one non-optional obligation in the consumer contract."""
    if not os.path.isdir(TOMBSTONE_ROOT):
        return
    tombstoned = set()
    for path in glob.glob(os.path.join(TOMBSTONE_ROOT, "*.jsonl")):
        for line in open(path, encoding="ascii"):
            line = line.strip()
            if line:
                tombstoned.add(json.loads(line)["id"])
    leaked = [r["id"] for r in records if r["id"] in tombstoned]
    check(not leaked, "TOMBSTONED RECORDS PRESENT IN FEED: %r" % leaked[:5])


def load_tombstoned_hashes():
    """path -> (tombstone_id, sha256_after_redaction).

    A privacy tombstone is the ONLY sanctioned exception to raw-zone
    immutability. It records the post-redaction digest of every file it
    touched, which is what lets a manifest mismatch be accepted without
    weakening the control:

      - the MANIFEST entry keeps the ORIGINAL hash, as proof of what the file
        was before anyone touched it
      - the tombstone records what it became, and why, and on whose authority
      - a file whose hash matches neither is still a hard failure

    So raw remains effectively immutable. Editing it without writing an
    attributable tombstone still fails a build; writing one is a deliberate,
    reviewable act rather than a silent hash bump.
    """
    mapping = {}
    tomb_dir = os.path.join(REPO_ROOT, "data", "privacy", "tombstones")
    for tomb_path in sorted(glob.glob(os.path.join(tomb_dir, "*.json"))):
        try:
            with open(tomb_path, encoding="utf-8") as f:
                tomb = json.load(f)
        except (ValueError, OSError):
            failures.append("unreadable tombstone: %s" % tomb_path)
            continue
        tid = tomb.get("tombstone_id", os.path.basename(tomb_path))
        for entry in tomb.get("affected", []):
            digest = entry.get("sha256_after_redaction")
            rel = entry.get("file")
            if digest and rel:
                mapping[os.path.normpath(os.path.join(REPO_ROOT, rel))] = (tid, digest)
    return mapping


def check_manifests():
    """Hashes are computed over LF. With core.autocrlf=true and no
    .gitattributes rule, a fresh clone would check these out as CRLF and every
    verification would fail on a machine other than the one that wrote them."""
    tombstoned = load_tombstoned_hashes()
    ok = bad = redacted = 0
    for manifest in glob.glob(os.path.join(REPO_ROOT, "data", "raw", "*",
                                           "dumps", "*", "MANIFEST.sha256")):
        base = os.path.dirname(manifest)
        for line in open(manifest, encoding="ascii"):
            digest, name = line.strip().split("  ")
            path = os.path.join(base, name)
            if not os.path.isfile(path):
                failures.append("manifest references missing file: %s" % path)
                continue
            h = hashlib.sha256()
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(65536), b""):
                    h.update(chunk)
            actual = h.hexdigest()
            if actual == digest:
                ok += 1
                continue
            claim = tombstoned.get(os.path.normpath(path))
            if claim and claim[1] == actual:
                redacted += 1
                continue
            bad += 1
            if claim:
                failures.append(
                    "hash mismatch AND tombstone disagrees: %s\n"
                    "      tombstone %s records a different post-redaction "
                    "digest. The file has been modified since it was "
                    "tombstoned." % (path, claim[0]))
            else:
                failures.append("hash mismatch: %s" % path)
    notes.append("manifest entries verified: %d ok, %d bad, %d redacted "
                 "under tombstone" % (ok, bad, redacted))


def check_ascii():
    """The repo is ASCII-only. Writing a replacement table with literal
    unicode, then 'fixing' it with an ascii-mode open that truncates on error,
    cost this session two files."""
    offenders = []
    for target in ASCII_GUARDED:
        full = os.path.join(REPO_ROOT, target)
        paths = []
        if os.path.isdir(full):
            for root, _dirs, files in os.walk(full):
                if "__pycache__" in root:
                    continue
                paths.extend(os.path.join(root, f) for f in files)
        elif os.path.isfile(full):
            paths.append(full)
        for path in paths:
            try:
                open(path, encoding="ascii").read()
            except (UnicodeDecodeError, ValueError):
                offenders.append(os.path.relpath(path, REPO_ROOT))
    check(not offenders, "non-ASCII in guarded paths: %r" % offenders[:5])


def check_registry_evidence():
    """A date without evidence is a guess wearing a fact's clothes."""
    path = os.path.join(REPO_ROOT, "config", "sources.json")
    if not os.path.isfile(path):
        return
    registry = json.load(open(path, encoding="ascii"))
    for key, entry in registry.items():
        if key.startswith("_"):
            continue
        if entry.get("source_available_at") and not entry.get("evidence"):
            failures.append("source %s has a date but no evidence entry" % key)


def check_landmine_guarded():
    """clean_events.py used to run its full destructive pipeline on any
    invocation, including --help."""
    path = os.path.join(REPO_ROOT, "scripts", "transformation", "clean_events.py")
    if not os.path.isfile(path):
        return
    body = open(path, encoding="utf-8").read()
    check("--write" in body and "REFUSING TO RUN" in body,
          "clean_events.py has lost its safety guard; it rewrites the "
          "serveable zone on any invocation")


# Count disagreements that are KNOWN, ACCEPTED and TRACKED.
#
# Same shape as the tombstone exception to raw-zone immutability: a divergence
# is tolerated only when someone has written down what it is and where it is
# being fixed. Anything not listed here fails.
#
# These are not "wontfix". Each is a real defect with an open issue; the entry
# exists so the check can be turned on TODAY, catching any NEW drift, without
# a pre-existing problem blocking every build until it is fixed. Delete an
# entry when its issue closes -- and the check will then start enforcing it.
# EMPTIED 2026-08-10, and kept as an empty dict rather than deleted, because the
# mechanism is still the right one and the next divergence should have to be
# declared here in a commit rather than discovered in production.
#
# It held three entries for nine months: manifest.json, stats.json and
# event_index.json each claiming 28 records against all_events.json's 1,194.
# Every one was true, documented, printed on every run, and passing.
#
# That is the shape Workshop 2 named as its own class 5, the KNOWING ALLOWLIST:
# a check that sees the defect perfectly and is configured to permit it. It
# defeats every remedy the estate proposed that week -- arming it does nothing
# because it is armed, re-aiming does nothing because it is aimed correctly, a
# freshness window does nothing because it is current. The check was never
# fooled. The reader was, by its exit code.
#
# The three files now have a producer (project_timeline_events.py builds them
# from the feed, and --check asserts byte-identity), so the entries are removed
# rather than updated. An entry added here should carry a return date, or it
# becomes what these were.
KNOWN_COUNT_DIVERGENCES = {}


def check_timeline_event_counts():
    """Do the timeline_events catalogue files agree with the data?

    This zone had NO invariant coverage until 2026-08-01, which is how a
    three-way disagreement -- manifest.json saying 28, MANIFEST.json saying
    1194, all_events.json holding 1194 -- survived in a collection that backs
    2,194 published pages.

    The check is deliberately about internal agreement rather than about any
    particular number being right. A catalogue that disagrees with the thing it
    catalogues is wrong whichever side is stale, and that is cheap to detect.
    """
    base = os.path.join(REPO_ROOT, "data", "serveable", "api", "timeline_events")
    main_path = os.path.join(base, "all_events.json")
    if not os.path.isfile(main_path):
        failures.append("timeline_events/all_events.json is missing")
        return

    try:
        with open(main_path, encoding="utf-8") as handle:
            events = json.load(handle)
    except ValueError as exc:
        failures.append("timeline_events/all_events.json does not parse: %s" % exc)
        return

    actual = len(events) if isinstance(events, (dict, list)) else 0
    notes.append("timeline_events records: %d" % actual)

    # Every catalogue file that claims a count must match, or be registered.
    for name, keys in (("manifest.json", ("total_events", "count")),
                       ("stats.json", ("total_events", "count")),
                       ("event_index.json", None)):
        path = os.path.join(base, name)
        if not os.path.isfile(path):
            continue
        rel = os.path.relpath(path, REPO_ROOT).replace("\\", "/")
        try:
            with open(path, encoding="utf-8") as handle:
                doc = json.load(handle)
        except ValueError:
            failures.append("%s does not parse" % rel)
            continue

        claimed = None
        if keys:
            for key in keys:
                if isinstance(doc, dict) and key in doc:
                    claimed = doc[key]
                    break
        elif isinstance(doc, (dict, list)):
            claimed = len(doc)

        if claimed is None or claimed == actual:
            continue

        if rel in KNOWN_COUNT_DIVERGENCES:
            notes.append("KNOWN divergence, %s: claims %s vs %d actual -- %s"
                         % (rel, claimed, actual, KNOWN_COUNT_DIVERGENCES[rel]))
        else:
            failures.append(
                "%s claims %s records but all_events.json holds %d. A "
                "catalogue that disagrees with what it catalogues is wrong "
                "whichever side is stale. If this divergence is known and "
                "tracked, register it in KNOWN_COUNT_DIVERGENCES with its "
                "issue number." % (rel, claimed, actual))


def main():
    records = load_feed()
    if records:
        notes.append("feed records: %d" % len(records))
        check_ids_unique(records)
        check_licences(records)
        check_opinions_namespaced(records)
        check_reviews_attributed(records)
        check_clocks(records)
        check_tombstones_honoured(records)
    check_manifests()
    check_timeline_event_counts()
    check_ascii()
    check_registry_evidence()
    check_landmine_guarded()

    for note in notes:
        print("  note: %s" % note)
    if failures:
        print("\nINVARIANTS VIOLATED (%d):" % len(failures))
        for failure in failures:
            print("  - %s" % failure)
        return 1
    print("\nAll invariants hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
