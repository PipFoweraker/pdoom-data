"""The postal gate must be able to FAIL. Standalone; no pytest required.

    python tests/test_postal_gate.py

Why this file exists
--------------------
Workshop 2 ruling R6, adopted 2026-08-09: no guard counts as installed until a
RED run of it has been observed. tests/test_privacy_gate.py makes that argument
in full for the email half; this is the postal half, and the same reasoning
applies without modification.

The split of cases here is the whole design of scan_postal.py, so it is worth
stating plainly. MUST_FIRE is dwelling-shaped text. MUST_NOT_FIRE contains the
institutional addresses that were ACTUALLY in the tracked tree on 2026-08-14 --
university departments and a defence contractor's published point of contact,
all of them extracted from academic paper title pages by the same unparsed-PDF
import that caused the email exposure.

Those institutional cases are the load-bearing ones. A guard that fired on all
ten would be muted within a week, and a muted alarm reads as coverage while
providing none. So they are asserted about here: if someone later widens the
patterns until affiliation blocks trip the gate, this file fails first and
says why, rather than the gate going noisy and then getting switched off.

The addresses in MUST_NOT_FIRE are published organisational addresses already
present in this public repository; asserting about them distributes them no
further than the corpus already does. Every address in MUST_FIRE is fabricated.
"""
import importlib.util
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO_ROOT, "scripts", "privacy", "scan_postal.py")

spec = importlib.util.spec_from_file_location("scan_postal", TOOL)
scan_postal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_postal)

# All fabricated. A leaked home address is the thing this gate exists to see,
# so the shapes are real even though the addresses are not.
MUST_FIRE = [
    ("plain street address, no institution nearby",
     "Contact the participant at 14 Wattlebird Crescent for the follow-up."),
    ("unit prefix",
     "Respondent 12 lives at Unit 7, 22 Kookaburra Street and declined."),
    ("apartment prefix, slashed number",
     "Delivery to Apt 3/118 Rosella Avenue was refused."),
    ("flat prefix",
     "Flat 2, 9 Bandicoot Road -- second interview scheduled."),
    ("australian suburb, state and postcode",
     "posted to Fitzroy North VIC 3068 on the following Tuesday"),
    ("australian locality, two-word suburb",
     "collected from Surry Hills NSW 2010 by the field team"),
    ("australian mobile, spaced",
     "call back on 0412 345 678 before six"),
    ("australian mobile, unspaced",
     "secondary contact 0498765432 listed on the form"),
    ("labelled handset",
     "Mobile: +61 3 9000 1234 -- preferred contact method"),
    ("labelled home line",
     "Home phone: 03 9123 4567 (evenings only)"),
    ("bare geocode at dwelling resolution",
     '"lat_long": "-37.8142176,144.9631608", "source": "field visit"'),
    ("street-then-number, german order, no institution nearby",
     "the parcel went to Lindenweg 14 and was signed for"),
    ("street-then-number, dutch order",
     "forwarded to Kerkstraat 22 without further comment"),
]

# Every one of these was in the tracked tree on 2026-08-14. They are
# organisational addresses printed on published papers, which is what the
# INSTITUTION window is for. If any of them starts firing, the gate is about to
# become noise.
MUST_NOT_FIRE = [
    ("university department, uk",
     "1 Oxford Internet Institute, University of Oxford, 1 St Giles, "
     "Oxford, OX1 3JS"),
    ("national library",
     "2 Alan Turing Institute, British Library, 96 Euston Rd, "
     "London NW1 2DB"),
    ("innovation centre",
     "3 Digital Catapult, 101 Euston Road, Kings Cross, London, NW1 2RA"),
    ("us university, state and zip",
     "1Data Science Institute, Columbia University, New York, NY 10027"),
    ("defence contractor point of contact",
     "Point of Contact Michael Ownby Solers, Inc. 1611 N. Kent St "
     "Arlington VA 22209"),
    ("german university, street-then-number",
     "Dellermann University of Kassel/Information Systems "
     "Pfannkuchstr.1, 34121 Kassel, Germany"),
    ("swiss university, street-then-number",
     "Institute of Information Management Mueller-Friedberg-Strasse 8, "
     "9000 St. Gallen"),
    ("institutional switchboard, unlabelled",
     "a credit card can be made by calling the Gift Services "
     "Department on 510-643-9789."),
    # Measured false-positive families. Both are "the digit run continues past
    # the match", found while building this gate against the real corpus.
    ("float that contains a well-formed mobile number",
     '"Training power draw (W)": "202329.0409413959", "Training time"'),
    ("hex digest that contains a well-formed mobile number",
     '"content_sha256": "0426717380a1fd51fed9cbd594e98f4b", "kind"'),
    ("second digest family",
     '"content_sha256": "08a4dc4c29b0456213446f67965260efef2b3c4fb512"'),
    ("geocode inside a maps link to a named public place",
     "the [preserve](https://www.google.com/maps/place/El+Segundo+Blue+"
     "Butterfly+Preserve/@33.9317558,-118.4363199,17z/data=!3m1!4b1)"),
    ("prose that contains the word home",
     "The neocortex is the home of human intelligence, more or less, and"),
    ("prose that contains the word level",
     "2. Implement Level 1 data sharing in both repos"),
    ("a version string that looks like a locality",
     "Released SA 2019 as a research preview, see the appendix"),
]


def run():
    failures = []

    for name, text in MUST_FIRE:
        hits = list(scan_postal.scan_line(text))
        if not hits:
            failures.append("MUST FIRE but did not: %s" % name)

    for name, text in MUST_NOT_FIRE:
        hits = list(scan_postal.scan_line(text))
        if hits:
            labels = ",".join(sorted(set(h[0] for h in hits)))
            failures.append("MUST NOT FIRE but did (%s): %s" % (labels, name))

    if failures:
        print("postal gate: FAILED")
        for f in failures:
            print("  " + f)
        return 1

    print("postal gate: %d must-fire and %d must-not-fire cases pass."
          % (len(MUST_FIRE), len(MUST_NOT_FIRE)))
    return 0


if __name__ == "__main__":
    sys.exit(run())
