#!/usr/bin/env python3
"""Project APPROVED quotes into a served collection the game can read.

    python scripts/build/project_quotes.py            # write
    python scripts/build/project_quotes.py --check    # assert committed

WHY THE GAME MUST NOT READ data/curated/quotes/quotes.jsonl DIRECTLY

That file is a RESEARCH INDEX. It holds every candidate found, most of which
nobody has been asked about yet, and a few that someone has refused. It exists
so a human can decide who to write to. It is not a publication queue, and a
consumer that read it directly would have exactly one mistake standing between
a candidate and a player's screen.

So the boundary is a build step rather than a rule. This projection emits only
records carrying a named permission basis, and there is no flag to make it emit
anything else. Copying a line out of the curated file by hand is still possible,
because nothing can stop a determined person, but it cannot happen by ACCIDENT:
the file the game reads simply does not contain the other quotes.

WHAT THE SERVED ZONE DELIBERATELY DOES NOT CARRY

The blocked list names ids and reasons and NEVER the quote text. A served file
that reported "these 22 are not approved" and then printed all 22 verbatim
would republish precisely what it was refusing to publish. The reasons are
useful to a consumer; the words are not theirs to have yet.

This mirrors project_watch_accepted.py, which reports a blocked atom with its
reason rather than dropping it silently, and for the same argument: a pipeline
that quietly discards a decision is worse than one that refuses out loud.
"""

import io
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))

import check_quote_permissions as gate  # noqa: E402

CURATED = os.path.join(REPO_ROOT, "data", "curated", "quotes", "quotes.jsonl")
OUT_DIR = os.path.join(REPO_ROOT, "data", "serveable", "api", "quotes")
FEED = os.path.join(OUT_DIR, "approved.jsonl")
LINEAGE = os.path.join(OUT_DIR, "LINEAGE.json")

SERVED_FIELDS = ("id", "text", "author", "source_url", "archive_url",
                 "published_at", "quote_kind", "placements", "context_note")


def load():
    if not os.path.isfile(CURATED):
        return []
    with io.open(CURATED, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def build():
    rows = load()
    served, withheld = [], []
    for row in rows:
        basis = (row.get("permission") or {}).get("basis")
        if basis in gate.SERVABLE_BASES:
            out = {k: row.get(k) for k in SERVED_FIELDS if k in row}
            # A consumer must be able to credit correctly without reading the
            # curated file, so the basis travels with the quote.
            out["permission_basis"] = basis
            # CC BY requires attribution in the manner the author specifies.
            # Where a source states its own citation form, that form is what a
            # consumer must show, so it travels as the credit line.
            author = row.get("author") or {}
            out["credit"] = author.get("display_preference") or author.get("name")
            perm = row.get("permission") or {}
            out["licence_spdx"] = perm.get("licence_spdx")
            out["granted_by"] = perm.get("granted_by")
            served.append(out)
        else:
            # id and reason only. Never the text.
            withheld.append({"id": row.get("id"), "basis": basis})
    served.sort(key=lambda r: r["id"])
    withheld.sort(key=lambda r: r["id"] or "")
    return served, withheld


def render(served, withheld):
    counts = {}
    for row in withheld:
        counts[row["basis"]] = counts.get(row["basis"], 0) + 1
    return {
        "build_version": "0.1.0",
        "producer": "scripts/build/project_quotes.py",
        "counts": {"served": len(served), "withheld": len(withheld),
                   "withheld_by_basis": dict(sorted(counts.items()))},
        "rule": (
            "A quote reaches this file only with a named permission basis: a "
            "licence that permits it, or a person who said yes. There is no "
            "flag to emit anything else."
        ),
        "withheld_carry_no_text": (
            "Withheld records appear here as an id and a basis and nothing "
            "else. Printing the text of a quote we are refusing to publish "
            "would republish it, which is the thing being refused."
        ),
        "withheld": withheld,
        "zone": "data/serveable/ is a build output. Never hand-edit it.",
    }


def write(path, payload_lines):
    with io.open(path, "w", encoding="ascii", newline="\n") as handle:
        for line in payload_lines:
            handle.write(line + "\n")


def main():
    check = "--check" in sys.argv
    served, withheld = build()
    lineage = render(served, withheld)
    lines = [json.dumps(r, ensure_ascii=True, sort_keys=True) for r in served]

    print("curated quotes   : %d" % (len(served) + len(withheld)))
    print("approved, served : %d" % len(served))
    print("withheld         : %d  %s"
          % (len(withheld), lineage["counts"]["withheld_by_basis"]))

    if check:
        problems = []
        if not os.path.isfile(FEED):
            problems.append("no committed feed at %s" % FEED)
        else:
            committed = [l.rstrip("\n") for l in io.open(FEED, encoding="ascii")
                         if l.strip()]
            if committed != lines:
                problems.append("feed differs: %d committed vs %d rebuilt"
                                % (len(committed), len(lines)))
        if os.path.isfile(LINEAGE):
            if json.load(io.open(LINEAGE, encoding="ascii")) != lineage:
                problems.append("lineage differs")
        else:
            problems.append("no committed lineage")
        if problems:
            print("CHECK FAILED:")
            for problem in problems:
                print("  - %s" % problem)
            print("Re-run without --check and commit the result.")
            return 1
        print("CHECK OK: committed output matches a fresh build")
        return 0

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    write(FEED, lines)
    with io.open(LINEAGE, "w", encoding="ascii", newline="\n") as handle:
        handle.write(json.dumps(lineage, indent=2, ensure_ascii=True,
                                sort_keys=True) + "\n")
    print("wrote %s" % os.path.relpath(FEED, REPO_ROOT))
    print("wrote %s" % os.path.relpath(LINEAGE, REPO_ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
