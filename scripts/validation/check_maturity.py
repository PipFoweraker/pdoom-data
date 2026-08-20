"""Report which maturity rung each served collection sits on.

    python scripts/validation/check_maturity.py
    python scripts/validation/check_maturity.py --json

Ruled by Pip 2026-08-06 (`pdoom-data#62`, L1-L5). L4 was ruled **BUILD** where
the other four were ruled **adopt** -- deliberately, and this file is that
distinction made real. Definitions alone are a vocabulary; a thing that reports
which rung a dataset is actually on is a standard.

The ladder: wood, bronze, silver, gold, iridium.

Three rules, all ruled:

- **L2. Every rung is a measurable predicate, never a judgement call.** The test
  applied while writing each one: could two people who dislike each other agree
  whether it passes, without talking? If not, it is not a predicate.
- **L3. A collection reports the highest rung whose predicates ALL pass.** No
  partial credit, so the first failing predicate is the next task rather than a
  score to be averaged away.
- **L5. The rung is written into the collection's LINEAGE**, so a consumer can
  see the maturity of what it is about to depend on.

This is a REPORT, not a gate. A dataset legitimately sits at wood while it is
being built, and gating would only teach people to route around the ladder.

Unknown is not a pass. Where a predicate cannot be evaluated, it fails and says
why -- consistent with the section 5c rule that you cannot report ok over something you
failed to measure.
"""
import argparse
import glob
import io
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVE = os.path.join(REPO_ROOT, "data", "serveable", "api")

RUNGS = ["wood", "bronze", "silver", "gold", "iridium"]

# Each collection: where it lives, which schema describes it, which script
# builds it. A None producer is itself the finding, not a gap in this file.
COLLECTIONS = {
    "timeline_events": {
        "path": os.path.join(SERVE, "timeline_events", "all_events.json"),
        "schema": os.path.join(REPO_ROOT, "config", "schemas", "event_v1.json"),
        "producer": None,
        "records": lambda d: d if isinstance(d, dict) else {},
    },
    "candidates": {
        "path": os.path.join(SERVE, "candidates", "all_candidates.jsonl"),
        "schema": os.path.join(REPO_ROOT, "config", "schemas", "candidate_v1.json"),
        "producer": "scripts/build/project_candidates.py",
        "records": None,
    },
    "reviewed": {
        "path": os.path.join(SERVE, "reviewed", "all_reviewed.jsonl"),
        # Deliberately the SAME schema as candidates: reviewed is a projection
        # of the candidate feed, so a second file would be a copy, and a copy
        # becomes a variant the moment either side changes. What reviewed
        # guarantees BEYOND candidate_v1 -- every record carrying at least one
        # attributed review -- is asserted in tests/test_reviewed_contract.py
        # instead, because it is a property of the collection rather than of a
        # record read in isolation.
        "schema": os.path.join(REPO_ROOT, "config", "schemas", "candidate_v1.json"),
        "producer": "scripts/build/project_reviewed.py",
        "records": None,
    },
    "frontier_labs": {
        "path": os.path.join(SERVE, "frontier_labs", "all_labs.json"),
        "schema": os.path.join(REPO_ROOT, "config", "schemas", "frontier_labs_v1.json"),
        "producer": "scripts/build/project_frontier_labs.py",
        "records": lambda d: {r["id"]: r for r in d.get("labs", [])},
    },
}

# A bare opinion field is one whose name promises a judgement without saying
# whose. Namespaced or attributed forms are fine; these exact names are not.
BARE_OPINION = {"salience", "importance", "rarity", "score", "tier", "quality",
                "verdict", "rating", "pdoom_impact"}


def load(path):
    """Return (records_dict_or_list, error). Never raises on bad input."""
    if not os.path.isfile(path):
        return None, "file does not exist"
    try:
        raw = io.open(path, encoding="utf-8").read()
    except OSError as e:
        return None, "unreadable: %s" % e
    if path.endswith(".jsonl"):
        out = []
        for i, line in enumerate(raw.split("\n"), 1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except ValueError as e:
                return None, "line %d does not parse: %s" % (i, e)
        return out, None
    try:
        return json.loads(raw), None
    except ValueError as e:
        return None, "does not parse: %s" % e


def as_records(name, doc):
    shaper = COLLECTIONS[name]["records"]
    if shaper:
        return list(shaper(doc).values())
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict):
        return list(doc.values())
    return []


