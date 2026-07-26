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


def check_manifests():
    """Hashes are computed over LF. With core.autocrlf=true and no
    .gitattributes rule, a fresh clone would check these out as CRLF and every
    verification would fail on a machine other than the one that wrote them."""
    ok = bad = 0
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
            if h.hexdigest() == digest:
                ok += 1
            else:
                bad += 1
                failures.append("hash mismatch: %s" % path)
    notes.append("manifest entries verified: %d ok, %d bad" % (ok, bad))


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
