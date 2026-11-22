"""Prove the source-portability gate fires, and fires only where it should.

    python tests/test_source_portability.py

Why this exists
---------------
`check_source_portability.py` was added on 2026-08-26 and wired into nothing:
not `check_all.py`, not `data-integrity.yml`. On 2026-08-29 it went red on a
false positive -- `webbrowser.open(url)` read as a file open -- and stayed red
for ten weeks with nobody seeing it, because a check nothing runs cannot fail
anyone. Found by the 2026-11-05 estate protocol pass (coordination
`reports/PASS_2026-11-05_pdoom-data.md`, card PDOOM-DATA-1).

So the gate's matcher is fed known-bad and known-good calls directly. The
must-not-fire half pins the false positive that hid it; the must-fire half
proves the narrowing did not blind the attribute arm, which still has to catch
`Path(...).open()` and `io.open()`.
"""
import ast
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))

import check_source_portability as csp

FAILURES = []


def offenders(source):
    return csp.offenders_in(ast.parse(source))


def check(label, condition, detail=""):
    if condition:
        print("  ok   " + label)
    else:
        print("  FAIL " + label + ((" -- " + detail) if detail else ""))
        FAILURES.append(label)


MUST_FIRE = [
    ("builtin read without encoding", "open(p)"),
    ("builtin write without encoding or newline", "open(p, 'w')"),
    ("builtin write with encoding but no newline", "open(p, 'w', encoding='utf-8')"),
    ("append mode by keyword, no newline", "open(p, mode='a', encoding='utf-8')"),
    ("Path.open without encoding", "Path(p).open()"),
    ("io.open without encoding", "io.open(p)"),
    ("write_text without newline", "Path(p).write_text(s, encoding='utf-8')"),
    ("read_text without encoding", "Path(p).read_text()"),
    # The exclusion is by bare module name. An attribute chain that merely
    # ends in .os is not the os module and must still be checked.
    ("self.os.open is not os.open", "self.os.open(p)"),
]

MUST_NOT_FIRE = [
    ("webbrowser.open -- the 2026-08-29 false positive", "webbrowser.open(url)"),
    ("os.open takes no codec", "os.open(p, os.O_RDONLY)"),
    ("binary read", "open(p, 'rb')"),
    ("binary write", "open(p, 'wb')"),
    ("read naming its encoding", "open(p, encoding='utf-8')"),
    ("write naming encoding and newline", "open(p, 'w', encoding='utf-8', newline='\\n')"),
    ("io.open done right", "io.open(p, 'w', encoding='utf-8', newline='\\n')"),
]


def main():
    print("must fire")
    for label, src in MUST_FIRE:
        found = offenders(src)
        check(label, len(found) == 1, "found %r in %r" % (found, src))
    print("must not fire")
    for label, src in MUST_NOT_FIRE:
        found = offenders(src)
        check(label, found == [], "found %r in %r" % (found, src))

    if FAILURES:
        print("\n%d case(s) failed." % len(FAILURES))
        return 1
    print("\nsource portability: %d must-fire and %d must-not-fire cases pass."
          % (len(MUST_FIRE), len(MUST_NOT_FIRE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
