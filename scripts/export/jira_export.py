"""Emit every OPEN issue as JSONL for the coordination seat to write into Jira.

    python scripts/export/jira_export.py --date 2026-08-10
    python scripts/export/jira_export.py --date 2026-08-10 --check

Written as a script rather than a shell heredoc, per coordination's section 5d.
Three of the 2026-08-08/09 defects were heredocs eating escapes, one of them
inside the tool whose job was proving that what was sent is what was stored.
This session hit a fourth: a heredoc collapsed a doubled backslash and turned an
intended `\\u2013` escape back into a literal en dash, twice, silently.

This seat produces the payload. It does NOT write to Jira: the only verified
Atlassian connection in the estate belongs to the coordination seat, and one MCP
connection is one identity, permanently.

Judgement lives in JUDGEMENT below, keyed by issue number
------------------------------------------------------------
`epic`, `tier` and `why` are this seat's opinions, not facts about the issue, so
they are written down where they can be argued with rather than computed from
labels. Labels here are too sparse to carry it -- 17 of 39 open issues have no
label at all.

An open issue with no entry in JUDGEMENT is a HARD ERROR, not a default. A
default would let a new issue enter the export silently classified, and "it got
a tier because nobody looked" is the failure mode this whole export exists to
end.
"""
import argparse
import io
import json
import os
import subprocess
import sys

REPO = "pdoom-data"
OWNER = "PipFoweraker"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Eight epics, reused. Deliberately not one per issue: a grouping with 39
# members and 39 names is a list, not a grouping.
EPICS = [
    "Data quality",          # what the records actually say
    "Pipeline and producers",# how they get built, and whether they rebuild
    "Boundary and contract", # ADR-001: what crosses to pdoom1, and as what
    "Curation and review",   # human judgement passes over the corpus
    "Privacy and compliance",
    "New datasets",          # sources not yet ingested
    "Consumer integration",  # website and game actually consuming this
    "Governance and session close",
]

# number: (epic, tier, why)
#   tier 1 = active commitment, something breaks or slips if it waits
#   tier 2 = real backlog, will be done, no consequence this month
#   tier 3 = someday / noise / probably should be closed
JUDGEMENT = {
    4:  ("New datasets", 3, "Open Philanthropy grants data was never scoped and nothing downstream asks for it."),
    5:  ("New datasets", 3, "Schmidt Sciences AI2050, same: an availability question nobody has needed answered in nine months."),
    6:  ("New datasets", 3, "Macroscopic, same shape as the other someday source investigations."),
    7:  ("New datasets", 3, "GiveWiki, same shape; no consumer has asked for funding data."),
    8:  ("New datasets", 3, "Cooperative AI Foundation, same shape."),
    9:  ("New datasets", 3, "Catalyze Impact, same shape."),
    16: ("Consumer integration", 2, "Static export shape for the game, which the timeline_events split in the corpus proposal would supersede."),
    17: ("Pipeline and producers", 3, "A code-review request from 2025 that predates every producer this repo now has; its findings would be about deleted code."),
    18: ("Pipeline and producers", 3, "Automation ask written before the pipeline existed; superseded by the actual producers and their --check."),
    19: ("Consumer integration", 3, "Speculative external-API integration with no named consumer."),
    21: ("Governance and session close", 2, "Public devblog and log consolidation; note the DEVBLOG append job it implies is de-armed and must stay so."),
    22: ("New datasets", 2, "Contributor schema and sync; real, unstarted, no external date."),
    24: ("Consumer integration", 1, "The grant-readiness demo: a data-only change appearing on site and game. Labelled priority:critical and open since 2025-12-12."),
    25: ("Curation and review", 2, "Manual pass to find game-worthy B-tier events; blocked in practice on what the corpus should be."),
    26: ("Boundary and contract", 1, "Per-event A/B/C/D tier for in-game filtering; this is an ADR-001 boundary question, not a data one."),
    29: ("Curation and review", 2, "A third independent salience opinion. Valuable, and only after the corpus question settles."),
    31: ("Curation and review", 2, "Review-queue orderings; a tooling improvement for a human pass that is not currently running."),
    32: ("Privacy and compliance", 1, "Two flagged records still undecided, and 'widen the screen' is exactly what 2026-08-09 proved necessary."),
    33: ("Data quality", 2, "source_available_at precision for four sources; a dated-claim correctness item now that check_evidence gates."),
    34: ("Boundary and contract", 1, "Move pdoom1 impacts into an export profile. CLAUDE.md names this as the tracked breach of ADR-001."),
    35: ("New datasets", 2, "OpenAlex adapter for citation-ranked publications; the strongest candidate replacement for the arXiv bulk import."),
    36: ("Curation and review", 3, "Testing disagreement-ordering against salience ordering; a research question with no consumer waiting."),
    37: ("New datasets", 2, "Frontier-labs dataset exists and is served; this issue is the extensibility half."),
    38: ("New datasets", 2, "Countdown-milestones dataset the website's clocks need; the website is the named consumer."),
    39: ("Boundary and contract", 1, "Machine-readable fact-vs-opinion. The dice-rolled researcher reactions are the live proof this is not theoretical."),
    43: ("Boundary and contract", 1, "What a reviewed record becomes when it crosses to pdoom1. Unblocked, and blocks the game consuming any review work."),
    47: ("Boundary and contract", 2, "Terminology and glossary; the workshop ruled that a single copy must live in one place and be referenced."),
    48: ("Governance and session close", 2, "How much to mechanically forbid on epistemic grounds. Genuinely open, and this week produced evidence for it."),
    51: ("Data quality", 1, "rarity is a length threshold on a discarded field and the game routes 90 percent of events on it."),
    52: ("Pipeline and producers", 1, "The producer now exists, but manifest.json, stats.json and event_index.json still claim 28 records against 1,194."),
    55: ("Governance and session close", 2, "Pip's 2026-08-02 rulings A1-A7; a tracking issue that should be closed once its children are filed."),
    58: ("Data quality", 1, "The corpus survey is stale and size is no longer the constraint. Answered by the 2026-08-09 corpus proposal, awaiting a ruling."),
    59: ("Governance and session close", 3, "A session-close record from 2026-08-04. Historical; its carries have been carried."),
    60: ("Data quality", 1, "Corpus refresh plan and the tier ladder mechanism. The ladder was built; the refresh plan is the corpus proposal."),
    62: ("Governance and session close", 3, "A day-scoped priority list from 2026-08-06 whose items are all now tracked elsewhere."),
    64: ("Data quality", 2, "R5 headline-metric options, measured. Note the 28-of-1,194 figure is reframed by the corpus proposal's finding about event_v1."),
    65: ("Data quality", 1, "1,166 of 1,194 events fail the schema they are published under, and the corpus proposal shows the schema is testing the wrong things."),
    68: ("Data quality", 2, "Mojibake titles. The producer no longer reproduces them and check_transcoding gates the species; verify and close."),
    70: ("Governance and session close", 3, "Session close 2026-08-04 to 08-07. Its headline -- main unverified -- was resolved on 2026-08-10."),
}

