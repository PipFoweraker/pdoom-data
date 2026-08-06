"""Build a self-contained scan view for a fast yes/no pass over candidates.

    python scripts/review/build_scan_view.py --limit 300 --out tools/scan_view.html

Why a scan view and not the existing queue
------------------------------------------
tools/review_queue.html is a QUEUE: one record at a time, keyboard-driven,
optimised for considered judgement with notes. That is the right shape for a
careful pass and the wrong shape for "skim three hundred and grab the obvious
ones", which is a different job.

This emits a dense list: everything visible at once, click or key to mark,
titles link out so a record can be opened before ruling on it. Same export
format as the queue, so both merge through the same path and a later careful
pass can revise an early rough one -- the review layer is append-only and
attributed by design.

Selection is scripts/review/select_window_candidates.py: forum posts whose
titles suggest one of the three categories that actually open a decision window
in pdoom1. Records already carrying a verdict are excluded, so repeated passes
work through the pile rather than re-asking.
"""
import argparse
import html
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import select_window_candidates as sel  # noqa: E402

FEED = os.path.join(REPO_ROOT, "data", "serveable", "api", "candidates",
                    "all_candidates.jsonl")


def gather(limit):
    """Tight-filter rows first, then fill to `limit` by karma alone.

    Every row records which basis surfaced it. That separation is the point:
    if verdicts get worse deeper into a pass, the cause could be the pile
    thinning OR the selector loosening, and without the label those two are
    indistinguishable afterwards. The basis is recomputed rather than stored in
    the opinion layer -- selection metadata does not belong in a record of what
    a human thought.
    """
    tight, loose = [], []
    for line in io.open(FEED, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("kind") != "forum_post":
            continue
        if rec.get("reviews"):
            continue
        if rec.get("privacy_review_required"):
            continue
        cat, hits = sel.score(rec.get("title") or "")
        row = {
            "id": rec["id"],
            "title": rec.get("title") or "",
            "date": (rec.get("published_at") or rec.get("occurred_at") or "")[:10],
            "karma": sel.karma_of(rec),
            "cat": cat or "no term match",
            "n": sum(len(v) for v in hits.values()) if cat else 0,
            "basis": "term" if cat else "karma",
            "url": (rec.get("source_urls") or [""])[0],
        }
        (tight if cat else loose).append(row)

    tight.sort(key=lambda r: (-r["n"], -(r["karma"] or 0)))
    loose.sort(key=lambda r: -(r["karma"] or 0))
    out = tight[:limit]
    if len(out) < limit:
        out += loose[:limit - len(out)]
    return out


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>pdoom-data scan view</title>
<style>
:root{--ink:#16201e;--soft:#5a6763;--rule:#d7dedb;--paper:#fcfcfb;
--yes:#1e6b3a;--no:#8c2f2f;--maybe:#8a6d1f;--accent:#1e4f52;}
@media(prefers-color-scheme:dark){:root{--ink:#e8e4dd;--soft:#a099;--rule:#333;
--paper:#131211;--yes:#6fbf8c;--no:#e08b8b;--maybe:#d9b76a;--accent:#6fb3b0;}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font:14px/1.4 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
header{position:sticky;top:0;background:var(--paper);border-bottom:2px solid var(--ink);
padding:10px 16px;z-index:5}
h1{margin:0 0 2px;font-size:15px;letter-spacing:.01em}
.sub{color:var(--soft);font-size:12px}
.bar{display:flex;gap:14px;align-items:center;margin-top:8px;flex-wrap:wrap}
button{font:inherit;padding:5px 11px;border:1px solid var(--accent);
background:var(--accent);color:var(--paper);border-radius:3px;cursor:pointer}
button.ghost{background:transparent;color:var(--accent)}
.count{font-variant-numeric:tabular-nums;color:var(--soft);font-size:12px}
main{padding:0 16px 120px}
.row{display:grid;grid-template-columns:34px 1fr 92px 62px 132px;gap:10px;
align-items:baseline;padding:7px 6px;border-bottom:1px solid var(--rule)}
.row:hover{background:rgba(127,127,127,.07)}
.row.done{opacity:.42}
.idx{color:var(--soft);font-variant-numeric:tabular-nums;font-size:12px}
.t{min-width:0}
.t a{color:inherit;text-decoration:none;border-bottom:1px solid var(--rule)}
.t a:hover{border-bottom-color:var(--accent)}
.meta{color:var(--soft);font-size:11.5px;margin-top:1px}
.row.karma .idx{color:var(--maybe)}
.k,.d{color:var(--soft);font-size:12px;font-variant-numeric:tabular-nums;text-align:right}
.v{display:flex;gap:4px;justify-content:flex-end}
.v b{cursor:pointer;padding:2px 8px;border:1px solid var(--rule);border-radius:3px;
font-weight:600;font-size:12px;user-select:none}
.v b:hover{border-color:var(--accent)}
.v b.on[data-v=accept]{background:var(--yes);border-color:var(--yes);color:var(--paper)}
.v b.on[data-v=unsure]{background:var(--maybe);border-color:var(--maybe);color:var(--paper)}
.v b.on[data-v=reject]{background:var(--no);border-color:var(--no);color:var(--paper)}
footer{position:fixed;bottom:0;left:0;right:0;background:var(--paper);
border-top:2px solid var(--ink);padding:9px 16px;display:flex;gap:14px;
align-items:center;justify-content:space-between;font-size:12.5px}
kbd{border:1px solid var(--rule);border-radius:3px;padding:0 5px;font-size:11px}
</style></head><body>
<header>
<h1>pdoom-data &mdash; scan view</h1>
<div class="sub">Forum posts whose titles suggest <b>funding_catastrophe</b>,
<b>organizational_crisis</b> or <b>institutional_decay</b> &mdash; the only three
categories that open a decision window in pdoom1. Records already carrying a
verdict are excluded.</div>
<div class="bar">
  <button id="export">Export verdicts</button>
  <button class="ghost" id="clear">Clear all</button>
  <span class="count" id="count"></span>
</div>
</header>
<main id="list"></main>
<footer>
<span>Click <b>Y</b> / <b>M</b> / <b>N</b>, or hover a row and press
<kbd>y</kbd> <kbd>m</kbd> <kbd>n</kbd>. <kbd>Esc</kbd> clears a row.
Titles open in a new tab.</span>
<span class="count" id="tally"></span>
</footer>
<script>
const DATA = __DATA__;
const V = {};
const list = document.getElementById('list');
let hovered = null;

function tally(){
  let a=0,u=0,r=0;
  for(const k in V){ if(V[k]==='accept')a++; else if(V[k]==='unsure')u++; else if(V[k]==='reject')r++; }
  document.getElementById('tally').textContent =
    a+' accept  '+u+' unsure  '+r+' reject  \\u2014  '+(a+u+r)+' of '+DATA.length;
  document.getElementById('count').textContent = DATA.length+' shortlisted, unreviewed';
}
function set(id,v){
  if(V[id]===v){ delete V[id]; } else { V[id]=v; }
  const row=document.querySelector('[data-id="'+CSS.escape(id)+'"]');
  row.querySelectorAll('.v b').forEach(b=>b.classList.toggle('on', V[id]===b.dataset.v));
  row.classList.toggle('done', !!V[id]);
  tally();
}
DATA.forEach((d,i)=>{
  const row=document.createElement('div');
  row.className='row'+(d.basis==='karma'?' karma':''); row.dataset.id=d.id;
  row.innerHTML =
    '<div class="idx">'+(i+1)+'</div>'+
    '<div class="t"><a href="'+d.url+'" target="_blank" rel="noopener">'+d.title+'</a>'+
      '<div class="meta">'+d.cat+(d.basis==="karma"?' &middot; <i>karma only, no term match</i>':'')+'</div></div>'+
    '<div class="d">'+d.date+'</div>'+
    '<div class="k">'+(d.karma===null?'&mdash;':d.karma)+'</div>'+
    '<div class="v">'+
      '<b data-v="accept">Y</b><b data-v="unsure">M</b><b data-v="reject">N</b>'+
    '</div>';
  row.addEventListener('mouseenter',()=>hovered=d.id);
  row.querySelectorAll('.v b').forEach(b=>
    b.addEventListener('click',()=>set(d.id,b.dataset.v)));
  list.appendChild(row);
});
document.addEventListener('keydown',e=>{
  if(!hovered) return;
  const m={y:'accept',m:'unsure',n:'reject'};
  if(m[e.key]){ set(hovered,m[e.key]); e.preventDefault(); }
  if(e.key==='Escape'&&V[hovered]) set(hovered,V[hovered]);
});
document.getElementById('clear').addEventListener('click',()=>{
  for(const k in V) delete V[k];
  document.querySelectorAll('.row').forEach(r=>{
    r.classList.remove('done'); r.querySelectorAll('.v b').forEach(b=>b.classList.remove('on'));
  });
  tally();
});
document.getElementById('export').addEventListener('click',()=>{
  const today=new Date().toISOString().slice(0,10);
  const recs={};
  for(const id in V){
    recs[id]={reviewer:"Pip Foweraker",verdict:V[id],tier_override:null,note:null,at:today};
  }
  const out={_metadata:{
    layer:"human_review",reviewer:"Pip Foweraker",precedence:"highest",
    nature:"ATTRIBUTED OPINION, not fact. Consumers may inherit this reviewer's judgement, filter to reviewers they trust, or ignore reviews entirely.",
    tool:"tools/scan_view.html",tool_version:"1.0.0",
    exported_at:new Date().toISOString(),record_count:Object.keys(recs).length,
    tombstone_count:0,
    pass_type:"rough scan for obvious accepts and rejects; later passes may revise",
    selection:"scripts/review/select_window_candidates.py"
  },records:recs,proposed_tombstones:[]};
  const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='human_review_'+today+'_scan.json';
  a.click();
});
tally();
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--out", default=os.path.join(REPO_ROOT, "tools", "scan_view.html"))
    args = ap.parse_args()

    rows = gather(args.limit)
    for r in rows:
        r["title"] = html.escape(r["title"])
        r["url"] = html.escape(r["url"], quote=True)

    page = PAGE.replace("__DATA__", json.dumps(rows, ensure_ascii=True))
    tmp = args.out + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(page)
    os.replace(tmp, args.out)
    print("wrote %s" % os.path.relpath(args.out, REPO_ROOT).replace("\\", "/"))
    print("rows: %d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
