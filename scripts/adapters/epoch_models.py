#!/usr/bin/env python3
"""Adapter: Epoch AI, Data on Notable AI Models.

One bulk CSV download, updated daily upstream, CC-BY-4.0. Gives dated model
releases with organisation, country, training compute, and citation counts --
the capability-progression spine for the timeline.

Usage:
    python scripts/adapters/epoch_models.py             # all years
    python scripts/adapters/epoch_models.py --since 2023-01-01

Writes one immutable dump under data/raw/epoch_ai/dumps/<timestamp>/.
Never touches the transformed or serveable zones.
"""

import argparse
import csv
import io
import json
import re
import sys

sys.path.insert(0, __file__.rsplit("epoch_models.py", 1)[0])

import _base  # noqa: E402

SOURCE_ID = "epoch_ai"
ADAPTER_VERSION = "0.1.0"
CSV_URL = "https://epoch.ai/data/notable_ai_models.csv"

LICENSE = {
    "spdx": "CC-BY-4.0",
    "url": "https://creativecommons.org/licenses/by/4.0/",
    "attribution": "Epoch AI, Data on Notable AI Models",
    "citation": (
        "Epoch AI. Data on Notable AI Models. Retrieved from "
        "https://epoch.ai/data/notable-ai-models"
    ),
    "source_terms_url": "https://epoch.ai/data/ai-models-documentation",
    "verified_at": "2026-07-25",
    "verified_by": "web search of first-party Epoch AI documentation pages",
}

# Null rather than guessed. Epoch's model database predates this ingest by
# several years but the exact public-availability date is unconfirmed, and a
# fabricated clock silently corrupts the in-game gating mechanic.
SOURCE_AVAILABLE_AT = None
SOURCE_AVAILABLE_AT_NOTE = (
    "UNVERIFIED. Needs a first-party check of when the notable-models database "
    "was first published. Until then this source is ungated."
)


# Characters that carry meaning in model names. Stripping them silently
# merged distinct models: PointNet++ onto PointNet, DeepLabV3+ onto DeepLabV3.
NAME_SUBSTITUTIONS = [("++", "_plusplus"), ("+", "_plus"), ("#", "_sharp")]


def slugify(text):
    name = _base.to_ascii(text).lower()
    for symbol, replacement in NAME_SUBSTITUTIONS:
        name = name.replace(symbol, replacement)
    slug = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return slug or "unnamed"


def parse_number(raw):
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(str(raw).strip().replace(",", ""))
    except ValueError:
        return None


