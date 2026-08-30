#!/usr/bin/env python3
"""One sitting of corpus review. One question, four answers, saved to disk.

    python scripts/review/serve_corpus_review.py --by "Pip Foweraker"

Opens a browser on a local page carrying the sample prepared by
scripts/review/prepare_corpus_review.py, and appends every judgement to
data/curated/corpus_review/<pass_id>/verdicts.jsonl as it happens.

THE QUESTION, and it is the only one asked
------------------------------------------
    Would you want this paper in an AI-safety reference corpus?

Not "is the description any good" -- that is our extractor's defect and
reviewing it would grade our own code. Not "does it belong in
timeline_events" -- that is one ruling, not 150. Per
docs/design/REVIEW_THE_BULK_2026-08-19.md section 1, this is the only
question with real per-record variance and no mechanical answer.

THE FOUR ANSWERS, and why four rather than three
------------------------------------------------
    yes        worth carrying
    no         not worth carrying
    unknown    looked at it, could not tell
    skip       deliberately passed over without judging

`unknown` and `skip` are first-class answers, stored as themselves, never
folded into `no` and never folded into each other. A paper outside the
reviewer's field is an honest `unknown` and its count is a finding in its
own right.

A FIFTH STATE EXISTS AND IT IS NOT A VALUE. A record with no row in
verdicts.jsonl is NOT YET REVIEWED. That is represented by absence. Nothing
in this file ever writes a value that means "unreviewed", because a value
can be read as a judgement and an absence cannot.

`retracted` is the sixth token and it is not an answer either: it is an undo,
and it returns a record to NOT YET REVIEWED by removing it from the state
projection while leaving both the original row and the retraction in the log.

WHAT THIS REUSES RATHER THAN REINVENTS
--------------------------------------
* The interaction model is `tools/review_queue.html`, unchanged in substance:
  one record per screen, the note box focused at all times so that typing --
  or Windows dictation on Win+H -- always lands somewhere, and verdicts bound
  to PUNCTUATION so that no letter can trigger one mid-sentence. That mapping
  is Pip's, already used, and is copied here rather than improved.
* The append-before-state discipline is `scripts/review/triage_watch.py` and
  `pdoom1/tools/art_review/serve_review.py`. In the 2026-08-14 art review 394
  of 470 judged assets were later found orphaned from the state file; the 470
  claim survived only because it was counted from the append-only log.
* Decided records leave the working set, which is what actually produces the
  pace. The queue shortens as it is worked.

WHY THIS IS A SERVER AND NOT A STATIC SHEET
-------------------------------------------
The design document argued for a static sheet with an export button. The
brief this was built to overrides that on one point: every judgement must be
on disk the moment it is made, so that closing the tab at review 91 leaves 91
judgements on disk. A page in a file:// tab cannot write to disk. The server
is 200 lines whose entire job is to append to a log, which is exactly the
shape `serve_review.py` settled on after three generations of surface.

NO VERDICT IS EVER WRITTEN BY THIS TOOL ON ITS OWN BEHALF
---------------------------------------------------------
Every row in verdicts.jsonl comes from a keypress and carries the name given
in --by, which is required. There are no defaults, no auto-fills, and no
seeded examples. An empty verdicts.jsonl is the correct state before a
sitting.

Other modes
-----------
    --summary        print the counts from the log and exit, write nothing
    --pass-id ID     pick a pass other than the newest
    --port N         default 8731, next free port if busy
    --no-browser     do not open a browser
"""

import argparse
import html as htmlmod
import io
import json
import os
import re
import socket
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
REVIEW_ROOT = os.path.join(REPO, "data", "curated", "corpus_review")
EVENTS = os.path.join(REPO, "data", "serveable", "api", "timeline_events",
                      "all_events.json")

TOOL = "serve_corpus_review.py"
TOOL_VERSION = "0.1.0"

# The four answers, plus the undo token. Enforced: a POST carrying anything
# else is refused rather than coerced.
ANSWERS = ("yes", "no", "unknown", "skip")
RETRACT = "retracted"
ACCEPTED = set(ANSWERS) | {RETRACT}

