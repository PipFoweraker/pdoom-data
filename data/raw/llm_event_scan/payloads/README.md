# LLM event-scan payloads

Immutable records of what a language-model scan of the public web said, on a
given date, about events missing from this dataset.

**These are proposals, not facts.** Nothing here has been reviewed by a human.
Nothing here belongs in `data/curated/` or `data/serveable/` until someone
reads the sources and decides.

## Why this source is different

Every other source in this repo is a dataset: it has an upstream schema, a
license, and a URL you can fetch again tomorrow and get the same bytes. This
one has none of those.

- **The run is not reproducible.** Re-running the scan produces different
  text. The payload IS the artefact, which is why the adapter reads from here
  rather than from the network.
- **There is no upstream license**, because there is no upstream dataset. The
  descriptions are independently written prose about public events, citing
  primary sources -- the link-and-summarise posture that `ADAPTER_SPEC.md`
  permits in place of ingesting licensed text.
- **The scanner can be fluently wrong.** It will produce a well-formed,
  plausible, correctly-formatted record for an event that did not happen, and
  that record is visually indistinguishable from a true one.

That last point is the whole reason for the structure below.

## What is preserved on purpose

**Every flag the scanner raised about its own output.** Contested dates,
403 walls, sources it judged too weak, claims it explicitly declined to make.
Smoothing these out would produce a cleaner file that is worth less.

**Null dates.** Where two sources disagreed irreconcilably, the date is
`null` and `date_kind` is `contested`. Per the repo's standing rule a null
clock is ungated and honest; a fabricated one cannot be told from a real one
later. Four records carry null dates for this reason and each says why.

**The distinction between when a thing happened and when it was reported.**
`date_kind: "action"` means the date the thing occurred; `"reported"` means
only a reporting date is known. Several export-control and revenue-share
items were reported but never published as rules, and flattening that
distinction would invent an official act that never occurred.

**Overlap between scans.** Three records appear in two payloads because two
scanners found them independently. This is NOT deduplicated here. Two
independent scans converging on the same event with the same date is
corroborating evidence, and merging at the bronze layer destroys it.
Deduplication is a curation decision.

**Retrieval accounting.** Each payload records how many records rest on a
page body actually fetched and read, how many on search-result summaries, and
how many on model memory. For the 2026 scan that is 23 / 3 / 0. Without this
number a later reader cannot tell a read corpus from a recalled one.

## The gate

    python scripts/validation/check_scan_claims.py

Runs in `check_all.py`. It enforces that claims are not overstated:

- a non-null date requires at least one source;
- a record with no sources requires a flag containing `UNVERIFIED`;
- `confidence: low` requires a flag explaining why;
- `date_kind` of `contested` or `unverified` requires a null date;
- any payload with an unsourced record requires a retrieval-accounting block;
- ASCII only.

**It cannot check whether the events are true.** No machine can. It checks
that the payload does not claim more than it knows, which is the part a
machine can enforce, and it is deliberately sabotage-tested: planting a date
on an unsourced record, or stripping an `UNVERIFIED` marker, both fail it.

## Payloads

| File | Scope | Records | Unsourced |
|---|---|---|---|
| `2026-08-14_governance.json` | Governance, regulation, institutions, 2024-08 to 2026-08 | 26 | 0 |
| `2026-08-14_labs.json` | Frontier lab behaviour and model incidents, 2024-08 to 2026-08 | 20 | 0 |
| `2026-08-14_recent2026.json` | Everything, 2026-01 to 2026-08, weighted recent | 27 | 3 |

All three scanned 2026-08-14. A fourth scan covering incidents, lawsuits,
whistleblowers and the safety-funding landscape was interrupted and restarted;
its payload is not yet here.

## Known limits of the 2026-08-14 batch

- **The session's web-search budget was exhausted at 200 calls**, so coverage
  is a strong first pass with a named remainder, not a sweep. Each payload
  lists what its scanner could not reach.
- **Several sources block automated fetch** -- openai.com, reuters.com,
  wired.com, ft.com, wsj.com, commerce.gov, axios.com among them -- so most
  OpenAI-primary claims rest on corroborated secondaries. Records say so.
- **Records dated after roughly May 2026 post-date the operating model's own
  reliable knowledge.** They were retrieved, not recalled, and the retrieval
  accounting is how you check that.

## Before promoting anything

1. Read the sources. The gate cannot do this and neither can the scanner.
2. Resolve every flagged date conflict, preferring primaries over secondaries.
3. Decide the overlap questions, e.g. whether the India AI Impact Summit is
   its own record or evidence attached to `ai_summit_pivot_2023_2025`.
4. Take particular care with records naming private individuals or live
   litigation. Several are flagged; the flags are not decoration.
