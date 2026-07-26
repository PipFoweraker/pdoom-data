# Adapter Specification v0.1

Contract that every external data source implements to enter pdoom-data.

Status: DRAFT. Written 2026-07-25 during the forward-fill campaign. Expect
revision once three or more adapters exist and the shared pain is visible.

## Why this exists

Before this spec, each source was integrated ad hoc. The alignment_research
import (2025-11, 2025-12) produced 1,166 records that reached the serveable
zone carrying no license, no provenance, and no distinction between "when the
thing happened" and "when we learned about it". That is not recoverable after
the fact, which is the whole reason the contract is mandatory at ingest.

## Zones (unchanged from docs/DATA_ZONES.md)

    data/raw/<source_id>/dumps/<UTC timestamp>/   BRONZE  immutable, committed
    data/enrichment/<layer>/<source_id>.json      SILVER  overlays, accretive
    data/serveable/...                            GOLD    build output only

An adapter writes ONLY to bronze. It never writes to enrichment or serveable.

## Adapter interface

Each adapter is a module under `scripts/adapters/` exposing:

    SOURCE_ID            str    snake_case, becomes the directory name
    LICENSE              dict   see "License block" below
    SOURCE_AVAILABLE_AT  str    ISO date the SOURCE DATASET became public,
                                or None if not yet verified
    fetch(since, until)  ->     iterator of raw source records (dicts)
    normalise(raw)       ->     one candidate record, or None to skip

`fetch` returns source-shaped data with as little alteration as possible.
`normalise` maps to the candidate record below. Keep them separate: re-running
normalise against a stored dump must never require a network call.

## License block

    {
      "spdx": "CC-BY-4.0",
      "url": "https://creativecommons.org/licenses/by/4.0/",
      "attribution": "Epoch AI, Data on Notable AI Models",
      "citation": "<full recommended citation text>",
      "source_terms_url": "<page where the terms were read>",
      "verified_at": "2026-07-25",
      "verified_by": "manual read of first-party page"
    }

Rules:

1. `spdx` MUST be read from a first-party page, never inferred. If the terms
   cannot be found, the adapter does not ship. Record the attempt instead.
2. ShareAlike sources (CC-BY-SA and friends) are EXCLUDED from this repo under
   the CC-BY-4.0 posture. Link-and-summarise is the permitted alternative:
   store the URL and an independently written summary, not the source text.
3. The license travels with every record. It is never assumed at build time.

## The four clocks

Every candidate record carries four timestamps. Collapsing them is the mistake
the existing `year` integer makes.

| Field                 | Meaning                                  | Used for |
|-----------------------|------------------------------------------|----------|
| `occurred_at`         | when the thing happened in the world     | timeline placement |
| `published_at`        | when it became publicly knowable         | can a player in year Y know this |
| `source_available_at` | when the containing DATASET became public| can a player in year Y have this tool |
| `ingested_at`         | when pdoom-data snapshotted it           | audit only, never game-visible |

`source_available_at` is a property of the source, not the record. It lives in
`config/sources.json` and is resolved by the build, NOT stamped by adapters.
(v0.1 of this spec said adapters stamp it. That was wrong: correcting a date
would then require re-downloading every dump. Superseded 2026-07-25.)

Set a clock to `null` rather than guessing. A null clock is ungated and
honest; a fabricated clock silently corrupts the gating mechanic and cannot be
distinguished from a real one later. Every non-null date in the registry
carries an `evidence` entry naming what was read; a date without evidence is
not permitted.

### Two gates, not one

These clocks answer different questions and must not be combined into a single
visibility test:

| Gate | Test | Governs |
|------|------|---------|
| Fact visibility | `published_at <= game_date` | whether a player can know a thing happened |
| Dataset unlock | `source_available_at <= game_date` | whether a player has the source as a research instrument |

Combining them hides every pre-2024 model release from every pre-2024 player,
because Epoch's database did not exist until 2024-06 even though AlphaGo was
public in 2016. The record carries both clocks; which gate applies to which
mechanic is a game decision and therefore belongs in pdoom1, not here.

