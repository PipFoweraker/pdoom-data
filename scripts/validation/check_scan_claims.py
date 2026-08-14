#!/usr/bin/env python3
"""Gate the LLM event-scan payloads in data/raw/llm_event_scan/payloads/.

Why this exists
---------------
These payloads are the output of language-model scans of the public web. That
makes them a different animal from every other source in this repo: there is
no upstream dataset with a license and a schema, the run is not reproducible,
and the scanner is capable of producing a fluent, plausible, well-formatted
record for an event that did not happen.

The whole value of the payload therefore rests on its claim tracking being
intact. A record that quietly loses its "UNVERIFIED" marker, or gains a date
it never had a source for, is worse than no record: it is indistinguishable
from a checked one, and the repo's standing rule is that a fabricated clock
cannot be told from a real one later.

So this gate enforces the properties that make the payloads honest, not the
properties that make them pretty:

  * A non-null date REQUIRES at least one source. This is the repo's
    never-guess-a-date rule applied to machine output. null is ungated and
    honest.
  * A record with no sources REQUIRES a flag containing UNVERIFIED. Absence
    of evidence has to be stated, not inferred from an empty list.
  * confidence: low REQUIRES a flag saying why. A low-confidence record with
    no explanation is an unexploded assumption.
  * Every scan REQUIRES retrieval accounting, so "how much of this was
    actually read" survives into the data rather than living in a chat log.
  * Every slug a flag CITES must resolve, either to another scan record or to
    the served corpus. See below.
  * ASCII only, per the repo standard.

It deliberately does NOT check whether the events are true. It cannot. It
checks that the payload does not overstate what is known about them, which is
the part a machine can enforce.

The cross-reference rule, and why it is the only part with an outside input
-------------------------------------------------------------------------
Records cite each other by slug inside their flags -- "Same matter as
us_export_controls_claude_fable_5_2026 in the labs payload", "the concrete
endpoint of the trend ai_summit_pivot_2023_2025 describes". Those are claims
about artifacts OTHER than the record making them, and that is what makes them
checkable: the claim lives here, the evidence lives somewhere this scan did not
produce.

`project_watchlist.py` already reads these same cross-references to seed
`possible_duplicate_of`, but it resolves them with `if slug in known_slugs`,
which SILENTLY DISCARDS any slug that does not resolve. A flag citing a record
that does not exist is therefore invisible there -- it degrades to no link at
all rather than to an error. This gate exists to make that case loud.

Two slugs currently resolve only against the served corpus rather than against
another payload (`eu_ai_act_watering_down_2024`, `ai_summit_pivot_2023_2025`).
That is correct and must stay legal: a scan record pointing at an event already
served is exactly the boundary judgement a curator needs. It also happens to be
the one genuinely EXTERNAL input available to this gate -- `all_events.json` is
built by a different pipeline from a different source, so a scan cannot make its
own citation resolve by construction.

What this gate still cannot do is validate DUPLICATE DETECTION. Comparing
similarity-detected pairs against `possible_duplicate_of` would compare one
computation over the payloads against another computation over the same
payloads, and a defect shared by both would be invisible to both -- the exact
shape of the redaction-verifier failure in CLAUDE.md. Whether two records are
the same event is decided by a human reading sources, and no check here claims
otherwise.

Exit codes: 0 all payloads sound, 1 at least one problem, 2 nothing to check.
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PAYLOAD_DIR = os.path.join(REPO_ROOT, "data", "raw", "llm_event_scan", "payloads")
SERVED_EVENTS = os.path.join(REPO_ROOT, "data", "serveable", "api",
                             "timeline_events", "all_events.json")

# A slug-shaped token: three or more lowercase_underscore segments. Matches
# project_watchlist.py's pattern deliberately, so the two agree on what counts
# as a citation and differ only in what they do with one that fails to resolve.
CITATION_RE = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+){2,}")
PAYLOAD_REF_RE = re.compile(r"\d{4}-\d{2}-\d{2}_[a-z0-9_]+\.json")

VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_DATE_KIND = {
    "action",       # the date the thing happened
    "reported",     # the date it was reported; the action date is unknown
    "contested",    # sources disagree; date must be null
    "unverified",   # no source retrieved at all; date must be null
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9_]+$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

REQUIRED_SCAN_KEYS = (
    "scan_id", "scan_scope", "scanned_at", "scanner", "operator",
    "instruction_summary", "records",
)
REQUIRED_RECORD_KEYS = (
    "slug", "title", "date", "date_kind", "description", "sources",
    "why_it_matters", "confidence", "flags",
)


def check_record(record, seen_slugs):
    problems = []

    for key in REQUIRED_RECORD_KEYS:
        if key not in record:
            problems.append("missing key %r" % key)
    if problems:
        return problems

    slug = record["slug"]
    if not SLUG_RE.match(slug or ""):
        problems.append("slug %r is not lowercase_with_underscores" % slug)
    if slug in seen_slugs:
        problems.append("duplicate slug %r within this payload" % slug)
    seen_slugs.add(slug)

    if not str(record.get("title") or "").strip():
        problems.append("empty title")
    if len(str(record.get("description") or "")) < 40:
        problems.append("description is too short to carry a claim")

    confidence = record.get("confidence")
    if confidence not in VALID_CONFIDENCE:
        problems.append("confidence %r not in %s"
                        % (confidence, sorted(VALID_CONFIDENCE)))

    date_kind = record.get("date_kind")
    if date_kind not in VALID_DATE_KIND:
        problems.append("date_kind %r not in %s"
                        % (date_kind, sorted(VALID_DATE_KIND)))

    sources = record.get("sources")
    if not isinstance(sources, list):
        problems.append("sources must be a list")
        sources = []
    for url in sources:
        if not str(url).startswith("http"):
            problems.append("source %r is not a URL" % url)

    flags = record.get("flags")
    if not isinstance(flags, list):
        problems.append("flags must be a list")
        flags = []
    flag_text = " ".join(str(f) for f in flags).upper()

    date = record.get("date")

    # The core rule. A date asserts a fact about the world; it needs evidence.
    if date is not None:
        if not DATE_RE.match(str(date)):
            problems.append("date %r is not YYYY-MM-DD (use null if unknown)"
                            % date)
        if not sources:
            problems.append(
                "date %r asserted with NO source -- never guess a date; "
                "set it to null" % date)
        if date_kind in ("contested", "unverified"):
            problems.append(
                "date_kind %r requires date null, but date is %r"
                % (date_kind, date))

    # Absence of evidence must be stated, not left to be inferred.
    if not sources and "UNVERIFIED" not in flag_text:
        problems.append(
            "no sources and no flag containing 'UNVERIFIED' -- an unsourced "
            "record must say so in its own flags")

    # A low-confidence record with no stated reason is an unexploded assumption.
    if confidence == "low" and not flags:
        problems.append("confidence 'low' with no flag explaining why")

    if record.get("primary_source_retrieved") is True and not sources:
        problems.append("primary_source_retrieved true but sources is empty")

    return problems


def check_payload(path):
    problems = []
    try:
        with open(path, encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        return ["could not read: %s" % exc]

    try:
        raw.encode("ascii")
    except UnicodeEncodeError as exc:
        bad = raw[exc.start:exc.start + 1]
        line = raw[:exc.start].count("\n") + 1
        problems.append("non-ASCII %r at line %d (repo is ASCII only)"
                        % (bad, line))

    try:
        payload = json.loads(raw)
    except ValueError as exc:
        return problems + ["invalid JSON: %s" % exc]

    for key in REQUIRED_SCAN_KEYS:
        if key not in payload:
            problems.append("payload missing key %r" % key)

    stamp = payload.get("scanned_at")
    if stamp and not ISO_RE.match(str(stamp)):
        problems.append("scanned_at %r is not ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ)"
                        % stamp)

    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return problems + ["payload has no records"]

    # Retrieval accounting is what lets a later reader tell a read corpus from
    # a recalled one. Required on any scan carrying an unsourced record.
    accounting = payload.get("retrieval_accounting")
    unsourced = [r for r in records if not r.get("sources")]
    if unsourced and not isinstance(accounting, dict):
        problems.append(
            "payload contains %d unsourced record(s) but has no "
            "retrieval_accounting block" % len(unsourced))

    seen = set()
    for index, record in enumerate(records):
        for problem in check_record(record, seen):
            problems.append("record %d (%s): %s"
                            % (index, record.get("slug", "?"), problem))
    return problems


def load_served_slugs():
    """Slugs of the served corpus, or None if it could not be read.

    None is NOT treated as "no cross-corpus references exist". A missing corpus
    disables the only external half of this check, so the caller fails loudly
    rather than passing a weaker check silently.
    """
    try:
        with open(SERVED_EVENTS, encoding="utf-8") as handle:
            return set(json.load(handle))
    except (OSError, ValueError):
        return None


def check_cross_references(payloads, served):
    """Every slug and payload name a claim cites must resolve somewhere real.

    `payloads` maps filename -> the whole payload dict. `served` is the
    served-corpus slug set or None. Resolution order is payload records first,
    then the served corpus; a citation that resolves to neither is a claim
    about a record that does not exist, which is the failure this catches.

    Both record-level flags and payload-level prose (`known_overlap`,
    `scanner_limits`) are checked, because both make claims about artifacts
    outside the record or payload asserting them.
    """
    problems = []

    if served is None:
        problems.append(
            "could not read %s -- the served corpus is the only external input "
            "this gate has, so its absence is a failure, not a skip"
            % os.path.relpath(SERVED_EVENTS, REPO_ROOT))
        served = set()

    payload_slugs = {r.get("slug")
                     for payload in payloads.values()
                     for r in payload.get("records") or []}
    payload_names = set(payloads)
    external = 0

    def scan(blob, where, own_slug=None):
        found_external = 0
        for slug in CITATION_RE.findall(blob):
            if slug == own_slug or slug in payload_slugs:
                continue
            if slug in served:
                found_external += 1
                continue
            problems.append(
                "%s: cites %r, which is not a scan record and not in the "
                "served corpus" % (where, slug))
        for ref in PAYLOAD_REF_RE.findall(blob):
            if ref not in payload_names:
                problems.append(
                    "%s: names payload %r, which does not exist" % (where, ref))
        return found_external

    for name in sorted(payloads):
        payload = payloads[name]

        for key in ("known_overlap", "instruction_summary", "scan_scope"):
            value = payload.get(key)
            if isinstance(value, str):
                external += scan(value, "%s %s" % (name, key))

        limits = payload.get("scanner_limits")
        if isinstance(limits, list):
            external += scan(" ".join(str(x) for x in limits),
                             "%s scanner_limits" % name)

        for index, record in enumerate(payload.get("records") or []):
            flags = record.get("flags")
            if not isinstance(flags, list):
                continue
            external += scan(
                " ".join(str(f) for f in flags),
                "%s record %d (%s)" % (name, index, record.get("slug", "?")),
                own_slug=record.get("slug"))

    return problems, external


def main():
    if not os.path.isdir(PAYLOAD_DIR):
        sys.stderr.write("no payload directory at %s\n" % PAYLOAD_DIR)
        return 2

    paths = sorted(os.path.join(PAYLOAD_DIR, name)
                   for name in os.listdir(PAYLOAD_DIR)
                   if name.endswith(".json"))
    if not paths:
        sys.stderr.write("no payloads to check in %s\n" % PAYLOAD_DIR)
        return 2

    failed = 0
    total_records = 0
    total_unsourced = 0
    loaded = {}
    for path in paths:
        name = os.path.basename(path)
        problems = check_payload(path)
        try:
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
            loaded[name] = payload
            records = payload.get("records", [])
            total_records += len(records)
            total_unsourced += sum(1 for r in records if not r.get("sources"))
        except Exception:                              # noqa: BLE001
            pass
        if problems:
            failed += 1
            print("FAIL %s" % name)
            for problem in problems:
                print("       %s" % problem)
        else:
            print("ok   %s" % name)

    cross_problems, external = check_cross_references(loaded,
                                                      load_served_slugs())
    if cross_problems:
        failed += 1
        print("FAIL cross-references between payloads and the served corpus")
        for problem in cross_problems:
            print("       %s" % problem)
    else:
        print("ok   cross-references resolve (%d to the served corpus)"
              % external)

    print()
    print("  %d payload(s), %d record(s), %d carrying no source"
          % (len(paths), total_records, total_unsourced))
    if failed:
        print("\n%d check(s) failed." % failed)
        return 1
    print("\nAll scan payloads hold their claim tracking.")
    print("NOTE: this gate checks that claims are not OVERSTATED. It cannot "
          "check whether the events are true, and it cannot validate duplicate "
          "detection -- only a human reading the sources can do either.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
