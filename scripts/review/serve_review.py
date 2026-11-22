#!/usr/bin/env python3
"""Screen-based review: the watch list and the event descriptions, in a browser.

    python scripts/review/serve_review.py --by "Pip Foweraker"
    python scripts/review/serve_review.py --by "..." --proposals <dump>/data.jsonl
    python scripts/review/serve_review.py --by "..." --port 8741 --no-browser

Opens a local page (127.0.0.1 only) with three tabs:

  WATCH TRIAGE   all 110 atoms. a / b / x / ? exactly as triage_watch.py.
  MONTH END      atoms already on Watch. Accept / reject (reason required,
                 because it is published) / keep watching.
  DESCRIPTIONS   arXiv abstract beside what is served now. Accept / keep /
                 undecided, with an optional EDITORIAL condensation that is
                 stored as attributed opinion and never served as the
                 description.

Why a browser and not the keyboard tools
----------------------------------------
Asked for by Pip on 2026-11-22: "a screen based html tool for me to render
decisions", for a sitting where he wants to read every item with human eyes
and see its sourcing before deciding how far to trust it. The keyboard tools
show one atom in 74 columns and hide the sources behind the description; for a
judgement about sourcing, the sources are the thing to look at.

One implementation of every decision
------------------------------------
This file decides NOTHING about what a key means. Watch mutations are
`triage_watch.apply_triage / apply_decide / apply_note`, description rows are
`review_descriptions.build_decision`, and the promotion warning is
`triage_watch.gate_reasons`, which imports the producer's own gate. The
keyboard tools call the same functions. So the two front ends cannot drift:
there is no second copy to drift.

Every action is written to disk before the page updates -- the watch list and
its append-only log, or decisions.jsonl -- so closing the tab, killing the
server or losing power costs nothing already clicked.

Do not run this and triage_watch.py at the same time. Each holds the watch
list in memory and rewrites the whole file on every decision, so the second
writer would silently undo the first one's work.
"""
import argparse
import glob
import io
import json
import os
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "review"))

import triage_watch as tw            # noqa: E402
import review_descriptions as rd     # noqa: E402

ABSTRACT_DUMPS = os.path.join(REPO, "data", "raw", "arxiv_abstracts", "dumps")
EVENTS = os.path.join(REPO, "data", "serveable", "api", "timeline_events",
                      "all_events.json")


def newest_proposals():
    """The newest arXiv abstract dump that actually holds its data.jsonl.

    data.jsonl is gitignored for this adapter (real abstracts carry non-ASCII
    the gate would reject), so a dump directory can exist on a seat with only
    its _metadata.json. Measured on Bort 2026-11-22: four dump dirs, one with
    data. Picking by directory name alone would pick an empty one.
    """
    found = sorted(glob.glob(os.path.join(ABSTRACT_DUMPS, "*", "data.jsonl")))
    return found[-1] if found else None


class State(object):
    def __init__(self, by, proposals_path):
        self.by = by
        self.lock = threading.Lock()
        self.rows = tw.load() if os.path.isfile(tw.WATCHLIST) else []
        self.by_id = {r["id"]: r for r in self.rows}
        self.proposals_path = proposals_path
        self.proposals = rd.load_proposals(proposals_path) if proposals_path else []
        self.prop_by_id = {p["id"]: p for p in self.proposals}
        self.titles = {}
        if os.path.isfile(EVENTS):
            with io.open(EVENTS, encoding="utf-8") as handle:
                events = json.load(handle)
            for key, ev in (events.items() if isinstance(events, dict)
                            else ((e.get("id"), e) for e in events)):
                self.titles[key] = ev.get("title") or ev.get("name")

    def rel(self, path):
        return os.path.relpath(path, REPO).replace("\\", "/")

    # ---- watch ----
    def watch_payload(self):
        return {"by": self.by, "rows": self.rows,
                "triage_keys": {k: [v[0], v[1], v[2]] for k, v in tw.KEYS.items()},
                "decide_keys": {k: [v[0], v[1]] for k, v in tw.DECIDE_KEYS.items()}}

    def triage(self, atom_id, key):
        if key not in tw.KEYS:
            raise ValueError("unknown triage key %r" % key)
        with self.lock:
            row = self.by_id[atom_id]
            tw.apply_triage(self.rows, row, key, self.by)
            return row

    def note(self, atom_id, note):
        note = " ".join((note or "").split())
        if not note:
            raise ValueError("empty note")
        with self.lock:
            row = self.by_id[atom_id]
            tw.apply_note(self.rows, row, note, self.by)
            return row

    def gate(self, atom_id):
        return tw.gate_reasons(self.by_id[atom_id], self.by)

    def decide(self, atom_id, status, note):
        with self.lock:
            row = self.by_id[atom_id]
            tw.apply_decide(self.rows, row, status, (note or "").strip() or None,
                            self.by)
            return row

    # ---- descriptions ----
    def descriptions_payload(self):
        decided = rd.load_decisions()
        items = []
        for p in self.proposals:
            items.append({
                "id": p["id"],
                "arxiv_id": p.get("arxiv_id"),
                "source_url": p.get("source_url"),
                "current_title": p.get("current_title"),
                "arxiv_title": p.get("arxiv_title"),
                "title_matches": p.get("title_matches"),
                "chars_dropped": p.get("chars_dropped") or [],
                "current_description": p.get("current_description"),
                "proposed": rd.trim(p.get("abstract_ascii")),
                "full_abstract": p.get("abstract_ascii"),
                "served_title": self.titles.get(p["id"]) or p.get("current_title"),
                "decision": decided.get(p["id"]),
            })
        return {"by": self.by,
                "proposals_file": self.rel(self.proposals_path) if self.proposals_path else None,
                "keys": {k: [v[0], v[1]] for k, v in rd.KEYS.items()},
                "items": items}

    def describe(self, record_id, verdict, editorial):
        p = self.prop_by_id[record_id]
        row = rd.build_decision(p, verdict, rd.trim(p.get("abstract_ascii")),
                                self.by, self.rel(self.proposals_path), editorial)
        with self.lock:
            rd.append_decision(row)
        return row