## Candidate record shape

    {
      "id": "<source_id>:<stable_source_key>",
      "title": str,
      "summary": str,                  # <= 400 chars, plain prose, no markup
      "kind": str,                     # see vocabulary below
      "occurred_at": "YYYY-MM-DD" | null,
      "published_at": "YYYY-MM-DD" | null,
      "source_available_at": "YYYY-MM-DD" | null,
      "ingested_at": "<ISO 8601 UTC>",
      "actors": [str],                 # orgs and people, free text for now
      "source_urls": [str],
      "archive_urls": [str],           # web.archive.org etc, may be empty
      "content_sha256": str | null,    # of the fetched blob, if one exists
      "license": { ...license block... },
      "signals": {                     # time-varying observations, not scalars
        "<name>": [{"observed_at": "<ISO>", "value": <number>}]
      },
      "airr_tags": {"causal": [str], "domain": [str]},
      "source_raw_key": str,           # key back into the raw dump
      "_provenance": {                 # per FIELD, not per record
        "<field>": {"layer": str, "method": str, "confidence": "high|medium|low"}
      }
    }

### `kind` vocabulary (v0.1, extend deliberately)

    model_release     a system was released or published
    publication       a paper, report, or preprint
    incident          something went wrong in the world
    policy            legislation, regulation, executive action, standard
    org_event         founding, closure, reorganisation, departure, dispute
    funding           a grant, round, fund launch, or funding collapse
    forum_post        community writing (LessWrong, EA Forum)
    benchmark         an evaluation result or benchmark milestone

### What is NOT in the candidate record

No `impacts`, no `rarity`, no `pdoom_impact`, no reaction text. Those are game
concerns and live in export profiles (`data/enrichment/profiles/<game>.json`).
This keeps the core neutral so a different game or a researcher can consume it
without inheriting pdoom1's resource model.

## Dump layout

    data/raw/<source_id>/dumps/<YYYY-MM-DD_HHMMSS>/
        data.jsonl           one candidate record per line
        raw.jsonl            source-shaped records, pre-normalise
        _metadata.json       run metadata, see below
        MANIFEST.sha256      hashes of every file in the dump

`_metadata.json` minimum keys:

    source_id, source_url, extraction_date, adapter_version, license,
    source_available_at, record_count, query_window {since, until},
    filters_applied, extraction_statistics {fetched, skipped, written,
    errors}, tool_versions, notes

## Archival posture

Bytes live offline, the index lives in git. For any source document with a
retrievable blob (PDF, page):

1. Compute `content_sha256` of the blob and store it in the record.
2. Submit the URL to a public web archive; store returned snapshot URLs in
   `archive_urls`.
3. Extract text if needed for mining; keep the text, discard the blob.
4. Mirror blobs to the offline archive target via `scripts/archive/mirror.py`.

`MANIFEST.sha256` in the dump is what lets the offline copy be verified years
later. Without step 1 a mined-then-discarded document has no provenance chain.

## Idempotence and re-runs

Re-running an adapter over the same window MUST produce a new dump directory
rather than mutating an existing one. Dumps are never edited or deleted. The
diff between consecutive dumps of the same source is itself evidence about how
the upstream source changed, which is data worth keeping.

## Rate limits and courtesy

Identify the client honestly in the User-Agent, including a contact address.
Respect documented rate limits and back off on 429. Where a source offers a
polite pool (OpenAlex `mailto`), use it. Prefer one bulk download over many
small requests where the source publishes one.

For small community-run sources, ask before scraping. A short email costs a
day and is the difference between a collaborator and an extractive scraper.

## Open questions

- `actors` is free text. It needs an entity resolution pass before it can be
  joined across sources. Deferred deliberately.
- `airr_tags` on raw records are a placeholder and are dropped by the build.
  Tags now arrive as enrichment layers under `data/enrichment/airr_tags/`
  and surface as `airr_tags_by_layer`, so a machine pass and a human pass
  can coexist without either overwriting the other.
- `source_available_at` is null for most sources pending a per-source
  research pass. Roughly 15 sources, perhaps an hour of work total.
