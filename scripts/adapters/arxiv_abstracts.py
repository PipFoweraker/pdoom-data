#!/usr/bin/env python3
"""Fetch real abstracts from arXiv for the bulk timeline events.

    python scripts/adapters/arxiv_abstracts.py --limit 50
    python scripts/adapters/arxiv_abstracts.py --limit 50 --dump-dir <existing>

Why this exists
---------------
1,166 of the 1,194 served timeline events carry a description that is a head
slice of raw document text -- section headings, PDF furniture, a technical
report cover page. Median length 30 characters. They are 97.7% of the public
event pages. See pdoom-data#88.

There is no local text to repair them from. The 1,166 served records share
ZERO ids and ZERO source URLs with the 1,000 records in
`data/raw/alignment_research/dumps/`. They are disjoint corpora, so
`enriched_alignment_research_events.json` -- which sits in the SERVEABLE zone
and is nonetheless a producer INPUT -- has no raw provenance in this repository
at all. Measured 2026-08-21.

What it does have is a source URL: 1,129 point at `arxiv.org/abs/`, 37 at
`distill.pub`. So the primary source is identifiable, and the honest repair is
to go and read it rather than to write a description here. arXiv's own API
returns the author-written abstract. **Nothing in this file composes prose.**

This is an adapter, so it obeys the adapter rules: it writes an immutable dump
under `data/raw/`, it never edits a previous one, and re-running it produces a
NEW dump. That dump is also the provenance the 1,166 records have never had.

ASCII, and the character that vanishes
--------------------------------------
The repo is ASCII-only. `_base.to_ascii` decomposes with NFKD, so `Lo"b` becomes
`Lob` and `Go"del` becomes `Godel` -- lossy but readable, and with no `?`
fallback, which is the rule that matters here.

But a character with no ASCII decomposition becomes the EMPTY STRING silently.
A mathematics abstract reading "alpha-divergence" in Greek would be served as
"-divergence" with nothing to show a character had been dropped. So every
proposal records `chars_dropped`, and the review tool shows it. A human decides;
the pipeline does not silently mangle and move on.

Politeness
----------
arXiv asks for no more than one request every three seconds and supports
batching by `id_list`. Batching is both faster and more polite than one request
per record, so this sends 50 ids per call with a 3.5-second gap between calls.
"""
import argparse
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "adapters"))

import _base  # noqa: E402

SOURCE_ID = "arxiv_abstracts"
ENRICHED = os.path.join(
    REPO_ROOT, "data", "serveable", "api", "timeline_events",
    "enriched_alignment_research", "enriched_alignment_research_events.json")
API = "http://export.arxiv.org/api/query"
BATCH = 50
GAP_SECONDS = 3.5
UA = "pdoom-data/1.0 (+https://github.com/PipFoweraker/pdoom-data)"
NS = {"a": "http://www.w3.org/2005/Atom"}

# Read, not assumed. https://info.arxiv.org/help/api/tou.html, fetched
# 2026-08-21, states: "You are free to use descriptive metadata about arXiv
# e-prints under the terms of the Creative Commons Universal (CC0 1.0) Public
# Domain Declaration." Its footnote 1 defines the term: "Descriptive metadata
# includes information for discovery and identification purposes, and includes
# fields such as title, abstract, authors, identifiers, and classification
# terms." So the abstract is metadata, and CC0-1.0 applies.
#
# The first version of this constant said NOASSERTION with reuse_basis
# "facts_and_link_only", and a verified_by claiming the Terms had been read
# when they had not. Both were wrong and in opposite directions: the basis was
# copied from the forum adapters, which store no post text, while this tool
# stores abstracts verbatim; and asserting a reading that did not happen is the
# exact failure this repository exists to prevent. The fix was to go and read
# them, which took two minutes.
#
# The same page's prohibition was read too: "Store and serve arXiv e-prints
# (PDFs, source files, or other content) from your servers." It does not reach
# abstracts, and nothing here fetches a PDF or a source file.
LICENSE = {
    "spdx": "CC0-1.0",
    "url": "https://creativecommons.org/publicdomain/zero/1.0/",
    "attribution": ("arXiv.org. Abstracts are authored text, offered by arXiv as "
                    "descriptive metadata. Attributed here as a courtesy that "
                    "CC0 does not require."),
    "citation": "arXiv API (export.arxiv.org/api/query), Atom summary field",
    "source_terms_url": "https://info.arxiv.org/help/api/tou.html",
    "verified_at": "2026-08-21",
    "verified_by": ("Fetched and read the arXiv API Terms of Use and its "
                    "footnote 1 defining descriptive metadata; see the comment "
                    "above this constant for both quotations."),
}