_LOCK = threading.Lock()


# --------------------------------------------------------------------------
# time

def now_local():
    """Wall clock WITH an explicit offset, e.g. 2026-08-24T10:31:02+10:00.

    Required on every judgement. A bare Z stamp loses which evening this was,
    and a naive stamp cannot be compared with anything.
    """
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------
# pass loading

def newest_pass():
    if not os.path.isdir(REVIEW_ROOT):
        return None
    passes = [d for d in sorted(os.listdir(REVIEW_ROOT))
              if os.path.isfile(os.path.join(REVIEW_ROOT, d, "frame.json"))]
    return passes[-1] if passes else None


def load_pass(pass_id):
    pass_dir = os.path.join(REVIEW_ROOT, pass_id)
    with io.open(os.path.join(pass_dir, "frame.json"), "r",
                 encoding="utf-8") as fh:
        frame = json.load(fh)

    dump_rel = (frame.get("abstract_dump") or {}).get("path")
    if not dump_rel:
        sys.exit("frame.json has no abstract_dump. Run:\n"
                 "  python scripts/review/prepare_corpus_review.py")
    dump_path = os.path.join(REPO, dump_rel.replace("/", os.sep))
    if not os.path.isfile(dump_path):
        sys.exit("abstract dump missing: %s\nIt is gitignored, like the other "
                 "raw dumps. Re-fetch it with the same seed:\n"
                 "  python scripts/review/prepare_corpus_review.py --n %d "
                 "--seed %d --pass-id %s"
                 % (dump_rel, frame["draw"]["n"], frame["draw"]["seed"],
                    pass_id))

    abstracts = {}
    with io.open(dump_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                row = json.loads(line)
                abstracts[row["record_id"]] = row

    with io.open(EVENTS, "r", encoding="utf-8") as fh:
        events = json.load(fh)
    ours = {}
    for key, rec in events.items():
        rid = rec.get("id", key)
        ours[rid] = rec

    records = []
    for i, s in enumerate(frame["sample"]):
        rid = s["record_id"]
        ab = abstracts.get(rid)
        if not ab:
            continue   # fetch missed it; recorded in the dump's _metadata
        mine = ours.get(rid, {})
        records.append({
            "n": i + 1,
            "record_id": rid,
            "arxiv_id": ab.get("arxiv_id") or s.get("arxiv_id"),
            "title": ab.get("title") or s.get("title") or "",
            "abstract": ab.get("abstract") or "",
            "authors": ab.get("authors") or [],
            # The month in the arXiv identifier, which is the v1 month by
            # arXiv's construction. NOT OAI's <created>, which is the date of
            # the version arXiv currently indexes and is up to a year later.
            "display_date": ab.get("display_date") or ab.get("id_month"),
            "primary_category": ab.get("primary_category"),
            "categories": ab.get("categories") or [],
            "url": ab.get("abs_url") or s.get("url"),
            "our_year": mine.get("year"),
            "our_description": mine.get("description") or "",
        })
    return pass_dir, frame, records


# --------------------------------------------------------------------------
# the log, and the state projected from it

def log_path(pass_dir):
    return os.path.join(pass_dir, "verdicts.jsonl")


def state_path(pass_dir):
    return os.path.join(pass_dir, "state.json")


def read_log(pass_dir):
    path = log_path(pass_dir)
    rows = []
    if not os.path.isfile(path):
        return rows
    with io.open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    # A torn last line from a hard kill. Reported, not repaired
                    # in place: the log is append-only and nothing rewrites it.
                    sys.stderr.write("WARNING: unparseable row in %s\n" % path)
    return rows


def project(rows):
    """State is a projection of the log. Last row per target wins.

    A `retracted` row DELETES the entry, which returns that record to NOT YET
    REVIEWED -- an absence, never a value.
    """
    state, orphan_notes = {}, {}
    for row in rows:
        target = row.get("target")
        verdict = (row.get("body") or {}).get("verdict")
        if row.get("motivation") == "commenting":
            note = (row.get("body") or {}).get("note")
            if target in state:
                state[target]["note"] = note
            else:
                # A note typed and then abandoned without a verdict. Kept
                # visible rather than silently dropped -- but NOT promoted
                # into a verdict, because a note is not a judgement.
                orphan_notes[target] = note
            continue
        if verdict == RETRACT:
            state.pop(target, None)
            continue
        if verdict not in ANSWERS:
            continue
        state[target] = {
            "verdict": verdict,
            "note": (row.get("body") or {}).get("note"),
            "creator": row.get("creator"),
            "created": row.get("created"),
        }
        orphan_notes.pop(target, None)
    return state, orphan_notes


def write_state(pass_dir, frame, rows):
    state, orphan_notes = project(rows)
    counts = {a: 0 for a in ANSWERS}
    for entry in state.values():
        counts[entry["verdict"]] += 1
    payload = {
        "pass_id": frame["pass_id"],
        "generated": now_local(),
        "note": ("PROJECTION of verdicts.jsonl, which is the source of truth. "
                 "Safe to delete; rebuilt on the next keypress. A record "
                 "absent from `records` below is NOT YET REVIEWED."),
        "question": frame["question"],
        "n_in_frame": frame["draw"]["n"],
        "counts": counts,
        "reviewed": sum(counts.values()),
        "not_yet_reviewed": frame["draw"]["n"] - sum(counts.values()),
        "log_rows": len(rows),
        "records": state,
        "notes_without_a_verdict": orphan_notes,
    }
    tmp = state_path(pass_dir) + ".tmp"
    with io.open(tmp, "w", encoding="ascii", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=True)
        fh.write("\n")
    os.replace(tmp, state_path(pass_dir))
    return payload


def append_row(pass_dir, row):
    """Append one row and FLUSH IT TO THE PLATTER before returning.

    os.fsync is the whole point. Without it a power cut or a hard kill can
    lose an hour of judgements that the buffer said were written, and the
    judgements are the expensive part.
    """
    path = log_path(pass_dir)
    line = json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n"
    with io.open(path, "a", encoding="ascii", newline="\n") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


# --------------------------------------------------------------------------
# HTML

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>corpus review -- __PASS__</title>
<style>
:root {
  --bg:#12141a; --panel:#1a1d26; --line:#2b3040; --ink:#e6e9f0; --dim:#8b93a7;
  --yes:#4ade80; --no:#f87171; --unk:#fbbf24; --skip:#94a3b8; --accent:#60a5fa;
}
* { box-sizing:border-box; }
html,body { height:100%; }
body { margin:0; background:var(--bg); color:var(--ink);
  font:16px/1.6 -apple-system,"Segoe UI",Roboto,sans-serif;
  display:flex; flex-direction:column; }
header { padding:8px 18px; background:var(--panel);
  border-bottom:1px solid var(--line); display:flex; gap:20px;
  align-items:baseline; flex-wrap:wrap; font-size:13px; color:var(--dim); }
header .q { color:var(--ink); font-size:15px; font-weight:600; }
header span.v { color:var(--ink); font-variant-numeric:tabular-nums; }
#saveflag { margin-left:auto; padding:2px 8px; border-radius:3px;
  background:#14311f; color:var(--yes); font-size:12px; }
#saveflag.bad { background:#3b1414; color:var(--no); }
main { flex:1; overflow-y:auto; padding:24px 40px 8px; }
.wrap { max-width:860px; margin:0 auto; }
h1 { font-size:27px; line-height:1.25; margin:0 0 6px; }
.meta { color:var(--dim); font-size:13px; margin-bottom:18px; }
.meta a { color:var(--accent); }
.abstract { font-size:17px; line-height:1.65; }
.ours { margin-top:22px; padding:10px 14px; border-left:3px solid var(--line);
  background:#161922; color:var(--dim); font-size:12.5px; }
.ours b { color:var(--unk); }
.ours .txt { white-space:pre-wrap; font-family:ui-monospace,Consolas,monospace;
  font-size:11.5px; max-height:74px; overflow:hidden; display:block;
  margin-top:4px; }
footer { background:var(--panel); border-top:1px solid var(--line);
  padding:10px 18px; }
.fwrap { max-width:860px; margin:0 auto; }
#note { width:100%; background:#0e1016; color:var(--ink);
  border:1px solid var(--line); border-radius:4px; padding:9px 11px;
  font:15px/1.45 inherit; resize:none; height:58px; }
#note:focus { outline:none; border-color:var(--accent); }
.keys { display:flex; gap:8px; margin-top:9px; flex-wrap:wrap;
  align-items:center; }
button { background:#232735; color:var(--ink); border:1px solid var(--line);
  border-radius:4px; padding:7px 13px; font:14px inherit; cursor:pointer; }
button:hover { background:#2d3348; }
button kbd { font-family:ui-monospace,Consolas,monospace; color:var(--dim);
  margin-right:6px; }
#b_yes { border-color:var(--yes); } #b_no { border-color:var(--no); }
#b_unk { border-color:var(--unk); } #b_skip { border-color:var(--skip); }
.hint { color:var(--dim); font-size:12px; margin-left:auto; text-align:right; }
#done { text-align:center; padding:60px 20px; }
#done h2 { color:var(--yes); }
code { font-family:ui-monospace,Consolas,monospace; }
</style>
</head>
<body>

<header>
  <span class="q">__QUESTION__</span>
  <span>reviewer <span class="v">__BY__</span></span>
  <span><span class="v" id="p_done">0</span>/<span class="v" id="p_tot">0</span> judged</span>
  <span>left <span class="v" id="p_left">0</span></span>
  <span><span class="v" id="p_rate">--</span>/min</span>
  <span id="saveflag">on disk</span>
</header>

<main><div class="wrap" id="card"></div></main>

<footer><div class="fwrap">
  <textarea id="note" placeholder="optional -- one sentence on where this paper matters. Win+H to dictate. Letters always land here; verdicts are on the punctuation keys, so nothing you say can trigger one."></textarea>
  <div class="keys">
    <button id="b_yes"><kbd>`</kbd>yes, carry it</button>
    <button id="b_no"><kbd>]</kbd>no</button>
    <button id="b_unk"><kbd>\</kbd>can't tell</button>
    <button id="b_skip"><kbd>[</kbd>skip</button>
    <button id="b_undo"><kbd>~</kbd>undo</button>
    <span class="hint">arrows move without judging &nbsp; Esc clears the note<br>
      every keypress is written to verdicts.jsonl before the next card</span>
  </div>
</div></footer>

<script>
"use strict";
var RECORDS = __RECORDS__;
var DONE    = __DONE__;
var BY      = __BY__;
var PASS    = __PASS_JSON__;
var MIRROR  = "pdoom_corpus_review_" + PASS;

var queue = [], idx = 0, stamps = [], lastShown = Date.now();
var undoStack = [];

function esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;")
    .replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/* Decided records leave the working set. That is what produces the pace:
   the queue shortens as it is worked, rather than being walked past. */
function rebuild() {
  queue = RECORDS.filter(function (r) { return !DONE[r.record_id]; });
  if (idx >= queue.length) idx = Math.max(0, queue.length - 1);
  render();
}

function render() {
  var tot = RECORDS.length, done = tot - queue.length;
  document.getElementById("p_done").textContent = done;
  document.getElementById("p_tot").textContent = tot;
  document.getElementById("p_left").textContent = queue.length;
  if (stamps.length > 1) {
    var mins = (stamps[stamps.length - 1] - stamps[0]) / 60000;
    document.getElementById("p_rate").textContent =
      mins > 0.05 ? ((stamps.length - 1) / mins).toFixed(1) : "--";
  }

  var card = document.getElementById("card");
  var r = queue[idx];
  if (!r) {
    card.innerHTML = '<div id="done"><h2>' + done + ' of ' + tot +
      ' judged.</h2><p>All of them are already in ' +
      '<code>verdicts.jsonl</code>. Nothing is waiting on an export button.' +
      '</p><p>Close the tab, then Ctrl-C the server.</p></div>';
    document.getElementById("note").blur();
    return;
  }

  var auth = r.authors.slice(0, 6).join(", ") +
             (r.authors.length > 6 ? ", et al." : "");
  var ourDesc = "";
  if (r.our_description) {
    ourDesc =
      '<div class="ours"><b>Not part of the question:</b> this is the ' +
      'description <i>we</i> publish for this record. It is unparsed PDF ' +
      'text from our own extractor, shown so the damage is visible and ' +
      'labelled. Judge the paper above, not this.' +
      '<span class="txt">' + esc(r.our_description.slice(0, 400)) + '</span>' +
      '</div>';
  }
  card.innerHTML =
    '<h1>' + esc(r.title) + '</h1>' +
    '<div class="meta">' + esc(auth) + ' &nbsp;|&nbsp; arXiv ' +
      esc(r.display_date || "") + ' &nbsp;|&nbsp; ' +
      esc(r.primary_category || "") + ' &nbsp;|&nbsp; ' +
      '<a href="' + esc(r.url) + '" target="_blank" rel="noopener">' +
      esc(r.arxiv_id) + '</a>' +
    '</div>' +
    '<div class="abstract">' + esc(r.abstract) + '</div>' +
    ourDesc;

  var box = document.getElementById("note");
  box.value = "";
  box.focus();
  lastShown = Date.now();
  window.scrollTo(0, 0);
  document.querySelector("main").scrollTop = 0;
}

function flag(ok) {
  var el = document.getElementById("saveflag");
  el.className = ok ? "" : "bad";
  el.textContent = ok ? "on disk" : "NOT SAVED -- see the terminal";
}

function post(path, payload, then) {
  fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(function (res) { return res.json(); })
    .then(function (j) { flag(!!j.ok); if (then) then(j); })
    .catch(function () { flag(false); });
}

/* Mirror to localStorage as well. The log on disk is the source of truth;
   this exists only so a browser left open across a server restart can still
   show what it already sent. */
function mirror() {
  try { localStorage.setItem(MIRROR, JSON.stringify(DONE)); } catch (e) {}
}

function decide(verdict) {
  var r = queue[idx];
  if (!r) return;
  var box = document.getElementById("note");
  var note = box.value.trim();
  var prev = DONE[r.record_id] || null;

  undoStack.push({ id: r.record_id, prev: prev });
  DONE[r.record_id] = { verdict: verdict, note: note || null, creator: BY };
  stamps.push(Date.now());
  mirror();

  post("/verdict", {
    target: r.record_id,
    verdict: verdict,
    note: note || null,
    previous: prev,
    seconds_on_screen: (Date.now() - lastShown) / 1000
  });

  /* Do not advance idx: the decided record leaves the queue, so the next
     one arrives in the same slot. */
  rebuild();
}

function undo() {
  var last = undoStack.pop();
  if (!last) return;
  post("/verdict", {
    target: last.id,
    verdict: last.prev ? last.prev.verdict : "retracted",
    note: last.prev ? last.prev.note : null,
    previous: DONE[last.id] || null,
    seconds_on_screen: 0
  });
  if (last.prev) DONE[last.id] = last.prev;
  else delete DONE[last.id];
  mirror();
  rebuild();
}

function move(d) {
  if (!queue.length) return;
  idx = (idx + d + queue.length) % queue.length;
  render();
}

/* Verdicts live on punctuation, copied unchanged from tools/review_queue.html.
   The reason is written there: at speed, a letter key that decides makes the
   note box unusable, and Windows dictation types letters. None of these four
   characters is produced by dictation. */
var ACTIONS = {
  "`":  function () { decide("yes"); },
  "]":  function () { decide("no"); },
  "\\": function () { decide("unknown"); },
  "[":  function () { decide("skip"); },
  "~":  function () { undo(); },
  "ArrowRight": function () { move(1); },
  "ArrowLeft":  function () { move(-1); },
  "Escape": function () { document.getElementById("note").value = ""; }
};

document.addEventListener("keydown", function (ev) {
  var f = ACTIONS[ev.key];
  if (f && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
    f(); ev.preventDefault(); ev.stopPropagation(); return;
  }
  var box = document.getElementById("note");
  if (box && document.activeElement !== box && ev.key.length === 1 &&
      !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
    box.focus();
  }
});

document.getElementById("b_yes").onclick  = function () { decide("yes"); };
document.getElementById("b_no").onclick   = function () { decide("no"); };
document.getElementById("b_unk").onclick  = function () { decide("unknown"); };
document.getElementById("b_skip").onclick = function () { decide("skip"); };
document.getElementById("b_undo").onclick = function () { undo(); };

/* A note typed but not yet committed by a verdict would otherwise die with
   the tab. This is the only thing that fires without a keypress, and it
   writes a `commenting` annotation, never a verdict. */
window.addEventListener("beforeunload", function () {
  var r = queue[idx];
  var box = document.getElementById("note");
  if (!r || !box || !box.value.trim()) return;
  var blob = new Blob([JSON.stringify({
    target: r.record_id, note: box.value.trim()
  })], { type: "application/json" });
  navigator.sendBeacon("/note", blob);
});

rebuild();
</script>
</body>
</html>
"""


def render_page(frame, records, done, by, pass_id):
    page = PAGE
    page = page.replace("__QUESTION__", htmlmod.escape(frame["question"]))
    page = page.replace("__PASS__", htmlmod.escape(pass_id))
    page = page.replace("__RECORDS__", json.dumps(records, ensure_ascii=True))
    page = page.replace("__DONE__", json.dumps(done, ensure_ascii=True))
    # First occurrence is the header text; second is the JS variable.
    page = page.replace("__BY__", htmlmod.escape(by), 1)
    page = page.replace("__BY__", json.dumps(by, ensure_ascii=True))
    page = page.replace("__PASS_JSON__",
                        json.dumps(re.sub(r"[^A-Za-z0-9_]", "_", pass_id)))
    return page


# --------------------------------------------------------------------------
# server

def make_handler(pass_dir, frame, records, by, pass_id):

    class Handler(BaseHTTPRequestHandler):

        def log_message(self, fmt, *a):
            pass  # the terminal is for verdict lines, not GET noise

        def _send(self, code, body, ctype="application/json"):
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path in ("/", "/index.html"):
                with _LOCK:
                    done, _ = project(read_log(pass_dir))
                page = render_page(frame, records, done, by, pass_id)
                self._send(200, page, "text/html")
            elif path == "/state.json":
                with _LOCK:
                    rows = read_log(pass_dir)
                self._send(200, json.dumps(write_state(pass_dir, frame, rows)))
            else:
                self._send(404, json.dumps({"ok": False, "error": "no such path"}))

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}

        def do_POST(self):
            path = self.path.split("?")[0]
            try:
                payload = self._body()
            except ValueError:
                self._send(400, json.dumps({"ok": False, "error": "bad json"}))
                return

            if path == "/verdict":
                verdict = payload.get("verdict")
                target = payload.get("target")
                if verdict not in ACCEPTED:
                    # Refused rather than coerced. Silently mapping an unknown
                    # token onto `no` is precisely the thing Pip ruled out.
                    self._send(400, json.dumps(
                        {"ok": False,
                         "error": "verdict %r is not one of %s"
                                  % (verdict, sorted(ACCEPTED))}))
                    return
                row = {
                    "pass_id": pass_id,
                    "target": target,
                    "body": {"verdict": verdict, "note": payload.get("note")},
                    "previous": payload.get("previous"),
                    "creator": by,
                    "created": now_local(),
                    "created_utc": now_utc(),
                    "motivation": "assessing",
                    "question": frame["question"],
                    "tool": "%s %s" % (TOOL, TOOL_VERSION),
                    "seconds_on_screen": round(
                        float(payload.get("seconds_on_screen") or 0), 2),
                }
                with _LOCK:
                    append_row(pass_dir, row)     # log FIRST, and fsync'd
                    rows = read_log(pass_dir)
                    state = write_state(pass_dir, frame, rows)
                c = state["counts"]
                sys.stdout.write(
                    "  %-8s %-28s  %3d/%d  [y%d n%d ?%d s%d]\n"
                    % (verdict, str(target)[:28], state["reviewed"],
                       frame["draw"]["n"], c["yes"], c["no"], c["unknown"],
                       c["skip"]))
                sys.stdout.flush()
                self._send(200, json.dumps({"ok": True,
                                            "reviewed": state["reviewed"]}))
                return

            if path == "/note":
                row = {
                    "pass_id": pass_id,
                    "target": payload.get("target"),
                    "body": {"note": payload.get("note")},
                    "creator": by,
                    "created": now_local(),
                    "created_utc": now_utc(),
                    "motivation": "commenting",
                    "tool": "%s %s" % (TOOL, TOOL_VERSION),
                }
                with _LOCK:
                    append_row(pass_dir, row)
                self._send(200, json.dumps({"ok": True}))
                return

            self._send(404, json.dumps({"ok": False, "error": "no such path"}))

    return Handler


def free_port(start):
    for port in range(start, start + 40):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
        finally:
            s.close()
    sys.exit("no free port in %d..%d" % (start, start + 40))


def print_summary(pass_dir, frame):
    rows = read_log(pass_dir)
    state, _ = project(rows)
    counts = {a: 0 for a in ANSWERS}
    for entry in state.values():
        counts[entry["verdict"]] += 1
    n = frame["draw"]["n"]
    print("pass      %s" % frame["pass_id"])
    print("question  %s" % frame["question"])
    print("log rows  %d  (append-only; revisions are kept, not overwritten)"
          % len(rows))
    print("")
    for a in ANSWERS:
        print("  %-8s %4d" % (a, counts[a]))
    print("  %-8s %4d   <- absence, not a value"
          % ("(none)", n - sum(counts.values())))
    print("")
    print("reviewed  %d of %d" % (sum(counts.values()), n))
    notes = sum(1 for e in state.values() if e.get("note"))
    print("notes     %d" % notes)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--by", help="reviewer name. Required to review; ADR-001 "
                                 "forbids anonymous verdicts.")
    ap.add_argument("--pass-id", default=None)
    ap.add_argument("--port", type=int, default=8731)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--summary", action="store_true",
                    help="print counts from the log and exit; writes nothing")
    args = ap.parse_args()

    pass_id = args.pass_id or newest_pass()
    if not pass_id:
        sys.exit("no prepared pass under data/curated/corpus_review/. Run:\n"
                 "  python scripts/review/prepare_corpus_review.py")
    pass_dir, frame, records = load_pass(pass_id)

    if args.summary:
        print_summary(pass_dir, frame)
        return 0

    if not args.by:
        sys.exit("--by is required. Every verdict names its reviewer "
                 "(ADR-001, and the same rule as triage_watch.py).")

    port = free_port(args.port)
    url = "http://127.0.0.1:%d/" % port
    done, _ = project(read_log(pass_dir))

    print("")
    print("  pass       %s" % pass_id)
    print("  question   %s" % frame["question"])
    print("  records    %d fetched of %d drawn" % (len(records),
                                                   frame["draw"]["n"]))
    print("  already    %d judged (resuming; decided records are not shown "
          "again)" % len(done))
    print("  reviewer   %s" % args.by)
    print("  verdicts   %s" % log_path(pass_dir).replace(REPO + os.sep, ""))
    print("  keys       ` yes   ] no   \\ can't tell   [ skip   ~ undo")
    print("  open       %s" % url)
    print("")
    print("  Every keypress is appended and fsync'd before the next card.")
    print("  Ctrl-C when done; nothing is lost by closing the tab.")
    print("")
    sys.stdout.flush()   # so the banner survives a redirected stdout

    handler = make_handler(pass_dir, frame, records, args.by, pass_id)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")
        print_summary(pass_dir, frame)
    return 0


if __name__ == "__main__":
    sys.exit(main())
