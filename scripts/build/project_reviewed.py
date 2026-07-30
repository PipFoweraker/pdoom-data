"""Promote human-accepted candidates into their own served collection.

    python scripts/build/project_reviewed.py           # build
    python scripts/build/project_reviewed.py --check   # assert committed

Why this exists
---------------
206 candidates were reviewed by a named human on 2026-07-26 and 140 were
accepted. Those verdicts were merged into the candidate feed and were
technically available -- but only to a consumer willing to stream 3,434 records
and filter on a nested field. In practice that meant the review work was doing
nothing for anyone downstream.

This is the promotion step: the accepted records become their own collection,
so a consumer can pull human-filtered material without knowing how the review
layer is shaped.

A second-order projection
-------------------------
Unusually for this repo, the input is itself a build output
(data/serveable/api/candidates/). That is deliberate: the review merge, the
privacy screen and the salience profiles all already happen there, and
duplicating them here would create the exact two-producers-one-zone problem
that cost this repo seven months. Run project_candidates.py first; this reads
what it produced.

What "accepted" does and does not mean
--------------------------------------
It means one named reviewer said accept. It is an ATTRIBUTED OPINION, not a
fact, and the attribution travels with every record rather than being flattened
into a boolean. A consumer may inherit that judgement, filter to reviewers it
trusts, or ignore the collection entirely.

It does NOT mean verified, endorsed, or game-ready. Promotion into a game
remains the consumer's call; there is no game_facing flag here and there will
not be one.
"""
import argparse
import glob
import io
import json
import os
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO_ROOT, "data", "serveable", "api", "candidates", "all_candidates.jsonl")
REVIEW_ROOT = os.path.join(REPO_ROOT, "data", "curated", "human_review")
OUT_DIR = os.path.join(REPO_ROOT, "data", "serveable", "api", "reviewed")

ACCEPT = "accept"


def load_reviewer_meta():
    """Who reviewed, and what each layer says about its own nature."""
    layers = []
    for path in sorted(glob.glob(os.path.join(REVIEW_ROOT, "*.json"))):
        with io.open(path, encoding="utf-8") as f:
            doc = json.load(f)
        meta = doc.get("_metadata", {})
        layers.append({
            "file": os.path.relpath(path, REPO_ROOT).replace("\\", "/"),
            "reviewer": meta.get("reviewer"),
            "layer": meta.get("layer"),
            "nature": meta.get("nature"),
            "tool": meta.get("tool"),
            "tool_version": meta.get("tool_version"),
            "record_count": meta.get("record_count"),
        })
    return layers


def build():
    if not os.path.isfile(SRC):
        sys.stderr.write(
            "missing %s\nRun scripts/build/project_candidates.py first; this "
            "collection is projected from that one.\n"
            % os.path.relpath(SRC, REPO_ROOT))
        sys.exit(2)

    out = []
    counts = defaultdict(int)
    reviewers = defaultdict(int)
    seen_ids = set()

    for line in io.open(SRC, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        counts["scanned"] += 1

        reviews = r.get("reviews") or []
        accepts = [rv for rv in reviews if rv.get("verdict") == ACCEPT]
        if not accepts:
            continue

        # Defence in depth. A record can carry an accept AND a later privacy
        # flag; the screen wins. Privacy failures are the kind that cannot be
        # undone by a later correction, so the check is repeated here rather
        # than trusted from upstream.
        if r.get("privacy_review_required"):
            counts["withheld_privacy"] += 1
            continue
        if any(rv.get("verdict") == "privacy" for rv in reviews):
            counts["withheld_privacy"] += 1
            continue

        rid = r.get("id")
        if rid in seen_ids:
            raise SystemExit(
                "duplicate id %r in the candidate feed -- a consumer keying by "
                "id would silently lose a record" % rid)
        seen_ids.add(rid)

        for rv in accepts:
            reviewers[rv.get("reviewer") or "unknown"] += 1

        counts["promoted"] += 1
        out.append(r)

    out.sort(key=lambda r: (r.get("published_at") or "", r.get("id") or ""))
    return out, counts, dict(sorted(reviewers.items()))


def write_jsonl(path, records):
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=True, sort_keys=True) + "\n")
    os.replace(tmp, path)


def write_json(path, obj):
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=True)
        f.write("\n")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="assert the committed output matches a fresh build")
    args = ap.parse_args()

    records, counts, reviewers = build()

    lineage = {
        "collection": "reviewed",
        "built_by": "scripts/build/project_reviewed.py",
        "projected_from": os.path.relpath(SRC, REPO_ROOT).replace("\\", "/"),
        "note": (
            "A second-order projection: the input is itself a build output. "
            "Run project_candidates.py first."
        ),
        "selection": (
            "records carrying at least one attributed review with verdict "
            "'accept', minus anything flagged for privacy review"
        ),
        "meaning": (
            "ATTRIBUTED OPINION, not fact. One named reviewer said accept. "
            "Not verified, not endorsed, not game-ready. Promotion into a game "
            "remains the consumer's call."
        ),
        "review_layers": load_reviewer_meta(),
        "counts": dict(sorted(counts.items())),
        "accepts_by_reviewer": reviewers,
    }

    feed_path = os.path.join(OUT_DIR, "all_reviewed.jsonl")
    lineage_path = os.path.join(OUT_DIR, "LINEAGE.json")

    print("scanned          : %d" % counts["scanned"])
    print("promoted         : %d" % counts["promoted"])
    print("withheld privacy : %d" % counts["withheld_privacy"])
    for who, n in reviewers.items():
        print("  accepts by %-20s %d" % (who, n))

    if args.check:
        if not os.path.isfile(feed_path):
            print("CHECK FAILED: %s does not exist" % feed_path)
            return 1
        fresh = "".join(json.dumps(r, ensure_ascii=True, sort_keys=True) + "\n"
                        for r in records)
        if io.open(feed_path, encoding="utf-8", newline="").read() != fresh:
            print("CHECK FAILED: committed feed differs from a fresh build")
            return 1
        with io.open(lineage_path, encoding="utf-8") as f:
            if json.load(f) != lineage:
                print("CHECK FAILED: committed LINEAGE differs from a fresh build")
                return 1
        print("CHECK OK: committed output matches a fresh build")
        return 0

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    write_jsonl(feed_path, records)
    write_json(lineage_path, lineage)
    print("wrote %s" % os.path.relpath(feed_path, REPO_ROOT).replace("\\", "/"))
    print("wrote %s" % os.path.relpath(lineage_path, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
