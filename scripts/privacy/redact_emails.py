"""Redact email addresses from the data zones, and tombstone what was removed.

    python scripts/privacy/redact_emails.py            # report only
    python scripts/privacy/redact_emails.py --write --date YYYY-MM-DD

Why this exists
---------------
The alignment-research import carries descriptions that are unparsed PDF text,
which included the contact addresses printed on academic papers. Those reached
data/serveable/api/timeline_events/, which is public, and were published as
pages on pdoom1.com.

pdoom1-website added a redaction step on 2026-07-29. That scrubbed the OUTPUT,
not the source. A consumer-side fix leaves the addresses here for every other
consumer to rediscover. The fix belongs at the source.

These are real people who did not consent to being in a game's dataset.

Why this parses instead of pattern-matching text
------------------------------------------------
An earlier version substituted on raw file text and produced three distinct
bugs in a row, all the same species:

1. The regex matched from the "n" of a backslash-n escape, consumed it, and
   left a bare backslash before the replacement -- an invalid JSON escape.
   Nine files stopped parsing.
2. The lookbehind added to fix that then SILENTLY SKIPPED every address
   preceded by an escape. Corruption traded for incompleteness.
3. str.splitlines() splits on form feed, vertical tab and U+2028. This corpus
   is extracted PDF text, full of form feeds, so JSONL records were torn in
   half mid-string.

A fourth bug lived in the residue check itself. Its pattern had been written
into a non-raw Python string by a shell heredoc, so the intended word-boundary
escape compiled to a literal BACKSPACE (0x08). The check could therefore never
match anything, and it reported clean while ten records still carried
addresses. It printed as a correct-looking pattern because 0x08 is invisible
in terminal output, and it passed every ASCII check because 0x08 is below 127.

The lesson is not "be careful with regexes". It is that text-level
manipulation of structured data is the wrong tool, and each guard added to
make it safe became another place for a bug to hide. This version parses the
document, redacts decoded string values where escape sequences do not exist,
and re-serialises. It cannot break an escape and it cannot skip one.

The cost is that files come back with normalised formatting. Accepted.

The fifth bug, 2026-08-09, and it was caused by the fix to the fourth
---------------------------------------------------------------------
The response to bug four was to make one function the single source of truth
for both detection and verification, so they could not disagree. They then
could not disagree while both being wrong. EMAIL did not match addresses whose
domain the PDF extractor had broken with a space, nor brace-group notation
naming several authors at once, so the verifier confirmed a clean result and
ten records stayed published for eight months.

CLAUDE.md already had the rule: a check must take at least one input from
OUTSIDE the system it is checking, and merging detection with verification
satisfies the first clause while violating the second. The worked example
recorded there is this very tool.

So verification is now residue_scan(), built on a different principle rather
than a different regex of the same shape, and any disagreement REFUSES the
write. It earned its place within a minute of being added, twice: it caught a
seven-author brace group that EMAIL still missed because the extractor had
line-wrapped it, and it forced the false-positive families to be characterised
rather than assumed.

Coverage was the other half of the failure. The 2026-08-01 run cleaned the raw
dumps and the serveable zone and never listed data/transformed/, which is
tracked, therefore public, and sits between them.

The sixth bug, 2026-08-13: mode (d), which the scanner could not see
--------------------------------------------------------------------
The three modes above are all things the PDF extractor does to an address. The
fourth is something THIS REPOSITORY does to one. Both importers cap a
description at 1,000 characters --

    scripts/enrichment/transform_enriched.py:204
    scripts/transformation/transform_to_timeline_events.py:228
        description = description[:997] + '...'

-- and when that cut lands inside a contact line it severs the address, leaving
the local part, the '@', and however much of the domain fitted:

    "...St.Gallen, Switzerland  \\nleimeister@un..."

RESIDUE ends in "\\.\\s?[A-Za-z]{2,24}", so it requires a TLD. A severed address
has no TLD, so the verifier could not match this at any setting. It was not
misconfigured and the regex was not buggy: the scanner was blind to the mode by
construction, which is why eight months of green runs said nothing about it.
Three files carried it at HEAD, all in the public serveable zone, and it was
live on raw.githubusercontent.com and on pdoom1.com.

Mode (d) is looser than (a)-(c) by nature -- take away the TLD and "pass@k"
and "leimeister@un" differ only in shape -- so it is bounded by measurement
rather than by taste. Measured over data/ entire, tracked and untracked,
2026-08-13: 808,633 decoded strings, 3,046 of them ending at a truncation
marker, 3 with an address-shaped token immediately before that marker, and all
3 were the same real address. The bounds below drop nothing that was real.

What this does NOT fix
----------------------
Redaction applies to HEAD. Addresses remain in git history, in existing clones
and in forks. Removing those requires a history rewrite, which is disruptive,
irreversible, and a separate decision.
"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOMBSTONE_DIR = os.path.join(REPO_ROOT, "data", "privacy", "tombstones")

REDACTION = "[email address redacted]"

# Applied ONLY to decoded string values, where escape sequences do not exist.
# Deliberately a plain raw string with no word-boundary escapes: they are
# unnecessary once the text is decoded, and the last attempt to include one is
# exactly what silently broke the residue check.
#
# WIDENED 2026-08-09, after ten records were found still carrying addresses in
# the public serveable zone. The previous pattern was correct about ordinary
# addresses and blind to three modes this corpus is full of, because the text
# is extracted from PDFs rather than typed:
#
#   1. Whitespace inside the domain, inserted by the extractor:
#      "thilo.hagendorff@uni -tuebingen.de", "roman.yampolskiy@louisville. edu",
#      "bcl.egb@cbs .dk".
#   2. Brace-group notation, which names several people in one address and was
#      the highest-volume mode: "{gilmer,muelly,goodfellow,mrtz,beenkim}@google.com"
#      is five data subjects in one match.
#   3. Whitespace before the '@': "{teinhonglo, sungtc, berlin} @ntnu.edu.tw".
#
# A domain label may be followed by a single optional space on either side of a
# '.' or '-'. It may NOT contain arbitrary runs of spaces, which would let the
# match run on into the following prose.
_LABEL = r"[A-Za-z0-9][A-Za-z0-9\-]{0,62}"
_DOMAIN = r"%s(?:\s?[.\-]\s?%s)*\s?\.\s?[A-Za-z]{2,24}" % (_LABEL, _LABEL)
# The brace body may contain NEWLINES. Excluding them was this pattern's own
# first bug, caught by the independent scanner within a minute of the widening:
# the group naming seven authors at fhstp.ac.at is line-wrapped by the PDF
# extractor between the fourth and fifth name. Bounded by 200 characters and by
# a closing brace immediately before the '@', so it cannot run away.
_LOCAL = r"(?:\{[^{}@]{1,200}\}|[A-Za-z0-9][A-Za-z0-9._%+\-]{0,63})"
EMAIL = re.compile(_LOCAL + r"\s*@\s*" + _DOMAIN)

# MODE (d), ADDED 2026-08-13. The domain is not damaged, it is ABSENT, because
# the importer's 1,000-character cap cut the string in the middle of it. See
# "The sixth bug" above for how this stayed invisible.
#
# Everything here is anchored to the truncation marker the importers actually
# write -- '...', from `description[:997] + '...'`, plus the U+2026 form that
# clean.py normalises INTO that, so a file caught before normalisation is still
# covered. The marker is what makes the rule safe: a severed address exists
# only where a cut happened, and the cut leaves a mark.
#
# Three bounds, and each one is load-bearing against a measured false-positive
# family rather than against an imagined one:
#
#   * The address must be the last thing before the marker, at the END of the
#     string. Measured: every marker-adjacent '@' in the corpus is end-of-
#     string, so the anchor costs nothing and it excludes the whole of prose.
#   * The local part must be attached to the '@' with NO whitespace. That is
#     the difference between "leimeister@un..." and "8 CPU cores @ 2.2...",
#     and it also excludes "@realDonaldTrump" and BibTeX "@article{", which
#     have no local part at all. Mode (c) tolerates a space before the '@';
#     mode (d) cannot afford to, and that gap is stated, not hidden.
#   * The local part must look like a local part rather than an inline token:
#     a brace group, or four-plus characters containing a separator, or -- if
#     it begins its own line, as a contact line in extracted PDF text does --
#     five-plus characters. Short bare tokens are what metric and LaTeX
#     notation is made of: pass(4), Acc(3), lx(2), math(4), ACDC(4).
#
# The residual risk, stated: a severed address with a short bare local part
# starting its own line ("\nbob@un...") is invisible to this. That is the
# price of not eating "pass@k", and pass@k appears in this corpus 21 times per
# dump while bob@un appears zero.
_MARKER = r"(?:\.\.\.|\u2026)"
SEVERED = re.compile(
    r"(?P<addr>" + _LOCAL + r"@(?:[A-Za-z0-9][A-Za-z0-9.\-]{0,23})?)"
    r"(?P<tail>" + _MARKER + r"[ \t]*)$")


def _severed_local_ok(local, line_start):
    """Does this local part look like a person, or like inline notation?"""
    if local.startswith("{"):
        # A brace group is several data subjects in one token and is not a
        # shape any notation family produces to the LEFT of an '@'.
        return True
    if not re.search(r"[A-Za-z]", local):
        return False
    if len(local) >= 4 and re.search(r"[._%+\-]", local):
        return True
    return line_start and len(local) >= 5


def _starts_its_line(text, index):
    """True only for a REAL preceding newline, never for the start of a string.

    Deliberate. "lx@par..." as an entire string looks line-initial and is a
    LaTeX internal cut at the boundary; "...Switzerland  \\nleimeister@un..."
    is a contact line. Requiring the newline separates them, and no description
    in this corpus opens with an address.
    """
    i = index - 1
    while i >= 0 and text[i] in " \t":
        i -= 1
    return i >= 0 and text[i] == "\n"


def severed_match(s):
    """The mode-(d) match in s, or None. Detection side; see severed_residue."""
    m = SEVERED.search(s)
    if not m or REDACTION in m.group("addr"):
        return None
    local = m.group("addr").split("@", 1)[0]
    if not _severed_local_ok(local, _starts_its_line(s, m.start("addr"))):
        return None
    return m

# INDEPENDENTLY WRITTEN, and that is the whole point of it.
#
# The previous version of this file made find_addresses() the single source of
# truth for both "does this need redacting" and "did the redaction work", on the
# reasoning that a separate verifier had once been the buggy one. That reasoning
# is wrong and CLAUDE.md already says why: a check must take at least one input
# from OUTSIDE the system it is checking, and when detection and verification
# share a function, a defect in that function is invisible to both. That is
# exactly what happened -- EMAIL missed three modes, so the verifier agreed the
# files were clean, and ten records stayed public.
#
# So this verifier is built on a different principle rather than a different
# regex of the same shape: it does not try to recognise an address. It finds
# every '@' that has word characters on both sides within a short window, which
# is deliberately over-broad, and the run REFUSES to write when the two
# disagree. A false alarm here costs a human thirty seconds. The alternative
# cost ten records eight months of publication.
RESIDUE = re.compile(r"[A-Za-z0-9][\w.%+\-{}, ]{0,80}@[\s]?[\w.\- ]{1,80}\.\s?[A-Za-z]{2,24}")

TARGET_GLOBS = [
    "data/serveable/api/timeline_events/**/*.json",
    # ADDED 2026-08-09. data/transformed/ is machine-derived and TRACKED, so
    # it is as public as the serveable zone, and it sits between the raw dumps
    # and the enriched projection. Leaving it out meant the 2026-08-01 run
    # cleaned both ends of the pipeline and not its middle, so any re-run of
    # the enrichment transform would have re-injected what had just been
    # removed. The gap was not a judgement about these files; nobody had
    # listed them.
    "data/transformed/**/*.jsonl",
    "data/raw/alignment_research/dumps/**/*.jsonl",
    "data/raw/epoch_ai/dumps/**/*.jsonl",
    "data/raw/mit_airr/dumps/**/*.jsonl",
]


def targets():
    seen = []
    for g in TARGET_GLOBS:
        for p in sorted(glob.glob(os.path.join(REPO_ROOT, g), recursive=True)):
            if os.path.isfile(p) and p not in seen:
                seen.append(p)
    return seen


def jsonl_lines(text):
    """Split JSONL on newline ONLY.

    str.splitlines() also splits on form feed, vertical tab, NEL, U+2028 and
    U+2029. This corpus is extracted PDF text and is full of form feeds.
    """
    return text.split("\n")


def load_doc(path, text):
    """Return (kind, parsed). kind is 'json', 'jsonl', or None if unparseable."""
    if path.endswith(".json"):
        try:
            return "json", json.loads(text)
        except ValueError:
            return None, None
    if path.endswith(".jsonl"):
        records = []
        for line in jsonl_lines(text):
            if not line.strip():
                records.append(None)
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                return None, None
        return "jsonl", records
    return None, None


def walk_strings(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for v in node:
            walk_strings(v, out)
    elif isinstance(node, dict):
        for v in node.values():
            walk_strings(v, out)


def find_addresses(parsed):
    """Every address EMAIL recognises, in every decoded string value.

    Detection only. Verification is residue_scan(), written on a different
    principle, and disagreement between the two refuses the write. See the
    comment above RESIDUE for why they must not be the same function.
    """
    strings = []
    walk_strings(parsed, strings)
    hits = []
    for s in strings:
        hits.extend(EMAIL.findall(s))
        m = severed_match(s)
        if m:
            hits.append(m.group("addr"))
    return hits


def severed_residue(s):
    """Mode (d) for the VERIFIER, and deliberately not severed_match().

    Same reason residue_scan() is not EMAIL: a defect shared by detection and
    verification is invisible to both. So this decomposes the string -- strip
    the marker, take the last line, take its last token, split on '@' -- where
    severed_match() applies a regex, and it drops the line-position condition
    entirely rather than reproducing it. That makes it strictly BROADER, which
    is the safe direction: where the two disagree the run refuses to write and
    a human widens EMAIL, which is exactly the workflow that caught mode (d).

    Honest about the limit of that independence: mode (d) has thin signal, so
    both sides end up agreeing that a bare four-character local part is
    notation rather than a person. They reach it by different code, not by a
    different principle, and if that judgement is wrong both are wrong.
    """
    text = s.rstrip(" \t")
    for marker in ("...", "\u2026"):
        if text.endswith(marker):
            text = text[:-len(marker)]
            break
    else:
        return None
    line = text.split("\n")[-1]
    if REDACTION in line:
        return None
    tokens = line.split()
    if not tokens:
        return None
    token = tokens[-1]
    if token.count("@") != 1:
        return None
    local, frag = token.split("@")
    if local.endswith("}"):
        # A brace group carries spaces and newlines, so the last whitespace
        # token is only its tail. Widen back to the opening brace, which is
        # what bounds it.
        head = text.rsplit("@", 1)[0]
        start = head.rfind("{")
        if start < 0 or "@" in head[start:]:
            return None
        local = head[start:].strip()
        token = local + "@" + frag
    elif not re.match(r"^[A-Za-z0-9][A-Za-z0-9._%+\-]*$", local):
        return None
    if frag and not re.match(r"^[A-Za-z0-9][A-Za-z0-9.\-]*$", frag):
        return None
    if re.search(r"\.[A-Za-z]{2,24}$", frag):
        # It kept a TLD, so it is not severed and modes (a)-(c) own it.
        return None
    if not _severed_local_ok(local, True):
        return None
    return token


def residue_scan(parsed):
    """Anything address-SHAPED that survived, by a deliberately over-broad rule.

    Not EMAIL, and not a variant of it. This exists to disagree.
    """
    strings = []
    walk_strings(parsed, strings)
    hits = []
    for s in strings:
        for m in RESIDUE.finditer(s):
            frag = m.group(0)
            if REDACTION in frag:
                continue
            # RESIDUE tolerates whitespace in the domain because the PDF
            # extractor inserts it -- "cbs .dk", "louisville. edu". Prose does
            # not stop at a domain, so without a bound the match runs on into
            # the sentence and every '@' in the corpus becomes a hit. Measured
            # on the 2025-12-24 dump: 21 fragments, 21 of them false, in four
            # families -- LaTeX internals (lx@paragraphsign, math@degree),
            # social handles (@realDonaldTrump, @jade), metric notation
            # (pass@k, Acc@100, P@K) and hardware specs (@ 2.20GHz).
            #
            # A real extraction artefact is one broken token, never a clause.
            # So: at most ONE whitespace character after the '@', and a domain
            # no longer than 40 characters. This is a bound on the SHAPE of the
            # damage, not a list of things to ignore -- an allowlist would have
            # to grow every time the corpus does.
            #
            # ONE, not two: at two, "our pass@k metric. TransCoder" survives as
            # a false positive. Every real artefact measured in this corpus has
            # exactly one inserted space -- "cbs .dk", "louisville. edu",
            # "uni -tuebingen.de". The residual risk is stated rather than
            # hidden: a domain broken twice by the extractor would be invisible
            # to this verifier, though EMAIL, which tolerates a space at every
            # label boundary, would still match it.
            domain = frag.split("@", 1)[1]
            if sum(1 for c in domain if c.isspace()) > 1 or len(domain) > 40:
                continue
            hits.append(frag.strip())
        # Mode (d). RESIDUE cannot reach these: it ends in a TLD and a severed
        # address has none, so this is a second pass rather than a looser
        # RESIDUE. Loosening RESIDUE to make the TLD optional would have made
        # every '@' in 800,000 strings a hit.
        severed = severed_residue(s)
        if severed:
            hits.append(severed)
    return hits


def scrub(node, counter):
    if isinstance(node, str):
        new, n = EMAIL.subn(REDACTION, node)
        counter[0] += n
        # Mode (d), after EMAIL rather than before it: an address that kept its
        # TLD is EMAIL's, and once EMAIL has replaced it there is no '@' left
        # for this to find. The truncation marker is KEPT. It is the importer's
        # mark that prose was cut, not part of the address, and removing it
        # would quietly turn a truncated description into an apparently
        # complete one.
        m = severed_match(new)
        if m:
            new = new[:m.start("addr")] + REDACTION + m.group("tail")
            counter[0] += 1
        return new
    if isinstance(node, list):
        return [scrub(v, counter) for v in node]
    if isinstance(node, dict):
        return dict((k, scrub(v, counter)) for k, v in node.items())
    return node


def serialise(kind, parsed):
    if kind == "json":
        return json.dumps(parsed, indent=2, ensure_ascii=True) + "\n"
    lines = []
    for rec in parsed:
        lines.append("" if rec is None else json.dumps(rec, ensure_ascii=True))
    return "\n".join(lines) + "\n"


def write_text(path, text):
    """Temp file plus os.replace.

    Never open an existing file with encoding='ascii' for writing: Python
    truncates on open and then raises on the first non-ASCII byte, destroying
    the file before the error surfaces.
    """
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked(paths):
    """Filter to files git actually tracks.

    The distinction is the whole scope of the gate and it is not cosmetic. The
    196MB alignment_research dump is gitignored, so its contents were never
    published and a machine that happens to hold it must not fail the build for
    everyone else. Same treatment data/raw/ gets in check_transcoding.py:
    reported, not gated.

    git is the authority here rather than a hardcoded list, which also makes
    this an input from outside the thing being checked -- a file added to a
    tracked zone tomorrow is covered without anyone remembering to add it.
    """
    if not paths:
        return []
    rels = [os.path.relpath(p, REPO_ROOT).replace("\\", "/") for p in paths]
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "-z", "--"] + rels,
            cwd=REPO_ROOT).decode("utf-8")
    except (OSError, subprocess.CalledProcessError):
        # No git, or git failed. Gate everything rather than silently
        # narrowing: a check that quietly shrinks its own scope on error is
        # the failure this repository keeps finding.
        sys.stderr.write("git ls-files unavailable; gating ALL targets.\n")
        return paths
    known = set(n for n in out.split("\0") if n)
    return [p for p, rel in zip(paths, rels) if rel in known]


def ci_gate():
    """Assert no TRACKED file carries an address-shaped fragment. Never writes.

    Asserts on residue_scan, the independently written scanner, NOT on EMAIL.
    Gating on EMAIL would make the redactor its own examiner, which is exactly
    how ten records stayed published for eight months: the pattern that failed
    to match them was also the pattern asked whether anything had been missed.
    """
    gated = tracked(targets())
    skipped = len(targets()) - len(gated)
    bad = 0
    for path in gated:
        rel = os.path.relpath(path, REPO_ROOT).replace("\\", "/")
        text = io.open(path, encoding="utf-8").read()
        kind, parsed = load_doc(path, text)
        if kind is None:
            print("UNPARSEABLE %s" % rel)
            bad += 1
            continue
        left = residue_scan(parsed)
        if left:
            # Count and file only. A privacy alarm that prints the addresses
            # it found publishes them into the CI log, which is public.
            print("FAIL %-64s %d address-shaped fragment(s)" % (rel, len(left)))
            bad += 1
    print()
    print("tracked files scanned : %d" % len(gated))
    print("untracked, reported not gated: %d" % skipped)
    if bad:
        print()
        print("%d file(s) carry address-shaped text. Run:" % bad)
        print("    python scripts/privacy/redact_emails.py --write --date YYYY-MM-DD")
        return 1
    print("No address-shaped text in any tracked zone.")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="actually redact. Without this, reports only.")
    ap.add_argument("--date", default=None,
                    help="ISO date for the tombstone. Required with --write; "
                         "never guessed, because a fabricated clock is "
                         "indistinguishable from a real one later.")
    ap.add_argument("--ci", action="store_true",
                    help="gate. Exit 1 if any TRACKED file still carries an "
                         "address-shaped fragment. Never writes.")
    args = ap.parse_args()

    if args.write and not args.date:
        sys.stderr.write("--write requires --date YYYY-MM-DD.\n")
        return 2
    if args.ci and args.write:
        sys.stderr.write("--ci never writes; do not combine it with --write.\n")
        return 2

    if args.ci:
        return ci_gate()

    report = []
    failed = []
    all_unique = set()
    total = 0

    for path in targets():
        rel = os.path.relpath(path, REPO_ROOT).replace("\\", "/")
        text = io.open(path, encoding="utf-8").read()
        kind, parsed = load_doc(path, text)
        if kind is None:
            failed.append("%s: does not parse; not touched" % rel)
            continue

        hits = find_addresses(parsed)
        residue_in = residue_scan(parsed)
        if not hits and not residue_in:
            continue

        # The two scanners disagree about this file BEFORE any scrubbing. That
        # is the condition the old single-function design could not express,
        # and it is the condition that let ten records stay public. Report it
        # and refuse the file rather than trusting the narrower answer.
        if residue_in and not hits:
            failed.append(
                "%s: %d address-shaped fragment(s) that EMAIL does not match; "
                "widen EMAIL before writing" % (rel, len(residue_in)))
            print("%-70s DISAGREEMENT residue=%d email=0" % (rel, len(residue_in)))
            continue

        uniq = set(h.lower() for h in hits)
        all_unique |= uniq
        total += len(hits)
        entry = {
            "file": rel,
            "occurrences": len(hits),
            "unique": len(uniq),
            "domains": dict(sorted(Counter(
                h.split("@", 1)[1].lower() for h in uniq).items())),
        }
        report.append(entry)
        # Counts and domains only. A redaction log that reprints what it
        # redacted is not a redaction.
        print("%-70s %4d occ  %3d uniq" % (rel, len(hits), len(uniq)))

        if not args.write:
            continue

        counter = [0]
        cleaned = scrub(parsed, counter)

        if find_addresses(cleaned):
            failed.append("%s: addresses survived scrubbing; not written" % rel)
            continue
        left = residue_scan(cleaned)
        if left:
            failed.append(
                "%s: the independent scanner still sees %d address-shaped "
                "fragment(s) after scrubbing; not written" % (rel, len(left)))
            continue

        out = serialise(kind, cleaned)
        kind2, reparsed = load_doc(path, out)
        if kind2 is None:
            failed.append("%s: output would not parse; not written" % rel)
            continue
        if find_addresses(reparsed):
            failed.append("%s: addresses reappeared after serialisation; "
                          "not written" % rel)
            continue
        if residue_scan(reparsed):
            failed.append("%s: the independent scanner sees address-shaped "
                          "fragments after serialisation; not written" % rel)
            continue

        write_text(path, out)
        entry["replacements"] = counter[0]
        entry["sha256_after_redaction"] = sha256_of(path)

    print()
    print("files affected    : %d" % len(report))
    print("unique addresses  : %d" % len(all_unique))
    print("total occurrences : %d" % total)
    for f in failed:
        print("REFUSED: " + f)

    if not args.write:
        print()
        print("REPORT ONLY. Re-run with --write --date YYYY-MM-DD.")
        return 0

    if not os.path.isdir(TOMBSTONE_DIR):
        os.makedirs(TOMBSTONE_DIR)

    tomb = {
        "tombstone_id": "email-redaction-%s" % args.date,
        "date": args.date,
        "reason_category": "personal_data_minimisation",
        "reason": (
            "Contact email addresses printed on academic papers were carried "
            "into descriptions by an unparsed-PDF-text import and reached the "
            "serveable zone, which is public. The data subjects did not "
            "consent to inclusion in a game dataset."
        ),
        "action": ("email addresses replaced with %r inside decoded string "
                   "values; documents re-serialised" % REDACTION),
        "content_recorded": False,
        "note_on_content": (
            "No redacted content is recorded here, not even hashed or "
            "partial. Counts and domains only. A tombstone that preserves "
            "what it erased defeats its purpose."
        ),
        "limits": (
            "Applies to HEAD only. Addresses remain in git history, in "
            "existing clones and in forks. Removing those requires a history "
            "rewrite, which is a separate and irreversible decision."
        ),
        "raw_zone_exception": (
            "data/raw/ is immutable by contract. CLAUDE.md permits exactly "
            "one exception, a privacy tombstone. The MANIFEST.sha256 entries "
            "are deliberately NOT updated: the original hash stays as proof "
            "of what the file was, and sha256_after_redaction below records "
            "what it became. check_invariants accepts a mismatch only when "
            "the current hash matches this record, so editing raw without an "
            "attributable tombstone still fails a build."
        ),
        "serveable_zone_anomaly": (
            "data/serveable/ is normally a build output that is never "
            "hand-edited. The timeline_events collections have no current "
            "producer, so they were edited in place. That is a pipeline "
            "defect, recorded rather than hidden. See issue #45."
        ),
        "affected": report,
        "refused": failed,
        "totals": {
            "files": len(report),
            "unique_addresses": len(all_unique),
            "occurrences": total,
        },
    }

    tomb_path = os.path.join(TOMBSTONE_DIR, "%s.json" % tomb["tombstone_id"])

    # MERGE rather than overwrite, added 2026-08-09 after this bit us.
    #
    # A second run on the same date finds nothing to do in the files the first
    # run already cleaned, so those files are absent from the second run's
    # report -- and writing that report over the first one DELETES their
    # recorded post-redaction digests. check_invariants then sees a raw file
    # whose hash matches neither its manifest nor any tombstone, which is a
    # hard failure by design, and the evidence needed to clear it has been
    # destroyed by the tool that was supposed to record it.
    #
    # Iterating on a redaction pattern means re-running, so this is the normal
    # case rather than an edge one. Entries are merged by file, later run wins.
    if os.path.isfile(tomb_path):
        try:
            with io.open(tomb_path, encoding="utf-8") as handle:
                prior = json.load(handle)
        except ValueError:
            prior = None
        if prior:
            merged = dict((e["file"], e) for e in prior.get("affected", []))
            for entry in tomb["affected"]:
                merged[entry["file"]] = entry
            tomb["affected"] = [merged[k] for k in sorted(merged)]
            tomb["totals"]["files"] = len(tomb["affected"])
            tomb["merged_with_earlier_run_on_same_date"] = True

    write_text(tomb_path, json.dumps(tomb, indent=2, ensure_ascii=True) + "\n")
    print()
    print("wrote %s" % os.path.relpath(tomb_path, REPO_ROOT).replace("\\", "/"))
    if failed:
        print("%d file(s) refused; the tombstone covers only what was written."
              % len(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
