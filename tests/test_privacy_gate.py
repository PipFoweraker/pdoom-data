"""The privacy gate must be able to FAIL. Standalone; no pytest required.

    python tests/test_privacy_gate.py

Why this file exists
--------------------
Workshop 2 ruling R6, adopted 2026-08-09: no guard counts as installed until a
RED run of it has been observed. A green gate proves nothing on its own -- the
previous residue check was green for eight months while ten records carried
addresses, and it was green because it could not match anything at all.

So every case below is an address the corpus ACTUALLY contained, in the form it
actually took, and the assertion is that the gate SEES it. If someone narrows
the pattern later, this fails rather than the gate going quietly blind.

The negative cases matter equally. An alarm that fires on `pass@k` gets muted by
a human within a week, and a muted alarm is worse than none because it reads as
coverage.
"""
import io
import importlib.util
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO_ROOT, "scripts", "privacy", "redact_emails.py")

spec = importlib.util.spec_from_file_location("redact_emails", TOOL)
redact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(redact)

# Every one of these was live in data/serveable/ on 2026-08-09. The local part
# is preserved because the SHAPE is the test; these are published papers'
# contact lines, and the addresses are being asserted about, not distributed
# any further than the corpus already did.
MUST_FIRE = [
    ("plain", "correspondence to plain.person@example.org for details"),
    ("space in domain, before the dot",
     "bcl.egb@cbs .dk  \n Copenhagen Business School"),
    ("space in domain, after the dot",
     "roman.yampolskiy@louisville. edu   \n \n Introduction"),
    ("space around a hyphen in the domain",
     "thilo.hagendorff@uni -tuebingen.de  \n Ethics"),
    ("brace group naming five people",
     "{gilmer,muelly,goodfellow,mrtz,beenkim}@google.com\nGoogle Brain"),
    ("brace group wrapped across a line",
     "{oliver.eigner, sebastian.eresheim,\nmartin.pirker}@fhstp.ac.at\nInstitute"),
    ("space before the at sign",
     "{teinhonglo,  sungtc, berlin} @ntnu.edu.tw  \n \n Abstract"),
    # MODE (d), added 2026-08-13. Not a mangling the PDF extractor performs --
    # one this repository performs, by capping description at 1,000 characters
    # in transform_enriched.py and transform_to_timeline_events.py. When the
    # cut lands inside a contact line the domain is severed, and RESIDUE
    # requires a TLD, so no setting of it could ever have matched these. The
    # first case is the exact text that was live in three files in the public
    # serveable zone, and on pdoom1.com, until this commit.
    ("severed by the 1,000-character cap, no TLD left",
     "St.Gallen, Switzerland  \nleimeister@un..."),
    ("severed with the whole domain gone",
     "Pfannkuchstr.1, 34121 Kassel, Germany  \nleimeister@..."),
    ("severed, dotted local part, mid-line",
     "Correspondence to thilo.hagendorff@uni-tue..."),
    ("severed brace group, several people at once",
     "Institute of IT Security  \n{oliver.eigner, sebastian.eresheim}@fhs..."),
    ("severed at a Unicode ellipsis, before clean.py normalises it",
     "St.Gallen, Switzerland  \nleimeister@un\u2026"),
]

