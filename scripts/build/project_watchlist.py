#!/usr/bin/env python3
"""Project the LLM scan payloads into watch-list atoms.

    python scripts/build/project_watchlist.py           # build
    python scripts/build/project_watchlist.py --check   # assert committed

Why this exists
---------------
The scan payloads in data/raw/llm_event_scan/payloads/ are immutable records
of what four machine scans SAID. They are the right shape for provenance and
the wrong shape for work: nothing in them can be rated, cleared, or decided,
because a bronze dump must never be edited.

So this is the layer where judgement lives. One atom per candidate event,
carrying the scan's claims as DERIVED fields and Pip's decisions as HUMAN
fields. Posts, sheets and any eventual promotion become projections over a
selection of atoms -- the same relation build outputs have to curated data
everywhere else in this repo.

The mechanic it is built for is Pip's, in his words: a thing happens, it goes
on Watch for the month, and at month end it is decided and the decision is
published with reasons. `watch_status` is exactly that state, and nothing may
infer it.

The rebuild rule that makes this safe
-------------------------------------
A rebuild MERGES human fields forward by id and never overwrites them. That is
not a convenience; it is the difference between a layer you can put judgement
into and one that eats it. --check compares only the derived half, so an atom
with a rating still passes.

If a candidate DISAPPEARS from the payloads while carrying a human decision,
the build refuses rather than silently dropping the decision. Bronze is
immutable, so that should be impossible -- which is exactly why it is worth
failing loudly if it ever happens.

What this deliberately does NOT do
----------------------------------
**It does not deduplicate.** Three or more events appear in two payloads under
DIFFERENT slugs, because two scanners described the same thing differently.
Merging them is a judgement about identity -- sometimes obvious, sometimes not:
kimi_k3 appears twice and those are two genuinely different events, a model
release and a sandbox escape. So near-duplicates are FLAGGED in
`possible_duplicate_of` and left for a human. A wrong auto-merge destroys a
record and looks like tidiness.

**It adds no game-facing fields.** No impacts, no rarity, no salience, no
`game_facing`. ADR-001: promotion is the consumer's call. `watch_status:
accepted` means one named person accepted it into pdoom-data's curated set. It
does not mean it is in a game, and pdoom1 remains free to ignore it.
"""

import argparse
import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PAYLOADS = os.path.join(REPO, "data", "raw", "llm_event_scan", "payloads")
OUT_DIR = os.path.join(REPO, "data", "curated", "watchlist")
OUT = os.path.join(OUT_DIR, "candidates.jsonl")

# Fields this script owns. --check compares exactly these.
DERIVED = ("id", "slug", "title", "date", "date_kind", "description",
           "sources", "why_it_matters", "scan_confidence", "scan_flags",
           "scans", "primary_source_retrieved", "possible_duplicate_of")

# Fields a human owns. Carried forward untouched on every rebuild, and never
# inferred, defaulted to a meaningful value, or repaired.
HUMAN = {
    # null | "watching" | "accepted" | "rejected"
    "watch_status": None,
    # ISO date the item went on Watch
    "watching_since": None,
    # ISO date the decision was made
    "decided_on": None,
    # the named person who decided. No anonymous verdicts, per ADR-001.
    "decided_by": None,
    # why. A decision without a reason cannot be argued with later.
    "decision_note": None,
    # Pip's own tier, free text. Set once, and every projection follows.
    "rating": None,
    # list of platforms, or null for "not yet ruled on". Null is NOT consent.
    "cleared_for": None,
    # a human's note, distinct from the scanner's flags
    "note": None,
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "its", "it",
    "at", "by", "with", "over", "after", "as", "is", "are", "first", "new",
    "ai", "us", "own",
}


def tokens(text):
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def find_near_duplicates(records):
    """Flag likely same-event pairs. Conservative, and never merges.

    Three signals, any of which flags a pair:
      * strong TITLE overlap (Jaccard >= 0.50);
      * moderate title overlap (>= 0.30) with dates within three days;
      * an explicit cross-reference: one record's scan flags name the other's
        slug.

    Similarity is computed on TITLES ONLY, and that is the whole lesson of the
    first version. It mixed in the first 160 characters of description, which
    DILUTED the strongest signal available: the two Hugging Face records have
    a 0.88 title similarity and scored 0.36 once descriptions were included --
    under the threshold. The detector reported zero duplicates across 93 atoms
    and looked like it had done its job. Descriptions add tokens faster than
    they add agreement, so they hurt a set-overlap measure.

    The third signal exists because similarity alone cannot catch everything.
    "US applies export controls to a domestic frontier model" and "US order
    bars foreign nationals from Fable 5 and Mythos 5" are the same event and
    share ZERO title tokens. No lexical measure will ever link them. But a
    human writing the payload already noticed and said so in a flag, so the
    cheapest reliable signal is to read what the scanners wrote down rather
    than to re-derive it.

    Weak heuristics are correct here because the output is a FLAG for a human,
    not an action. A missed pair costs a duplicate in a review queue; a wrong
    merge destroys a record and looks like tidiness.
    """
    flags = {r["id"]: set() for r in records}
    known_slugs = {r["slug"] for r in records}
    items = list(records)

    # Signal 3, first: explicit cross-references written into the payloads.
    for record in records:
        blob = " ".join(record["scan_flags"] or [])
        for slug in re.findall(r"[a-z0-9]+(?:_[a-z0-9]+){2,}", blob):
            if slug in known_slugs and slug != record["slug"]:
                flags[record["id"]].add(slug)
                flags[slug].add(record["id"])

    for i, left in enumerate(items):
        left_tokens = tokens(left["title"])
        for right in items[i + 1:]:
            right_tokens = tokens(right["title"])
            if not left_tokens or not right_tokens:
                continue
            overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)

            close_dates = False
            if left["date"] and right["date"]:
                try:
                    from datetime import date
                    ld = date(*[int(p) for p in left["date"].split("-")])
                    rd = date(*[int(p) for p in right["date"].split("-")])
                    close_dates = abs((ld - rd).days) <= 3
                except (ValueError, TypeError):
                    close_dates = False

            if overlap >= 0.50 or (overlap >= 0.30 and close_dates):
                flags[left["id"]].add(right["id"])
                flags[right["id"]].add(left["id"])

    for record in records:
        found = sorted(flags[record["id"]])
        record["possible_duplicate_of"] = found or None


