"""Produce all_events.json, the most-consumed file in the ecosystem.

    python scripts/build/project_timeline_events.py            # write
    python scripts/build/project_timeline_events.py --check    # assert committed == fresh

Why this exists
---------------
Until now `data/serveable/api/timeline_events/all_events.json` had NO PRODUCER.
1,194 records, written by two commits on 2025-12-24 and never regenerated. It is
the only file pdoom1-website's daily sync reads and the origin of the game's
1,194-record snapshot, and nothing in this repository could rebuild it.

The consequence was not theoretical. A file that cannot be rebuilt cannot be
corrected at source, so every fix to it was a hand-edit to a zone whose contract
forbids hand-editing -- the PII redaction had to do exactly that, and its
tombstone records the anomaly rather than hiding it.

What this does NOT decide
-------------------------
Whether the 1,166 bulk research records belong in this collection at all is an
open question (pdoom-data#65: they fail `event_v1`, the schema they are published
under). All three seats voted for two projections; the contents question was not
ruled and this script does not rule it. It reproduces TODAY's composition and
makes it checkable. The split point is `build()`; changing it later is an edit,
not a project.

Composition, verified by set equality rather than assumed
---------------------------------------------------------
    data/raw/events/*.json                              28 hand-authored
    UNION
    .../timeline_events/enriched_alignment_research/  1,166 bulk arXiv + distill
    = 1,194, exactly the committed set.

WHAT REBUILDING IT IMMEDIATELY FOUND
------------------------------------
Two records, `uk_ai_safety_to_security_2025` and `us_aisi_to_caisi_2025`, exist
in three mutually inconsistent forms, and all three of this repo's documented
Windows text landmines are visible in that one pair:

  institutional_decay_events.json   'UK AI Safety Institute <U+2192> ...' CORRECT
  historical_events.json            'UK AI Safety Institute ? ...'       the '?'
                                    fallback, the exact shredding CLAUDE.md warns
                                    fix_ascii.py would do to every arrow
  all_events.json (SERVED, PUBLIC)  'UK AI Safety Institute \xe2\u2020\u2019 ...'

That third form is mojibake: U+2192 encoded UTF-8 and decoded CP1252. It is
verified, not inferred -- `served.encode('cp1252').decode('utf-8')` returns the
correct title exactly. This is the transcoding species from coordination#10,
whose whole point is that it injects PLAUSIBLE PRINTABLE characters, so a
control-character scan returns clean on a corrupted file.

It reached 1,194 public pages and the game's snapshot, and nothing saw it,
because a file with no producer has nothing to be compared against.

The repair is neither of the two damaged forms. Per CLAUDE.md: use an explicit
substitution map that ERRORS on unmapped characters, never a '?' fallback. So
U+2192 becomes '->' and any non-ASCII character not in the map fails the build
rather than being guessed at.

Ordering and normalisation, and how they were established
----------------------------------------------------------
Established by differencing against the committed file, not by preference:
`tags` and `sources` are sorted; every other field is passed through. That
reproduces 1,192 of 1,194 records exactly. The remaining two are the corruption
above, which this script deliberately does not reproduce.

Where two raw files carry the same id, precedence is explicit below rather than
incidental to filename order.
"""
import argparse
import io
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(REPO_ROOT, "data", "raw", "events")
OUT_DIR = os.path.join(REPO_ROOT, "data", "serveable", "api", "timeline_events")
ENRICHED = os.path.join(
    OUT_DIR, "enriched_alignment_research", "enriched_alignment_research_events.json")

# Explicit precedence, lowest priority LAST. historical_events.json is last
# because it is the file that was run through a '?' fallback: its copies of the
# two contested records have had their arrows destroyed, so any other file's
# copy is better evidence of what the record says.
RAW_PRECEDENCE = (
    "historical_events.json",
    "funding_catastrophe_events.json",
    "organizational_crisis_events.json",
    "technical_research_breakthrough_events.json",
    "institutional_decay_events.json",
)

# Explicit substitution map. A character that is not in here FAILS the build.
# CLAUDE.md: never a '?' fallback -- it shredded every arrow in the file that
# holds the damaged copies of these very records.
ASCII_SUBSTITUTIONS = {
    u"\u2192": "->",      # rightwards arrow
    u"\u2190": "<-",      # leftwards arrow
    u"\u2014": " -- ",    # em dash
    u"\u2013": "-",       # en dash
    u"\u2018": "'",       # left single quote
    u"\u2019": "'",       # right single quote
    u"\u201c": '"',       # left double quote
    u"\u201d": '"',       # right double quote
    u"\u2026": "...",     # ellipsis
    u"\u00a0": " ",       # non-breaking space
}

SORTED_LIST_FIELDS = ("tags", "sources")


def load(path):
    with io.open(path, encoding="utf-8") as handle:
        return json.load(handle)


def repair_mojibake(text):
    """Recover a UTF-8 string that was decoded as CP1252, if that is what it is.

    Only returns a different string when the round trip SUCCEEDS, which is the
    signature of the specific corruption rather than a guess about it. A string
    that is merely unusual is returned untouched.
    """
    if all(ord(ch) < 128 for ch in text):
        return text
    try:
        recovered = text.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    if recovered == text:
        return text
    return recovered


def to_ascii(text, where, problems):
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        elif ch in ASCII_SUBSTITUTIONS:
            out.append(ASCII_SUBSTITUTIONS[ch])
        else:
            problems.append("%s: no substitution for %r (U+%04X); add it to "
                            "ASCII_SUBSTITUTIONS deliberately rather than "
                            "guessing" % (where, ch, ord(ch)))
            out.append(ch)
    return "".join(out)


