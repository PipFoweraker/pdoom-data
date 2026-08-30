"""Assert that the tip of a branch carries a COMPLETED run -- from outside Actions.

    python scripts/validation/check_push_receipt.py
    python scripts/validation/check_push_receipt.py --ref origin/main --repo PipFoweraker/pdoom-data

WHY THIS EXISTS. From this seat's sealed Workshop 2 position (docs/workshop-2/
position.md, 2026-08-09, merged as pdoom-data#97):

    pdoom-data's main has not been CI-verified for 69 hours, and the reason is
    not that a check failed. Two merge commits produced NO check runs at all.
    Every surface a reader consults -- the Actions tab, `gh run list`, the last
    recorded conclusion -- shows green, because green is what the PREVIOUS run
    said and nothing distinguishes "passed" from "never ran".

That was the C5 bet and nothing was built for it. This is it. A workflow can
fail to trigger for reasons that produce no artifact at all: a YAML error above
the trigger, a disabled workflow, a skipped merge commit, an Actions outage, a
billing stop. Absence is the failure mode, and absence is invisible to every
tool that reads the last conclusion.

THE TWO CLAUSES, both of which a naive version fails.

1. OBSERVE THE ACTUAL STATE, not a proxy. The state is "does a completed run
   exist for THIS EXACT SHA" -- not "was the last run green", which is a
   different commit's answer wearing this commit's clothes.

2. DO NOT DERIVE WHAT TO LOOK FOR FROM THE SYSTEM BEING CHECKED. The list of
   workflows that OUGHT to have run is read from the committed
   .github/workflows/*.yml, which git holds. Whether they DID run is read from
   the GitHub API. Neither source can make the other agree with it. Asking the
   API "what ran?" and then asserting those runs passed is the inverted form:
   it cannot see a workflow that never started, which is the whole defect.

AND IT REFUSES TO RUN INSIDE GITHUB ACTIONS. That refusal is load-bearing, not
hygiene. A receipt check executing as a workflow step is a system reporting on
its own liveness: the run that would prove absence is the run that did not
happen, so it is not there to report anything. This must be invoked from a
seat, a cron on a machine, or another repository.
"""

import argparse
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")


def refuse_inside_actions():
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        sys.stderr.write(
            "check_push_receipt refuses to run inside GitHub Actions.\n"
            "\n"
            "This check exists to detect a workflow that NEVER STARTED. Run as a\n"
            "workflow step it can only execute when the workflow did start, so it\n"
            "would pass in exactly the cases it was built to catch, and would be\n"
            "absent -- reporting nothing -- in the failure it is looking for.\n"
            "\n"
            "Invoke it from a seat, a cron on a machine, or another repository.\n")
        raise SystemExit(2)


def expected_workflows():
    """Workflow names that a push to a branch OUGHT to start.

    Read from the committed YAML, which is the artifact git holds, so the
    expectation does not come from the API being questioned. Parsed with a
    narrow regex rather than a YAML library because this repo pins no YAML
    dependency and the shape needed is two lines.
    """
    names = []
    unnamed = []
    if not os.path.isdir(WORKFLOW_DIR):
        return names, unnamed
    for filename in sorted(os.listdir(WORKFLOW_DIR)):
        if not filename.endswith((".yml", ".yaml")):
            continue                      # .disabled and friends are not armed
        path = os.path.join(WORKFLOW_DIR, filename)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        block = re.search(r"^on:(.*?)(?=^\S)", text, re.M | re.S)
        if not block or not re.search(r"^\s+push:", block.group(1), re.M):
            continue                      # dispatch-only or PR-only: not owed
        name = re.search(r"^name:\s*(.+)$", text, re.M)
        if name:
            names.append(name.group(1).strip().strip("'\""))
        else:
            unnamed.append(filename)
    return names, unnamed


def tip_sha(ref):
    out = subprocess.run(["git", "rev-parse", ref], cwd=REPO_ROOT,
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("cannot resolve %s: %s" % (ref, out.stderr.strip()))
    return out.stdout.strip()


def check_runs_for(repo, sha):
    """Every WORKFLOW run GitHub holds for this exact commit.

    Deliberately the actions/runs endpoint and not commits/<sha>/check-runs.
    check-runs reports JOB names -- "Assert data and pipeline invariants" --
    while .github/workflows/ declares WORKFLOW names -- "Data Integrity". The
    first draft of this file compared the two and reported both workflows
    missing on a commit that had run both successfully. A receipt check that
    cries wolf gets muted, and a muted check is the thing it was built to
    replace.
    """
    out = subprocess.run(
        ["gh", "api", "--paginate",
         "repos/%s/actions/runs?head_sha=%s" % (repo, sha),
         "--jq", ".workflow_runs[] | {name, status, conclusion, event}"],
        cwd=REPO_ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("gh api failed for %s@%s:\n%s"
                         % (repo, sha[:12], out.stderr.strip()))
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def main():
    refuse_inside_actions()
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="origin/main",
                        help="the ref whose tip must carry a receipt")
    parser.add_argument("--repo", default="PipFoweraker/pdoom-data")
    args = parser.parse_args()

    expected, unnamed = expected_workflows()
    sha = tip_sha(args.ref)
    runs = check_runs_for(args.repo, sha)

    print("%s tip %s" % (args.ref, sha[:12]))
    print("expected on push (from .github/workflows/): %s"
          % (", ".join(expected) or "none"))

    problems = []
    for filename in unnamed:
        problems.append("%s triggers on push but declares no `name:`, so no "
                        "receipt can be matched to it" % filename)

    by_name = {}
    for run in runs:
        by_name.setdefault(run["name"], []).append(run)

    if not runs:
        problems.append(
            "NO workflow run of ANY kind exists for this commit. This is the "
            "'never ran' case: the Actions tab and `gh run list` will still "
            "show the PREVIOUS commit's green.")

    for name in expected:
        got = by_name.get(name)
        if not got:
            problems.append("%r: no run for this commit -- it did not start, "
                            "which is not the same as failing" % name)
            continue
        incomplete = [r for r in got if r["status"] != "completed"]
        failed = [r for r in got
                  if r["status"] == "completed"
                  and r["conclusion"] not in ("success", "skipped", "neutral")]
        if incomplete:
            problems.append("%r: still %s -- no receipt yet"
                            % (name, incomplete[0]["status"]))
        elif failed:
            problems.append("%r: completed with conclusion %r"
                            % (name, failed[0]["conclusion"]))
        else:
            print("  receipt: %-38s %s" % (name, got[0]["conclusion"]))

    extra = sorted(set(by_name) - set(expected))
    if extra:
        print("  also ran (not owed on push): %s" % ", ".join(extra))

    if problems:
        print("\nCHECK FAILED: the tip of %s does not carry a full receipt."
              % args.ref)
        for problem in problems:
            print("  - %s" % problem)
        return 1

    print("\nreceipt OK: every push-triggered workflow has a completed, "
          "non-failing run against this exact commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
