"""Assert the month-end decision pass records what it claims, and refuses what it should.

    python tests/test_decide_watch.py

Why this exists
---------------
Until 2026-08-21 NOTHING in this repository could set `watch_status` to
`accepted`. The triage pass has four keys and they map to `watching`,
`watching`, `rejected` and undecided. `project_watch_accepted.py` was written,
tested and wired into CI to serve accepted atoms, and no tool could produce one
-- which is the whole reason `api/watch/accepted.jsonl` has held zero records
since it was created. The mechanic had a front half and no back half.

This pass is the back half, and it is the point in the system where a named
human's judgement becomes a published fact. Three things therefore have to hold,
and each is a case below:

  1. **No anonymous verdicts.** `--by` is required by argparse, so the failure
     is at the command line rather than in the data. Asserted anyway, because
     the day someone gives it a default is the day that stops being true.
  2. **No unexplained decisions.** Accept and reject both block on a reason.
     `decision_note` has been null on every atom since the field existed, and a
     reason that is optional is a reason that is absent.
  3. **No decision recorded that cannot be served.** Accepting an atom with no
     date or no source produces a record `project_watch_accepted.py` will block.
     The pass says so first and requires confirmation.

Every case drives the REAL loop over a temporary watch list. None of them touch
`data/curated/watchlist/`, and the last case asserts that.
"""
import io
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "review"))

import triage_watch as tw  # noqa: E402

REAL_WATCHLIST = tw.WATCHLIST
REAL_LOG = tw.LOG


def atom(aid, **over):
    """An atom in the shape project_watchlist.py emits."""
    base = {
        "id": aid,
        "slug": aid,
        "title": "Title for " + aid,
        "date": "2026-08-01",
        "date_kind": "action",
        "description": "A description.",
        "sources": ["https://example.org/" + aid],
        "why_it_matters": "Because.",
        "scan_confidence": "high",
        "scan_flags": [],
        "scans": ["2026-08-14_governance"],
        "primary_source_retrieved": True,
        "possible_duplicate_of": [],
        "watch_status": "watching",
        "watching_since": "2026-08-15",
        "decided_on": None,
        "decided_by": None,
        "decision_note": None,
        "rating": "A",
        "cleared_for": None,
        "note": None,
    }
    base.update(over)
    return base


def drive(atoms, keystrokes, extra_argv=()):
    """Run the real decide loop over a temp watch list. Returns (rows, log)."""
    tmp = tempfile.mkdtemp()
    old_argv, old_stdin, old_stdout = sys.argv, sys.stdin, sys.stdout
    try:
        tw.WATCHLIST = os.path.join(tmp, "candidates.jsonl")
        tw.LOG = os.path.join(tmp, "triage_log.jsonl")
        with io.open(tw.WATCHLIST, "w", encoding="ascii", newline="\n") as fh:
            for a in atoms:
                fh.write(json.dumps(a, ensure_ascii=True, sort_keys=True) + "\n")

        sys.argv = ["triage_watch.py", "--by", "Test Reviewer", "--decide"]
        sys.argv.extend(extra_argv)
        sys.stdin = io.StringIO("\n".join(keystrokes) + "\n")
        sys.stdout = io.StringIO()
        try:
            tw.main()
        finally:
            captured = sys.stdout.getvalue()
            sys.stdout = old_stdout

        rows = [json.loads(l) for l in
                io.open(tw.WATCHLIST, encoding="utf-8") if l.strip()]
        log = []
        if os.path.isfile(tw.LOG):
            log = [json.loads(l) for l in
                   io.open(tw.LOG, encoding="utf-8") if l.strip()]
        return {r["id"]: r for r in rows}, log, captured
    finally:
        sys.argv, sys.stdin, sys.stdout = old_argv, old_stdin, old_stdout
        tw.WATCHLIST, tw.LOG = REAL_WATCHLIST, REAL_LOG
        shutil.rmtree(tmp, ignore_errors=True)


def check(name, condition, detail=""):
    return [] if condition else ["  %s%s" % (name, (" -- " + detail) if detail else "")]


