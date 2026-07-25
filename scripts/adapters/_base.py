#!/usr/bin/env python3
"""Shared plumbing for source adapters.

See docs/ADAPTER_SPEC.md for the contract. This module deliberately holds no
source-specific logic: it does HTTP politely, writes bronze-zone dumps in the
mandated layout, and refuses to write a dump missing its license block.

ASCII only, per ASCII_CODING_STANDARDS.md. Character tables in this file use
escape sequences, never literals, so the file passes its own gate.
"""

import hashlib
import json
import os
import time
import unicodedata
from datetime import datetime, timezone

ADAPTER_FRAMEWORK_VERSION = "0.1.0"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_ROOT = os.path.join(REPO_ROOT, "data", "raw")

CONTACT = "pipfoweraker@gmail.com"
USER_AGENT = (
    "pdoom-data/0.1 (+https://github.com/PipFoweraker/pdoom-data; %s)" % CONTACT
)

VALID_KINDS = {
    "model_release",
    "publication",
    "incident",
    "policy",
    "org_event",
    "funding",
    "forum_post",
    "benchmark",
}

CONFIDENCE_LEVELS = {"high", "medium", "low"}

CHAR_REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": "\"",
    "\u201d": "\"",
    "\u2013": "-",
    "\u2014": "--",
    "\u2026": "...",
    "\u00a0": " ",
    "\u2192": "->",
    "\u2190": "<-",
    "\u00d7": "x",
    "\u2212": "-",
    "\u2010": "-",
    "\u2011": "-",
}


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def dump_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")


def sha256_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def sha256_text(text):
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_session():
    """A requests session with honest identification."""
    import requests

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def polite_get(session, url, max_attempts=5, timeout=60, **kwargs):
    """GET with exponential backoff on 429 and 5xx.

    Raises on final failure so a caller never mistakes a rate-limit wall for
    an empty result set.
    """
    delay = 2.0
    last = None
    for _attempt in range(max_attempts):
        response = session.get(url, timeout=timeout, **kwargs)
        last = response
        if response.status_code < 400:
            return response
        if response.status_code in (429, 500, 502, 503, 504):
            retry_after = response.headers.get("Retry-After")
            if retry_after and str(retry_after).isdigit():
                wait = float(retry_after)
            else:
                wait = delay
            time.sleep(min(wait, 60.0))
            delay = min(delay * 2, 60.0)
            continue
        response.raise_for_status()
    last.raise_for_status()
    return last


def polite_post(session, url, max_attempts=5, timeout=60, **kwargs):
    """POST with the same backoff policy. Used by the GraphQL sources."""
    delay = 2.0
    last = None
    for _attempt in range(max_attempts):
        response = session.post(url, timeout=timeout, **kwargs)
        last = response
        if response.status_code < 400:
            return response
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(delay, 60.0))
            delay = min(delay * 2, 60.0)
            continue
        response.raise_for_status()
    last.raise_for_status()
    return last


def to_ascii(text):
    """Lossy but predictable ASCII coercion for text destined for the repo."""
    if text is None:
        return None
    out = []
    for char in str(text):
        if ord(char) < 128:
            out.append(char)
        elif char in CHAR_REPLACEMENTS:
            out.append(CHAR_REPLACEMENTS[char])
        else:
            normalised = unicodedata.normalize("NFKD", char)
            out.append("".join(c for c in normalised if ord(c) < 128))
    return "".join(out)


def clean_summary(text, limit=400):
    """Collapse whitespace, coerce to ASCII, truncate on a word boundary.

    The existing arXiv import shipped raw PDF text as descriptions, complete
    with hard line breaks and hyphenation artifacts. This is the minimum
    defence; it does not attempt to repair broken extraction.
    """
    if not text:
        return ""
    collapsed = " ".join(to_ascii(text).split())
    if len(collapsed) <= limit:
        return collapsed
    cut = collapsed[:limit]
    space = cut.rfind(" ")
    if space > limit * 0.6:
        cut = cut[:space]
    return cut.rstrip(" ,;:.-") + "..."