def derive():
    if not os.path.isdir(PAYLOADS):
        sys.stderr.write("no payload directory at %s\n" % PAYLOADS)
        return None

    records = []
    by_slug = {}
    for name in sorted(os.listdir(PAYLOADS)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(PAYLOADS, name), encoding="utf-8") as handle:
            payload = json.load(handle)
        scan_id = payload["scan_id"]
        for row in payload["records"]:
            slug = row["slug"]
            if slug in by_slug:
                # Identical slug in two payloads means two scanners made the
                # SAME claim under the same name. That is corroboration, so the
                # scans are merged onto one atom and both sources kept.
                existing = by_slug[slug]
                existing["scans"] = sorted(set(existing["scans"] + [scan_id]))
                for url in row.get("sources") or []:
                    if url not in existing["sources"]:
                        existing["sources"].append(url)
                for flag in row.get("flags") or []:
                    if flag not in existing["scan_flags"]:
                        existing["scan_flags"].append(flag)
                continue
            record = {
                "id": slug,
                "slug": slug,
                "title": row["title"],
                "date": row["date"],
                "date_kind": row["date_kind"],
                "description": row["description"],
                "sources": list(row.get("sources") or []),
                "why_it_matters": row.get("why_it_matters"),
                "scan_confidence": row["confidence"],
                "scan_flags": list(row.get("flags") or []),
                "scans": [scan_id],
                "primary_source_retrieved": row.get("primary_source_retrieved"),
                "possible_duplicate_of": None,
            }
            by_slug[slug] = record
            records.append(record)

    records.sort(key=lambda r: r["id"])
    find_near_duplicates(records)
    return records


def load_existing():
    if not os.path.isfile(OUT):
        return {}
    existing = {}
    with open(OUT, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                existing[row["id"]] = row
    return existing


def merge_human(records, existing):
    """Carry human fields forward. Never overwrite, never infer.

    Returns (records, orphans) where orphans are ids that carry a human
    decision but no longer appear in the payloads.
    """
    for record in records:
        prior = existing.get(record["id"], {})
        for field, default in HUMAN.items():
            record[field] = prior.get(field, default)

    live = {r["id"] for r in records}
    orphans = []
    for record_id, prior in existing.items():
        if record_id in live:
            continue
        if any(prior.get(field) not in (None, [], "") for field in HUMAN):
            orphans.append(record_id)
    return records, orphans


def serialise(records):
    return "".join(json.dumps(r, ensure_ascii=True, sort_keys=True) + "\n"
                   for r in records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    records = derive()
    if records is None:
        return 2

    existing = load_existing()
    records, orphans = merge_human(records, existing)

    if orphans:
        sys.stderr.write(
            "REFUSING: %d atom(s) carry a human decision but no longer appear "
            "in any payload: %s\n"
            "  Bronze is immutable, so this should be impossible. Something "
            "edited a dump. Do not rebuild until it is understood -- "
            "rebuilding would discard those decisions.\n"
            % (len(orphans), ", ".join(sorted(orphans)[:5])))
        return 1

    fresh = serialise(records)

    if args.check:
        if not os.path.isfile(OUT):
            print("CHECK FAILED: %s does not exist" % os.path.relpath(OUT, REPO))
            return 1
        with open(OUT, encoding="utf-8") as handle:
            committed = handle.read()

        def project(blob):
            out = []
            for line in blob.splitlines():
                if line.strip():
                    row = json.loads(line)
                    out.append({k: row.get(k) for k in DERIVED})
            return out

        if project(committed) != project(fresh):
            print("CHECK FAILED: committed watch-list disagrees with the "
                  "payloads on a derived field")
            return 1
        decided = sum(1 for line in committed.splitlines() if line.strip()
                      and json.loads(line).get("watch_status"))
        print("CHECK OK: %d atoms, derived fields match the payloads "
              "(%d carry a human watch_status, preserved)"
              % (len(records), decided))
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="ascii", newline="\n") as handle:
        handle.write(fresh)

    dupes = sum(1 for r in records if r["possible_duplicate_of"])
    undated = sum(1 for r in records if not r["date"])
    unsourced = sum(1 for r in records if not r["sources"])
    carried = sum(1 for r in records if any(
        r.get(f) not in (None, [], "") for f in HUMAN))

    print("wrote %s" % os.path.relpath(OUT, REPO))
    print("  %d atoms from %d payload(s)"
          % (len(records), len({s for r in records for s in r["scans"]})))
    print("  %d flagged as possible duplicates (NOT merged -- a human decides)"
          % dupes)
    print("  %d with a null date, %d with no source at all" % (undated, unsourced))
    print("  %d carry a human field, preserved across this rebuild" % carried)
    print("  watch_status is null on every new atom. Nothing infers it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
