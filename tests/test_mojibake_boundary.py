#!/usr/bin/env python3
"""Assert that a wrong decode fails at the boundary, and that the ASCII fold
can no longer manufacture a letter out of an accent.

    python tests/test_mojibake_boundary.py

Why this exists
---------------
On 2026-08-22, diffing the 2026-07-25 Epoch dump against a fresh fetch produced
59 "changes", of which roughly eight were real. The rest were one defect:

    scripts/adapters/epoch_models.py:fetch()  ->  text = response.text

`requests` guesses. For a `text/*` body with no `charset` parameter it falls
back to ISO-8859-1 per RFC 2616, and Epoch AI serves `Content-Type: text/csv`
with no charset. So UTF-8 bytes were decoded as latin-1 -- silently, because a
latin-1 decode of UTF-8 cannot fail -- and `to_ascii` then NFKD-folded the
resulting U+00C3 to the LETTER `A`. "Universite de Montreal" was stored as
"UniversitA de MontrAal", and `e` cannot be recovered from `A`.

THE PART WORTH KEEPING: why the existing detector could not have caught it
--------------------------------------------------------------------------
`scripts/validation/check_transcoding.py` exists for exactly this species and
is correct. It greps for the LEAD characters U+00C2, U+00C3, U+00E2 and then
confirms with a round trip.

It never had a chance. `to_ascii` runs BEFORE the dump is written, and folding
turns U+00C3 into `A`. By the time anything reaches disk the stored string is
pure ASCII, carries no lead character, and round-trips to nothing. The ASCII
gate destroyed the evidence the transcoding detector looks for.

Two guards, each correct alone, composing into a hole. That is why the fix sits
upstream of both -- raise at the boundary, repair at the fold -- and why case 5
pins the blindness itself, so nobody later "simplifies" the repair back out of
`to_ascii` on the grounds that a detector already covers this species.

The direction of failure is the point, as in test_schema_gates.py: a decoder
that wrongly REJECTS good text goes red and someone looks. A decoder that
wrongly ACCEPTS bad bytes is silent for a month, which is what happened.

ASCII-only source, per ASCII_CODING_STANDARDS.md: every non-ASCII character in
this file is written as an escape, never as a literal.
"""

import os
import sys
import unicodedata

# Windows consoles default to cp1252 and raise on the first non-ASCII byte
# written to stdout. This file deals in mojibake, so it would die printing
# its own evidence. No-op on UTF-8 platforms.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts", "adapters"))

import _base  # noqa: E402

FAILURES = []
CHECKS = [0]

# Escapes, never literals. U+00E9 is e-acute; U+2192 is a rightwards arrow;
# U+00C2/C3/E2 are the lead characters check_transcoding.py greps for.
CLEAN = u"Universit\u00e9 de Montr\u00e9al"
ARROW = u"AI Safety Institute \u2192 AI Security Institute"
LEADS = (u"\u00c2", u"\u00c3", u"\u00e2")
CURLY = u"\u2018quoted\u2019"


def check(condition, message):
    CHECKS[0] += 1
    if condition:
        print("  PASS  %s" % message)
    else:
        print("  FAIL  %s" % message)
        FAILURES.append(message)


class FakeResponse(object):
    """The parts of requests.Response that decode_response touches, reproducing
    the same guess: .text honours .encoding, and a text/* body with no charset
    arrives pre-set to ISO-8859-1 the way requests sets it."""

    def __init__(self, body_utf8, content_type):
        self.content = body_utf8
        self.headers = {"Content-Type": content_type}
        self.url = "https://example.invalid/data.csv"
        lowered = content_type.lower()
        if lowered.startswith("text/") and "charset=" not in lowered:
            self.encoding = "ISO-8859-1"          # requests' RFC 2616 fallback
        elif "charset=" in lowered:
            self.encoding = lowered.split("charset=")[1].strip()
        else:
            self.encoding = None

    @property
    def text(self):
        return self.content.decode(self.encoding or "utf-8", "replace")


def naive_fold(text):
    """The fold as it behaved before this fix: NFKD, drop what will not fold.
    Reproduced here rather than imported, so case 5 measures the historical
    damage instead of measuring the current implementation against itself."""
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        else:
            out.append(unicodedata.normalize("NFKD", ch)
                       .encode("ascii", "ignore").decode("ascii"))
    return "".join(out)