# The only external date this repo holds. pdoom1 holds the IP/trademark one.
EXTERNAL_DEADLINES = {
    24: "2026-09-09",  # Manifund closes; the demo is what it is evidence for
}

BLOCKED_BY = {
    26: ["pdoom-data#43"],
    25: ["pdoom-data#58", "pdoom-data#65"],
    29: ["pdoom-data#58"],
    31: ["pdoom-data#58"],
    34: ["pdoom-data#43"],
    43: ["pdoom1#1102"],
    51: ["pdoom1#1102"],
    64: ["pdoom-data#65"],
    65: ["pdoom-data#43"],
    16: ["pdoom-data#58"],
    24: ["pdoom1-website#249"],
}


def fetch_open():
    out = subprocess.check_output([
        "gh", "issue", "list", "--repo", "%s/%s" % (OWNER, REPO),
        "--state", "open", "--limit", "200",
        "--json", "number,title,url,labels"], cwd=REPO_ROOT)
    return json.loads(out.decode("utf-8"))


def build(issues):
    unjudged = sorted(i["number"] for i in issues if i["number"] not in JUDGEMENT)
    if unjudged:
        raise SystemExit(
            "REFUSING: %d open issue(s) have no entry in JUDGEMENT: %s\n"
            "Classify them deliberately. A default tier is how work gets "
            "imported that nobody has looked at." % (len(unjudged), unjudged))
    rows = []
    for i in sorted(issues, key=lambda x: x["number"]):
        n = i["number"]
        epic, tier, why = JUDGEMENT[n]
        assert epic in EPICS, "unknown epic %r on #%d" % (epic, n)
        rows.append({
            "repo": REPO,
            "number": n,
            "title": i["title"],
            "url": i["url"],
            "labels": [l["name"] for l in i["labels"]],
            "epic": epic,
            "tier": tier,
            "external_deadline": EXTERNAL_DEADLINES.get(n),
            "blocked_by": BLOCKED_BY.get(n, []),
            "why": why,
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True,
                    help="ISO date for the filename. Never guessed.")
    ap.add_argument("--check", action="store_true",
                    help="assert the committed file matches a fresh export")
    args = ap.parse_args()

    rows = build(fetch_open())
    text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)

    out_dir = os.path.join(REPO_ROOT, "docs", "jira")
    out_path = os.path.join(out_dir, "export_%s.jsonl" % args.date)

    if args.check:
        if not os.path.isfile(out_path):
            print("MISSING: %s" % out_path)
            return 1
        current = io.open(out_path, encoding="utf-8", newline="").read()
        if current != text:
            print("DIFFERS from a fresh export (issues change; this is not "
                  "necessarily a defect, but the file is not current)")
            return 1
        print("CHECK OK: %d rows, matches a fresh export" % len(rows))
        return 0

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    tmp = out_path + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(text)
    os.replace(tmp, out_path)

    by_tier = {}
    by_epic = {}
    for r in rows:
        by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
        by_epic[r["epic"]] = by_epic.get(r["epic"], 0) + 1
    print("wrote %s" % os.path.relpath(out_path, REPO_ROOT).replace("\\", "/"))
    print("rows: %d" % len(rows))
    for t in sorted(by_tier):
        print("  tier %d: %d" % (t, by_tier[t]))
    print()
    for e in EPICS:
        print("  %-30s %d" % (e, by_epic.get(e, 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
