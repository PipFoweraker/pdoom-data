#!/usr/bin/env python3
"""Adapter: LessWrong and EA Forum posts, karma-ranked.

Fetches the top-scoring posts per year via each site's public GraphQL API.
Karma is the point: it is an external, reproducible, time-anchored salience
signal, which is exactly what the existing A/B/C/D tier system lacks (that
scores provenance and length, not importance).

LICENSING POSTURE: this adapter stores bibliographic metadata and a hyperlink
only -- title, author display name, date, karma, comment count, tags, URL. It
does NOT retain post text. Facts and links are not a derivative work, so no
license grant from the forums or their authors is relied upon. If post text is
ever wanted, that is a separate decision requiring first-party terms review.

Usage:
    python scripts/adapters/forum_posts.py --forum lw  --since 2023 --until 2026
    python scripts/adapters/forum_posts.py --forum eaf --top-per-year 300
    python scripts/adapters/forum_posts.py --forum both --dry-run

Writes immutable dumps under data/raw/forum_lesswrong/ and data/raw/forum_eaforum/.
"""

import argparse
import json
import sys
import time

sys.path.insert(0, __file__.rsplit("forum_posts.py", 1)[0])

import _base  # noqa: E402

ADAPTER_VERSION = "0.1.0"
PAGE_SIZE = 50
SLEEP_BETWEEN_REQUESTS = 1.0

FORUMS = {
    "lw": {
        "source_id": "forum_lesswrong",
        "name": "LessWrong",
        "endpoint": "https://www.lesswrong.com/graphql",
        "site": "https://www.lesswrong.com/",
    },
    "eaf": {
        "source_id": "forum_eaforum",
        "name": "EA Forum",
        "endpoint": "https://forum.effectivealtruism.org/graphql",
        "site": "https://forum.effectivealtruism.org/",
    },
}

QUERY = """{posts(input:{terms:{limit:%d, offset:%d, after:"%s", before:"%s",
sortedBy:"top"}}){results{_id title postedAt baseScore commentCount pageUrl
user{displayName} tags{name}}}}"""

# Null, not guessed. Both forums long predate this ingest, but the exact dates
# a player-era gate should use are unconfirmed. Candidate values to VERIFY:
# LessWrong ~2009 (and LessWrong 2.0 ~2017-2018, a materially different site),
# EA Forum ~2011. Recorded as hints in dump metadata, not as data.
SOURCE_AVAILABLE_AT = None


def license_block(forum):
    return {
        "spdx": "NOASSERTION",
        "url": None,
        "attribution": (
            "%s (%s). Post authors retain all rights to their content."
            % (forum["name"], forum["site"])
        ),
        "citation": "%s, post metadata retrieved via public GraphQL API" % forum["name"],
        "source_terms_url": forum["site"],
        "verified_at": "2026-07-25",
        "verified_by": (
            "No license relied upon. Bibliographic metadata and hyperlink only; "
            "no post text is stored. Terms not separately reviewed because no "
            "copyrightable expression is retained."
        ),
        "reuse_basis": "facts_and_link_only",
    }


def fetch_year(session, forum, year, top_n):
    """Return up to top_n posts for one calendar year, karma-descending."""
    after = "%d-01-01" % year
    before = "%d-01-01" % (year + 1)
    collected = []
    seen = set()
    offset = 0
    while len(collected) < top_n:
        limit = min(PAGE_SIZE, top_n - len(collected))
        query = QUERY % (limit, offset, after, before)
        response = _base.polite_post(
            session, forum["endpoint"], json={"query": query},
            headers={"Content-Type": "application/json"},
        )
        body = response.json()
        if "errors" in body:
            messages = [e.get("message", "")[:200] for e in body["errors"][:3]]
            raise RuntimeError("%s %d: %r" % (forum["source_id"], year, messages))
        results = (body.get("data") or {}).get("posts", {}).get("results") or []
        if not results:
            break
        fresh = 0
        for post in results:
            key = post.get("_id")
            if key and key not in seen:
                seen.add(key)
                collected.append(post)
                fresh += 1
        offset += len(results)
        if fresh == 0:
            break
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    return collected