def run_cases():
    out = []

    # 1. accept with a reason
    rows, log, _ = drive([atom("a1")], ["y", "clearly in scope", "q"])
    r = rows["a1"]
    out += check("accept sets watch_status", r["watch_status"] == "accepted",
                 repr(r["watch_status"]))
    out += check("accept names the decider", r["decided_by"] == "Test Reviewer",
                 repr(r["decided_by"]))
    out += check("accept dates the decision", bool(r["decided_on"]))
    out += check("accept records the reason",
                 r["decision_note"] == "clearly in scope", repr(r["decision_note"]))
    out += check("accept is logged", any(e.get("pass") == "decide" for e in log))
    out += check("the log keeps the PRIOR state, not just the new one",
                 log[0]["prev"]["watch_status"] == "watching",
                 json.dumps(log[0].get("prev")))

    # 2. reject with a reason
    rows, _, _ = drive([atom("a2")], ["x", "out of scope", "q"])
    r = rows["a2"]
    out += check("reject sets watch_status", r["watch_status"] == "rejected")
    out += check("reject records the reason", r["decision_note"] == "out of scope")
    out += check("reject names the decider", r["decided_by"] == "Test Reviewer")

    # 3. an empty reason does not record a decision; it re-prompts
    rows, _, _ = drive([atom("a3")], ["y", "", "second thoughts", "q"])
    r = rows["a3"]
    out += check("an empty reason is refused, then accepted on retry",
                 r["watch_status"] == "accepted"
                 and r["decision_note"] == "second thoughts",
                 "%s / %r" % (r["watch_status"], r["decision_note"]))

    # 4. '-' abandons the atom rather than recording an empty reason
    rows, log, _ = drive([atom("a4")], ["y", "-", "q"])
    r = rows["a4"]
    out += check("'-' leaves the atom on Watch", r["watch_status"] == "watching",
                 repr(r["watch_status"]))
    out += check("'-' records nothing in the log", not log, json.dumps(log))

    # 5. keep watching clears any earlier decision fields
    rows, _, _ = drive([atom("a5", decided_on="2026-08-01",
                             decided_by="Someone Else")], ["k", "q"])
    r = rows["a5"]
    out += check("keep-watching stays watching", r["watch_status"] == "watching")
    out += check("keep-watching clears a stale decider",
                 r["decided_by"] is None and r["decided_on"] is None,
                 "%r / %r" % (r["decided_by"], r["decided_on"]))

    # 6. accepting an ungateable atom warns and, unconfirmed, changes nothing
    rows, log, text = drive([atom("a6", date=None)], ["y", "n", "q"])
    r = rows["a6"]
    out += check("an undated accept is warned about",
                 "WILL NOT SERVE IT" in text)
    out += check("an unconfirmed gated accept changes nothing",
                 r["watch_status"] == "watching" and not log,
                 "%s / %d log entries" % (r["watch_status"], len(log)))

    # 7. ...and confirmed, it IS recorded, because refusing a human's decision
    #    silently is worse than recording one the build will report as blocked
    rows, _, _ = drive([atom("a7", sources=[])],
                       ["y", "y", "accepting despite the gap", "q"])
    out += check("a confirmed gated accept is recorded",
                 rows["a7"]["watch_status"] == "accepted",
                 repr(rows["a7"]["watch_status"]))

    # 8. an atom never triaged is not swept into the month-end pass
    rows, log, text = drive([atom("a8", watch_status=None)], ["y", "why", "q"])
    out += check("an untriaged atom is not decidable",
                 rows["a8"]["watch_status"] is None and not log,
                 repr(rows["a8"]["watch_status"]))
    out += check("...and the pass says what to run instead",
                 "Nothing on Watch to decide" in text)

    # 9. the derived half is never rewritten
    rows, _, _ = drive([atom("a9")], ["y", "fine", "q"])
    src = atom("a9")
    derived = ("title", "date", "description", "sources", "scans",
               "scan_confidence", "possible_duplicate_of")
    same = all(rows["a9"][k] == src[k] for k in derived)
    out += check("decisions do not touch derived fields", same)

    # 10. no anonymous verdicts, asserted at the parser
    old = sys.argv
    try:
        sys.argv = ["triage_watch.py", "--decide"]
        raised = False
        try:
            tw.main()
        except SystemExit:
            raised = True
        except Exception:
            raised = True
        out += check("--by is required", raised)
    finally:
        sys.argv = old

    return out


def check_real_data_untouched(before):
    after = io.open(REAL_WATCHLIST, encoding="utf-8").read()
    if after != before:
        return ["  THE REAL WATCH LIST WAS MODIFIED BY THIS TEST"]
    return []


def main():
    before = io.open(REAL_WATCHLIST, encoding="utf-8").read()
    failures = run_cases()
    failures += check_real_data_untouched(before)
    if failures:
        print("DECIDE PASS FAILED")
        for f in failures:
            print(f)
        return 1
    print("decide pass: accept, reject, keep, empty-reason refusal, abandon, "
          "gate warning, untriaged exclusion, derived-field safety and the "
          "no-anonymous-verdict rule all hold; real watch list untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