def normalise(record, record_id, problems):
    out = {}
    for field, value in record.items():
        if field in SORTED_LIST_FIELDS and isinstance(value, list):
            value = sorted(value)
        if isinstance(value, str):
            value = to_ascii(repair_mojibake(value), "%s.%s" % (record_id, field),
                             problems)
        elif isinstance(value, list):
            value = [
                to_ascii(repair_mojibake(v), "%s.%s[]" % (record_id, field), problems)
                if isinstance(v, str) else v
                for v in value
            ]
        out[field] = value
    return out


def build():
    problems = []
    records = {}
    provenance = {}

    names = sorted(n for n in os.listdir(RAW_DIR) if n.endswith(".json"))
    unknown = [n for n in names if n not in RAW_PRECEDENCE]
    if unknown:
        problems.append("raw/events holds files with no declared precedence: %s. "
                        "Add them to RAW_PRECEDENCE so which copy wins is a "
                        "decision rather than an accident of filename order."
                        % ", ".join(unknown))

    for name in RAW_PRECEDENCE:
        path = os.path.join(RAW_DIR, name)
        if not os.path.isfile(path):
            continue
        for record_id, record in load(path).items():
            records[record_id] = normalise(record, record_id, problems)
            provenance[record_id] = name

    hand_authored = len(records)

    for record in load(ENRICHED):
        record_id = record["id"]
        records[record_id] = normalise(record, record_id, problems)
        provenance.setdefault(record_id, "enriched_alignment_research")

    return records, hand_authored, provenance, problems


def render(records, hand_authored, provenance):
    payload = dict(records)

    by_source = {}
    for name in provenance.values():
        by_source[name] = by_source.get(name, 0) + 1

    lineage = {
        "build_version": "0.1.0",
        "producer": "scripts/build/project_timeline_events.py",
        "counts": {
            "records": len(records),
            "hand_authored": hand_authored,
            "bulk_research": len(records) - hand_authored,
            "by_source_file": dict(sorted(by_source.items())),
        },
        "composition": (
            "data/raw/events/*.json UNION "
            "data/serveable/api/timeline_events/enriched_alignment_research/. "
            "Verified by set equality against the committed file, not assumed."
        ),
        "normalisation": (
            "tags and sources are sorted; all other fields pass through. "
            "Established by differencing against the committed file."
        ),
        "known_defect": (
            "1,166 of these 1,194 records fail event_v1, the schema this "
            "collection is published under. Tracked as pdoom-data#65. This "
            "producer does not rule on it -- all three seats voted for two "
            "projections and the contents question is open."
        ),
        "repairs_applied": (
            "uk_ai_safety_to_security_2025 and us_aisi_to_caisi_2025 carried a "
            "UTF-8-decoded-as-CP1252 arrow in the served file and a '?' fallback "
            "in historical_events.json. Both are replaced with '->' via an "
            "explicit substitution map that errors on unmapped characters."
        ),
        "policy": {
            "identity": (
                "pdoom1 made a source commit, record count and generated-at "
                "stamp a CONDITION of its vote, so a consumer can state which "
                "corpus it read. The record count is here. The commit and "
                "timestamp are NOT YET EMITTED, because a wall-clock stamp "
                "would make --check non-deterministic and the release-time "
                "stamping step does not exist yet. This is an unmet condition, "
                "stated rather than quietly dropped."
            ),
            "zone": "data/serveable/ is a build output. Never hand-edit it.",
        },
    }
    return payload, lineage


def write_json(path, obj):
    """Write via temp + os.replace.

    Never open an existing file with encoding='ascii' for writing: Python
    truncates on open and then raises on the first non-ASCII byte, destroying the
    file before the error surfaces. That ate two files in one session.
    """
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=True, sort_keys=False)
        handle.write("\n")
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="assert the committed output matches a fresh build; "
                             "write nothing")
    parser.add_argument("--diff", action="store_true",
                        help="list record ids that differ from the committed file")
    args = parser.parse_args()

    records, hand_authored, provenance, problems = build()
    for problem in problems:
        print("BUILD: " + problem)
    if problems:
        return 1

    payload, lineage = render(records, hand_authored, provenance)

    print("records             : %d" % lineage["counts"]["records"])
    print("  hand authored     : %d" % lineage["counts"]["hand_authored"])
    print("  bulk research     : %d" % lineage["counts"]["bulk_research"])

    feed_path = os.path.join(OUT_DIR, "all_events.json")
    lineage_path = os.path.join(OUT_DIR, "LINEAGE.json")

    if args.check or args.diff:
        if not os.path.isfile(feed_path):
            print("CHECK FAILED: %s does not exist" % feed_path)
            return 1
        committed = load(feed_path)
        differing = sorted(set(committed) ^ set(payload))
        changed = sorted(k for k in set(committed) & set(payload)
                         if committed[k] != payload[k])
        if args.diff:
            print("ids only on one side : %d" % len(differing))
            for record_id in differing[:20]:
                print("  " + record_id)
            print("ids with changed content: %d" % len(changed))
            for record_id in changed[:20]:
                print("  " + record_id)
            return 0
        if committed != payload:
            print("CHECK FAILED: committed feed differs from a fresh build "
                  "(%d ids on one side, %d changed). data/serveable/ is a build "
                  "output; re-run without --check."
                  % (len(differing), len(changed)))
            return 1
        if os.path.isfile(lineage_path):
            if load(lineage_path) != lineage:
                print("CHECK FAILED: committed LINEAGE differs from a fresh build.")
                return 1
        print("CHECK OK: committed output matches a fresh build")
        return 0

    write_json(feed_path, payload)
    write_json(lineage_path, lineage)
    print("wrote %s" % os.path.relpath(feed_path, REPO_ROOT).replace("\\", "/"))
    print("wrote %s" % os.path.relpath(lineage_path, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
