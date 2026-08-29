#!/usr/bin/env python3
"""Prove check_review_targets can FAIL, and fails on the right things.

    python tests/test_review_targets_gate.py

A gate that cannot fail is worse than no gate, because it reports green. This
repository has shipped three of them -- `blog_manager` validated the wrong
thing and said it passed for eleven months, and three maturity-ladder
predicates could not fail. So the guard gets must-fire cases before it gets
trusted.

Each case builds a throwaway feed, review layer and migration file on disk and
runs the checker's own functions against them. Nothing here reads the real
corpus: a gate tested only against data that currently passes is a gate tested
against one sample.
"""

import io
import json
import os
import shutil
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))

import check_review_targets as crt  # noqa: E402

CHECKS = [0]
FAILURES = []


def check(condition, message):
    CHECKS[0] += 1
    if condition:
        print("  PASS  %s" % message)
    else:
        print("  FAIL  %s" % message)
        FAILURES.append(message)


def scenario(tmp, served, review_records, migrations):
    """Point the checker at a synthetic corpus and return its exit code."""
    feed = os.path.join(tmp, "all_candidates.jsonl")
    with io.open(feed, "w", encoding="utf-8", newline="\n") as handle:
        for record_id in served:
            handle.write(json.dumps({"id": record_id}) + "\n")

    review_dir = os.path.join(tmp, "human_review")
    if os.path.isdir(review_dir):
        shutil.rmtree(review_dir)
    os.makedirs(review_dir)
    payload = {"_metadata": {"reviewer": "Test Reviewer"},
               "records": review_records}
    with io.open(os.path.join(review_dir, "layer.json"), "w",
                 encoding="ascii", newline="\n") as handle:
        handle.write(json.dumps(payload))

    mig_path = os.path.join(tmp, "id_migrations.json")
    with io.open(mig_path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(json.dumps({"migrations": migrations}))

    crt.FEED, crt.REVIEW_ROOT, crt.MIGRATIONS = feed, review_dir, mig_path
    return crt.main()


ACCEPT = {"verdict": "accept", "reviewer": "Test Reviewer", "at": "2026-01-01"}


def main():
    print("review-targets gate: must fire, and must not over-fire\n")
    tmp = tempfile.mkdtemp(prefix="review_targets_")
    saved = (crt.FEED, crt.REVIEW_ROOT, crt.MIGRATIONS)
    try:
        print("MUST NOT FIRE -- these are healthy corpora")
        check(scenario(tmp, ["a:1", "a:2"], {"a:1": ACCEPT}, []) == 0,
              "a verdict on a record that exists passes")
        check(scenario(tmp, ["a:1"], {}, []) == 0,
              "no verdicts at all passes")
        check(scenario(tmp, ["a:new"], {"a:old": ACCEPT},
                       [{"old_id": "a:old", "new_id": "a:new"}]) == 0,
              "a verdict carried across a DECLARED migration passes")
        check(scenario(tmp, ["a:1"], {"a:1": {"note": "no verdict, just a note"}},
                       []) == 0,
              "a note-only entry is still a substantive record and resolves")

        print("\nMUST FIRE -- each of these is a real loss")
        check(scenario(tmp, ["a:2"], {"a:1": ACCEPT}, []) == 1,
              "THE 2026-08-22 CASE: an id vanished and the verdict orphaned")
        check(scenario(tmp, ["a:other"], {"a:old": ACCEPT},
                       [{"old_id": "a:old", "new_id": "a:new"}]) == 1,
              "a migration pointing at an id that is not in the feed fires")
        check(scenario(tmp, [], {"a:1": ACCEPT}, []) == 1,
              "an empty feed with verdicts outstanding fires")
        check(scenario(tmp, ["a:1", "a:2"], {"a:1": ACCEPT, "a:3": ACCEPT},
                       []) == 1,
              "one good verdict does not mask one orphaned verdict")

        print("\nAn entry with nothing substantive is not a verdict")
        check(scenario(tmp, ["a:1"], {"a:missing": {"verdict": None,
                                                    "tier_override": None,
                                                    "note": None}}, []) == 0,
              "an empty entry pointing nowhere does NOT fire -- it was never judgement")
    finally:
        crt.FEED, crt.REVIEW_ROOT, crt.MIGRATIONS = saved
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n%d checks, %d failed" % (CHECKS[0], len(FAILURES)))
    if FAILURES:
        for failure in FAILURES:
            print("  FAILED: %s" % failure)
        return 1
    print("OK: the gate fires on undeclared loss and stays quiet on declared moves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