def lineage_path(name):
    return os.path.join(os.path.dirname(COLLECTIONS[name]["path"]), "LINEAGE.json")


def read_lineage(name):
    p = lineage_path(name)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except ValueError:
        return None


def producer_check_passes(rel):
    """Run the producer's --check. Slow but it is the whole silver claim."""
    try:
        r = subprocess.run([sys.executable, os.path.join(REPO_ROOT, rel), "--check"],
                           capture_output=True, text=True, timeout=180, cwd=REPO_ROOT)
        return r.returncode == 0, (r.stdout or r.stderr).strip().split("\n")[-1][:110]
    except (OSError, subprocess.SubprocessError) as e:
        return False, "could not run: %s" % e


# --- predicates. Each returns (ok, detail). ------------------------------

def p_exists(name, doc, recs, err):
    if err:
        return False, err
    return True, "%d records" % len(recs)


def p_schema(name, doc, recs, err):
    s = COLLECTIONS[name]["schema"]
    if not s:
        return False, "no schema file declared for this collection"
    if not os.path.isfile(s):
        return False, "declared schema missing: %s" % os.path.basename(s)
    return True, os.path.basename(s)


def p_validates(name, doc, recs, err):
    s = COLLECTIONS[name]["schema"]
    try:
        import jsonschema
    except ImportError:
        return False, "jsonschema not installed, so this cannot be measured"
    schema = json.load(io.open(s, encoding="utf-8"))
    v = jsonschema.Draft7Validator(schema)
    bad = 0
    for r in recs:
        if next(v.iter_errors(r), None) is not None:
            bad += 1
    if bad:
        return False, "%d of %d records fail the schema" % (bad, len(recs))
    return True, "%d records validate" % len(recs)


def p_sources(name, doc, recs, err):
    missing = sum(1 for r in recs
                  if not (r.get("sources") or r.get("source_urls")))
    if missing:
        return False, "%d of %d records carry no source" % (missing, len(recs))
    return True, "every record carries a source"


def p_producer(name, doc, recs, err):
    rel = COLLECTIONS[name]["producer"]
    if not rel:
        return False, "NO PRODUCER: nothing in this repo rebuilds this file"
    if not os.path.isfile(os.path.join(REPO_ROOT, rel)):
        return False, "declared producer missing: %s" % rel
    return True, rel


def p_check(name, doc, recs, err):
    rel = COLLECTIONS[name]["producer"]
    ok, detail = producer_check_passes(rel)
    return ok, detail


def p_lineage(name, doc, recs, err):
    lin = read_lineage(name)
    if lin is None:
        return False, "no LINEAGE.json"
    if not lin.get("inputs") and not lin.get("projected_from"):
        return False, "LINEAGE names no inputs"
    return True, "inputs recorded"


def p_schema_version(name, doc, recs, err):
    s = COLLECTIONS[name]["schema"]
    schema = json.load(io.open(s, encoding="utf-8"))
    if not schema.get("version"):
        return False, "schema declares no version for a consumer to pin"
    return True, "schema version %s" % schema["version"]


DATED_FIELDS = ("occurred_at", "published_at", "source_available_at")


def p_evidence(name, doc, recs, err):
    """Dated claims carry the evidence for the date, in the collection's own form.

    Rewritten 2026-08-21 because the first version passed VACUOUSLY on three of
    the four collections. It selected records having `founded` OR `occurred_at`,
    then only ever inspected `founded` -- a frontier_labs field. Any collection
    using `occurred_at` therefore entered the loop with a non-empty list and
    left it with a count of zero, and reported ok having measured nothing.

    Found when `reviewed` reported GOLD on first wiring. A predicate that cannot
    fail is the exact thing L2 was written to forbid, and it had been sitting in
    the file that enforces L2.

    Two forms are recognised, and a collection using neither FAILS rather than
    passing, per the module docstring: unknown is not a pass.
    """
    founded = [r for r in recs if r.get("founded")]
    if founded:
        without = [r for r in founded
                   if not ((r.get("founded_evidence") or r.get("evidence") or {})
                           .get("quote"))]
        if without:
            return False, "%d of %d founding dates carry no evidence quote" % (
                len(without), len(founded))
        return True, "%d founding dates carry an evidence quote" % len(founded)

    present = [f for f in DATED_FIELDS if any(f in r for r in recs)]
    if not present:
        return False, ("no dated claims in a form this predicate can check "
                       "(neither `founded` nor %s)" % ", ".join(DATED_FIELDS))
    without = 0
    for r in recs:
        prov = r.get("_provenance") or {}
        for f in present:
            if f in r and f not in prov:
                without += 1
                break
    if without:
        return False, "%d of %d records carry a date with no _provenance entry" % (
            without, len(recs))
    return True, "%d records: every one of %s carries a _provenance entry" % (
        len(recs), "/".join(present))