def normalise(post, forum, rank, year, ingested_at):
    posted = (post.get("postedAt") or "")[:10] or None
    title = _base.to_ascii((post.get("title") or "").strip())
    if not title:
        return None

    author = ((post.get("user") or {}) or {}).get("displayName")
    tags = [_base.to_ascii(t.get("name", "")) for t in (post.get("tags") or [])]
    tags = [t for t in tags if t]

    signals = {}
    score = post.get("baseScore")
    if score is not None:
        signals.update(_base.signal("karma", score, ingested_at))
    comments = post.get("commentCount")
    if comments is not None:
        signals.update(_base.signal("comment_count", comments, ingested_at))
    # Rank within its own year: comparable across years in a way raw karma is
    # not, since forum traffic and vote inflation drift over time.
    signals.update(_base.signal("karma_rank_in_year", rank, ingested_at))

    return {
        "id": "%s:%s" % (forum["source_id"], post.get("_id")),
        "title": title,
        "summary": "",
        "kind": "forum_post",
        "occurred_at": posted,
        "published_at": posted,
        "source_available_at": SOURCE_AVAILABLE_AT,
        "ingested_at": ingested_at,
        "actors": [_base.to_ascii(author)] if author else [],
        "source_urls": [post.get("pageUrl")] if post.get("pageUrl") else [],
        "archive_urls": [],
        "content_sha256": None,
        "license": license_block(forum),
        "signals": signals,
        "airr_tags": {"causal": [], "domain": []},
        "source_raw_key": post.get("_id"),
        "extra": {
            "forum": forum["name"],
            "forum_tags": tags,
            "rank_year": year,
        },
        "_provenance": {
            "title": {"layer": "raw", "method": "upstream_field", "confidence": "high"},
            "summary": {"layer": "raw", "method": "not_collected",
                        "confidence": "low"},
            "occurred_at": {"layer": "raw", "method": "upstream_postedAt",
                            "confidence": "high"},
            "published_at": {"layer": "raw", "method": "upstream_postedAt",
                             "confidence": "high"},
            "source_available_at": {"layer": "raw", "method": "unverified_null",
                                    "confidence": "low"},
            "actors": {"layer": "raw", "method": "upstream_display_name",
                       "confidence": "medium"},
            "signals": {"layer": "raw", "method": "upstream_field",
                        "confidence": "high"},
        },
    }


def run_forum(session, key, args):
    forum = FORUMS[key]
    ingested_at = _base.utc_now_iso()
    candidates = []
    raw_rows = []
    per_year = {}

    for year in range(args.since, args.until + 1):
        posts = fetch_year(session, forum, year, args.top_per_year)
        per_year[str(year)] = len(posts)
        print("  %s %d: %d posts" % (forum["source_id"], year, len(posts)))
        for rank, post in enumerate(posts, start=1):
            record = normalise(post, forum, rank, year, ingested_at)
            if record is None:
                continue
            candidates.append(record)
            raw_rows.append(json.loads(_base.to_ascii(json.dumps(post))))

    print("  %s total: %d" % (forum["source_id"], len(candidates)))

    if args.dry_run:
        problems = []
        for record in candidates:
            problems.extend(_base.validate_candidate(record))
        print("  validation problems: %d" % len(problems))
        if candidates:
            print(json.dumps(candidates[0], indent=2, sort_keys=True)[:900])
        return None

    metadata = {
        "source_url": forum["endpoint"],
        "source_name": forum["name"],
        "extraction_method": "graphql_api",
        "adapter_version": ADAPTER_VERSION,
        "license": license_block(forum),
        "source_available_at": SOURCE_AVAILABLE_AT,
        "source_available_at_note": (
            "UNVERIFIED. Candidate values to check before enabling gating: "
            "LessWrong approx 2009 (LessWrong 2.0 approx 2017-2018, a "
            "materially different site); EA Forum approx 2011. Recorded as "
            "hints, not as data."
        ),
        "query_window": {"since": args.since, "until": args.until},
        "filters_applied": {
            "sorted_by": "top",
            "top_per_year": args.top_per_year,
            "text_retained": False,
        },
        "extraction_statistics": {
            "fetched": len(candidates),
            "written": len(candidates),
            "per_year": per_year,
            "errors": 0,
        },
        "tool_versions": {"python": sys.version.split()[0]},
        "notes": (
            "Metadata and hyperlink only; no post text retained. Karma is an "
            "external salience signal, stored as a dated observation because "
            "scores keep accruing after publication."
        ),
    }
    return _base.write_dump(forum["source_id"], candidates, raw_rows, metadata)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forum", choices=["lw", "eaf", "both"], default="both")
    parser.add_argument("--since", type=int, default=2023)
    parser.add_argument("--until", type=int, default=2026)
    parser.add_argument("--top-per-year", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    session = _base.get_session()
    keys = ["lw", "eaf"] if args.forum == "both" else [args.forum]
    for key in keys:
        path = run_forum(session, key, args)
        if path:
            print("  wrote dump: %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
