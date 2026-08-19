"""Run every check in this repository and report one verdict.

    python scripts/validation/check_all.py
    python scripts/validation/check_all.py --quick    # skip the rebuild checks

The single entry point. If you have just cloned this repository and want to
know whether it is in good order, run this and nothing else.

Two classes of check, and the distinction is deliberate:

  GATING     a failure means something is wrong right now. Exits non-zero.
  REPORTING  information about where the repo stands. Never fails the run.

The maturity ladder is REPORTING by ruling (pdoom-data#62, L4): a collection
legitimately sits at wood while it is being built, and gating on it would only
teach people to route around the ladder.

Dependencies are checked first and named individually, because "ImportError:
No module named yaml" three checks deep is a worse experience than being told
up front which one command fixes it.
"""
import argparse
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (label, argv, gating?)
GATING = [
    ("repository invariants", ["scripts/validation/check_invariants.py"], True),
    ("write-capable workflows de-armed", ["scripts/validation/check_workflow_disarm.py"], True),
    ("evidence supports its claims", ["scripts/validation/check_evidence.py"], True),
    # Ran in data-integrity.yml and NOT here, which is how main went red on
    # 2026-08-10 with a local check_all passing minutes earlier: the corpus
    # proposal landed on main and its accepted-drift entry landed on an
    # unmerged branch. Second instance in one day of "run this and nothing
    # else" being false. The entry point is now the thing CI runs.
    ("references in prose resolve", ["scripts/validation/check_references.py"], True),
    ("no transcoding corruption in derived zones", ["scripts/validation/check_transcoding.py"], True),
    ("no email addresses in tracked zones", ["scripts/privacy/redact_emails.py", "--ci"], True),
    # LLM scan payloads are the one source with no upstream schema and a
    # scanner capable of writing a fluent record for an event that did not
    # happen. This gate does not check that they are TRUE -- it checks they do
    # not overstate what is known: no date without a source, no unsourced
    # record without an UNVERIFIED flag.
    ("scan payloads hold their claim tracking",
     ["scripts/validation/check_scan_claims.py"], True),
    ("privacy gate can still fail", ["tests/test_privacy_gate.py"], True),
    # Same reasoning as the privacy gate. The cross-reference half of
    # check_scan_claims.py currently reports every citation resolving, and a
    # detector that never fires is indistinguishable from one that cannot.
    ("scan cross-reference check fires", ["tests/test_scan_cross_references.py"], True),
    ("dump-space tests", ["tests/test_dump_spaces.py"], True),
    ("migration tests", ["tests/test_migration.py"], True),
    ("transcoding detector fires", ["tests/test_transcoding_detector.py"], True),
]

REBUILD = [
    # The watch list is where judgement lives, so its rebuild has an extra
    # duty: it must carry human fields forward untouched. --check compares
    # only the derived half, which is what lets a rated atom still pass.
    ("watch-list rebuild is byte-identical",
     ["scripts/build/project_watchlist.py", "--check"], True),
    # The dataset-quality counts are quoted in public funding copy, where a
    # reader can check them against the served JSON in thirty seconds. A draft
    # carried "801 descriptions begin Introduction" when the real figure is 35;
    # 801 was 81 percent with the decimal lost. Computed now, so it regenerates
    # rather than rotting.
    ("dataset quality counts match the corpus",
     ["scripts/analysis/dataset_quality.py", "--check"], True),
    # The Watch mechanic's output. Accepted atoms reach a consumer through here
    # and NOT through all_events.json: event_v1 requires impacts, rarity and
    # pdoom_impact, which ADR-001 puts on the wrong side of the boundary
    # (pdoom-data#34), and that file already has exactly one producer.
    ("accepted watch atoms project cleanly",
     ["scripts/build/project_watch_accepted.py", "--check"], True),
    ("candidates rebuild is byte-identical", ["scripts/build/project_candidates.py", "--check"], True),
    ("frontier_labs rebuild is byte-identical", ["scripts/build/project_frontier_labs.py", "--check"], True),
    ("reviewed rebuild is byte-identical", ["scripts/build/project_reviewed.py", "--check"], True),
    # Both of these ran in data-integrity.yml and NOT here, so "run check_all.py
    # and nothing else" was false for two of the five projections -- including
    # the one that guards the timeline_events sidecars. Found 2026-08-10 while
    # giving those sidecars a producer. A single entry point that covers most of
    # the checks is the same defect class as a catalogue that describes most of
    # its collection.
    ("timeline_events rebuild is byte-identical", ["scripts/build/project_timeline_events.py", "--check"], True),
    ("taxonomy rebuild is byte-identical", ["scripts/build/project_taxonomy.py", "--check"], True),
]

REPORTING = [
    ("maturity ladder", ["scripts/validation/check_maturity.py"], False),
]

# module -> what installs it, and what stops working without it.
DEPS = [
    ("yaml", "PyYAML", "the workflow de-arm guard cannot parse workflows"),
    ("jsonschema", "jsonschema", "schema validation is skipped, so bad records pass"),
]


def check_deps():
    missing = []
    for mod, pkg, consequence in DEPS:
        try:
            __import__(mod)
        except ImportError:
            missing.append((pkg, consequence))
    if not missing:
        return True
    print("MISSING DEPENDENCIES")
    for pkg, consequence in missing:
        print("  %-14s without it, %s" % (pkg, consequence))
    print()
    print("  pip install -r requirements-checks.txt")
    print()
    print("Refusing to run: a check that silently skips is worse than one that")
    print("does not run, because the first reports success.")
    return False


def run(label, argv, gating):
    started = time.time()
    try:
        r = subprocess.run([sys.executable] + [os.path.join(REPO_ROOT, argv[0])] + argv[1:],
                           capture_output=True, text=True, cwd=REPO_ROOT, timeout=300)
        ok = r.returncode == 0
        tail = (r.stdout or r.stderr).strip().split("\n")
        detail = tail[-1][:88] if tail and tail[-1] else ""
    except (OSError, subprocess.SubprocessError) as e:
        ok, detail = False, "could not run: %s" % str(e)[:70]
    took = time.time() - started
    mark = "PASS" if ok else ("FAIL" if gating else "----")
    print("  [%s] %-42s %5.1fs  %s" % (mark, label, took, detail))
    return ok


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true",
                    help="skip the rebuild checks, which are the slow ones")
    args = ap.parse_args()

    if not check_deps():
        return 2

    failures = []

    print("GATING -- a failure here means something is wrong now")
    for label, argv, gating in GATING:
        if not run(label, argv, gating):
            failures.append(label)

    if args.quick:
        print()
        print("  (rebuild checks skipped by --quick)")
    else:
        print()
        print("REBUILD -- committed output must match a fresh build")
        for label, argv, gating in REBUILD:
            if not run(label, argv, gating):
                failures.append(label)

    print()
    print("REPORTING -- never fails the run")
    for label, argv, gating in REPORTING:
        run(label, argv, gating)

    print()
    if failures:
        print("FAILED: %d gating check(s) -- %s" % (len(failures), ", ".join(failures)))
        return 1
    print("All gating checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
