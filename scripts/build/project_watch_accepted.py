#!/usr/bin/env python3
"""Project accepted watch-list atoms into a served collection.

    python scripts/build/project_watch_accepted.py            # write
    python scripts/build/project_watch_accepted.py --check     # assert committed

WHY THIS IS A SEPARATE COLLECTION AND NOT `all_events.json`

The Watch mechanic is: a thing happens, it goes on Watch for the month, and at
month end it is decided and the decision is published with reasons. Until now
the decision had nowhere to go -- 93 atoms sat in `data/curated/watchlist/` with
no route to any consumer, which makes the whole mechanic a private opinion.

The obvious destination is `all_events.json`. It is the wrong one, twice over.

**First, `event_v1` demands the fields ADR-001 says do not belong here.** Its
`required` list is id, title, year, category, description, **impacts**, sources,
tags, **rarity**, **pdoom_impact**, **safety_researcher_reaction**,
**media_reaction** -- and `additionalProperties: false`, so a record cannot be
partially conformant. Promoting an atom into that schema means inventing a
cash delta, a rarity tier and a p(doom) impact for a real-world event on the
strength of nothing. CLAUDE.md is explicit that those fields are a known breach,
tracked as `pdoom-data#34`, and that no more of that kind may be added meanwhile.
Promoting 93 events through that schema would multiply the breach by four.

**Second, `all_events.json` has exactly one producer and that was hard won.**
`project_timeline_events.py` is it. The zone previously had none, was hand-edited
because it could not be rebuilt, and `clean_events.py` once collapsed it from
1,194 records to 28. Adding a second writer to that file is the specific mistake
this repository has already paid seven months for.

So accepted atoms are served on their own, in a neutral shape: what happened,
when, who said so, and who decided. No impacts, no rarity, no p(doom) delta, no
reaction text. **A consumer that wants an event to cost the player thirty cash
computes that itself** -- which is ADR-001's operative test, since a consumer who
disagreed with our weighting would otherwise have to fork the data rather than
ignore a field.

WHAT CANNOT BE PROMOTED, AND WHY THE GATE IS THE POINT

An atom must carry a date, at least one source, and a named decider. Those are
not tidiness:

  * **No date** -- the whole collection is a timeline. `pdoom-data` has never
    guessed a date and will not start at the moment of publication; 19 of the 93
    are null on purpose because sources disagreed or only a month was known.
  * **No source** -- three atoms are flagged UNVERIFIED by the scanners that
    proposed them. Serving an unsourced claim as an accepted event is exactly
    the fluent-and-wrong failure the scan gate exists to catch.
  * **No named decider** -- ADR-001 permits no anonymous verdicts. `accepted`
    means one named person accepted it, and the name travels with the record so
    a consumer can filter on reviewers it trusts.

An atom that fails a gate is REPORTED, not silently dropped. A promotion path
that quietly discards a human's decision is worse than one that refuses.
"""

import argparse
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WATCHLIST = os.path.join(REPO, "data", "curated", "watchlist", "candidates.jsonl")
OUT_DIR = os.path.join(REPO, "data", "serveable", "api", "watch")
OUT = os.path.join(OUT_DIR, "accepted.jsonl")
LINEAGE = os.path.join(OUT_DIR, "lineage.json")

# Fields a promoted record carries. Deliberately neutral: every one is a fact
# about the world or about who decided, and none is a weighting.
SERVED_FIELDS = (
    "id", "title", "occurred_at", "date_kind", "description", "why_it_matters",
    "sources", "primary_source_retrieved", "scan_confidence", "scan_flags",
    "scans", "accepted_by", "accepted_on", "decision_note", "watching_since",
)