def normalise_date(raw):
    """Epoch publishes YYYY-MM-DD; accept YYYY and YYYY-MM defensively."""
    value = (raw or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    if re.fullmatch(r"\d{4}-\d{2}", value):
        return value + "-01"
    if re.fullmatch(r"\d{4}", value):
        return value + "-01-01"
    return None


def fetch(session):
    response = _base.polite_get(session, CSV_URL)
    text = response.text
    rows = list(csv.DictReader(io.StringIO(text)))
    return rows, _base.sha256_text(text)


def build_summary(row):
    """Prefer the upstream abstract; otherwise state the facts we have.

    Deliberately does not invent narrative. A constructed summary is marked
    'derived' in the provenance envelope so a reviewer can tell them apart.
    """
    abstract = (row.get("Abstract") or "").strip()
    if abstract:
        return _base.clean_summary(abstract), "upstream_abstract"

    parts = []
    org = (row.get("Organization") or "").strip()
    if org:
        parts.append("Released by %s" % _base.to_ascii(org))
    domain = (row.get("Domain") or "").strip()
    if domain:
        parts.append("domain: %s" % _base.to_ascii(domain))
    task = (row.get("Task") or "").strip()
    if task:
        parts.append("task: %s" % _base.to_ascii(task))
    compute = parse_number(row.get("Training compute (FLOP)"))
    if compute:
        parts.append("training compute approx %.1e FLOP" % compute)
    return _base.clean_summary(". ".join(parts) + ".") if parts else "", "derived"


def normalise(row, ingested_at):
    name = (row.get("Model") or "").strip()
    if not name:
        return None

    published = normalise_date(row.get("Publication date"))
    org = (row.get("Organization") or "").strip()
    actors = [a.strip() for a in re.split(r"[,;]", _base.to_ascii(org)) if a.strip()]

    urls = []
    for key in ("Link", "Reference"):
        value = (row.get(key) or "").strip()
        if value.startswith("http") and value not in urls:
            urls.append(value)

    signals = {}
    citations = parse_number(row.get("Citations"))
    if citations is not None:
        signals.update(_base.signal("citations", citations, ingested_at))
    compute = parse_number(row.get("Training compute (FLOP)"))
    if compute is not None:
        signals.update(_base.signal("training_compute_flop", compute, ingested_at))
    params = parse_number(row.get("Parameters"))
    if params is not None:
        signals.update(_base.signal("parameters", params, ingested_at))

    summary, summary_method = build_summary(row)

    record = {
        "id": "%s:%s" % (SOURCE_ID, slugify(name)),
        "title": _base.to_ascii(name),
        "summary": summary,
        "kind": "model_release",
        "occurred_at": published,
        "published_at": published,
        "source_available_at": SOURCE_AVAILABLE_AT,
        "ingested_at": ingested_at,
        "actors": actors,
        "source_urls": urls,
        "archive_urls": [],
        "content_sha256": _base.sha256_text(json.dumps(row, sort_keys=True)),
        "license": LICENSE,
        "signals": signals,
        "airr_tags": {"causal": [], "domain": []},
        "source_raw_key": _base.to_ascii(name),
        "extra": {
            "organization_categorization": _base.to_ascii(
                row.get("Organization categorization")
            ),
            "country": _base.to_ascii(row.get("Country (of organization)")),
            "notability_criteria": _base.to_ascii(row.get("Notability criteria")),
            "frontier_model": _base.to_ascii(row.get("Frontier model")),
            "open_weights": _base.to_ascii(row.get("Open model weights?")),
            "model_accessibility": _base.to_ascii(row.get("Model accessibility")),
            "epoch_confidence": _base.to_ascii(row.get("Confidence")),
        },
        "_provenance": _base.provenance(
            {
                "title": ("raw", "upstream_field", "high"),
                "summary": ("raw", summary_method, "high" if summary_method
                            == "upstream_abstract" else "medium"),
                "occurred_at": ("raw", "upstream_publication_date", "high"),
                "published_at": ("raw", "upstream_publication_date", "high"),
                "source_available_at": ("raw", "unverified_null", "low"),
                "actors": ("raw", "split_upstream_organization", "medium"),
                "signals": ("raw", "upstream_field", "high"),
            }
        ),
    }
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default=None, help="ISO date lower bound")
    parser.add_argument("--until", default=None, help="ISO date upper bound")
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch and normalise but write nothing")
    args = parser.parse_args()

    ingested_at = _base.utc_now_iso()
    session = _base.get_session()
    rows, source_sha = fetch(session)

    kept_raw = []
    candidates = []
    skipped_no_date = 0
    skipped_window = 0

    for row in rows:
        record = normalise(row, ingested_at)
        if record is None:
            continue
        when = record["published_at"]
        if when is None:
            skipped_no_date += 1
            continue
        if args.since and when < args.since:
            skipped_window += 1
            continue
        if args.until and when > args.until:
            skipped_window += 1
            continue
        candidates.append(record)
        kept_raw.append({k: _base.to_ascii(v) for k, v in row.items()})

    print("fetched rows      : %d" % len(rows))
    print("skipped, no date  : %d" % skipped_no_date)
    print("skipped, window   : %d" % skipped_window)
    print("candidates        : %d" % len(candidates))

    if args.dry_run:
        problems = []
        for record in candidates:
            problems.extend(_base.validate_candidate(record))
        print("validation problems: %d" % len(problems))
        if candidates:
            print(json.dumps(candidates[0], indent=2, sort_keys=True)[:1200])
        return 0

    metadata = {
        "source_url": CSV_URL,
        "source_name": "Epoch AI Notable AI Models",
        "extraction_method": "bulk_csv_download",
        "adapter_version": ADAPTER_VERSION,
        "license": LICENSE,
        "source_available_at": SOURCE_AVAILABLE_AT,
        "source_available_at_note": SOURCE_AVAILABLE_AT_NOTE,
        "source_payload_sha256": source_sha,
        "query_window": {"since": args.since, "until": args.until},
        "filters_applied": {
            "requires_publication_date": True,
            "since": args.since,
            "until": args.until,
        },
        "extraction_statistics": {
            "fetched": len(rows),
            "skipped_no_date": skipped_no_date,
            "skipped_window": skipped_window,
            "written": len(candidates),
            "errors": 0,
        },
        "tool_versions": {"python": sys.version.split()[0]},
        "notes": (
            "Bulk CSV, updated daily upstream. Re-running produces a new dump "
            "directory; diffs between dumps are evidence of upstream change."
        ),
    }

    dump_dir = _base.write_dump(SOURCE_ID, candidates, kept_raw, metadata)
    print("wrote dump        : %s" % dump_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