# Every change made to an author's words, named, in order, with its reason.
# Recorded in the dump so a served description can be justified without reading
# this file, and so that adding a step is a visible act rather than a diff.
TRANSFORMATIONS = [
    {"step": "whitespace_collapse",
     "what": "runs of whitespace and newlines collapsed to single spaces",
     "why": "arXiv wraps the abstract for display; the wrapping is not content",
     "lossy": False},
    {"step": "ascii_coerce",
     "what": "_base.to_ascii, NFKD decomposition with no '?' fallback",
     "why": "the repository is ASCII-only and enforces it in CI",
     "lossy": True,
     "note": ("an accented letter survives as its base letter; a character with "
              "no ASCII decomposition is DELETED, which is why chars_dropped is "
              "recorded per record and shown to the reviewer before the choice")},
    {"step": "sentence_trim",
     "what": "cut at the last sentence boundary at or before 600 characters",
     "why": ("event_v1 allows 1000; 600 is an editorial choice, not a schema "
             "requirement, so it is named here as a choice"),
     "lossy": True,
     "note": "applied only when the abstract exceeds the limit; is_excerpt records it"},
]


def arxiv_id(record):
    for url in record.get("sources") or []:
        match = re.search(r"arxiv\.org/abs/([^ /]+)", url or "")
        if match:
            return match.group(1)
    return None


def load_served():
    doc = json.load(io.open(ENRICHED, encoding="utf-8"))
    return doc if isinstance(doc, list) else list(doc.values())


def dropped_characters(text):
    """Characters that to_ascii would delete entirely, with no replacement.

    Returned rather than suppressed. This is the failure mode the explicit
    substitution map in project_timeline_events.py exists to prevent, and the
    only difference here is that a human can see it before it is served.
    """
    out = []
    for char in str(text or ""):
        if ord(char) < 128:
            continue
        if char in getattr(_base, "CHAR_REPLACEMENTS", {}):
            continue
        stripped = "".join(c for c in unicodedata.normalize("NFKD", char)
                           if ord(c) < 128)
        if not stripped:
            out.append(char)
    return sorted(set(out))


