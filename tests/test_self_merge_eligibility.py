#!/usr/bin/env python3
"""Assert the self-merge eligibility gate can actually fail.

    python tests/test_self_merge_eligibility.py

Why this exists
---------------
A check that passes is indistinguishable from a check that cannot fail. This
repo has shipped both kinds, and says so in
``.github/workflows/data-integrity.yml``: a redaction verifier that used a
silently broken pattern and reported clean while ten records still carried
addresses, and -- in a sibling -- a CI gate that reported green while running
zero tests.

The gate under test decides whether a human may merge without Pip, so the cost
of it silently passing everything is a review that never happens. Its own
``--self-test`` replays the full rule table and prints the failure text a reader
will see; these cases pin the rules one at a time, so none can be weakened
behind a table that still passes.

Hermetic: no network, no GitHub, no git history. Every assertion is a pure
function over (labels, changed paths, PR body).

Each case names the real thing it stands for, because a test called
``test_bad_input_2`` teaches nothing when it fires eighteen months from now.
"""

import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "validation"
    ),
)

import check_self_merge_eligibility as sme  # noqa: E402

RED_URL = "https://github.com/PipFoweraker/pdoom-data/actions/runs/1234567890"
GOOD_BODY = "Adds the gate.\n\nRED-RUN: %s -- guard label, no declaration in body\n" % RED_URL

PASSED = FAILED = 0


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print("  PASS %s" % name)
    else:
        FAILED += 1
        print("  FAIL %s%s" % (name, (" -> " + detail) if detail else ""))


def section(title):
    print("\n%s" % title)


# ---------------------------------------------------------------------------
section("What counts as documentation")
# ---------------------------------------------------------------------------

for path in ("docs/DATA_DICTIONARY.md", "README.md", "docs/adr/0001.md", "CLAUDE.md"):
    check("documentation: %s" % path, sme.is_documentation(path))

for path in (
    "scripts/build/project_candidates.py",
    "scripts/validation/check_invariants.py",
    ".github/workflows/data-integrity.yml",
    "data/serveable/all_events.json",
    # .md and .txt inside the zones: provenance records, not prose. Waving these
    # through would let a data-zone edit merge under a docs label.
    "data/raw/alignment_research/README.md",
    "data/raw/funding_sources/sff/screenshots/README.txt",
    "VERSION",
    "requirements.txt",
    "requirements-checks.txt",
):
    check("not documentation: %s" % path, not sme.is_documentation(path))

check("windows separators normalised", sme.is_documentation("docs\\DATA_DICTIONARY.md"))

# ---------------------------------------------------------------------------
section("The RED-RUN declaration: a verdict is not a record without a reason")
# ---------------------------------------------------------------------------

check("empty body has no declaration", sme.find_red_run("") is None)
check("prose alone has no declaration", sme.find_red_run("Adds a check. It works.") is None)
check("bare run id is not a declaration", sme.find_red_run("RED-RUN: 1234567890") is None)
check("bare url is not a declaration", sme.find_red_run("RED-RUN: %s" % RED_URL) is None)
check("token reason is not a reason", sme.find_red_run("RED-RUN: 1234567890 -- x") is None)
check(
    "url plus reason parses",
    sme.find_red_run("RED-RUN: %s -- inverted the assertion" % RED_URL) is not None,
)
check(
    "numeric id plus reason parses",
    sme.find_red_run("RED-RUN: 1234567890 -- inverted the assertion") is not None,
)
check("a short number is not a run id", sme.find_red_run("RED-RUN: 42 -- inverted it") is None)
check(
    "case-insensitive, found among prose",
    sme.find_red_run("Fixes it.\n\nred-run: 1234567890 -- ran with the guard removed\n\nCheers")
    is not None,
)
check(
    "the format string the failure message prints actually parses",
    sme.find_red_run(
        sme.RED_RUN_FORMAT.replace("<run-url-or-run-id>", "1234567890").replace(
            "<what was broken to make it fail>", "removed the assertion"
        )
    )
    is not None,
)

# ---------------------------------------------------------------------------
section("Label parsing: seeing zero labels would pass everything")
# ---------------------------------------------------------------------------

check(
    "json array of names",
    sme.parse_labels('["class:guard", "ship:now"]') == ["class:guard", "ship:now"],
)
check("json array of objects", sme.parse_labels('[{"name": "class:docs"}]') == ["class:docs"])
check(
    "comma separated", sme.parse_labels("class:guard, needs:pip") == ["class:guard", "needs:pip"]
)
check(
    "newline separated",
    sme.parse_labels("class:guard\nneeds:pip\n") == ["class:guard", "needs:pip"],
)
check("empty", sme.parse_labels("") == [])
check("malformed json", sme.parse_labels("[not json") == [])

# ---------------------------------------------------------------------------
section("The five rules, end to end")
# ---------------------------------------------------------------------------

check("no class label is neutral", sme.run([], ["scripts/build/project_candidates.py"], "") == [])
check("unrelated labels are neutral", sme.run(["bug"], ["data/serveable/x.json"], "") == [])
check("needs:pip alone is neutral", sme.run(["needs:pip"], ["data/serveable/x.json"], "") == [])

check("docs-only diff passes", sme.run(["class:docs"], ["docs/DATA_DICTIONARY.md"], "") == [])

_mixed = sme.run(
    ["class:docs"], ["docs/DATA_DICTIONARY.md", "scripts/build/project_candidates.py"], ""
)
check("docs class over a script fails", bool(_mixed))
check(
    "and it names the offending path",
    bool(_mixed)
    and "scripts/build/project_candidates.py" in _mixed[0]
    and "docs/DATA_DICTIONARY.md" not in _mixed[0],
)

check("docs class with no changed paths fails", bool(sme.run(["class:docs"], [], "")))

_undeclared = sme.run(["class:guard"], [".github/workflows/x.yml"], "Adds a check.")
check("guard class with no declaration fails", bool(_undeclared))
check("and it prints the expected format", bool(_undeclared) and "RED-RUN:" in _undeclared[0])

check(
    "guard class with a declaration passes",
    sme.run(["class:guard"], [".github/workflows/x.yml"], GOOD_BODY) == [],
)
check(
    "a guard may live anywhere in the tree",
    sme.run(["class:guard"], ["scripts/validation/check_thing.py"], GOOD_BODY) == [],
)

check(
    "needs:pip fails a guard claim even with a RED run",
    bool(sme.run(["class:guard", "needs:pip"], [".github/workflows/x.yml"], GOOD_BODY)),
)
check(
    "needs:pip fails a docs claim even on a clean docs diff",
    bool(sme.run(["class:docs", "needs:pip"], ["docs/DATA_DICTIONARY.md"], "")),
)
check(
    "both class labels fail",
    bool(sme.run(["class:guard", "class:docs"], ["docs/DATA_DICTIONARY.md"], GOOD_BODY)),
)
check(
    "label matching is case-insensitive",
    bool(sme.run(["Class:Guard"], [".github/workflows/x.yml"], "no declaration")),
)

# ---------------------------------------------------------------------------
section("The checker's own rule table")
# ---------------------------------------------------------------------------

check("--self-test agrees with these tests", sme.self_test() == 0)
check(
    "the table contains both polarities",
    {case[4] for case in sme.SELF_TEST_CASES} == {0, 1},
    "a table with one polarity proves nothing",
)

print("\n%d passed, %d failed" % (PASSED, FAILED))
sys.exit(1 if FAILED else 0)