def make_handler(state, page):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):   # quiet: the page is the feedback
            pass

        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else body.encode("ascii")
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=us-ascii")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=True))

        def do_GET(self):
            if self.path == "/":
                return self._send(200, page, "text/html")
            if self.path == "/api/watch":
                return self._json(200, state.watch_payload())
            if self.path == "/api/descriptions":
                return self._json(200, state.descriptions_payload())
            return self._json(404, {"error": "no such path"})

        def do_POST(self):
            # Same-origin only. The server binds 127.0.0.1, but a page on any
            # other site can still POST to localhost; refusing a foreign
            # Origin closes that.
            origin = self.headers.get("Origin")
            host = "http://%s" % self.headers.get("Host", "")
            if origin and origin != host:
                return self._json(403, {"error": "foreign origin refused"})
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                if self.path == "/api/watch/triage":
                    out = state.triage(body["id"], body["key"])
                elif self.path == "/api/watch/note":
                    out = state.note(body["id"], body["note"])
                elif self.path == "/api/watch/gate":
                    out = {"reasons": state.gate(body["id"])}
                elif self.path == "/api/watch/decide":
                    out = state.decide(body["id"], body["status"], body.get("note"))
                elif self.path == "/api/descriptions/decide":
                    out = state.describe(body["id"], body["verdict"],
                                         body.get("editorial"))
                else:
                    return self._json(404, {"error": "no such path"})
            except (KeyError, ValueError) as exc:
                return self._json(400, {"error": str(exc)})
            return self._json(200, out)
    return Handler


def running_instance(start, span=50):
    """URL of a serve_review already listening near `start`, else None.

    Found the hard way on 2026-11-22: a first start whose stdout was buffered
    looked dead, a second start took the next free port, and two servers each
    held the watch list in memory. Either one's next write would have silently
    reverted the other's. A second instance is refused, not tolerated.
    """
    import urllib.request
    for port in range(start, start + span):
        url = "http://127.0.0.1:%d/" % port
        try:
            with urllib.request.urlopen(url + "api/watch", timeout=0.3) as r:
                if r.status == 200 and b'"triage_keys"' in r.read():
                    return url
        except Exception:
            continue
    return None


def free_port(start):
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise SystemExit("no free port in %d-%d" % (start, start + 49))


PAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "serve_review_page.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--by", required=True,
                    help="reviewer name. Required -- no anonymous verdicts")
    ap.add_argument("--proposals",
                    help="arXiv abstract dump data.jsonl (default: newest with data)")
    ap.add_argument("--port", type=int, default=8741)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    proposals = args.proposals or newest_proposals()
    if proposals and not os.path.isfile(proposals):
        sys.stderr.write("no such proposals file: %s\n" % proposals)
        return 2
    state = State(args.by.strip(), proposals)
    with io.open(PAGE_PATH, encoding="ascii") as handle:
        page = handle.read()

    already = running_instance(args.port)
    if already:
        sys.stderr.write("a review server is already running at %s -- open that "
                         "one. Two would each rewrite the watch list and undo "
                         "each other.\n" % already)
        return 3
    port = free_port(args.port)
    url = "http://127.0.0.1:%d/" % port
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(state, page))
    print("review server for %s at %s" % (state.by, url), flush=True)
    print("  watch list: %d atom(s)" % len(state.rows))
    print("  descriptions: %d proposal(s) from %s"
          % (len(state.proposals), state.rel(proposals) if proposals else "NONE"))
    print("every click is on disk before the page updates. Ctrl-C to stop.", flush=True)
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped. nothing was in flight.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
