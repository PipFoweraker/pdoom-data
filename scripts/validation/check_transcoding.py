"""Assert that no data file carries a UTF-8-decoded-as-CP1252 corruption.

    python scripts/validation/check_transcoding.py
    python scripts/validation/check_transcoding.py --verbose

Why this exists
---------------
On 2026-08-06, writing the missing producer for `all_events.json` (pdoom-data#52)
found two served records whose titles were mojibake: `U+2192` encoded UTF-8 and
decoded as CP1252, so `UK AI Safety Institute -> AI Security Institute` reached
the public site as `UK AI Safety Institute <U+00E2><U+2020><U+2019> ...`. It had
been served that way since 2025-12-24.

Every gate this repository had passed on that file, and each for a defensible
reason:

  the ASCII gate       `json.dump(ensure_ascii=True)` escapes the corruption to
                       `\\uXXXX`, so the bytes on disk really are ASCII
  the control scan     all three injected codepoints are above 32
  count invariants     the record count of a corrupted record is still 1
  schema validation    a corrupted title is still a string

That is the defining property of the transcoding species (`coordination#10`):
**it injects plausible printable characters.** Structural checks cannot see it,
because nothing about the result is structurally wrong. A well-formed file that
is wrong.

Why this is a SEPARATE file from the producer
---------------------------------------------
`project_timeline_events.py` already repairs this corruption on the way through,
via `repair_mojibake()`. Detecting it by calling that function would satisfy
clause 1 of the check rule (`pdoom1#1075`) and **violate clause 2**: a defect in
the shared function would be invisible to both the repair and the check, which is
exactly how the redaction verifier here reported clean while ten records still
carried addresses.

So this file deliberately does not import from `scripts/build/`. It was written
against the corruption's definition rather than against the repair's
implementation, and if the two disagree that disagreement is the finding.

The detection, and why the round trip is the load-bearing half
---------------------------------------------------------------
A string is reported when both hold:

  1. it contains one of the LEAD characters -- `U+00C2`, `U+00C3`, `U+00E2` --
     which are what the first byte of a 2- or 3-byte UTF-8 sequence becomes when
     read as CP1252. Cheap, and it is the grep `coordination#10` already
     documents.
  2. `s.encode('cp1252').decode('utf-8')` SUCCEEDS and returns something
     DIFFERENT.

Clause 1 alone over-reports: French and Portuguese prose in a source title is
not corruption. Clause 2 is what makes it a measurement rather than a guess --
arbitrary text does not survive that round trip, because valid UTF-8 is a
narrow target. The pair has no false positive in this repository's 4,800-odd
records today; where one appears, the fix is a listed exemption with a reason,
never a loosened rule.

What this does NOT catch, stated because a check that oversells itself is worse
than none:

  * the `?` fallback, the other form the same two records exist in. `?` is a
    legitimate character and the original codepoint is gone, so the damage is
    unrecoverable AND undetectable from the artifact alone. Only comparison
    against a better source finds it -- which is what a producer with `--check`
    is for.
  * a double transcode, or one whose second decode is not valid UTF-8. Those
    fail the round trip and pass this check. No instance is known here.
  * corruption in fields this walks past, if any zone gains a non-JSON format.
"""
import argparse
import io
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_ROOT, "data")

# The first byte of a UTF-8 multi-byte sequence, read as CP1252. Any mojibake of
# this species contains at least one of these; nothing else is scanned.
#
# Written as escapes, not as literals. This repository is ASCII-only and enforces
# it, so a check for non-ASCII corruption cannot spell its own needle in the
# corruption it hunts. U+00C2 is A-circumflex, U+00C3 A-tilde, U+00E2 a-circumflex.
LEAD = ("\u00c2", "\u00c3", "\u00e2")

# path (repo-relative, forward slashes) -> why a hit there is not a defect.
# Empty, and it should stay that way. An entry here is a claim that a file
# legitimately contains a lead character in text that also survives a CP1252 ->
# UTF-8 round trip, which is a coincidence rare enough to want the reason on the
# record.
EXEMPT = {}


def recovers(text):
    """Return the recovered string if text is mojibake of this species, else None."""
    if not any(ch in text for ch in LEAD):
        return None
    try:
        recovered = text.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None
    return recovered if recovered != text else None


def walk(node, path, found):
    """Depth-first over parsed JSON, reporting every corrupted string with its path."""
    if isinstance(node, str):
        recovered = recovers(node)
        if recovered is not None:
            found.append((path, node, recovered))
    elif isinstance(node, dict):
        for key, value in node.items():
            recovered = recovers(key)
            if recovered is not None:
                found.append((path + "/<key>", key, recovered))
            walk(value, "%s/%s" % (path, key), found)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            walk(value, "%s[%d]" % (path, i), found)


