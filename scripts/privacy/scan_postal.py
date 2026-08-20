"""Scan tracked zones for DWELLING-shaped postal, geographic and telephone text.

    python scripts/privacy/scan_postal.py            # report
    python scripts/privacy/scan_postal.py --ci       # exit 1 on any finding

Why this is a separate tool from redact_emails.py
-------------------------------------------------
redact_emails.py finds contact EMAIL addresses. Its name is honest and its
coverage is email-shaped: RESIDUE requires an at-sign or the wreckage of one.
A postal address contains no at-sign, so no setting of that tool could ever
have matched one. check_all.py nevertheless labels it "no email addresses in
tracked zones" while the tool prints "No address-shaped text", and the word
"address" doing double duty there is exactly the kind of wording that lets a
gap read as coverage. This file closes the postal half.

What it deliberately does NOT fire on, and why that is the whole design
----------------------------------------------------------------------
This corpus is unparsed PDF text from academic papers, so it is full of author
affiliation blocks: university departments, corporate labs and a defence
contractor's published point of contact. As of 2026-08-14 there are ten such
addresses in the tracked tree and not one of them is a person's home.

A guard that fired on those ten would be muted by a human inside a week, and
tests/test_privacy_gate.py already records why that is worse than no guard:
"An alarm that fires on `pass@k` gets muted by a human within a week, and a
muted alarm is worse than none because it reads as coverage."

So the discriminator is not a longer street-type list. It is the presence of an
INSTITUTIONAL token in the surrounding window. A published affiliation address
travels with the name of the institution that published it; a leaked home
address does not. That is a property of how the two kinds of text come to
exist, not a heuristic about their spelling, which is why it is worth gating
on. The failure mode it accepts is a home address that happens to sit within
INSTITUTION_WINDOW characters of the word "University" -- reported below as a
known bound rather than hidden.

Every pattern here is scoped to a shape that indicates a DWELLING or a
personal handset:

  UNIT_DWELLING   Unit/Apt/Flat/Villa + number. Note "Suite" and "Level" are
                  absent: both are commercial, and "Level 1" is ordinary prose
                  in this repository's own documentation.
  AU_LOCALITY     Suburb + state + 4-digit postcode. Zero in the corpus today.
                  The corpus is US/UK/EU academic, so an Australian locality
                  appearing in it is anomalous by construction -- this is a
                  tripwire for hand-entered local data, which is the way a
                  real person's home would most plausibly arrive.
  BARE_GEOCODE    A coordinate pair at 4+ decimal places NOT inside a URL.
                  4 decimals is ~11m, which resolves a single dwelling. The
                  one existing pair in the corpus sits inside a Google Maps
                  link to a named nature preserve; a link to a public place is
                  a citation, whereas a bare pair in a data field is a geocode.
                  That distinction is structural, so it is enforced by looking
                  for the URL rather than by allowlisting the coordinates.
  PERSONAL_PHONE  An Australian mobile prefix, or a number labelled Mobile /
                  Cell / Home. The two telephone numbers in the corpus are an
                  institutional switchboard and a published work line; neither
                  is labelled, and neither is a handset.
  STREET_*        Number-then-street (English order) or street-then-number
                  (German/Dutch order), and ONLY when no institutional token
                  appears nearby.

tests/ is excluded from the scan: test_privacy_gate.py holds real addresses as
deliberate fixtures, and a scanner that reported its own test corpus would be
untrustworthy in the one direction that matters.
"""
import argparse
import io
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# How far either side of a street match to look for an institutional token.
# 160 characters is about two lines of extracted PDF text, which is the
# distance between an author's affiliation line and the street beneath it.
INSTITUTION_WINDOW = 160

STREET_TYPE = (
    r"(?:St|Street|Rd|Road|Ave|Avenue|Av|Ln|Lane|Ct|Court|Dr|Drive|Pl|Place|"
    r"Way|Cres|Crescent|Terrace|Tce|Parade|Pde|Hwy|Highway|Blvd|Boulevard|"
    r"Close|Grove|Esplanade|Circuit|Cct|Walk|Rise|Mews|Row|Square|Sq)"
)

