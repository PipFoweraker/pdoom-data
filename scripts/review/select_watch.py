#!/usr/bin/env python3
"""Select watch-list atoms for a post, a sheet, or a review sitting.

A projection over data/curated/watchlist/candidates.jsonl. It holds no copy of
any event and writes nothing: change a rating or a clearance on the atom and
re-run, and every selection follows. This is the half that makes the atom
layer worth having -- rate once, and it percolates.

    select_watch.py --status watching --rating A
    select_watch.py --platform bluesky --limit 3
    select_watch.py --scan 2026-08-14_governance --undecided --format brief
    select_watch.py --needs-attention

Formats:
    brief   one line per atom, for scanning a list
    post    quotable block per atom, for assembling copy
    ids     ids only, for piping into another tool
"""

import argparse
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WATCHLIST = os.path.join(REPO, "data", "curated", "watchlist", "candidates.jsonl")


def load():
    if not os.path.isfile(WATCHLIST):
        sys.stderr.write("no watch list -- run scripts/build/project_watchlist.py\n")
        return None
    with open(WATCHLIST, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", help="watch_status: watching, accepted, rejected")
    parser.add_argument("--undecided", action="store_true",
                        help="watch_status is null -- not yet triaged")
    parser.add_argument("--rating")
    parser.add_argument("--platform",
                        help="cleared for this platform. A null cleared_for is "
                             "NOT treated as cleared.")
    parser.add_argument("--scan", help="only atoms seen by this scan id")
    parser.add_argument("--dated", action="store_true", help="only atoms with a date")
    parser.add_argument("--sourced", action="store_true",
                        help="only atoms with at least one source URL")
    parser.add_argument("--needs-attention", action="store_true",
                        help="atoms a human should look at first: no source, "
                             "or a null date, or flagged as a possible duplicate")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--format", choices=("brief", "post", "ids"),
                        default="brief")
    args = parser.parse_args()

    rows = load()
    if rows is None:
        return 2

    if args.status:
        rows = [r for r in rows if r.get("watch_status") == args.status]
    if args.undecided:
        rows = [r for r in rows if not r.get("watch_status")]
    if args.rating:
        rows = [r for r in rows if r.get("rating") == args.rating]
    if args.platform:
        # Null means "not yet ruled on". That is not consent, and treating it
        # as consent is how an uncleared quote reaches a timeline.
        rows = [r for r in rows
                if isinstance(r.get("cleared_for"), list)
                and args.platform in r["cleared_for"]]
    if args.scan:
        rows = [r for r in rows if args.scan in r.get("scans", [])]
    if args.dated:
        rows = [r for r in rows if r.get("date")]
    if args.sourced:
        rows = [r for r in rows if r.get("sources")]
    if args.needs_attention:
        rows = [r for r in rows
                if not r.get("sources")
                or not r.get("date")
                or r.get("possible_duplicate_of")]

    rows.sort(key=lambda r: (r.get("date") or "9999", r["id"]))
    if args.limit:
        rows = rows[:args.limit]

    if not rows:
        sys.stderr.write("nothing selected.\n")
        if args.platform:
            sys.stderr.write("  note: a null cleared_for is not treated as "
                             "cleared, so nothing is publishable until ruled on.\n")
        return 1

    for row in rows:
        if args.format == "ids":
            print(row["id"])
            continue
        if args.format == "brief":
            marks = []
            if not row["sources"]:
                marks.append("NO-SOURCE")
            if not row["date"]:
                marks.append("NO-DATE")
            if row["possible_duplicate_of"]:
                marks.append("DUP?")
            if row["scan_confidence"] == "low":
                marks.append("LOW-CONF")
            print("%-11s %-9s %s%s"
                  % (row["date"] or "----------",
                     (row.get("watch_status") or "-")[:9],
                     row["title"][:60],
                     ("  [" + " ".join(marks) + "]") if marks else ""))
            continue

        print("=" * 72)
        print("%s  (%s)" % (row["title"], row["id"]))
        print("date: %s (%s)   scan confidence: %s"
              % (row["date"] or "NULL", row["date_kind"], row["scan_confidence"]))
        if row.get("watch_status"):
            print("watch: %s since %s%s"
                  % (row["watch_status"], row.get("watching_since") or "?",
                     ("  decided %s by %s" % (row.get("decided_on"),
                                              row.get("decided_by")))
                     if row.get("decided_on") else ""))
        print()
        print(row["description"])
        print()
        if row.get("why_it_matters"):
            print("why: %s" % row["why_it_matters"])
        for url in row["sources"]:
            print("  src: %s" % url)
        if not row["sources"]:
            print("  src: NONE -- this atom carries no retrieved source")
        for flag in row["scan_flags"]:
            print("  flag: %s" % flag)
        if row["possible_duplicate_of"]:
            print("  possible duplicate of: %s"
                  % ", ".join(row["possible_duplicate_of"]))
        print()

    if args.format != "ids":
        sys.stderr.write("\n%d atom(s).\n" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