def signal(name, value, observed_at=None):
    """Build a time-varying observation. Never store a bare scalar.

    A 2018 paper's citation count is a different number in 2019 and in 2026;
    which one a player should see depends on the game clock. Storing the
    observation date makes that answerable rather than a fudge.
    """
    return {name: [{"observed_at": observed_at or utc_now_iso(), "value": value}]}


def provenance(field_map):
    """Map field -> (layer, method, confidence) into a _provenance envelope."""
    out = {}
    for field, spec in field_map.items():
        layer, method, confidence = spec
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError("bad confidence %r for field %r" % (confidence, field))
        out[field] = {"layer": layer, "method": method, "confidence": confidence}
    return out


def validate_candidate(record):
    """Fail loudly at ingest rather than quietly at serving time."""
    problems = []
    for required in ("id", "title", "kind", "license", "ingested_at"):
        if not record.get(required):
            problems.append("missing %s" % required)
    kind = record.get("kind")
    if kind and kind not in VALID_KINDS:
        problems.append("unknown kind %r" % kind)
    lic = record.get("license") or {}
    for required in ("spdx", "attribution", "source_terms_url", "verified_at"):
        if not lic.get(required):
            problems.append("license missing %s" % required)
    spdx = str(lic.get("spdx", "")).upper()
    if "-SA" in spdx:
        problems.append("ShareAlike license %r excluded by repo policy" % spdx)
    for clock in ("occurred_at", "published_at", "source_available_at"):
        if clock not in record:
            problems.append("clock %s absent (use null if unknown)" % clock)
    return problems


def write_dump(source_id, candidates, raw_records, metadata):
    """Write a bronze-zone dump. Returns the dump directory path.

    Refuses to write if any candidate fails validation, because a dump that
    reaches disk is treated as immutable and gets committed.
    """
    failures = []
    seen_ids = {}
    for index, record in enumerate(candidates):
        problems = validate_candidate(record)
        record_id = record.get("id")
        # Duplicate ids are silent corruption: a consumer keying by id loses
        # one of the pair, and an attributed review lands on the wrong record.
        # Caught here rather than downstream, where it looks like a mystery.
        if record_id in seen_ids:
            problems.append("duplicate id, first seen at index %d"
                            % seen_ids[record_id])
        else:
            seen_ids[record_id] = index
        if problems:
            failures.append((index, record_id or "?", problems))
    if failures:
        raise ValueError(
            "%d of %d candidates failed validation; first few: %r"
            % (len(failures), len(candidates), failures[:5])
        )

    dump_dir = os.path.join(RAW_ROOT, source_id, "dumps", dump_stamp())
    os.makedirs(dump_dir, exist_ok=True)

    def write_jsonl(name, rows):
        path = os.path.join(dump_dir, name)
        with open(path, "w", encoding="ascii", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")

    write_jsonl("data.jsonl", candidates)
    write_jsonl("raw.jsonl", raw_records)

    meta = dict(metadata)
    meta.setdefault("source_id", source_id)
    meta.setdefault("extraction_date", utc_now_iso())
    meta["adapter_framework_version"] = ADAPTER_FRAMEWORK_VERSION
    meta["record_count"] = len(candidates)
    meta["raw_record_count"] = len(raw_records)
    meta_path = os.path.join(dump_dir, "_metadata.json")
    with open(meta_path, "w", encoding="ascii", newline="\n") as handle:
        json.dump(meta, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")

    manifest_path = os.path.join(dump_dir, "MANIFEST.sha256")
    with open(manifest_path, "w", encoding="ascii", newline="\n") as handle:
        for name in ("_metadata.json", "data.jsonl", "raw.jsonl"):
            digest = sha256_file(os.path.join(dump_dir, name))
            handle.write("%s  %s\n" % (digest, name))

    return dump_dir
