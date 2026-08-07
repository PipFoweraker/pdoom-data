"""Prove the transcoding detector fires, and fires only where it should.

    python tests/test_transcoding_detector.py

Why a test rather than trusting the checker's own clean run
-----------------------------------------------------------
`check_transcoding.py` currently reports zero corruptions in every derived
zone. That is the answer we wanted, which is exactly when a check deserves the
least trust: a detector that never fires and a detector that cannot fire produce
identical output. The redaction verifier in this repository reported clean while
ten records still carried addresses, and what caught it was a second opinion
written separately.

So these cases feed it the known 2025-12-24 corruption -- verbatim, as escapes --
and assert it recovers the original exactly.

Every string here is written with `\\uXXXX` escapes. Typing the characters would
put non-ASCII in the source of a repository that forbids it, and would also make
the test unreadable in any console that mangles them, which this seat's console
does.
"""
import io
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))

import check_transcoding as ct

FAILURES = []


def check(label, condition, detail=""):
    if condition:
        print("  ok   " + label)
    else:
        print("  FAIL " + label + ((" -- " + detail) if detail else ""))
        FAILURES.append(label)


def test_recovers_the_known_corruption():
    """The two records that reached the public site on 2025-12-24."""
    print("known corruption from pdoom-data#68")
    correct = "UK AI Safety Institute \u2192 AI Security Institute"
    corrupt = "UK AI Safety Institute \u00e2\u2020\u2019 AI Security Institute"

    # The corruption is what CP1252 makes of UTF-8 bytes. Derived here rather
    # than asserted, so the fixture cannot drift away from its own definition.
    derived = correct.encode("utf-8").decode("cp1252")
    check("fixture matches a real UTF-8 -> CP1252 transcode", derived == corrupt,
          ascii(derived))
    check("detector recovers the original exactly", ct.recovers(corrupt) == correct,
          ascii(ct.recovers(corrupt)))

    second = "US AISI \u2192 Center for AI Standards and Innovation"
    check("second record recovers too",
          ct.recovers(second.encode("utf-8").decode("cp1252")) == second)


def test_no_false_positives():
    """Text that is merely non-ASCII is not corruption."""
    print("strings that must NOT be reported")
    check("plain ASCII", ct.recovers("UK AI Safety Institute -> AI Security Institute") is None)
    # U+00EE encodes to a single CP1252 byte that is not valid UTF-8 on its own,
    # so the round trip fails and the string is left alone. This is the property
    # that lets accented source titles coexist with the check.
    check("legitimate accented prose", ct.recovers("Beno\u00eet Ma\u00eetre") is None)
    check("an arrow that survived correctly", ct.recovers("A \u2192 B") is None)
    check("empty string", ct.recovers("") is None)


def test_jsonl_is_split_on_newline_only():
    """Regression: str.splitlines() fragmented 12 records and invented 12 findings.

    U+2028 and U+0085 appear inside string values in the alignment_research
    corpus. splitlines() treats both as line terminators; JSONL does not.
    """
    print("JSONL line splitting")
    path = os.path.join(REPO_ROOT, "tests", "_tmp_transcoding_fixture.jsonl")
    record = {"id": "x", "text": "before\u2028after and \u0085more"}
    io.open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(record) + "\n")
    try:
        found = ct.scan_file(path, "tests/_tmp_transcoding_fixture.jsonl")
        check("a record containing U+2028 and U+0085 parses as ONE line",
              found == [], repr(found))
    finally:
        os.remove(path)


def main():
    for fn in (test_recovers_the_known_corruption,
               test_no_false_positives,
               test_jsonl_is_split_on_newline_only):
        fn()
    print()
    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("transcoding detector: all cases pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
