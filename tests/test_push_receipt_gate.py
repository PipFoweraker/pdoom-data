#!/usr/bin/env python3
"""Prove check_push_receipt distinguishes "passed" from "never ran".

    python tests/test_push_receipt_gate.py

The live check needs the network and a gh token, so it cannot be a gating
check. Its LOGIC can be, and that is the part that was wrong first time: the
first draft compared workflow names from .github/workflows/ against JOB names
from the commits/<sha>/check-runs endpoint, and reported both workflows missing
on a commit that had run both successfully. A receipt check that cries wolf
gets muted, and a muted check is exactly what it was built to replace.

So the API call is stubbed and the decision logic is exercised directly. The
case that matters most is the empty one -- no runs at all -- because that is
the failure the Actions tab renders as the previous commit's green.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))

import check_push_receipt as cpr  # noqa: E402

CHECKS = [0]
FAILURES = []


def check(condition, message):
    CHECKS[0] += 1
    if condition:
        print("  PASS  %s" % message)
    else:
        print("  FAIL  %s" % message)
        FAILURES.append(message)


def run_with(runs, expected=("Data Integrity", "Docs CI")):
    """Exercise main() against a stubbed API and a stubbed expectation."""
    saved = (cpr.check_runs_for, cpr.expected_workflows, cpr.tip_sha, sys.argv)
    try:
        cpr.check_runs_for = lambda repo, sha: runs
        cpr.expected_workflows = lambda: (list(expected), [])
        cpr.tip_sha = lambda ref: "0" * 40
        sys.argv = ["check_push_receipt.py"]
        return cpr.main()
    finally:
        (cpr.check_runs_for, cpr.expected_workflows,
         cpr.tip_sha, sys.argv) = saved


def done(name, conclusion="success"):
    return {"name": name, "status": "completed",
            "conclusion": conclusion, "event": "push"}


def main():
    print("push receipt: absence must be louder than failure\n")

    print("MUST NOT FIRE")
    check(run_with([done("Data Integrity"), done("Docs CI")]) == 0,
          "both expected workflows completed successfully")
    check(run_with([done("Data Integrity"), done("Docs CI"),
                    done("Some PR-only job")]) == 0,
          "an extra run that is not owed on push does not fail the receipt")
    check(run_with([done("Data Integrity", "skipped"), done("Docs CI")]) == 0,
          "a deliberately skipped workflow is not a failure")

    print("\nMUST FIRE -- and the first is the whole point")
    check(run_with([]) == 1,
          "THE C5 CASE: no runs at all. Absence, which every other surface "
          "renders as the previous commit's green")
    check(run_with([done("Data Integrity")]) == 1,
          "one of two workflows never started")
    check(run_with([done("Data Integrity"), done("Docs CI", "failure")]) == 1,
          "a workflow that completed with failure")
    check(run_with([done("Data Integrity"),
                    {"name": "Docs CI", "status": "in_progress",
                     "conclusion": None, "event": "push"}]) == 1,
          "a workflow still running is not yet a receipt")
    check(run_with([done("Data Integrity"), done("Docs CI", "cancelled")]) == 1,
          "a cancelled workflow is not a receipt")

    print("\nThe name mismatch that broke the first draft")
    check(run_with([done("Assert data and pipeline invariants"),
                    done("Documentation Quality Assurance")]) == 1,
          "JOB names do not satisfy WORKFLOW expectations -- the endpoint "
          "must be actions/runs, not commits/<sha>/check-runs")

    print("\nThe refusal that makes the check meaningful")
    saved = os.environ.get("GITHUB_ACTIONS")
    os.environ["GITHUB_ACTIONS"] = "true"
    raised = None
    try:
        cpr.refuse_inside_actions()
    except SystemExit as exc:
        raised = exc
    finally:
        if saved is None:
            os.environ.pop("GITHUB_ACTIONS", None)
        else:
            os.environ["GITHUB_ACTIONS"] = saved
    check(raised is not None and raised.code == 2,
          "refuses to run inside GitHub Actions, with a distinct exit code")

    os.environ.pop("GITHUB_ACTIONS", None)
    try:
        cpr.refuse_inside_actions()
        outside_ok = True
    except SystemExit:
        outside_ok = False
    check(outside_ok, "and runs happily outside it")

    print("\n%d checks, %d failed" % (CHECKS[0], len(FAILURES)))
    if FAILURES:
        for failure in FAILURES:
            print("  FAILED: %s" % failure)
        return 1
    print("OK: a workflow that never started fails the receipt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
