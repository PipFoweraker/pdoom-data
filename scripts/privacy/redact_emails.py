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
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOMBSTONE_DIR = os.path.join(REPO_ROOT, "data", "privacy", "tombstones")

REDACTION = "[email address redacted]"

# Applied ONLY to decoded string values, where escape sequences do not exist.
# Deliberately a plain raw string with no word-boundary escapes: they are
# unnecessary once the text is decoded, and the last attempt to include one is
# exactly what silently broke the residue check.
EMAIL = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._%+-]{0,63}@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")

TARGET_GLOBS = [
    "data/serveable/api/timeline_events/**/*.json",
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
    """Every address in every decoded string value.

    Deliberately the single source of truth for BOTH "does this file need
    redacting" and "did the redaction work". When detection and verification
    use different code they can disagree, and last time the verifier was the
    one that was wrong.
    """
    strings = []
    walk_strings(parsed, strings)
    hits = []
    for s in strings:
        hits.extend(EMAIL.findall(s))
    return hits


def scrub(node, counter):
    if isinstance(node, str):
        new, n = EMAIL.subn(REDACTION, node)
        counter[0] += n
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
    args = ap.parse_args()

    if args.write and not args.date:
        sys.stderr.write("--write requires --date YYYY-MM-DD.\n")
        return 2

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
        if not hits:
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

        out = serialise(kind, cleaned)
        kind2, reparsed = load_doc(path, out)
        if kind2 is None:
            failed.append("%s: output would not parse; not written" % rel)
            continue
        if find_addresses(reparsed):
            failed.append("%s: addresses reappeared after serialisation; "
                          "not written" % rel)
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
