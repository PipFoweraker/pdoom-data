"""Assert that each maturity-ladder predicate can return False.

    python tests/test_maturity_predicates.py

Why this exists
---------------
L2 of the ladder ruling says every rung is a measurable predicate, never a
judgement call, and the test applied when writing them was "could two people who
dislike each other agree whether it passes, without talking?". That test does
not catch a predicate that says yes to everyone. Three did, and they sat in the
file that enforces L2:

  1. `p_contract_test` searched tests/ AND scripts/validation/ for the words
     "contract" and the collection name -- and scripts/validation/ contains
     check_maturity.py, whose own predicate label is the string "consumer-
     contract test exists" and whose COLLECTIONS dict names all four
     collections. It matched itself for every collection from the day L4
     shipped and COULD NOT FAIL. `frontier_labs` was reported GOLD on that
     basis, including in a briefing to Pip on the morning of 2026-08-21.

  2. `p_evidence` selected records having `founded` OR `occurred_at`, then only
     ever inspected `founded`. For any collection not using `founded` it
     iterated, counted nothing, and returned ok.

  3. `p_no_bare_opinion` scanned `recs[:500]`, leaving 85% of candidates and
     58% of timeline_events unexamined while reporting on all of them.

All three failed OPEN. That is the direction that never announces itself, which
is why this file tests the false branch first and the true branch second.

Coverage is PARTIAL and stated rather than implied: the predicates exercised
here are p_exists, p_validates, p_sources, p_evidence, p_no_bare_opinion,
p_contract_test and p_cadence. Not yet covered: p_schema, p_producer, p_check,
p_lineage, p_schema_version, p_privacy_ci, p_self_report, p_drift. Those need
filesystem fixtures the same way, and leaving them out of the count is the
honest form -- a suite that silently covers half is the same species of defect
as the predicates above.
"""
import io
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "validation"))

import check_maturity as cm  # noqa: E402

SCHEMA = os.path.join(REPO, "config", "schemas", "candidate_v1.json")


def base_record():
    """One real served record, so fixtures share the shape producers emit."""
    feed = os.path.join(REPO, "data", "serveable", "api", "candidates",
                        "all_candidates.jsonl")
    for line in io.open(feed, encoding="utf-8"):
        if line.strip():
            return json.loads(line)
    raise AssertionError("served candidate feed is empty")


def with_temp_collection(name, path, schema=None, producer=None):
    """Register a throwaway collection, returning a restore callable."""
    previous = dict(cm.COLLECTIONS)
    cm.COLLECTIONS[name] = {"path": path, "schema": schema,
                            "producer": producer, "records": None}

    def restore():
        cm.COLLECTIONS.clear()
        cm.COLLECTIONS.update(previous)
    return restore


CASES = []


def case(name, fn, expect):
    CASES.append((name, fn, expect))


# --- p_exists -------------------------------------------------------------
case("p_exists fails when the file could not be read",
     lambda: cm.p_exists("candidates", None, [], "file does not exist")[0], False)
case("p_exists passes on a readable file",
     lambda: cm.p_exists("candidates", None, [base_record()], None)[0], True)


# --- p_sources ------------------------------------------------------------
def _sources_one_missing():
    good = base_record()
    bad = json.loads(json.dumps(good))
    bad["source_urls"] = []
    return cm.p_sources("candidates", None, [good, bad], None)[0]


case("p_sources fails when ONE record of many carries no source",
     _sources_one_missing, False)
case("p_sources passes when every record carries a source",
     lambda: cm.p_sources("candidates", None, [base_record()], None)[0], True)


# --- p_no_bare_opinion ----------------------------------------------------
def _bare_opinion_on_record_501():
    """The regression test for recs[:500].

    The bare field is placed on record 501 specifically. Under the old slice
    this returned True -- a clean bill of health over a corpus it had not read.
    """
    good = base_record()
    recs = [json.loads(json.dumps(good)) for _ in range(600)]
    recs[500]["salience"] = 0.9
    return cm.p_no_bare_opinion("candidates", None, recs, None)[0]


case("p_no_bare_opinion fails on a bare field beyond the old 500-record slice",
     _bare_opinion_on_record_501, False)
case("p_no_bare_opinion fails on a bare rarity field",
     lambda: cm.p_no_bare_opinion(
         "candidates", None, [dict(base_record(), rarity="common")], None)[0], False)
case("p_no_bare_opinion passes on namespaced salience only",
     lambda: cm.p_no_bare_opinion("candidates", None, [base_record()], None)[0], True)


# --- p_evidence -----------------------------------------------------------
def _evidence_no_provenance():
    r = base_record()
    r.pop("_provenance", None)
    return cm.p_evidence("candidates", None, [r], None)[0]


def _evidence_unmeasurable():
    """Neither `founded` nor any dated field: unknown must not be a pass."""
    return cm.p_evidence("candidates", None, [{"id": "x", "title": "t"}], None)[0]


