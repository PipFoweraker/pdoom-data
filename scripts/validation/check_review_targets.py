"""Every attributed human verdict must land on a record that still exists.

WHY THIS EXISTS. On 2026-08-22 an adapter repaired two corrupted titles. A
title is slugified into an id, so both ids moved, and the two accepts Pip had
recorded against the old ids stopped matching anything. Nothing failed. The
rebuild checks passed, because the committed output genuinely did match a fresh
build -- a fresh build of the corpus that had quietly lost them. The only
visible symptom was the reviewed feed going from 518 records to 516, two lines
in a file of five hundred, and it was found by counting rather than by any gate.

`data/curated/` is defined in CLAUDE.md as human judgement that is NOT
reproducible: delete it and someone has to decide again. A verdict that no
longer points at anything has been deleted in every sense that matters, and it
is the one kind of loss this repository cannot rebuild its way out of.

THE CHECK TAKES ITS INPUT FROM OUTSIDE THE THING IT CHECKS, which is the rule
`pdoom1#1075` states and the reason this is not merely another rebuild
assertion. It reads the curated review layers -- files a human wrote, that no
build produces -- and asserts each id resolves in the served feed, which a
build does produce. Neither artifact can make the other agree with it. A
projection bug cannot hide from this by being self-consistent, because the
expectation was never derived from the projection.

An id that has legitimately moved is not an error: it is declared in
data/curated/id_migrations.json with evidence and a decider, and this check
follows the same mapping the projection does. What it refuses is an
UNDECLARED disappearance.
"""

import io
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
REVIEW_ROOT = os.path.join(REPO_ROOT, "data", "curated", "human_review")
MIGRATIONS = os.path.join(REPO_ROOT, "data", "curated", "id_migrations.json")
FEED = os.path.join(REPO_ROOT, "data", "serveable", "api", "candidates",
                    "all_candidates.jsonl")


def load_migrations():
    if not os.path.isfile(MIGRATIONS):
        return {}
    with io.open(MIGRATIONS, encoding="ascii") as handle:
        payload = json.load(handle)
    return {e["old_id"]: e["new_id"]
            for e in (payload.get("migrations") or [])
            if e.get("old_id") and e.get("new_id")}


def served_ids():
    ids = set()
    with io.open(FEED, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                ids.add(json.loads(line)["id"])
    return ids


def verdicts():
    """(record_id, reviewer, layer_filename) for every substantive entry."""
    out = []
    if not os.path.isdir(REVIEW_ROOT):
        return out
    for name in sorted(os.listdir(REVIEW_ROOT)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(REVIEW_ROOT, name)
        with io.open(path, encoding="ascii") as handle:
            payload = json.load(handle)
        reviewer = (payload.get("_metadata") or {}).get("reviewer") or "unknown"
        for record_id, entry in (payload.get("records") or {}).items():
            if not entry.get("verdict") and not entry.get("tier_override") \
                    and not entry.get("note"):
                continue
            out.append((record_id, entry.get("reviewer") or reviewer, name))
    return out


def main():
    if not os.path.isfile(FEED):
        print("no served candidates feed at %s; build it first" % FEED)
        return 1

    ids = served_ids()
    migrations = load_migrations()
    rows = verdicts()

    orphans = []
    migrated = 0
    for record_id, reviewer, layer in rows:
        target = migrations.get(record_id, record_id)
        if target != record_id:
            migrated += 1
        if target not in ids:
            orphans.append((record_id, target, reviewer, layer))

    # A migration that points at nothing is its own defect: it asserts an
    # identity that the corpus does not contain, which is a claim we can check
    # and therefore must.
    dangling = sorted(new for old, new in migrations.items() if new not in ids)

    if orphans or dangling:
        print("CHECK FAILED: human judgement points at records that do not exist.")
        for record_id, target, reviewer, layer in sorted(orphans):
            via = "" if target == record_id else " (migrated to %s)" % target
            print("  %s%s -- verdict by %s in %s" % (record_id, via, reviewer, layer))
        for new_id in dangling:
            print("  id_migrations.json sends a verdict to %s, which is not in "
                  "the feed" % new_id)
        print("")
        print("If a title was repaired and the slug moved, declare it in")
        print("data/curated/id_migrations.json with evidence and a decider.")
        print("If the record genuinely left upstream, tombstone it -- do NOT")
        print("add a migration to keep the count up.")
        return 1

    print("review targets: %d attributed verdict(s) across %d record(s) all "
          "resolve in the served feed; %d carried across a declared id "
          "migration" % (len(rows), len({r[0] for r in rows}), migrated))
    return 0


if __name__ == "__main__":
    sys.exit(main())