def load_atoms():
    if not os.path.isfile(WATCHLIST):
        return None
    with open(WATCHLIST, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def gate(atom):
    """Reasons this atom may not be served. Empty list means promotable."""
    blocked = []
    if not atom.get("date"):
        blocked.append("no date -- this collection is a timeline, and a "
                       "guessed clock cannot be told from a real one later")
    if not atom.get("sources"):
        blocked.append("no source -- flagged UNVERIFIED by the scan that "
                       "proposed it; serving it would publish an unchecked claim")
    if not atom.get("decided_by"):
        blocked.append("no named decider -- ADR-001 permits no anonymous "
                       "verdicts")
    return blocked


def promote(atom):
    return {
        "id": atom["id"],
        "title": atom["title"],
        "occurred_at": atom["date"],
        "date_kind": atom["date_kind"],
        "description": atom["description"],
        "why_it_matters": atom.get("why_it_matters"),
        "sources": list(atom.get("sources") or []),
        "primary_source_retrieved": atom.get("primary_source_retrieved"),
        "scan_confidence": atom.get("scan_confidence"),
        "scan_flags": list(atom.get("scan_flags") or []),
        "scans": list(atom.get("scans") or []),
        "accepted_by": atom.get("decided_by"),
        "accepted_on": atom.get("decided_on"),
        "decision_note": atom.get("decision_note"),
        "watching_since": atom.get("watching_since"),
    }


def build():
    atoms = load_atoms()
    if atoms is None:
        return None, None, ["no watch list at %s" % os.path.relpath(WATCHLIST, REPO)]

    accepted = [a for a in atoms if a.get("watch_status") == "accepted"]
    served, blocked = [], []
    for atom in sorted(accepted, key=lambda a: (a.get("date") or "", a["id"])):
        reasons = gate(atom)
        if reasons:
            blocked.append((atom["id"], reasons))
        else:
            served.append(promote(atom))

    counts = {}
    for atom in atoms:
        state = atom.get("watch_status") or "undecided"
        counts[state] = counts.get(state, 0) + 1

    lineage = {
        "build_version": "0.1.0",
        "producer": "scripts/build/project_watch_accepted.py",
        "source": "data/curated/watchlist/candidates.jsonl",
        "record_count": len(served),
        "watch_status_counts": counts,
        "blocked_from_promotion": [
            {"id": i, "reasons": r} for i, r in blocked],
        "_shape": ("Neutral. No impacts, rarity, pdoom_impact or reaction text. "
                   "This collection is NOT event_v1 and does not claim to be -- "
                   "event_v1 requires those fields, and ADR-001 says they are on "
                   "the wrong side of the boundary (pdoom-data#34)."),
        "_for_consumers": ("Promotion into a game remains your call. 'accepted' "
                           "means one named person accepted this into "
                           "pdoom-data's curated set. It does not mean verified, "
                           "endorsed, or game-ready, and there is no game_facing "
                           "flag here."),
    }
    return served, lineage, []


def serialise(served, lineage):
    body = "".join(json.dumps(r, ensure_ascii=True, sort_keys=True) + "\n"
                   for r in served)
    meta = json.dumps(lineage, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    return body, meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    served, lineage, problems = build()
    if problems:
        for p in problems:
            sys.stderr.write("%s\n" % p)
        return 2

    body, meta = serialise(served, lineage)

    if args.check:
        for path, fresh in ((OUT, body), (LINEAGE, meta)):
            name = os.path.relpath(path, REPO)
            if not os.path.isfile(path):
                print("CHECK FAILED: %s does not exist" % name)
                return 1
            with open(path, encoding="utf-8") as fh:
                if fh.read() != fresh:
                    print("CHECK FAILED: %s disagrees with the watch list" % name)
                    return 1
        print("CHECK OK: %d accepted atom(s) served; %d blocked from promotion."
              % (len(served), len(lineage["blocked_from_promotion"])))
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    for path, fresh in ((OUT, body), (LINEAGE, meta)):
        with open(path, "w", encoding="ascii", newline="\n") as fh:
            fh.write(fresh)

    print("wrote %s" % os.path.relpath(OUT, REPO))
    print("  watch_status: %s"
          % ", ".join("%s %d" % kv
                      for kv in sorted(lineage["watch_status_counts"].items())))
    print("  served: %d" % len(served))
    if lineage["blocked_from_promotion"]:
        print("  BLOCKED, accepted but not servable -- these are decisions that "
              "cannot be published yet, not records to forget:")
        for row in lineage["blocked_from_promotion"]:
            print("    %s" % row["id"])
            for reason in row["reasons"]:
                print("      - %s" % reason)
    else:
        print("  blocked: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
