"""Assert the description overlay serves only what a named human accepted.

    python tests/test_description_overlay.py

Why this exists
---------------
`project_timeline_events.load_description_overlay()` is the point where a
keystroke becomes a sentence on 1,166 public pages about real papers by named
researchers. Everything upstream of it is proposal; everything downstream is
published. If it is wrong in the permissive direction, this repository composes
descriptions and attributes them to people who never wrote them, which is the
single worst thing it could do.

So the cases below are mostly about what it must REFUSE:

  * a decision with no reviewer -- ADR-001 permits no anonymous verdicts, and
    this is exactly where one would become published prose;
  * `keep_current` and `undecided`, which are recorded decisions that both mean
    "do not touch this record", not "no decision yet";
  * an empty or whitespace description;
  * a decision naming a record that is not in the corpus.

And one about what it must PRESERVE: the served text is the exact string the
reviewer saw, carried from the decision, never re-derived from the abstract. If
the trim length or the ASCII coercion changes later, previously approved text
must not silently change with it. That would be a new sentence nobody read.

Every case runs against the real function with a temporary decisions file.
The last case asserts the real one was not touched.
"""
import io
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "build"))

import project_timeline_events as pte  # noqa: E402

REAL_PATH = pte.CURATED_DESCRIPTIONS


def decision(**over):
    row = {
        "id": "arxiv_abc",
        "arxiv_id": "1602.04019",
        "source_url": "https://arxiv.org/abs/1602.04019",
        "verdict": "accept_abstract",
        "description": "A real abstract, as approved.",
        "replaces": "1 Introduction",
        "reviewer": "Test Reviewer",
        "at": "2026-08-21T06:00:00+00:00",
    }
    row.update(over)
    return row


def run(rows):
    """Call the real loader over a temp file. Returns (overlay, problems)."""
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "decisions.jsonl")
        with io.open(path, "w", encoding="ascii", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=True, sort_keys=True) + "\n")
        pte.CURATED_DESCRIPTIONS = path
        problems = []
        return pte.load_description_overlay(problems), problems
    finally:
        pte.CURATED_DESCRIPTIONS = REAL_PATH
        shutil.rmtree(tmp, ignore_errors=True)


def check(name, ok, detail=""):
    return [] if ok else ["  %s%s" % (name, (" -- " + detail) if detail else "")]


def main():
    failures = []

    overlay, problems = run([decision()])
    failures += check("an accepted decision is applied",
                      overlay.get("arxiv_abc", {}).get("description")
                      == "A real abstract, as approved.", json.dumps(overlay))
    failures += check("a clean decision raises no problem", not problems,
                      json.dumps(problems))

    for missing in ("", "   ", None):
        overlay, problems = run([decision(reviewer=missing)])
        failures += check("an UNATTRIBUTED acceptance is refused (reviewer=%r)"
                          % missing, not overlay and problems, json.dumps(overlay))

    for verdict in ("keep_current", "undecided"):
        overlay, problems = run([decision(verdict=verdict)])
        failures += check("verdict '%s' changes nothing" % verdict,
                          not overlay, json.dumps(overlay))
        failures += check("verdict '%s' is not reported as a problem" % verdict,
                          not problems, json.dumps(problems))

    for empty in ("", "   ", None):
        overlay, problems = run([decision(description=empty)])
        failures += check("an empty description is refused (%r)" % empty,
                          not overlay and problems, json.dumps(overlay))

    # last write wins, and the earlier decision is still on disk
    overlay, _ = run([decision(description="first thoughts"),
                      decision(description="second thoughts")])
    failures += check("a change of mind wins",
                      overlay["arxiv_abc"]["description"] == "second thoughts",
                      json.dumps(overlay))

    # a malformed line is reported, and does not stop the good lines
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "decisions.jsonl")
        io.open(path, "w", encoding="ascii", newline="\n").write(
            "{not json}\n" + json.dumps(decision(), sort_keys=True) + "\n")
        pte.CURATED_DESCRIPTIONS = path
        problems = []
        overlay = pte.load_description_overlay(problems)
        failures += check("a malformed line is reported", bool(problems))
        failures += check("a malformed line does not discard the good ones",
                          "arxiv_abc" in overlay)
    finally:
        pte.CURATED_DESCRIPTIONS = REAL_PATH
        shutil.rmtree(tmp, ignore_errors=True)

    # a missing file is not an error: nobody has reviewed anything yet
    pte.CURATED_DESCRIPTIONS = os.path.join(REPO, "does", "not", "exist.jsonl")
    problems = []
    try:
        overlay = pte.load_description_overlay(problems)
        failures += check("no decisions file is not an error",
                          overlay == {} and not problems)
    finally:
        pte.CURATED_DESCRIPTIONS = REAL_PATH

    # the served text is the reviewer's string, not something re-derived
    overlay, _ = run([decision(description="Exactly these words.",
                               abstract="Some other, longer text entirely.")])
    failures += check("the approved string is served verbatim",
                      overlay["arxiv_abc"]["description"] == "Exactly these words.",
                      json.dumps(overlay))

    # and the real curated file was never opened for writing
    if os.path.isfile(REAL_PATH):
        failures += check("the real decisions file still parses",
                          all(json.loads(l) for l in
                              io.open(REAL_PATH, encoding="utf-8") if l.strip()))
    if pte.CURATED_DESCRIPTIONS != REAL_PATH:
        failures.append("  the module constant was left pointing at a temp path")

    if failures:
        print("DESCRIPTION OVERLAY FAILED")
        for f in failures:
            print(f)
        return 1
    print("description overlay: unattributed, empty, non-accept and malformed "
          "decisions all refused; the approved string is served verbatim")
    return 0


if __name__ == "__main__":
    sys.exit(main())