def p_no_bare_opinion(name, doc, recs, err):
    """Every record, not the first 500.

    The `recs[:500]` slice this replaces left 2,934 of 3,434 candidates and 694
    of 1,194 events unexamined -- 85% and 58%. A bare `salience` added by a
    later adapter, or appearing only on the tail of a forward-fill, was invisible
    to a predicate that reported "no bare opinion fields" in full confidence.
    Scanning all of them costs milliseconds; the slice bought nothing.
    """
    found = set()
    for r in recs:
        for k in r:
            if k in BARE_OPINION:
                found.add(k)
    if found:
        return False, "bare opinion field(s): %s" % ", ".join(sorted(found))
    return True, "no bare opinion fields in any of %d records" % len(recs)


def p_contract_test(name, doc, recs, err):
    """A test that fails when the shape a consumer depends on changes.

    Rewritten 2026-08-21. The first version searched every file under tests/ AND
    scripts/validation/ for the words "contract" and the collection name -- and
    scripts/validation/ contains THIS FILE. Writing a comment here that
    mentioned `tests/test_reviewed_contract.py`, a file that did not exist, was
    enough to award `reviewed` the gold rung. The ladder read its own source and
    called it evidence.

    That is the failure the check rule names in as many words: a check must take
    at least one input from OUTSIDE the system it is checking, and must not
    derive what to look for from that same system. Two changes follow from it:

      1. Only `tests/test_*.py` counts, never this directory, and never this
         file. The searched set no longer contains the searcher.
      2. The test is RUN, and must exit 0. A file whose name contains the right
         words is a claim; a file that executes and passes is a measurement. A
         contract test that has been red for a month should not hold up a rung.
    """
    if os.environ.get("PDOOM_MATURITY_RUNNING"):
        # Reached from inside a test this predicate itself launched. Running
        # again would recurse: the first attempt at this spawned Python
        # processes until the run was killed by hand, because the regression
        # test written to catch the self-match contains the words "contract"
        # and "maturity" and so matched itself. Two independent guards, since
        # either alone would have stopped it and neither is obvious later.
        return False, "not evaluated: already running inside a contract test"

    candidates = []
    for p in sorted(glob.glob(os.path.join(REPO_ROOT, "tests", "test_*.py"))):
        if os.path.abspath(p) == os.path.abspath(__file__):
            continue
        try:
            t = io.open(p, encoding="utf-8").read()
        except OSError:
            continue
        if "check_maturity" in t:
            # A test that exercises the ladder is not a contract test for a
            # collection, whatever words it contains. This is the searcher
            # excluding itself and everything that reads it -- the whole point
            # being that a check must not derive what to look for from the
            # system it is checking.
            continue
        if "contract" in t.lower() and name in t:
            candidates.append(p)
    if not candidates:
        return False, "no test under tests/ names this collection as a contract"
    env = dict(os.environ)
    env["PDOOM_MATURITY_RUNNING"] = "1"
    for p in candidates:
        try:
            r = subprocess.run([sys.executable, p], capture_output=True,
                               text=True, timeout=180, cwd=REPO_ROOT, env=env)
        except (OSError, subprocess.SubprocessError) as e:
            return False, "%s could not run: %s" % (os.path.basename(p), e)
        if r.returncode != 0:
            return False, "%s exists but FAILS" % os.path.basename(p)
    return True, ", ".join(os.path.basename(p) for p in candidates) + " (run, passing)"


def p_cadence(name, doc, recs, err):
    lin = read_lineage(name)
    if not lin or not lin.get("cadence"):
        return False, "no declared re-ingest cadence"
    return True, str(lin["cadence"])


def p_drift(name, doc, recs, err):
    return False, "no upstream drift check exists"


