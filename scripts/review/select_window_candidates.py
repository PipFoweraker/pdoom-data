"""Surface candidates likely to open a decision window in pdoom1.

    python scripts/review/select_window_candidates.py --limit 20

Why this exists
---------------
pdoom1 demotes every `technical_research_breakthrough` record and every
`arxiv*` id to a grey feed line: options never presented, effects never
applied. Measured, that is 1,174 of 1,194 records. A decision window opens
only for `funding_catastrophe`, `organizational_crisis` and
`institutional_decay` -- twenty records, all of them hand-authored.

So reviewing candidates at random cannot widen the game's decision surface.
Reviewing candidates that plausibly belong to those three categories is the
only selection work that can. This script surfaces those, best-first, so a
scarce human pass is spent where it changes something.

What this is NOT
----------------
This is a **shortlist heuristic, not a classifier**. It reads titles, because
forum-post records carry metadata and a link only -- summaries are empty by
licence. A title match is a reason to look, never a verdict. Every row it emits
is a question for a human, and the human's answer is the opinion of record.

The score is deliberately explainable rather than accurate: each row reports
which terms fired and what its karma signal was, so a reviewer can see why it
was put in front of them and discount accordingly.
"""
import argparse
import io
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEED = os.path.join(REPO_ROOT, "data", "serveable", "api", "candidates",
                    "all_candidates.jsonl")

# Terms grouped by the pdoom1 category they suggest. Chosen from what actually
# opens a window today, not from what a taxonomy would suggest.
TERMS = {
    "funding_catastrophe": [
        "funding", "funder", "grant", "grants", "donor", "donation", "money",
        "budget", "runway", "salary", "salaries", "philanthrop", "ftx",
        "openphil", "open phil", "endowment", "fundrais", "invest", "raise",
        "financial", "bankrupt", "clawback", "payout", "cost",
    ],
    "organizational_crisis": [
        "resign", "resignation", "left ", "leaving", "quit", "fired",
        "departure", "depart", "board", "ceo", "leadership", "coup", "ousted",
        "staff", "team", "hiring", "layoff", "restructur", "merger",
        "acquisition", "spin out", "spinout", "split", "founder", "exodus",
        "shut down", "shutdown", "closure", "dissolv", "scandal", "drama",
    ],
    "institutional_decay": [
        "governance", "policy", "regulat", "oversight", "institution",
        "accountab", "transparen", "audit", "compliance", "safety team",
        "safety case", "commitment", "broken promise", "walked back",
        "conflict of interest", "capture", "lobby", "whistleblow", "nda",
        "non-disparage", "charter", "mission",
    ],
}


def score(title):
    """Return (best_category, hits_by_category). Explainable by construction."""
    low = " " + title.lower() + " "
    hits = {}
    for cat, terms in TERMS.items():
        found = [t.strip() for t in terms if t in low]
        if found:
            hits[cat] = found
    if not hits:
        return None, {}
    best = max(hits, key=lambda c: len(hits[c]))
    return best, hits


def karma_of(rec):
    sig = (rec.get("signals") or {}).get("karma") or []
    if not sig:
        return None
    try:
        return max(int(s.get("value", 0)) for s in sig)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", action="store_true",
                    help="emit JSON for tooling instead of a reading list")
    args = ap.parse_args()

    rows = []
    scanned = already = 0
    for line in io.open(FEED, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        scanned += 1

        # Only forum posts can plausibly be org/funding/institutional; model
        # releases are research-breakthrough shaped and would demote.
        if rec.get("kind") != "forum_post":
            continue
        # Never re-surface something a human has already ruled on.
        if rec.get("reviews"):
            already += 1
            continue
        if rec.get("privacy_review_required"):
            continue

        cat, hits = score(rec.get("title") or "")
        if not cat:
            continue

        k = karma_of(rec)
        n_terms = sum(len(v) for v in hits.values())
        rows.append({
            "id": rec["id"],
            "title": rec.get("title") or "",
            "date": rec.get("published_at") or rec.get("occurred_at"),
            "karma": k,
            "suggested_category": cat,
            "terms": sorted(set(t for v in hits.values() for t in v)),
            "n_terms": n_terms,
            "tier": (rec.get("salience_tier_by_profile") or {}).get("default_v1"),
            "url": (rec.get("source_urls") or [None])[0],
        })

    # Rank: term-match strength first, then karma. Karma is a popularity signal
    # and a weak proxy for importance, so it breaks ties rather than leading.
    rows.sort(key=lambda r: (-r["n_terms"], -(r["karma"] or 0)))
    out = rows[:args.limit]

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=True))
        return 0

    print("scanned %d records, %d forum posts already reviewed, %d shortlisted"
          % (scanned, already, len(rows)))
    print("showing top %d\n" % len(out))
    for i, r in enumerate(out, 1):
        k = "karma %s" % r["karma"] if r["karma"] is not None else "karma n/a"
        print("%2d. %s" % (i, r["title"]))
        print("    %s | %s | tier %s | %s" % (r["date"], k, r["tier"], r["id"]))
        print("    suggests: %s  (matched: %s)"
              % (r["suggested_category"], ", ".join(r["terms"][:6])))
        print("    %s" % r["url"])
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
