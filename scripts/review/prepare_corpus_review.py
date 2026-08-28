#!/usr/bin/env python3
"""Prepare one corpus-review sitting: draw the frame, then fetch the abstracts.

    python scripts/review/prepare_corpus_review.py --n 150 --seed 20260824

This is step B1 of docs/design/REVIEW_THE_BULK_2026-08-19.md, made
unconditional. It costs machine time and no ruling. It writes NO verdict and
sets NO human field anywhere; it prepares a sitting and nothing else.

Order matters and is enforced
-----------------------------
frame.json is written BEFORE a single abstract is fetched. A sample frame
chosen after seeing the material is not a sample. The frame carries the seed,
the population, n, the drawn ids, the exclusions, and the question asked
verbatim, so a reader who trusts none of this can redraw it.

What it draws from
------------------
The population is the 1,129 arXiv records inside the 1,166 bulk records of
data/serveable/api/timeline_events/all_events.json -- identified by
`source_id` being present AND the record's source URL being on arxiv.org.
The 37 Distill records are EXCLUDED, and the exclusion is recorded in the
frame with its reason: the abstract fetch below is keyed on an arXiv
identifier and there is no equivalent single call for Distill. That is a
limitation of this instrument, not a judgement about Distill.

Why fetch abstracts at all
--------------------------
The published `description` on these records is unparsed PDF text -- 841 of
the 1,129 are exactly 30 characters. A reviewer reading those would be
grading our own extractor, which is `pdoom1#1075` clause 2: do not derive
what to look for from the system you are checking. The abstract comes from
arXiv, which is outside this system, so the judgement is about the paper.

Network
-------
Two arXiv endpoints, tried in that order.

1. https://export.arxiv.org/api/query -- the Atom API, batched, three
   requests for n=150. Measured 2026-08-24 from this address: it answers
   `HTTP 429 Rate exceeded` to every request including a single id, so the
   fallback below is not decorative.
2. https://export.arxiv.org/oai2 -- OAI-PMH GetRecord, one id per call,
   with a 1 second pause and Retry-After honoured. About three minutes for
   n=150. Measured working from this address on the same day.

If neither returns anything this fails loudly and writes no dump, rather
than writing a dump of empty abstracts -- an abstract-shaped blank would be
indistinguishable from a paper with nothing to say.
"""

import argparse
import io
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

EVENTS = os.path.join(REPO, "data", "serveable", "api", "timeline_events",
                      "all_events.json")
REVIEW_ROOT = os.path.join(REPO, "data", "curated", "corpus_review")
DUMP_ROOT = os.path.join(REPO, "data", "raw", "arxiv_abstracts", "dumps")

TOOL = "prepare_corpus_review.py"
TOOL_VERSION = "0.1.0"

# The question, stated once, carried into the frame and onto every screen.
QUESTION = "Would you want this paper in an AI-safety reference corpus?"

# The answer vocabulary, stated once, carried into the frame and enforced by
# scripts/review/serve_corpus_review.py. Four values, and the distinctions
# between them are the point.
VERDICTS = {
    "yes": "worth carrying in an AI-safety reference corpus",
    "no": "not worth carrying",
    "unknown": ("looked at it and could not tell -- NOT a rejection, "
                "NOT an absence of review"),
    "skip": ("deliberately passed over without judging -- NOT unreviewed, "
             "NOT 'could not tell'"),
}
# A record with no row in verdicts.jsonl is NOT YET REVIEWED. That is a fifth
# state and it is represented by absence, never by a value.

ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_OAI = "https://export.arxiv.org/oai2"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
OAI_NS = "{http://www.openarchives.org/OAI/2.0/}"
OAI_ARXIV = "{http://arxiv.org/OAI/arXiv/}"
UA = "pdoom-data corpus-review prep (contact pip@beacongcr.org)"

ABS_RE = re.compile(r"arxiv\.org/abs/([^\s/?#]+)", re.I)