def _evidence_founded_without_quote():
    return cm.p_evidence("frontier_labs", None,
                         [{"id": "x", "founded": "2015-12-11"}], None)[0]


case("p_evidence fails when a dated record carries no _provenance entry",
     _evidence_no_provenance, False)
case("p_evidence fails when it cannot measure at all, rather than passing",
     _evidence_unmeasurable, False)
case("p_evidence fails on a founding date with no evidence quote",
     _evidence_founded_without_quote, False)
case("p_evidence passes on a real record carrying provenance for its dates",
     lambda: cm.p_evidence("candidates", None, [base_record()], None)[0], True)


# --- p_validates ----------------------------------------------------------
def _validates_bad_record():
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, "f.jsonl")
        bad = base_record()
        bad["source_urls"] = ["https://a.example/x, https://b.example/y"]
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            json.dumps(bad, ensure_ascii=True) + "\n")
        restore = with_temp_collection("tmpcoll", p, schema=SCHEMA)
        try:
            return cm.p_validates("tmpcoll", None, [bad], None)[0]
        finally:
            restore()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


case("p_validates fails on a record the schema rejects",
     _validates_bad_record, False)
case("p_validates passes on a served record",
     lambda: (lambda r: (lambda restore: (
         cm.p_validates("tmpcoll2", None, [r], None)[0], restore())[0])(
             with_temp_collection("tmpcoll2", "x", schema=SCHEMA)))(base_record()),
     True)


# --- p_contract_test ------------------------------------------------------
def _contract_self_match():
    """The regression test for the ladder reading its own source.

    'maturity' appears in check_maturity.py, as does 'contract'. Under the old
    predicate any collection whose name appeared in that file matched it. If
    this ever returns True again, the searched set contains the searcher.
    """
    return cm.p_contract_test("maturity", None, [], None)[0]


case("p_contract_test does not match check_maturity.py's own source",
     _contract_self_match, False)
case("p_contract_test fails for a collection no test names",
     lambda: cm.p_contract_test("zzz_no_such_collection", None, [], None)[0], False)


# --- p_cadence ------------------------------------------------------------
def _cadence_missing():
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, "f.jsonl")
        io.open(os.path.join(tmp, "LINEAGE.json"), "w", encoding="utf-8",
                newline="\n").write(json.dumps({"inputs": [1]}) + "\n")
        restore = with_temp_collection("tmpcad", p)
        try:
            return cm.p_cadence("tmpcad", None, [], None)[0]
        finally:
            restore()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _cadence_present():
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, "f.jsonl")
        io.open(os.path.join(tmp, "LINEAGE.json"), "w", encoding="utf-8",
                newline="\n").write(
                    json.dumps({"inputs": [1], "cadence": "weekly"}) + "\n")
        restore = with_temp_collection("tmpcad2", p)
        try:
            return cm.p_cadence("tmpcad2", None, [], None)[0]
        finally:
            restore()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


case("p_cadence fails when LINEAGE declares no cadence", _cadence_missing, False)
case("p_cadence passes when LINEAGE declares one", _cadence_present, True)


COVERED = ["p_exists", "p_validates", "p_sources", "p_evidence",
           "p_no_bare_opinion", "p_contract_test", "p_cadence"]
NOT_COVERED = ["p_schema", "p_producer", "p_check", "p_lineage",
               "p_schema_version", "p_privacy_ci", "p_self_report", "p_drift"]


def main():
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        print("FAIL: jsonschema is not installed, so p_validates cannot be")
        print("      exercised. A suite that skips a case is not a suite that")
        print("      passes it.")
        return 1

    failures = []
    for name, fn, expect in CASES:
        try:
            got = fn()
        except Exception as e:  # a predicate that raises is a failure, loudly
            failures.append("%s -- raised %s: %s" % (name, type(e).__name__, e))
            continue
        if got != expect:
            failures.append("%s -- returned %s, expected %s" % (name, got, expect))

    # Every predicate named in the ladder must appear in one of the two lists,
    # so adding a predicate without deciding whether it is tested is itself a
    # failure rather than a silent gap.
    declared = set(COVERED) | set(NOT_COVERED)
    actual = set()
    for _rung, preds in cm.LADDER:
        for _label, fn in preds:
            actual.add(fn.__name__)
    undeclared = sorted(actual - declared)
    if undeclared:
        failures.append("predicate(s) neither covered nor declared uncovered: %s"
                        % ", ".join(undeclared))
    stale = sorted(declared - actual)
    if stale:
        failures.append("declared predicate(s) no longer in the ladder: %s"
                        % ", ".join(stale))

    if failures:
        print("MATURITY PREDICATE SUITE FAILED")
        for f in failures:
            print("  " + f)
        return 1

    print("maturity predicates: %d cases pass over %d of %d predicates; %d "
          "declared untested (%s)"
          % (len(CASES), len(COVERED), len(actual), len(NOT_COVERED),
             ", ".join(NOT_COVERED)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