def scan_file(abspath, relpath):
    """Parse one .json or .jsonl file and return its findings.

    A parse failure is returned as a finding rather than raised: this check is
    about content, and a file that cannot be parsed is a different check's job,
    but silently skipping it would let a corrupted file pass by being broken.
    """
    found = []
    try:
        text = io.open(abspath, encoding="utf-8").read()
    except UnicodeDecodeError as e:
        return [("%s (not valid UTF-8)" % relpath, str(e), "")]

    if relpath.endswith(".jsonl"):
        # split("\n"), NOT splitlines(). str.splitlines() also breaks on U+000B,
        # U+000C, U+0085, U+2028 and U+2029, and this corpus contains those
        # characters INSIDE JSON string values. Using it fragmented 12 records
        # into halves that each failed to parse, and the first draft of this
        # check reported all 12 as findings -- a checker inventing failures in
        # the data it was written to protect. JSONL is delimited by U+000A and
        # nothing else.
        for lineno, line in enumerate(text.split("\n"), 1):
            line = line.strip()
            if not line:
                continue
            try:
                walk(json.loads(line), "%s:%d" % (relpath, lineno), found)
            except ValueError:
                found.append(("%s:%d" % (relpath, lineno), "does not parse as JSON", ""))
    else:
        try:
            walk(json.loads(text), relpath, found)
        except ValueError:
            found.append((relpath, "does not parse as JSON", ""))
    return found


def show(actual, recovered, window=30):
    """Print the corruption and its repair as a short ASCII-safe window.

    Two properties, both learned the hard way while writing this:

    WINDOW. The corpus holds 40 KB `text` fields. A first draft printed the
    whole string, so one finding in a newsletter dump produced 48 KB of output
    and buried the finding it had just made.

    ascii(). The corruption is by definition non-ASCII, and this console
    re-mangles it on the way out -- a corrupted title printed here came back
    looking CORRECT, which very nearly got this check discarded as a false
    positive. Escaping means the reader sees codepoints, not whatever the
    terminal decided to render.
    """
    if not recovered:
        print("  " + actual)
        return
    hits = [actual.find(c) for c in LEAD if c in actual]
    i = min(hits) if hits else 0
    lo, hi = max(0, i - window), i + window // 2
    print("  is       : " + ascii(actual[lo:hi]))
    print("  should be: " + ascii(recovered[lo:hi]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true",
                        help="print every file scanned, not only the findings")
    args = parser.parse_args()

    findings = []
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(DATA_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in sorted(filenames):
            if not name.endswith((".json", ".jsonl")):
                continue
            abspath = os.path.join(dirpath, name)
            relpath = os.path.relpath(abspath, REPO_ROOT).replace("\\", "/")
            if relpath in EXEMPT:
                print("exempt: %s -- %s" % (relpath, EXEMPT[relpath]))
                continue
            scanned += 1
            if args.verbose:
                print("scanning " + relpath)
            findings.extend(scan_file(abspath, relpath))

    print("scanned %d JSON/JSONL files under data/" % scanned)

    # Zone split, and it is the difference between a usable gate and a red build
    # nobody can fix. data/raw/ is IMMUTABLE by contract: a corrupted string in a
    # 2025-12-24 dump is a true fact about what the source delivered, and
    # repairing it in place would be forging the historical record. So raw is
    # REPORTED. Every derived zone is GATED, because a corruption there is
    # reproducible by re-running code and therefore fixable at the producer.
    gating = [f for f in findings if not f[0].startswith("data/raw/")]
    reported = [f for f in findings if f[0].startswith("data/raw/")]

    for path, actual, recovered in reported:
        print()
        print("note: RAW, not gated -- " + path)
        show(actual, recovered)
    if reported:
        print()
        print("%d corruption(s) in data/raw/. Immutable by contract, so they are"
              % len(reported))
        print("not failures here. They are the reason a producer must repair on")
        print("the way THROUGH, and the reason the derived zones are gated below.")

    if gating:
        print()
        for path, actual, recovered in gating:
            print("FAIL: " + path)
            show(actual, recovered)
        print()
        print("%d transcoding corruption(s) in a DERIVED zone. These are UTF-8"
              % len(gating))
        print("bytes that were read as CP1252. Repair at the PRODUCER, never by")
        print("hand-editing a served file -- and never with a '?' fallback, which")
        print("destroys the character instead of recovering it.")
        return 1

    print("No transcoding corruption in any derived zone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
