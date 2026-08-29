"""Assert the aggregator fallback fills only what is empty, and says so.

    python tests/test_source_fallback.py

Why this exists
---------------
`apply_source_fallback()` writes a URL into a record that had none. That is the
single most dangerous kind of edit in this repo: it makes a record look sourced.
Done wrongly it manufactures provenance, and a manufactured source is worse than
a missing one, because a missing one is visible and a manufactured one is not.

Ruled by Pip on 2026-08-21 as option B, over leaving the six records unsourced
(A) and over dropping them from the served feed (C).

Four properties hold it honest, and each has a case below:

  1. It NEVER overwrites an existing source. A record that has a primary paper
     keeps pointing at the paper.
  2. The URL is READ FROM `config/sources.json`, not typed into the producer.
     If the registry and the served feed ever disagree, that is a defect and
     this test is where it surfaces.
  3. It invents nothing. A record whose source id is not in the registry stays
     empty, and the ladder goes on failing for it, which is correct.
  4. Every record it touches carries `_provenance.source_urls` naming the
     method `aggregator_fallback`. No other record carries that key, so a
     consumer can tell an aggregator URL from a primary one today.

The count case is the one that matters most. It pins the number of fallback
records to exactly the six that were measured. A future change that silently
falls back for hundreds of records would still satisfy every other case here
and would turn this one red.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "build"))

import project_candidates as pc  # noqa: E402

FEED = os.path.join(REPO, "data", "serveable", "api", "candidates",
                    "all_candidates.jsonl")
SOURCES = os.path.join(REPO, "config", "sources.json")

# The five measured on 2026-08-29, with the reason each carried no source. They
# are listed rather than counted so that a change of WHICH records fall back is
# as visible as a change of how many -- which is exactly what it caught.
#
# epoch_ai:eagle_2 was the sixth until 2026-08-29. It fell back because the
# adapter dropped its schemeless URL; _base.py now parses that form, so the
# record carries https://arxiv.org/abs/2501.14818 from upstream and no longer
# needs the registry. Removed because the fix landed, NOT because the
# expectation was inconvenient -- the URL was checked in the served feed.
EXPECTED_FALLBACK = {
    "epoch_ai:yi_large":        "Link blank in Epoch's own CSV",
    "epoch_ai:gpt_5_2":         "Link blank in Epoch's own CSV",
    "epoch_ai:gpt_5_1_codex":   "Link blank in Epoch's own CSV",
    "epoch_ai:midjourney_v1":   "Link blank in Epoch's own CSV",
    "epoch_ai:exaone_4_5":      "author list in the Link column upstream",
}


def registry():
    doc = json.load(io.open(SOURCES, encoding="utf-8"))
    return {k: v for k, v in doc.items() if k != "_schema"}


def served():
    return [json.loads(l) for l in io.open(FEED, encoding="utf-8") if l.strip()]


def failures_for_unit_cases():
    out = []
    reg = registry()
    epoch_url = reg["epoch_ai"]["url"]

    # 1. never overwrites
    r = {"id": "epoch_ai:x", "source_urls": ["https://arxiv.org/abs/1"],
         "_provenance": {}}
    changed = pc.apply_source_fallback(r, reg)
    if changed or r["source_urls"] != ["https://arxiv.org/abs/1"]:
        out.append("  overwrote an existing source: %r" % (r["source_urls"],))
    if "source_urls" in r["_provenance"]:
        out.append("  marked a record it did not change")

    # 2. fills an empty one from the registry
    r = {"id": "epoch_ai:x", "source_urls": [], "_provenance": {}}
    changed = pc.apply_source_fallback(r, reg)
    if not changed or r["source_urls"] != [epoch_url]:
        out.append("  did not fill an empty source_urls from the registry: %r"
                   % (r.get("source_urls"),))
    prov = r["_provenance"].get("source_urls") or {}
    if prov.get("method") != "aggregator_fallback":
        out.append("  filled without recording the method: %r" % (prov,))
    if prov.get("confidence") != "low":
        out.append("  aggregator fallback not recorded as low confidence: %r"
                   % (prov,))

    # 3. invents nothing for an unknown source
    r = {"id": "not_a_source:x", "source_urls": [], "_provenance": {}}
    changed = pc.apply_source_fallback(r, reg)
    if changed or r["source_urls"]:
        out.append("  invented a source for an id not in the registry: %r"
                   % (r["source_urls"],))

    # 4. a registry entry with no url cannot produce one
    r = {"id": "epoch_ai:x", "source_urls": [], "_provenance": {}}
    changed = pc.apply_source_fallback(r, {"epoch_ai": {"name": "no url here"}})
    if changed or r["source_urls"]:
        out.append("  produced a URL from a registry entry that has none")

    return out


def failures_for_corpus():
    out = []
    reg = registry()
    rows = served()

    marked = {}
    for r in rows:
        prov = (r.get("_provenance") or {}).get("source_urls") or {}
        if prov.get("method") == "aggregator_fallback":
            marked[r["id"]] = r

    unexpected = sorted(set(marked) - set(EXPECTED_FALLBACK))
    missing = sorted(set(EXPECTED_FALLBACK) - set(marked))
    if unexpected:
        out.append("  %d record(s) fall back that were not expected to: %s"
                   % (len(unexpected), ", ".join(unexpected[:10])))
    if missing:
        out.append("  expected fallback did not happen for: %s"
                   % ", ".join(missing))

    # The URL served must equal the registry's, not a copy that has drifted.
    for rid, r in sorted(marked.items()):
        want = [reg[rid.split(":", 1)[0]]["url"]]
        if r["source_urls"] != want:
            out.append("  %s serves %r but the registry says %r"
                       % (rid, r["source_urls"], want))

    # No record may still be sourceless: that is the bronze predicate itself,
    # asserted here too so the reason is legible when it breaks.
    sourceless = [r["id"] for r in rows if not (r.get("source_urls") or [])]
    if sourceless:
        out.append("  %d record(s) still carry no source: %s"
                   % (len(sourceless), ", ".join(sourceless[:10])))

    # And the fallback must stay rare. If this number grows, something upstream
    # broke and the feed is quietly citing an aggregator for real events.
    if len(marked) > len(EXPECTED_FALLBACK):
        out.append("  fallback count grew to %d, above the measured %d"
                   % (len(marked), len(EXPECTED_FALLBACK)))
    return out


def main():
    failures = failures_for_unit_cases() + failures_for_corpus()
    if failures:
        print("SOURCE FALLBACK FAILED")
        for f in failures:
            print(f)
        return 1
    print("source fallback: 4 unit properties hold; exactly %d served records "
          "fall back, all to the registry URL, all marked in _provenance"
          % len(EXPECTED_FALLBACK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
