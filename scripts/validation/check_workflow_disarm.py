"""Assert that the write-capable workflows stay de-armed.

Why this exists
---------------
Two workflows in this repository can commit to the repository:

    data-pipeline-automation.yml   runs clean_events.py, rewrites data/serveable/
    weekly-data-refresh.yml        extracts to data/raw/, which is immutable

Both were, until 2026-07-30, inert only because of a YAML syntax error. Anyone
who repaired the syntax -- a reasonable thing to do when asked to "fix the
broken CI" -- would have armed a bot that rewrites the serveable zone from
1,194 records to 28 on the next push touching data/raw/.

The repair landed together with a trigger de-arm. But a de-arm that lives only
in a YAML comment is one careless edit from being undone, and the person who
undoes it will not have read the comment. So the constraint is asserted here
instead, where it fails a build.

This does not claim the workflows are correct. It claims only that they cannot
run unattended.

Re-arming, deliberately
-----------------------
Remove the workflow from DISARMED below, in the same commit that arms it, with
the reasoning in the commit message. That makes arming a visible, reviewable
act rather than a side effect.
"""
import io
import os
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "check_workflow_disarm: PyYAML is required.\n"
        "  pip install pyyaml\n"
    )
    sys.exit(3)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")

# workflow filename -> why it must not run unattended
DISARMED = {
    "data-pipeline-automation.yml":
        "stage 2A runs clean_events.py, which rewrites data/serveable/ and "
        "auto-commits; the canonical producer for that zone is unsettled",
    "weekly-data-refresh.yml":
        "auto-commits extracted data into data/raw/, a zone whose contract "
        "says dumps are immutable and re-runs produce new dumps",
}

# Triggers that fire without a human deciding to fire them.
UNATTENDED = ("push", "schedule", "pull_request", "pull_request_target",
              "issue_comment", "repository_dispatch")

failures = []
notes = []


def trigger_keys(doc):
    """Return the trigger names for a parsed workflow.

    PyYAML resolves the unquoted key `on` to the boolean True under YAML 1.1
    -- the same class of surprise as the Norway problem, where `no` becomes
    False. GitHub Actions reads YAML 1.2, where `on` stays a string. So the
    key can arrive either way and both must be tried.
    """
    trig = doc.get("on")
    if trig is None:
        trig = doc.get(True)
    if trig is None:
        return None
    if isinstance(trig, dict):
        return sorted(trig.keys())
    if isinstance(trig, list):
        return sorted(str(t) for t in trig)
    return [str(trig)]


def main():
    if not os.path.isdir(WORKFLOW_DIR):
        print("no .github/workflows directory; nothing to check")
        return 0

    present = set(os.listdir(WORKFLOW_DIR))

    for name, reason in sorted(DISARMED.items()):
        if name not in present:
            notes.append("%s is listed as de-armed but no longer exists "
                         "(renamed or deleted?)" % name)
            continue

        path = os.path.join(WORKFLOW_DIR, name)
        text = io.open(path, encoding="utf-8").read()

        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as e:
            failures.append("%s does not parse as YAML: %s"
                            % (name, str(e).splitlines()[0]))
            continue

        if not isinstance(doc, dict):
            failures.append("%s did not parse to a mapping" % name)
            continue

        keys = trigger_keys(doc)
        if keys is None:
            failures.append("%s has no trigger block at all" % name)
            continue

        armed = [k for k in keys if k in UNATTENDED]
        if armed:
            failures.append(
                "%s is ARMED on %s.\n"
                "      Why this is guarded: %s.\n"
                "      If arming is intended, remove the entry from DISARMED in\n"
                "      %s in the same commit."
                % (name, "/".join(armed), reason,
                   os.path.relpath(__file__, REPO_ROOT).replace("\\", "/")))
        else:
            print("ok   %-32s triggers: %s" % (name, ", ".join(keys) or "(none)"))

    # Every workflow must parse, de-armed or not. A file that does not parse is
    # a workflow whose triggers cannot be reasoned about.
    for name in sorted(present):
        if not name.endswith((".yml", ".yaml")):
            continue
        path = os.path.join(WORKFLOW_DIR, name)
        try:
            yaml.safe_load(io.open(path, encoding="utf-8").read())
        except yaml.YAMLError as e:
            failures.append("%s does not parse as YAML: %s"
                            % (name, str(e).splitlines()[0]))

    for n in notes:
        print("note: " + n)

    if failures:
        print()
        for f in failures:
            print("FAIL: " + f)
        return 1

    print("\nAll write-capable workflows are de-armed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
