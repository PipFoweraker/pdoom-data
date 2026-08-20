#!/usr/bin/env python3
"""Fast keyboard triage of the watch list. One key per atom.

    python scripts/review/triage_watch.py --by "Pip Foweraker"
    python scripts/review/triage_watch.py --by "..." --needs-attention
    python scripts/review/triage_watch.py --by "..." --redo   # include decided

Why this exists
---------------
`select_watch.py` reads and writes nothing, so the only way to set a rating or
a watch_status was to hand-edit 93 JSONL rows. That turns a 20-minute sitting
into a 3-hour one, and a 3-hour sitting does not happen.

The design target is Pip's own measured pace: 470 art assets in 23 minutes,
about 2.9 seconds each. Everything here follows from that number.

  * **One axis, four keys.** No tag field, no required free text. The art
    review measured this directly: a `harvest` tag designed that morning was
    used ZERO times that afternoon, and zero shelf verdicts survived, because
    at 2.9 seconds an asset there is no room to type. A slow-lane feature
    offered in a fast lane is not used, it is skipped.
  * **One stated mapping** does the work of 93 decisions, rather than asking
    for status and rating separately.
  * **Note-taking is optional and never blocks.** `n` opens one when he wants
    one; nothing waits for it.

Append-only, like the art review
--------------------------------
Every keystroke is appended to `triage_log.jsonl` BEFORE the atom file is
rewritten, and the log keeps mind-changes rather than overwriting them. That
design earned its keep in the art review within four hours: fifteen assets were
revised mid-session, one went remix five times before landing on keep. Under a
state file alone every earlier judgement would have been lost and the record
would have shown a confident single verdict that was never how it happened.

The file is also rewritten after EVERY keystroke, so a crash or a Ctrl-C
costs nothing. A triage tool that loses an hour of decisions is worse than no
tool, because the decisions are the expensive part.

No anonymous verdicts
---------------------
`--by` is required, per ADR-001. A verdict with no name attached cannot be
argued with, inherited, or filtered by a consumer who trusts one reviewer and
not another.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WATCHLIST = os.path.join(REPO, "data", "curated", "watchlist", "candidates.jsonl")
LOG = os.path.join(REPO, "data", "curated", "watchlist", "triage_log.jsonl")

# key -> (rating, watch_status, label). The ONE mapping, stated once.
KEYS = {
    "a": ("A", "watching", "strong -- on Watch, front of the queue"),
    "b": ("B", "watching", "worth watching, second tier"),
    "x": ("X", "rejected", "not for the corpus"),
    "?": ("?", None, "unsure -- look again, stays undecided"),
}


def read_key(prompt):
    """One keypress, no Enter, when the terminal allows it.

    Falls back to line input rather than failing: a pipe or a dumb terminal
    should still be able to drive this, and the fallback is announced once.

    WINDOWS. `termios` does not exist on Windows, so this fell straight through
    to the line-input fallback on Pip's own seat -- the only seat that runs it.
    Every atom needed a key AND Enter, which is two keystrokes and a hand move
    per atom against a design target of 2.9 seconds. The tool was silently in
    its slow lane on the machine it was written for, and nothing said so,
    because the fallback is the same code path as a pipe. `msvcrt` is present
    and gives a true single keypress. Measured 2026-08-21: termios NO,
    msvcrt YES.

    Guarded on isatty because `msvcrt.getwch` reads the CONSOLE, not stdin, so
    under a pipe it would ignore the piped input and wait for a human.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()
    if sys.stdin.isatty():
        try:
            import msvcrt
        except ImportError:
            msvcrt = None
        if msvcrt is not None:
            char = msvcrt.getwch()
            if char in ("\x00", "\xe0"):
                msvcrt.getwch()   # arrow/function key: swallow the second half
                char = "s"
            if char == "\x03":
                # Ctrl-C does not raise under getwch. Treat it as "stop and
                # save", which is what it already meant: the atom file is
                # rewritten after every keystroke, so nothing is in flight.
                char = "q"
            sys.stdout.write(char + "\n")
            sys.stdout.flush()
            return char.lower()
    try:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write(char + "\n")
        sys.stdout.flush()
        return char.lower()
    except Exception:                                   # noqa: BLE001
        return (sys.stdin.readline() or "q").strip().lower()[:1] or "q"