# Measured false positives from the 2025-12-24 dump: 21 fragments, 21 of them
# not addresses. One per family, plus the one that survived the first bound.
MUST_NOT_FIRE = [
    ("LaTeX internal", "lx@paragraphsign of polynomial time algorithms. As"),
    ("social handle", "accused of using @realDonaldTrump to troll his critics. While"),
    ("metric notation", "computing pass@k in this way can have high variance. We"),
    ("metric notation, capitalised", "Test Acc@100 of prediction of voltages. We"),
    ("hardware spec", "parallelized over 8 CPU cores @ 2.20GHz processors. We"),
    ("dataset name", "Histopathology Images -The ACDC@LungHP Challenge 2019. IEEE"),
    ("the one that survived a looser bound",
     "which is similar to our pass@k metric. TransCoder"),
    ("already redacted", "contact [email address redacted] , see above"),
    # Added with mode (d). A TLD-less rule is looser than the three above it by
    # construction -- strip the TLD and "pass@k" and "leimeister@un" are the
    # same shape -- so the families that were merely quiet before are now the
    # ones under load.
    ("BibTeX entry", "@article{Vaswani2017, title={Attention}, year={2017}}"),
    ("BibTeX mid-sentence", "as reported in @inproceedings{Amodei2016, pages"),
    ("metric notation alone on its own line",
     "we report this in\npass@k form. Results"),
    ("LaTeX internal alone on its own line",
     "the macro\nlx@paragraphsign is expanded. As"),
    ("dataset name alone on its own line",
     "evaluated on\nACDC@LungHP and two others. IEEE"),
    # Idempotence. This is what a redacted contact line looks like AFTER this
    # tool has run on it, marker preserved. If mode (d) fires on its own output
    # the gate can never go green again.
    ("a mode-(d) redaction that already happened",
     "St.Gallen, Switzerland  \n[email address redacted]..."),
]

# The truncation cap is the whole mechanism of mode (d), so the false-positive
# families have to be tested AT it, not only away from it. Cutting each family
# at every character position and marking the cut is 400-odd cases for free,
# and it is the difference between "pass@k is safe" and "pass@k is safe at the
# one boundary I happened to think of". Both marker forms, and each family
# tested twice: as its own string, and with a line above it, because a line
# above is what turns a token into a line-initial one.
CUT_MARKERS = ("...", "\u2026")
CUT_PREFIXES = ("", "Extracted from the paper, page 1  \n")


def main():
    failures = []

    for label, text in MUST_FIRE:
        if not redact.residue_scan({"description": text}):
            failures.append("MISSED (%s): the gate does not see this" % label)
        # Seeing it is half the job. A scanner that fires on something scrub()
        # cannot remove refuses every write and gets switched off.
        cleaned = redact.scrub({"description": text}, [0])
        if redact.residue_scan(cleaned):
            failures.append("NOT REMOVED (%s): scrub() leaves what the gate "
                            "sees" % label)

    for label, text in MUST_NOT_FIRE:
        hits = redact.residue_scan({"description": text})
        if hits:
            failures.append("FALSE ALARM (%s): %r" % (label, hits[:1]))

    cuts = 0
    for label, text in MUST_NOT_FIRE:
        for prefix in CUT_PREFIXES:
            body = prefix + text
            for i in range(len(prefix), len(body) + 1):
                for marker in CUT_MARKERS:
                    cut = body[:i] + marker
                    cuts += 1
                    hits = redact.residue_scan({"description": cut})
                    if hits:
                        failures.append(
                            "FALSE ALARM AT THE CUT (%s) %r -> %r"
                            % (label, cut[-40:], hits[:1]))

    # The gate must survive the shapes this corpus is built from: form feeds,
    # nested structures, and lists. A scanner that only walks top-level strings
    # would pass every case above and miss the actual documents.
    nested = {"events": [{"description": "see bcl.egb@cbs .dk\x0c for contact"}]}
    if not redact.residue_scan(nested):
        failures.append("MISSED: address nested in a list of dicts")

    # And scrubbing must actually remove what the scanner sees, or the two
    # halves of this tool disagree in the direction that publishes.
    cleaned = redact.scrub(nested, [0])
    if redact.residue_scan(cleaned):
        failures.append("scrub() left something residue_scan() still sees")

    if failures:
        for f in failures:
            print("FAIL " + f)
        print()
        print("%d case(s) failed. The privacy gate is not trustworthy." % len(failures))
        return 1

    print("privacy gate: %d must-fire and %d must-not-fire cases pass, "
          "plus %d truncation cuts of the must-not-fire families"
          % (len(MUST_FIRE) + 1, len(MUST_NOT_FIRE), cuts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