def p_privacy_ci(name, doc, recs, err):
    """CI runs a privacy script that exists on disk.

    The first version searched the workflow for the substring "privacy" or
    "redact", which a comment, a job name or a step title satisfies just as
    well as a step that runs something. Same defect class as p_contract_test:
    a word standing in for a behaviour. This resolves the referenced script
    paths and requires at least one to exist, so a renamed or deleted script
    turns the predicate red instead of leaving a green name behind.
    """
    wf = os.path.join(REPO_ROOT, ".github", "workflows", "data-integrity.yml")
    if not os.path.isfile(wf):
        return False, "no data-integrity workflow"
    t = io.open(wf, encoding="utf-8").read()
    refs = re.findall(r"(scripts/[A-Za-z0-9_/]*(?:privacy|redact|address)"
                      r"[A-Za-z0-9_/]*\.py)", t)
    live = [p for p in dict.fromkeys(refs)
            if os.path.isfile(os.path.join(REPO_ROOT, p))]
    if not live:
        if refs:
            return False, ("CI names %s but no such file exists"
                           % ", ".join(sorted(set(refs))))
        return False, "no privacy script is run by data-integrity.yml"
    return True, "CI runs %s" % ", ".join(live)


def p_self_report(name, doc, recs, err):
    lin = read_lineage(name)
    if not lin or not lin.get("maturity"):
        return False, "LINEAGE does not carry its own rung (L5)"
    return True, "self-reports %s" % lin["maturity"]


LADDER = [
    ("wood", [("exists and parses", p_exists)]),
    ("bronze", [("has a schema", p_schema),
                ("validates", p_validates),
                ("every record has a source", p_sources)]),
    ("silver", [("has a producer", p_producer),
                ("producer --check passes", p_check),
                ("lineage names inputs", p_lineage)]),
    ("gold", [("schema is versioned", p_schema_version),
              ("dated claims carry evidence", p_evidence),
              ("no bare opinion fields", p_no_bare_opinion),
              ("consumer-contract test exists", p_contract_test)]),
    ("iridium", [("declared re-ingest cadence", p_cadence),
                 ("upstream drift check", p_drift),
                 ("privacy check in CI", p_privacy_ci),
                 ("self-reports its rung", p_self_report)]),
]


def assess(name):
    doc, err = load(COLLECTIONS[name]["path"])
    recs = as_records(name, doc) if not err else []
    reached = None
    blocker = None
    trail = []
    for rung, preds in LADDER:
        for label, fn in preds:
            try:
                ok, detail = fn(name, doc, recs, err)
            except Exception as e:  # a predicate that crashes is a fail, loudly
                ok, detail = False, "predicate raised: %s" % e
            trail.append((rung, label, ok, detail))
            if not ok:
                blocker = (rung, label, detail)
                return reached or "below wood", blocker, trail, len(recs)
        reached = rung
    return reached, None, trail, len(recs)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true",
                    help="show every predicate, not just the blocker")
    args = ap.parse_args()

    out = {}
    for name in COLLECTIONS:
        rung, blocker, trail, n = assess(name)
        out[name] = {
            "rung": rung,
            "records": n,
            "next": None if not blocker else {
                "rung": blocker[0], "predicate": blocker[1], "detail": blocker[2]},
        }
        if args.verbose:
            out[name]["trail"] = [
                {"rung": r, "predicate": p, "ok": o, "detail": d} for r, p, o, d in trail]

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=True))
        return 0

    print("maturity ladder: %s" % " < ".join(RUNGS))
    print()
    width = max(len(k) for k in out)
    for name, v in sorted(out.items(), key=lambda kv: RUNGS.index(kv[1]["rung"])
                          if kv[1]["rung"] in RUNGS else -1):
        print("%-*s  %-8s  %6d records" % (width, name, v["rung"].upper(), v["records"]))
        if v["next"]:
            print("%-*s  next: %s / %s" % (width, "", v["next"]["rung"],
                                           v["next"]["predicate"]))
            print("%-*s        %s" % (width, "", v["next"]["detail"]))
        print()
    if args.verbose:
        for name in out:
            print("--- %s ---" % name)
            for t in out[name].get("trail", []):
                print("  [%s] %-32s %s" % ("ok" if t["ok"] else "XX",
                                           t["predicate"], t["detail"]))
            print()
    print("Report, not a gate. A collection legitimately sits at wood while it")
    print("is being built. The first failing predicate is the next task.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
