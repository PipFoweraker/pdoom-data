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
later. **19 records carry a null date**, and each says why: 3 `contested`,
4 `unverified`, and 12 `reported` where only a month, a year or a period was
retrieved. This paragraph said "four" until 2026-08-15, which was the count
across the first three payloads before the incidents-and-funding scan landed.

**The distinction between when a thing happened and when it was reported.**
`date_kind: "action"` means the date the thing occurred; `"reported"` means
only a reporting date is known. Several export-control and revenue-share
items were reported but never published as rules, and flattening that
distinction would invent an official act that never occurred.

**Overlap between scans.** Records appear in two payloads because two scanners
found them independently. This is NOT deduplicated here. Two independent scans
converging on the same event is corroborating evidence, and merging at the
bronze layer destroys it. Deduplication is a curation decision, and
`data/curated/watchlist/` is where it is made -- `possible_duplicate_of`
carries **7 pairs** across the four payloads.

**Convergence means the same EVENT, not necessarily the same date.** Of the 7
pairs, `openai_models_breach_hugging_face_2026` (labs, 2026-07-09) and
`openai_models_escaped_sandbox_hacked_hugging_face_2026` (2026 scan,
2026-07-21) are the same incident anchored to different acts -- the intrusion
and OpenAI's disclosure -- and they also differ on the containment date, 13
versus 16 July. Both are `date_kind: action`. Resolving which act the record
should carry is a curation decision, not a defect.

### Erratum: the 2026 payload's `known_overlap` paragraph is wrong

`2026-08-14_recent2026.json` states that "Records 1, 2 and 20 in this payload
also appear in 2026-08-14_labs.json". Measured against the labs payload
directly, on 2026-08-15:

| Claimed | Actual |
|---|---|
| record 1, `character_ai_google_settle_teen_suicide_suits_2026` | no counterpart; labs has no Character.AI record at all |
| record 2, `grok_deepfake_paywall_and_country_bans_2026` | no counterpart; the nearest labs record is `grok_mechahitler_incident_2025`, a different event 14 months earlier |
| record 20, `anthropic_claude_breached_three_organisations_2026` | correct -- pairs with labs record 19, same date, shared source |
| not claimed | record 18 pairs with labs record 18, the Hugging Face convergence, which is the strongest one in the batch |

The payload is a bronze dump and is **not edited to fix this** -- what a scan
said is the artefact. The correction lives here, and the judgement lives in the
watch list. The 2026 scan's per-record flags about overlap are accurate; it is
the payload-level summary paragraph that is not.

**The lesson is a schema one.** That claim is prose about record positions, so
nothing mechanical can check it, and nothing did for a day. A future payload
should carry the claim as data -- a list of `{slug, other_payload, other_slug}`
alongside the prose rationale -- at which point the gate below checks it the
same way it already checks slug citations.

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
- every slug a flag cites resolves, to another scan record or to the served
  corpus, and every payload filename a flag names exists;
- ASCII only.

The cross-reference rule is the only part with an input from outside the scans.
`all_events.json` is built by a different pipeline from different sources, so a
scan cannot make its own citation resolve. It also closes a silent hole:
`project_watchlist.py` reads the same citations to seed `possible_duplicate_of`
but drops any that fail to resolve, so a flag naming a record that does not
exist degrades there into no link rather than an error. Two citations currently
resolve only against the served corpus, `ai_summit_pivot_2023_2025` and
`eu_ai_act_watering_down_2024`, and that is legal and deliberate.

`tests/test_scan_cross_references.py` proves the check fires -- a detector that
has never failed is indistinguishable from one that cannot.

**It cannot check whether the events are true.** No machine can. It checks
that the payload does not claim more than it knows, which is the part a
machine can enforce, and it is deliberately sabotage-tested: planting a date
on an unsourced record, or stripping an `UNVERIFIED` marker, both fail it.

## Payloads

| File | Scope | Records | Unsourced |
|---|---|---|---|
| `2026-08-14_governance.json` | Governance, regulation, institutions, 2024-08 to 2026-08 | 26 | 0 |
| `2026-08-14_incidents_funding.json` | Incidents, harms, lawsuits, whistleblowers, safety funding | 20 | 0 |
| `2026-08-14_labs.json` | Frontier lab behaviour and model incidents, 2024-08 to 2026-08 | 20 | 0 |
| `2026-08-14_recent2026.json` | Everything, 2026-01 to 2026-08, weighted recent | 27 | 3 |

All four scanned 2026-08-14, 93 records in total. The incidents-and-funding
scan was interrupted and restarted, and landed on 2026-08-15; this section
described it as "not yet here" until then.

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