def now_local():
    """Local wall clock WITH its offset. Never a bare Z, never a naive stamp."""
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_population():
    """The 1,129 arXiv bulk records, in a deterministic order.

    Sorted by record id so the draw depends on the seed alone and not on the
    JSON file's key order, which is a build artefact.
    """
    with io.open(EVENTS, "r", encoding="utf-8") as fh:
        events = json.load(fh)

    arxiv, distill, other = [], [], []
    for key, rec in events.items():
        if "source_id" not in rec:
            continue  # one of the 28 hand-authored narrative records
        urls = rec.get("sources") or []
        arx = [u for u in urls if "arxiv.org" in u.lower()]
        if arx:
            m = ABS_RE.search(arx[0])
            if not m:
                other.append(key)
                continue
            arxiv.append({
                "record_id": rec.get("id", key),
                "event_key": key,
                "source_id": rec["source_id"],
                "title": rec.get("title", ""),
                "year": rec.get("year"),
                "arxiv_id": m.group(1),
                "url": arx[0],
                "our_description": rec.get("description", ""),
            })
        elif any("distill" in u.lower() for u in urls):
            distill.append(key)
        else:
            other.append(key)

    arxiv.sort(key=lambda r: r["record_id"])
    return arxiv, distill, other


def base_id(arxiv_id):
    """Strip a version suffix from a modern arXiv id. Old-style ids
    (`cs/0501001`) have no version and no digit-leading form, so they pass
    through untouched rather than being split on the `v` in `cs`."""
    if re.match(r"^\d{4}\.\d{4,5}", arxiv_id):
        return arxiv_id.split("v")[0]
    return re.sub(r"v\d+$", "", arxiv_id)


def id_month(arxiv_id):
    """`2112.09332` -> `2021-12`. The YYMM prefix of a modern arXiv identifier
    IS the month of version 1, by arXiv's own construction, and it is the only
    v1 date available from OAI-PMH (see the note in fetch_oai). Old-style ids
    (`cs/0501001`) carry YYMM too; anything else returns None rather than a
    guess."""
    m = re.match(r"^(\d{2})(\d{2})\.\d{4,5}", arxiv_id)
    if not m:
        m = re.match(r"^[a-z-]+(?:\.[A-Z]{2})?/(\d{2})(\d{2})\d{3}", arxiv_id)
    if not m:
        return None
    yy, mm = int(m.group(1)), m.group(2)
    year = 1900 + yy if yy >= 91 else 2000 + yy
    return "%04d-%s" % (year, mm)


def fetch_oai(arxiv_id, timeout=60):
    """One OAI-PMH GetRecord. Used because the Atom API answers 429 from this
    address; OAI is the same publisher, a different endpoint, one id per call.

    Returns a record dict or None if arXiv reports the id does not exist.
    """
    url = ("%s?verb=GetRecord&metadataPrefix=arXiv&identifier=oai:arXiv.org:%s"
           % (ARXIV_OAI, base_id(arxiv_id)))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=timeout).read()
    root = ET.fromstring(raw)

    err = root.find(OAI_NS + "error")
    if err is not None:
        return None

    meta = root.find(".//" + OAI_ARXIV + "arXiv")
    if meta is None:
        return None

    def txt(tag):
        v = meta.findtext(OAI_ARXIV + tag)
        return " ".join(v.split()) if v else None

    authors = []
    for a in meta.findall(OAI_ARXIV + "authors/" + OAI_ARXIV + "author"):
        fore = a.findtext(OAI_ARXIV + "forenames") or ""
        key = a.findtext(OAI_ARXIV + "keyname") or ""
        authors.append(" ".join((fore + " " + key).split()))

    cats = (txt("categories") or "").split()
    bare = txt("id") or base_id(arxiv_id)
    return {
        "arxiv_id": arxiv_id,
        "arxiv_id_base": base_id(arxiv_id),
        "title": txt("title") or "",
        "abstract": txt("abstract") or "",
        # NOT the v1 submission date. Measured 2026-08-24: OAI-PMH <created>
        # for 1803.04585 is 2019-02-24 although the identifier says 2018-03,
        # and for 2112.09332 (WebGPT) it is 2022-06-01 although the identifier
        # says 2021-12. It is the creation date of the version arXiv currently
        # indexes. Named for what it is, because a field called `published`
        # holding this would have produced a confident wrong answer to
        # "does our year agree with arXiv" -- it produced one here, in draft,
        # before the field was checked against the raw XML.
        "oai_created_indexed_version": txt("created"),
        "oai_updated": txt("updated"),
        "id_month": id_month(arxiv_id),
        "display_date": id_month(arxiv_id),
        "authors": authors,
        "primary_category": cats[0] if cats else None,
        "categories": cats,
        "doi": txt("doi"),
        "comment": txt("comments"),
        "abs_url": "https://arxiv.org/abs/%s" % bare,
        "_fetched_via": "oai-pmh",
    }


