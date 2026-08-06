"""Assert the taxonomy gate can actually fail.

    python tests/test_taxonomy_gate.py

Why this exists
---------------
A check that passes is indistinguishable from a check that cannot fail. This
repo has shipped both: a redaction verifier that used a silently broken pattern
and reported clean while ten records still carried addresses, and -- in a
sibling -- a CI gate that reported green while running zero tests.

project_taxonomy.py's validate() passed on its first run. That is what it should
do, and it is also exactly what a validator that never returns anything would
do. These cases distinguish the two.

Each case names the real failure it stands for, because a test whose name is
'test_bad_input_2' teaches nothing when it fires eighteen months from now.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "build"))

import project_taxonomy  # noqa: E402


def case(name, source, expect_fragment):
    problems = project_taxonomy.validate(source)
    hit = [p for p in problems if expect_fragment in p]
    if not hit:
        print("FAIL  %s" % name)
        print("      expected a problem containing %r" % expect_fragment)
        print("      got: %r" % problems)
        return False
    print("ok    %s" % name)
    return True


def main():
    ok = True

    # A term list without definitions is a word list. The reader would have to
    # ask a person, which is the state the taxonomy artifact replaces.
    ok &= case(
        "a term with no definition is refused",
        {"minted_here": [{"term": "salience", "definition": "  ", "status": "ruled",
                          "authority": "ADR-001"}],
         "minted_elsewhere": []},
        "has no definition")

    # 'ruled' with no citation is indistinguishable from 'this seat decided'.
    # The entire taxonomy grant rests on that difference being visible.
    ok &= case(
        "'ruled' without an authority citation is refused",
        {"minted_here": [{"term": "verdict", "definition": "accept/reject/unsure",
                          "status": "ruled", "authority": ""}],
         "minted_elsewhere": []},
        "cites no authority")

    # coordination#15's failure: two repos each believing they own one term,
    # neither knowing the other does.
    ok &= case(
        "a term claimed by both this repo and another is refused",
        {"minted_here": [{"term": "rarity", "definition": "d", "status": "proposed",
                          "authority": "x"}],
         "minted_elsewhere": [{"term": "rarity", "minted_by": "pdoom1",
                               "note": "n", "status": "contested"}]},
        "claimed in BOTH")

    # A pointer with no owner is not a pointer.
    ok &= case(
        "a foreign term with no owning repo is refused",
        {"minted_here": [],
         "minted_elsewhere": [{"term": "epoch", "minted_by": "", "note": "n",
                               "status": "ruled"}]},
        "does not say which repo mints it")

    # An unrecognised status silently becomes 'whatever the reader assumes'.
    ok &= case(
        "an unknown status value is refused",
        {"minted_here": [{"term": "zone", "definition": "d", "status": "final",
                          "authority": "x"}],
         "minted_elsewhere": []},
        "expected one of")

    ok &= case(
        "a duplicate term within one list is refused",
        {"minted_here": [
            {"term": "dump", "definition": "d", "status": "ruled", "authority": "x"},
            {"term": "dump", "definition": "d", "status": "ruled", "authority": "x"}],
         "minted_elsewhere": []},
        "appears twice")

    # And the positive control: the real source must pass, or the cases above
    # prove only that a validator rejects everything.
    with io.open(project_taxonomy.SOURCE, encoding="utf-8") as handle:
        real = json.load(handle)
    problems = project_taxonomy.validate(real)
    if problems:
        print("FAIL  the committed taxonomy source does not validate")
        for problem in problems:
            print("      " + problem)
        ok = False
    else:
        print("ok    the committed taxonomy source validates")

    print("")
    if not ok:
        print("TAXONOMY GATE TESTS FAILED")
        return 1
    print("All taxonomy gate tests pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