# Tokens that mark an address as belonging to an organisation rather than a
# household. Matched case-sensitively where capitalisation is load-bearing.
INSTITUTION = re.compile(
    r"\b(?:Universit(?:y|e|at|eit|ies)|Universidad|Universita|Univ|"
    r"Institut(?:e|es|o|ion)?|Inc|Incorporated|Ltd|Limited|LLC|LLP|GmbH|AG|"
    r"BV|NV|SA|PLC|plc|Corp|Corporation|Company|Co|Department|Dept|Faculty|"
    r"School|College|Academy|Laborator(?:y|ies)|Lab|Labs|Librar(?:y|ies)|"
    r"Cent(?:er|re)|Hospital|Clinic|Foundation|Trust|Council|Ministry|Agency|"
    r"Bureau|Office|Campus|Building|Hall|Suite|Museum|Catapult|Research|"
    r"Association|Society|Consortium|Group|Division|Unit of|Chair of|"
    r"Hochschule|Fachhochschule|Politecnico|Ecole|Escuela|CNRS|INRIA|"
    r"Business School|Graduate School|Medical|Observatory|Academy)\b"
)

# Australia Post allocates postcodes in per-state blocks, so a state and a
# postcode that disagree are not an address. This matters because a bare
# four-digit number is also a year: "Released SA 2019 as a research preview" is
# ordinary prose about a model, and 2019 is not a South Australian postcode.
# Checking the pair against the real allocation is a structural test rather
# than a guess about wording, and it is what an address actually has to satisfy.
# NSW and ACT genuinely overlap in the 2600s; both are accepted there.
STATE_RANGES = {
    "NSW": ((1000, 2599), (2619, 2899), (2921, 2999)),
    "ACT": ((200, 299), (2600, 2618), (2900, 2920)),
    "VIC": ((3000, 3999), (8000, 8999)),
    "QLD": ((4000, 4999), (9000, 9999)),
    "SA": ((5000, 5799), (5800, 5999)),
    "WA": ((6000, 6797), (6800, 6999)),
    "TAS": ((7000, 7799), (7800, 7999)),
    "NT": ((800, 899), (900, 999)),
}


def au_locality_is_plausible(match):
    """True when the postcode falls in a block actually issued to the state."""
    state = match.group("state")
    try:
        postcode = int(match.group("pc"))
    except (TypeError, ValueError):
        return False
    return any(lo <= postcode <= hi for lo, hi in STATE_RANGES.get(state, ()))


PATTERNS = [
    (
        "UNIT_DWELLING",
        re.compile(
            r"\b(?:Unit|Apt|Apartment|Flat|Villa|Townhouse)\s*\.?\s*\d{1,4}"
            r"(?:\s*[/,-]\s*\d{1,5})?\s*[,/]?\s+(?:[A-Z][A-Za-z'-]+\s+){1,3}"
            + STREET_TYPE + r"\b"
        ),
        False,
    ),
    (
        "AU_LOCALITY",
        re.compile(
            r"\b[A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?[\s,]+"
            r"(?P<state>NSW|VIC|QLD|WA|SA|TAS|ACT|NT)[\s,]+(?P<pc>\d{4})\b"
        ),
        False,
    ),
    (
        "BARE_GEOCODE",
        re.compile(r"[-+]?\d{1,3}\.\d{4,}\s*,\s*[-+]?\d{1,3}\.\d{4,}"),
        False,
    ),
    (
        "PERSONAL_PHONE",
        re.compile(
            # Labelled handset: the label is what makes it personal. The colon
            # is required, because "Cell 5" and "the home of human
            # intelligence" are both ordinary text in this corpus and a
            # contact line is punctuated.
            r"(?:\b(?:Mobile|Cell|Cellular|Home|Handy)\b[ \t]*"
            r"(?:phone|no\.?|number)?[ \t]*:[ \t]*\+?\d[\d\s.-]{7,15}\d)"
            # Australian mobile prefix. Two measured false-positive families
            # forced these bounds, and both are "the run continues past the
            # match" rather than anything about phone numbers:
            #   float   "Training power draw (W)": "202329.0409413959"
            #   digest  "content_sha256": "...0426717380a1fd51fed9..."
            # So the boundary rejects an adjacent word character or decimal
            # point, not merely an adjacent digit.
            r"|(?:(?<![\w.])(?:\+?61[\s.-]?4|04)\d{2}[\s.-]?\d{3}[\s.-]?\d{3}"
            r"(?![\w.]))"
        ),
        False,
    ),
    (
        "STREET_NUMBER_FIRST",
        re.compile(
            r"\b\d{1,5}[A-Za-z]?(?:[-/]\d{1,5}[A-Za-z]?)?\s+"
            r"(?:[A-Z][A-Za-z'-]+\s+){1,3}" + STREET_TYPE + r"\b"
        ),
        True,
    ),
    (
        "STREET_NUMBER_LAST",
        re.compile(
            r"\b[A-Z][a-zA-Z'-]{2,}(?:str|strasse|straat|straede|gasse|weg|"
            r"platz|allee|laan|vej|gata|gatan)\.?\s?\d{1,4}\b"
        ),
        True,
    ),
]