def fetch_batch(ids, timeout=60):
    """One arXiv Atom API call. Returns {arxiv_id_without_version: record}."""
    query = "id_list=%s&max_results=%d" % (",".join(ids), len(ids))
    url = "%s?%s" % (ARXIV_API, query)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=timeout).read()
    root = ET.fromstring(raw)

    out = {}
    for entry in root.findall(ATOM + "entry"):
        eid = (entry.findtext(ATOM + "id") or "").strip()
        m = re.search(r"arxiv\.org/abs/(.+)$", eid)
        bare = m.group(1) if m else eid
        key = base_id(bare)
        authors = [a.findtext(ATOM + "name") or ""
                   for a in entry.findall(ATOM + "author")]
        prim = entry.find(ARXIV_NS + "primary_category")
        cats = [c.get("term") for c in entry.findall(ATOM + "category")]
        out[key] = {
            "arxiv_id": bare,
            "arxiv_id_base": key,
            "title": " ".join((entry.findtext(ATOM + "title") or "").split()),
            "abstract": " ".join((entry.findtext(ATOM + "summary") or "").split()),
            # The Atom API's <published> IS the v1 date, unlike OAI's
            # <created>. Two endpoints, two meanings, so two field names.
            "atom_published_v1": entry.findtext(ATOM + "published"),
            "atom_updated": entry.findtext(ATOM + "updated"),
            "id_month": id_month(bare),
            "display_date": (entry.findtext(ATOM + "published") or "")[:7]
                            or id_month(bare),
            "authors": authors,
            "primary_category": prim.get("term") if prim is not None else None,
            "categories": cats,
            "doi": entry.findtext(ARXIV_NS + "doi"),
            "comment": entry.findtext(ARXIV_NS + "comment"),
            "abs_url": eid,
            "_fetched_via": "atom-api",
        }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=150,
                    help="sample size (default 150)")
    ap.add_argument("--seed", type=int, default=20260824,
                    help="RNG seed, recorded in frame.json")
    ap.add_argument("--pass-id", default=None,
                    help="folder name under data/curated/corpus_review/")
    ap.add_argument("--batch", type=int, default=50,
                    help="arXiv ids per API call (default 50)")
    ap.add_argument("--pause", type=float, default=3.0,
                    help="seconds between Atom API calls (arXiv asks for 3)")
    ap.add_argument("--oai-pause", type=float, default=1.0,
                    help="seconds between OAI-PMH calls")
    ap.add_argument("--oai-only", action="store_true",
                    help="skip the Atom API and go straight to OAI-PMH")
    ap.add_argument("--dry-run", action="store_true",
                    help="draw and report, write nothing, fetch nothing")
    args = ap.parse_args()

    pass_id = args.pass_id or ("%s_worth-carrying_n%d"
                               % (datetime.now().strftime("%Y-%m-%d"), args.n))

    population, distill, other = load_population()
    print("population: %d arXiv bulk records "
          "(excluded: %d Distill, %d unparseable-source)"
          % (len(population), len(distill), len(other)))
    if args.n > len(population):
        sys.exit("n=%d exceeds population %d" % (args.n, len(population)))

    rng = random.Random(args.seed)
    sample = rng.sample(population, args.n)
    print("drew %d with seed %d" % (len(sample), args.seed))

    if args.dry_run:
        for row in sample[:5]:
            print("  %s  %s  %s" % (row["arxiv_id"], row["year"],
                                    row["title"][:60]))
        print("dry run: nothing written")
        return 0

    # ---- frame.json FIRST, before a single byte is fetched -----------------
    pass_dir = os.path.join(REVIEW_ROOT, pass_id)
    os.makedirs(pass_dir, exist_ok=True)
    frame = {
        "pass_id": pass_id,
        "created": now_local(),
        "created_utc": now_utc(),
        "tool": "%s %s" % (TOOL, TOOL_VERSION),
        "question": QUESTION,
        "verdict_vocabulary": VERDICTS,
        "unreviewed_is_absence": ("A record with no row in verdicts.jsonl is "
                                  "NOT YET REVIEWED. That state is represented "
                                  "by absence and must never be rendered as a "
                                  "verdict value."),
        "population": {
            "source": "data/serveable/api/timeline_events/all_events.json",
            "definition": ("bulk records (source_id present) whose first "
                           "source URL is on arxiv.org"),
            "size": len(population),
            "excluded": {
                "distill": {
                    "count": len(distill),
                    "reason": ("the abstract fetch is keyed on an arXiv "
                               "identifier; no equivalent single call exists "
                               "for Distill. Not a judgement about Distill."),
                },
                "hand_authored_narrative": {
                    "count": 28,
                    "reason": "not bulk records; not part of this question",
                },
                "unparseable_source_url": {"count": len(other)},
            },
        },
        "draw": {
            "method": "random.Random(seed).sample over the population sorted "
                      "by record_id",
            "seed": args.seed,
            "n": args.n,
        },
        "abstract_dump": None,   # filled in below
        "sample": [
            {"record_id": r["record_id"], "arxiv_id": r["arxiv_id"],
             "title": r["title"], "year": r["year"], "url": r["url"]}
            for r in sample
        ],
        "human_fields_set_by_this_tool": 0,
    }
    frame_path = os.path.join(pass_dir, "frame.json")
    write_json(frame_path, frame)
    print("frame written BEFORE fetch: %s" % rel(frame_path))

    # ---- then fetch --------------------------------------------------------
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    dump_dir = os.path.join(DUMP_ROOT, stamp)
    os.makedirs(dump_dir, exist_ok=True)

    ids = [r["arxiv_id"] for r in sample]
    fetched, errors = {}, []
    t0 = time.time()

    # Path 1: the Atom API, three requests for n=150. Tried first because it
    # is 50x fewer requests. It answers 429 "Rate exceeded" from this address
    # as of 2026-08-24, so path 2 is not a theoretical fallback.
    if not args.oai_only:
        for i in range(0, len(ids), args.batch):
            chunk = [c for c in ids[i:i + args.batch]
                     if base_id(c) not in fetched]
            if not chunk:
                continue
            try:
                fetched.update(fetch_batch(chunk))
                print("  api: fetched %d/%d" % (len(fetched), len(ids)))
            except (urllib.error.URLError, ET.ParseError, OSError) as exc:
                errors.append({"endpoint": "atom-api", "batch_start": i,
                               "error": "%s: %s" % (type(exc).__name__, exc)})
                print("  api batch failed at %d: %s -- falling back to OAI"
                      % (i, exc))
                break
            if i + args.batch < len(ids):
                time.sleep(args.pause)

    # Path 2: OAI-PMH, one id per call, slower and reliable.
    remaining = [i2 for i2 in ids if base_id(i2) not in fetched]
    for n_done, aid in enumerate(remaining, 1):
        for attempt in range(4):
            try:
                got = fetch_oai(aid)
                if got:
                    fetched[base_id(aid)] = got
                break
            except urllib.error.HTTPError as exc:
                wait = float(exc.headers.get("Retry-After") or (5 * (attempt + 1)))
                if attempt == 3:
                    errors.append({"endpoint": "oai", "arxiv_id": aid,
                                   "error": "HTTPError %s" % exc.code})
                    break
                time.sleep(min(wait, 30.0))
            except (urllib.error.URLError, ET.ParseError, OSError) as exc:
                if attempt == 3:
                    errors.append({"endpoint": "oai", "arxiv_id": aid,
                                   "error": "%s: %s" % (type(exc).__name__, exc)})
                    break
                time.sleep(3.0 * (attempt + 1))
        if n_done % 10 == 0 or n_done == len(remaining):
            print("  oai: fetched %d/%d" % (len(fetched), len(ids)))
        time.sleep(args.oai_pause)

    elapsed = time.time() - t0

    if not fetched:
        sys.exit("no abstracts fetched -- refusing to write an empty dump. "
                 "Errors: %s" % errors)

    rows, missing = [], []
    for r in sample:
        got = fetched.get(base_id(r["arxiv_id"])) or fetched.get(r["arxiv_id"])
        if not got:
            missing.append(r["arxiv_id"])
            continue
        row = dict(got)
        row["record_id"] = r["record_id"]
        row["source_id"] = r["source_id"]
        rows.append(row)

    data_path = os.path.join(dump_dir, "data.jsonl")
    with io.open(data_path, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    meta = {
        "extraction_date": now_utc(),
        "source_name": "arxiv_abstracts",
        "source_url": ARXIV_API,
        "extraction_method": "api",
        "extractor_version": TOOL_VERSION,
        "data_format": "jsonl",
        "record_count": len(rows),
        "extraction_type": "sample",
        "filters_applied": {
            "id_list": "the %d arXiv ids drawn in %s/frame.json" % (len(ids), pass_id),
            "pass_id": pass_id,
            "seed": args.seed,
        },
        "extraction_status": "complete" if not errors and not missing else "partial",
        "extraction_notes": ("Abstracts for one corpus-review sitting. Fetched "
                             "AFTER the frame was written, per "
                             "docs/design/REVIEW_THE_BULK_2026-08-19.md B1."),
        "fields_extracted": sorted(rows[0].keys()) if rows else [],
        "attribution": "arXiv.org, per its API terms of use",
        "license": "arXiv metadata is CC0 1.0; abstracts remain under their "
                   "authors' terms and are used here for review display only",
        "rate_limit_info": {
            "authenticated": False,
            "endpoints": ["atom-api", "oai-pmh"],
            "pause_seconds": {"atom_api": args.pause, "oai": args.oai_pause},
            "time_elapsed_seconds": round(elapsed, 3),
        },
        "extraction_statistics": {
            "records_requested": len(ids),
            "records_written": len(rows),
            "records_missing": len(missing),
            "missing_arxiv_ids": missing,
            "errors_encountered": len(errors),
            "errors": errors,
        },
        "data_quality": {
            "ascii_compliance_checked": False,
            "ascii_note": ("data.jsonl is UTF-8 and gitignored, like the other "
                           "raw dumps. Author names and mathematics in real "
                           "abstracts are not ASCII and folding them would be "
                           "damage, not compliance."),
        },
    }
    write_json(os.path.join(dump_dir, "_metadata.json"), meta)

    frame["abstract_dump"] = {
        "path": rel(data_path),
        "record_count": len(rows),
        "missing": missing,
        "fetched_at": now_local(),
    }
    write_json(frame_path, frame)

    print("")
    print("dump:  %s  (%d records, %d missing)"
          % (rel(dump_dir), len(rows), len(missing)))
    print("frame: %s" % rel(frame_path))
    print("")
    print("Now start the sitting:")
    print('  python scripts/review/serve_corpus_review.py --by "Your Name"')
    return 0


def rel(path):
    return os.path.relpath(path, REPO).replace("\\", "/")


def write_json(path, obj):
    """Write via a temp file and os.replace. Never open an existing file for
    writing directly -- CLAUDE.md's landmine, which ate two files once.

    ensure_ascii=True is on purpose: everything this writes into
    data/curated/ is committed and has to pass validate_ascii.py. JSON's
    backslash-u escaping is lossless, so this is not the shredding `?`
    fallback that legacy/fix_ascii.py does.
    """
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="ascii", newline="\n") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=True, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


if __name__ == "__main__":
    sys.exit(main())