def load():
    with open(WATCHLIST, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def save(rows):
    tmp = WATCHLIST + ".tmp"
    with open(tmp, "w", encoding="ascii", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
    os.replace(tmp, WATCHLIST)


def append_log(entry):
    with open(LOG, "a", encoding="ascii", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True, sort_keys=True) + "\n")


def render(row, position, total):
    flags = []
    if not row["sources"]:
        flags.append("NO SOURCE")
    if not row["date"]:
        flags.append("NO DATE")
    if row["possible_duplicate_of"]:
        flags.append("DUP? " + ", ".join(row["possible_duplicate_of"]))
    if row["scan_confidence"] == "low":
        flags.append("LOW CONFIDENCE")

    print("\n" + "=" * 74)
    print("[%d/%d]  %s   %s"
          % (position, total, row["date"] or "no date", row["title"]))
    print("-" * 74)
    print(row["description"])
    if row.get("why_it_matters"):
        print("\nwhy: %s" % row["why_it_matters"])
    if flags:
        print("\n!! " + "  |  ".join(flags))
    if row.get("watch_status") or row.get("rating"):
        print("\ncurrently: %s / %s"
              % (row.get("rating") or "-", row.get("watch_status") or "-"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--by", required=True,
                        help="reviewer name. Required -- no anonymous verdicts")
    parser.add_argument("--needs-attention", action="store_true",
                        help="only atoms with no source, no date, or a duplicate flag")
    parser.add_argument("--scan", help="only atoms from this scan id")
    parser.add_argument("--redo", action="store_true",
                        help="include atoms already decided")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    if not os.path.isfile(WATCHLIST):
        sys.stderr.write("no watch list -- run scripts/build/project_watchlist.py\n")
        return 2

    rows = load()
    by_id = {r["id"]: r for r in rows}

    queue = list(rows)
    if not args.redo:
        queue = [r for r in queue if not r.get("watch_status")]
    if args.needs_attention:
        queue = [r for r in queue
                 if not r["sources"] or not r["date"]
                 or r["possible_duplicate_of"]]
    if args.scan:
        queue = [r for r in queue if args.scan in r.get("scans", [])]
    queue.sort(key=lambda r: (r.get("date") or "9999", r["id"]))
    if args.limit:
        queue = queue[:args.limit]

    if not queue:
        print("Nothing to triage. Use --redo to revisit decided atoms.")
        return 0

    print("Triage: %d atom(s), reviewer %s" % (len(queue), args.by))
    print()
    for key, (rating, status, label) in KEYS.items():
        print("  %s  %s" % (key, label))
    print("  n  add a note to the atom just decided")
    print("  s  skip, change nothing")
    print("  q  stop and save")
    print("\nEvery keystroke is written before the next atom is shown.")

    today = date.today().isoformat()
    decided = 0
    last = None

    for position, row in enumerate(queue, start=1):
        render(row, position, len(queue))
        key = read_key("\n  [a/b/x/?/n/s/q] > ")

        if key == "q":
            break
        if key == "s":
            last = None
            continue
        if key == "n":
            if last is None:
                print("  (no atom to annotate yet)")
                continue
            note = input("  note> ").strip()
            if note:
                by_id[last]["note"] = note
                append_log({"id": last, "field": "note", "value": note,
                            "by": args.by,
                            "at": datetime.now(timezone.utc).isoformat()})
                save(rows)
            continue
        if key not in KEYS:
            print("  (unrecognised key, nothing changed)")
            continue

        rating, status, _label = KEYS[key]
        prior = {"rating": row.get("rating"),
                 "watch_status": row.get("watch_status")}

        # Log BEFORE mutating, so a crash loses the atom file, never the record.
        append_log({
            "id": row["id"],
            "prev": prior,
            "next": {"rating": rating, "watch_status": status},
            "by": args.by,
            "at": datetime.now(timezone.utc).isoformat(),
        })

        row["rating"] = rating
        row["watch_status"] = status
        if status == "watching":
            row["watching_since"] = row.get("watching_since") or today
            row["decided_on"] = None
            row["decided_by"] = None
        elif status == "rejected":
            row["decided_on"] = today
            row["decided_by"] = args.by
        else:
            row["watching_since"] = None

        save(rows)
        decided += 1
        last = row["id"]

    print("\n%d decision(s) recorded by %s." % (decided, args.by))
    counts = {}
    for row in rows:
        state = row.get("watch_status") or "undecided"
        counts[state] = counts.get(state, 0) + 1
    print("watch list now: %s"
          % ", ".join("%s %d" % kv for kv in sorted(counts.items())))
    print("\nrun scripts/build/project_watchlist.py --check to confirm the "
          "derived half is untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