def main():
    print("mojibake boundary: raise at the edge, repair at the fold\n")

    # -- 1. the exact production shape: text/csv, no charset -----------------
    print("1. a text/* body with no charset is decoded as UTF-8, not latin-1")
    r = FakeResponse(CLEAN.encode("utf-8"), "text/csv")
    check(r.text != CLEAN,
          "FORCED: raw requests behaviour still mangles it, so the guard has work to do")
    got = _base.decode_response(r)
    check(got == CLEAN, "decode_response returns the original text intact")
    check(_base.to_ascii(got) == "Universite de Montreal",
          "and it folds to 'Universite de Montreal', not 'UniversitA de MontrAal'")

    # -- 2. a declared charset is honoured, not overridden -------------------
    print("\n2. a server that DOES declare a charset is believed")
    r = FakeResponse(CLEAN.encode("utf-8"), "text/csv; charset=utf-8")
    check(_base.decode_response(r) == CLEAN, "declared utf-8 round-trips")

    # -- 3. the boundary REFUSES text that is still double-decoded ----------
    print("\n3. FORCED FAILURE: decode_response raises rather than returning damage")
    damaged = CLEAN.encode("utf-8").decode("latin-1")
    r = FakeResponse(damaged.encode("utf-8"), "text/csv")
    raised = None
    try:
        _base.decode_response(r)
    except _base.MojibakeError as exc:
        raised = exc
    check(raised is not None,
          "raises MojibakeError on text still mojibake after decoding")
    check(raised is None or "example.invalid" in str(raised),
          "and the message names the URL, so the failure is actionable")

    # -- 4. both species, because this repo has met both --------------------
    print("\n4. both corruption species are detected and repaired")
    for label, codec in (("latin-1 (Epoch, 2026-07-25)", "latin-1"),
                         ("cp1252 (timeline events, 2026-08-06)", "cp1252")):
        for src in (CLEAN, ARROW):
            try:
                bad = src.encode("utf-8").decode(codec)
            except UnicodeDecodeError:
                continue
            check(_base.looks_like_mojibake(bad), "%s: detected" % label)
            check(_base.repair_mojibake(bad) == src, "%s: repaired exactly" % label)

    print("\n   and clean text is never touched")
    for good in (CLEAN, ARROW, "University of Montreal", "", "plain"):
        check(not _base.looks_like_mojibake(good), "not flagged: %s" % ascii(good[:26]))
        check(_base.repair_mojibake(good) == good, "unchanged: %s" % ascii(good[:26]))

    # -- 5. the composition hole, pinned ------------------------------------
    print("\n5. THE HOLE: folding first destroys what check_transcoding greps for")
    damaged = CLEAN.encode("utf-8").decode("latin-1")
    check(any(lead in damaged for lead in LEADS),
          "before folding, a lead character is present and the detector can see it")
    folded_badly = naive_fold(damaged)
    check(folded_badly == "UniversitA de MontrAal",
          "a naive fold reproduces the historical damage exactly: %s" % ascii(folded_badly))
    check(not any(lead in folded_badly for lead in LEADS),
          "after folding, NO lead character survives: the detector is blind by then")
    check(not _base.looks_like_mojibake(folded_badly),
          "and the round trip cannot see it either -- the damage is unrecoverable")
    check(_base.to_ascii(damaged) == "Universite de Montreal",
          "which is why to_ascii must repair BEFORE it folds")

    # -- 6. the fold is otherwise unchanged ---------------------------------
    print("\n6. the fold is otherwise unchanged")
    check(_base.to_ascii(None) is None, "None passes through")
    check(_base.to_ascii("already ascii") == "already ascii", "ASCII is identity")
    check(_base.to_ascii(CURLY) == "'quoted'", "CHAR_REPLACEMENTS still applied")

    print("\n%d checks, %d failed" % (CHECKS[0], len(FAILURES)))
    if FAILURES:
        for f in FAILURES:
            print("  FAILED: %s" % f)
        return 1
    print("OK: a wrong decode fails at the boundary; the fold repairs before folding.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
