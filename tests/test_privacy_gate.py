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
]


def main():
    failures = []

    for label, text in MUST_FIRE:
        if not redact.residue_scan({"description": text}):
            failures.append("MISSED (%s): the gate does not see this" % label)

    for label, text in MUST_NOT_FIRE:
        hits = redact.residue_scan({"description": text})
        if hits:
            failures.append("FALSE ALARM (%s): %r" % (label, hits[:1]))

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

    print("privacy gate: %d must-fire and %d must-not-fire cases pass"
          % (len(MUST_FIRE) + 1, len(MUST_NOT_FIRE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