def fetch_batch(ids, session_gap=GAP_SECONDS):
    query = urllib.parse.urlencode({"id_list": ",".join(ids),
                                    "max_results": str(len(ids))})
    request = urllib.request.Request(API + "?" + query, headers={"User-Agent": UA})
    body = urllib.request.urlopen(request, timeout=60).read().decode("utf-8")
    time.sleep(session_gap)
    out = {}
    for entry in ET.fromstring(body).findall("a:entry", NS):
        raw_id = (entry.findtext("a:id", default="", namespaces=NS) or "")
        match = re.search(r"arxiv\.org/abs/([^ /]+)", raw_id)
        if not match:
            continue
        key = match.group(1)
        # arXiv answers with a VERSIONED id -- 1602.04019v2 -- while the served
        # record's URL carries the bare one. Keyed on the versioned form the
        # first run retrieved 50 entries and matched 0 of them, and reported
        # "arXiv returned nothing" about a response that contained everything.
        # Index both forms so the caller can ask either way.
        bare = re.sub(r"v[0-9]+$", "", key)
        entry_row = {
            "arxiv_id": key,
            "entry_id": raw_id,
            "title": " ".join((entry.findtext("a:title", default="",
                                              namespaces=NS) or "").split()),
            "abstract": " ".join((entry.findtext("a:summary", default="",
                                                 namespaces=NS) or "").split()),
            "published": entry.findtext("a:published", default=None, namespaces=NS),
            "updated": entry.findtext("a:updated", default=None, namespaces=NS),
        }
        out[key] = entry_row
        out.setdefault(bare, entry_row)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50,
                        help="how many records to fetch abstracts for")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--out", help="write here instead of a new dump dir")
    args = parser.parse_args()

    served = load_served()
    wanted = []
    for record in served:
        aid = arxiv_id(record)
        if aid:
            wanted.append((record, aid))
    wanted = wanted[args.offset:args.offset + args.limit]
    if not wanted:
        print("nothing to fetch")
        return 0

    print("fetching %d abstract(s) from arXiv in batches of %d"
          % (len(wanted), BATCH))
    fetched = {}
    for start in range(0, len(wanted), BATCH):
        chunk = [aid for _r, aid in wanted[start:start + BATCH]]
        try:
            fetched.update(fetch_batch(chunk))
        except (urllib.error.URLError, ET.ParseError, OSError) as exc:
            print("  batch %d FAILED: %s: %s" % (start // BATCH + 1,
                                                 type(exc).__name__, exc))
            continue
        print("  batch %d: %d ids sent, %d entries so far"
              % (start // BATCH + 1, len(chunk), len(fetched)))

    ingested = _base.utc_now_iso()
    proposals = []
    missing = []
    for record, aid in wanted:
        entry = fetched.get(aid)
        if not entry:
            missing.append((record["id"], aid))
            continue
        abstract = entry["abstract"]
        proposals.append({
            "id": record["id"],
            "arxiv_id": aid,
            # The VERSIONED entry this text was actually read from. Absent from
            # the first dump, which made its own audit_chain claim false -- the
            # chain said a reader could get back to the exact Atom entry and
            # they could only get back to the paper. An abstract can change
            # between v1 and v3, so without the version the chain stops one
            # step short of the words.
            "entry_id": entry["entry_id"],
            "arxiv_version": entry["arxiv_id"],
            "source_url": "https://arxiv.org/abs/%s" % aid,
            "current_description": record.get("description") or "",
            "current_title": record.get("title") or "",
            "arxiv_title": entry["title"],
            "abstract": abstract,
            "abstract_ascii": _base.to_ascii(abstract),
            "chars_dropped": dropped_characters(abstract),
            "title_matches": (_base.to_ascii(entry["title"]).lower().strip()
                              == _base.to_ascii(record.get("title") or "").lower().strip()),
            "published": entry["published"],
            "ingested_at": ingested,
            "license": LICENSE,
        })

    out_path = args.out
    if not out_path:
        stamp = _base.dump_stamp()
        out_dir = os.path.join(REPO_ROOT, "data", "raw", SOURCE_ID, "dumps", stamp)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "data.jsonl")
        meta = {
            "source_id": SOURCE_ID,
            "dump_stamp": stamp,
            "fetched_at": ingested,
            "api": API,
            "requested": len(wanted),
            "retrieved": len(proposals),
            "not_returned": [{"id": i, "arxiv_id": a} for i, a in missing],
            "license": LICENSE,
            "transformations": TRANSFORMATIONS,
            "audit_chain": [
                "served description",
                "<- data/curated/event_descriptions/decisions.jsonl (named reviewer, exact approved string)",
                "<- this dump's data.jsonl, field abstract (verbatim, unmodified)",
                "<- entry_id, the versioned arXiv Atom entry this was read from",
                "<- the paper itself at source_url",
            ],
            "note": ("Abstracts for records in enriched_alignment_research_"
                     "events.json, which has no raw provenance in this repo. "
                     "See pdoom-data#88."),
        }
        io.open(os.path.join(out_dir, "_metadata.json"), "w",
                encoding="ascii", newline="\n").write(
                    json.dumps(meta, indent=2, ensure_ascii=True) + "\n")

    with io.open(out_path, "w", encoding="ascii", newline="\n") as handle:
        for row in proposals:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")

    print()
    print("retrieved %d of %d requested" % (len(proposals), len(wanted)))
    if missing:
        print("  arXiv returned nothing for %d: %s"
              % (len(missing), ", ".join(a for _i, a in missing[:8])))
    mismatched = [p for p in proposals if not p["title_matches"]]
    print("  titles differing from the served record: %d" % len(mismatched))
    dropping = [p for p in proposals if p["chars_dropped"]]
    print("  abstracts with a character ASCII would DELETE: %d" % len(dropping))
    for p in dropping[:5]:
        print("      %-28s %s" % (p["arxiv_id"], " ".join(
            "U+%04X" % ord(c) for c in p["chars_dropped"])))
    print()
    print("wrote %s" % out_path)
    print("nothing is served yet. Review with:")
    print('  python scripts/review/review_descriptions.py --by "..." '
          "--proposals %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