# Findings inside a URL are citations, not geocodes or postal fields.
URL_RUN = re.compile(r"(?:https?://|www\.)[^\s\"'<>)\]}]+")

SKIP_PREFIXES = (
    "tests/",                      # deliberate fixtures, see module docstring
    "data/privacy/tombstones/",    # record counts only, by design
    "scripts/privacy/scan_postal.py",
)

SKIP_SUFFIXES = (
    ".sha256", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz",
    ".woff", ".woff2", ".ico", ".db", ".sqlite",
)


def tracked_files():
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=REPO_ROOT, universal_newlines=True
    )
    for rel in out.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        if rel.startswith(SKIP_PREFIXES) or rel.endswith(SKIP_SUFFIXES):
            continue
        path = os.path.join(REPO_ROOT, rel)
        if os.path.isfile(path):
            yield rel, path


def url_spans(line):
    return [(m.start(), m.end()) for m in URL_RUN.finditer(line)]


def inside(span, spans):
    return any(a <= span[0] and span[1] <= b for a, b in spans)


def scan_line(line):
    """Yield (label, start, end) for each dwelling-shaped finding in line."""
    spans = None
    for label, pattern, needs_no_institution in PATTERNS:
        for m in pattern.finditer(line):
            if label in ("BARE_GEOCODE", "STREET_NUMBER_FIRST",
                         "STREET_NUMBER_LAST", "PERSONAL_PHONE"):
                if spans is None:
                    spans = url_spans(line)
                if inside((m.start(), m.end()), spans):
                    continue
            if label == "AU_LOCALITY" and not au_locality_is_plausible(m):
                continue
            if needs_no_institution:
                lo = max(0, m.start() - INSTITUTION_WINDOW)
                hi = min(len(line), m.end() + INSTITUTION_WINDOW)
                if INSTITUTION.search(line[lo:hi]):
                    continue
            yield label, m.start(), m.end()


def scan_repo():
    findings = []
    for rel, path in tracked_files():
        try:
            with io.open(path, encoding="utf-8", errors="replace") as handle:
                for lineno, line in enumerate(handle, 1):
                    for label, start, end in scan_line(line):
                        findings.append((rel, lineno, label, start, end))
        except (IOError, OSError) as exc:
            print("WARN could not read %s: %s" % (rel, exc), file=sys.stderr)
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ci", action="store_true",
                    help="exit 1 if anything is found")
    ap.add_argument("--show-offsets", action="store_true",
                    help="print match offsets; never prints matched text")
    args = ap.parse_args()

    findings = scan_repo()

    if not findings:
        print("No dwelling-shaped postal, geographic or telephone text "
              "in any tracked zone.")
        return 0

    by_label = {}
    for rel, lineno, label, start, end in findings:
        by_label.setdefault(label, []).append((rel, lineno, start, end))

    print("FOUND %d dwelling-shaped item(s) in %d file(s)."
          % (len(findings), len(set(f[0] for f in findings))))
    print("Matched text is NOT printed: this tool must be safe to run in CI,")
    print("whose logs are public on a public repository.")
    for label in sorted(by_label):
        hits = by_label[label]
        print("\n  %s -- %d hit(s)" % (label, len(hits)))
        for rel, lineno, start, end in hits[:25]:
            if args.show_offsets:
                print("    %s:%d (cols %d-%d)" % (rel, lineno, start, end))
            else:
                print("    %s:%d" % (rel, lineno))
        if len(hits) > 25:
            print("    ... and %d more" % (len(hits) - 25))
    print("\nEach hit is a candidate, not a verdict. Confirm whether it is a")
    print("dwelling before redacting, and tombstone what you remove.")
    return 1 if args.ci else 0


if __name__ == "__main__":
    sys.exit(main())
