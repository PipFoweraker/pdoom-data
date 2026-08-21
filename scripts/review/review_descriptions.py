#!/usr/bin/env python3
"""Eyeball each proposed description against the one being served. One key each.

    python scripts/review/review_descriptions.py --by "Pip Foweraker" \
        --proposals data/raw/arxiv_abstracts/dumps/<stamp>/data.jsonl

    ... --flagged     only the ones with a warning on them
    ... --limit 50
    ... --redo        revisit records already decided

Why this exists
---------------
1,166 of 1,194 served timeline events describe themselves with a slice of raw
PDF text -- "1 Introduction", "1 Background and Overview", a technical report
cover page. Median 30 characters. They are 97.7% of the public event pages
(pdoom-data#88).

`arxiv_abstracts.py` fetches the author-written abstract from arXiv for each
one. **Neither that tool nor this one composes any prose.** The proposal is the
source's own abstract, and the only transformation is ASCII coercion and a
length trim at a sentence boundary.

So the machine proposes and a named human decides, which is the same shape as
the watch-list triage and for the same reason: an unattributed change to what
1,166 public pages say about real papers by real researchers is not something
this repository should be able to make on its own.

What a decision means
---------------------
    y   accept -- serve the abstract instead of the current description
    n   keep the current description as it stands
    ?   undecided -- neither, look again
    s   skip without recording anything
    q   stop and save

Nothing is served by this tool. It writes attributed decisions to
`data/curated/event_descriptions/decisions.jsonl`; a producer applies them.
That separation is deliberate -- a review tool that also publishes is one
keystroke away from publishing something nobody read.

The two flags, and why they interrupt
-------------------------------------
**TITLE DIFFERS.** arXiv's title for this id is not the served record's title.
Usually punctuation or capitalisation, but it can mean the record points at the
wrong paper, and pasting a stranger's abstract onto the wrong event is worse
than any PDF fragment.

**CHARACTERS WOULD BE DELETED.** `_base.to_ascii` decomposes with NFKD, so an
accented letter survives as its base letter, but a character with no ASCII
decomposition becomes the empty string with nothing left behind to show it was
there. An abstract about pi, phi and psi in Greek reads as gaps. One of the
first fifty has exactly this. Shown before the choice, never after.
"""
import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "review"))

from triage_watch import read_key  # noqa: E402  -- one keypress, one implementation

DECISIONS_DIR = os.path.join(REPO, "data", "curated", "event_descriptions")
DECISIONS = os.path.join(DECISIONS_DIR, "decisions.jsonl")

KEYS = {
    "y": ("accept_abstract", "serve the arXiv abstract"),
    "n": ("keep_current", "keep what is served now"),
    "?": ("undecided", "neither -- look again"),
}

TRIM_AT = 600


def trim(text, limit=TRIM_AT):
    """Cut at a sentence boundary at or before `limit`, never mid-word.

    A hard character cut produces "we show that the model" and reads as
    truncation damage, which is the thing being fixed.
    """
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    window = text[:limit]
    for stop in (". ", "? ", "! "):
        cut = window.rfind(stop)
        if cut > limit * 0.5:
            return window[:cut + 1].strip()
    cut = window.rfind(" ")
    return (window[:cut] if cut > 0 else window).strip() + " ..."


def load_proposals(path):
    return [json.loads(line) for line in io.open(path, encoding="utf-8")
            if line.strip()]


def load_decisions():
    if not os.path.isfile(DECISIONS):
        return {}
    out = {}
    for line in io.open(DECISIONS, encoding="utf-8"):
        if line.strip():
            row = json.loads(line)
            out[row["id"]] = row          # last write wins; the file keeps both
    return out


def append_decision(entry):
    os.makedirs(DECISIONS_DIR, exist_ok=True)
    with io.open(DECISIONS, "a", encoding="ascii", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True, sort_keys=True) + "\n")


def render(p, position, total, proposed):
    print("\n" + "=" * 78)
    print("[%d/%d]  %s" % (position, total, p["current_title"][:64]))
    print("        %s" % p["source_url"])
    warn = []
    if not p.get("title_matches"):
        warn.append("TITLE DIFFERS -- arXiv says: %s" % p["arxiv_title"][:60])
    if p.get("chars_dropped"):
        warn.append("CHARACTERS WOULD BE DELETED: %s"
                    % " ".join("U+%04X" % ord(c) for c in p["chars_dropped"]))
    for w in warn:
        print("  !! " + w)
    print("-" * 78)
    print("NOW SERVED (%d chars):" % len(p["current_description"]))
    print("    %r" % p["current_description"][:220])
    print()
    print("PROPOSED, arXiv abstract (%d chars):" % len(proposed))
    for line in _wrap(proposed, 74):
        print("    " + line)


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--by", required=True,
                    help="reviewer name. Required -- no anonymous verdicts")
    ap.add_argument("--proposals", required=True)
    ap.add_argument("--flagged", action="store_true",
                    help="only proposals carrying a title or character warning")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    if not os.path.isfile(args.proposals):
        sys.stderr.write("no such proposals file: %s\n" % args.proposals)
        return 2

    proposals = load_proposals(args.proposals)
    decided = load_decisions()

    queue = proposals
    if not args.redo:
        queue = [p for p in queue if p["id"] not in decided]
    if args.flagged:
        queue = [p for p in queue
                 if p.get("chars_dropped") or not p.get("title_matches")]
    if args.limit:
        queue = queue[:args.limit]

    if not queue:
        print("Nothing to review. --redo revisits decided records.")
        return 0

    print("Description review: %d proposal(s), reviewer %s" % (len(queue), args.by))
    print()
    for key, (_verdict, label) in KEYS.items():
        print("  %s  %s" % (key, label))
    print("  s  skip, record nothing")
    print("  q  stop and save")
    print("\nNothing is served by this tool. Decisions are written to")
    print("data/curated/event_descriptions/decisions.jsonl and applied by a build.")

    counts = {}
    for position, p in enumerate(queue, start=1):
        proposed = trim(p["abstract_ascii"])
        render(p, position, len(queue), proposed)
        key = read_key("\n  [y/n/?/s/q] > ")

        if key == "q":
            break
        if key == "s":
            continue
        if key not in KEYS:
            print("  (unrecognised key, nothing recorded)")
            continue

        verdict, _label = KEYS[key]
        append_decision({
            "id": p["id"],
            "arxiv_id": p["arxiv_id"],
            "source_url": p["source_url"],
            "verdict": verdict,
            "description": proposed if verdict == "accept_abstract" else None,
            "replaces": p["current_description"],
            "reviewer": args.by,
            "at": datetime.now(timezone.utc).isoformat(),
            "proposals_file": os.path.relpath(args.proposals, REPO).replace("\\", "/"),
            "title_matches": p.get("title_matches"),
            "chars_dropped": p.get("chars_dropped") or [],
        })
        counts[verdict] = counts.get(verdict, 0) + 1

    print("\n%d decision(s) recorded by %s: %s"
          % (sum(counts.values()), args.by,
             ", ".join("%s %d" % kv for kv in sorted(counts.items())) or "none"))
    print("written to %s" % os.path.relpath(DECISIONS, REPO).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
