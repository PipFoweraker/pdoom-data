# pdoom-data

The data hub for the P(Doom) game ecosystem: historical AI-safety events, the
pipelines that shape them, and the schemas other projects depend on.

If you are an AI assistant working in this repository, read `CLAUDE.md` first --
it is written for you, and this file is not.

---

## What you can actually fetch today

Everything below lives in `data/serveable/`, which is a **build output**. Never
edit it by hand. Every collection can be regenerated, and each has a `--check`
that proves the committed copy matches a fresh build.

| Collection | Records | What it is |
|---|---|---|
| `api/timeline_events/all_events.json` | 1,194 | the original event corpus -- read the caveat below |
| `api/candidates/all_candidates.jsonl` | 3,434 | 2023-2026 forward-fill from Epoch AI, LessWrong and the EA Forum; mostly unreviewed |
| `api/reviewed/all_reviewed.jsonl` | 204 | every candidate a named human has looked at, with the verdict they gave |
| `api/frontier_labs/all_labs.json` | 46 | AI labs with founding dates and the evidence for each date |

**The caveat on the 1,194.** That number decomposes into **28 hand-authored
events and 1,166 bulk arXiv/Distill imports**. The imported records carry
descriptions that are unparsed PDF text, complete with broken ligatures, and
1,129 of them share a single impact vector. It is 28 curated events plus a paper
dump wearing an event costume. Do not plan around 1,194 usable events.

**The caveat on the 140.** "Accepted" means one named reviewer said accept. It
is an attributed opinion, not a verification, and these are candidate records --
**not** the `event_v1` shape, so a game engine cannot ingest them without a
mapping layer.

## The rule that shapes everything here

**Facts live here. Opinions are attributed. Game balance lives in pdoom1.**

The test applied to every field:

> If another consumer disagreed with this value, would they have to fork the
> data, or could they just ignore a field?

Fork means the field is on the wrong side of the line. In practice you will find
`salience_by_profile.default_v1` rather than a bare `salience`, reviews that name
their reviewer rather than anonymous verdicts, and no `game_facing` flag anywhere
-- deciding what reaches players is your call, not ours.

It also means opinions ship **on purpose**, clearly labelled. A cheap human
judgement is often worth inheriting, and hiding it destroys that option for
everyone downstream.

## Dates, and why some are missing

Several records have a null date and that is deliberate. A null is honest and can
be filtered; a plausible-looking date invented to fill a gap is indistinguishable
from a real one six months later.

Where a date exists it carries its evidence: the URL that was read and the
verbatim sentence containing the date. Where sources disagree -- founded versus
incorporated versus publicly announced -- every candidate is recorded and
labelled rather than silently collapsed into one.

## Quick start

    git clone https://github.com/PipFoweraker/pdoom-data.git
    cd pdoom-data

    # Nothing to install for the integrity checks; they are stdlib only.
    python scripts/validation/check_invariants.py
    python scripts/build/project_candidates.py --check

Reading a collection is just reading a file:

    import json

    with open("data/serveable/api/frontier_labs/all_labs.json") as f:
        labs = json.load(f)["labs"]

    # Count only dedicated labs. Counting every row double-counts Google,
    # which appears five times with five different founding dates.
    dedicated = [l for l in labs if l["lab_kind"] == "dedicated_ai_lab"]

## Layout

    data/raw/           immutable source dumps; re-running an adapter makes a new one
    data/transformed/   machine-derived, reproducible by re-running code
    data/enrichment/    machine-derived enrichment (taxonomy tags, research imports)
    data/curated/       human judgement: review verdicts, hand-researched records
    data/serveable/     build output; what consumers fetch
    config/schemas/     JSON Schema for each collection
    scripts/adapters/   how external sources get in
    scripts/build/      projections into the serveable zone
    scripts/validation/ the assertions that keep all of the above honest
    tools/              event browser and review queue; open the HTML directly
    docs/               full documentation, starting at DOCUMENTATION_INDEX.md
    legacy/             moved out of the root in 2026-07; read its README first

`data/curated/` is the one unlike the others: it holds decisions a person made,
it cannot be regenerated, and losing it means someone has to decide again.

## Adding a data source

Read `docs/ADAPTER_SPEC.md` and `scripts/adapters/README.md`. Two things catch
people out:

- **ShareAlike licences are refused mechanically**, not by anyone remembering.
  `validate_candidate()` rejects any dump whose SPDX contains `-SA`. The
  workaround is link-and-summarise rather than ingest.
- **Two clocks, not one.** `published_at` says when a fact became knowable;
  `source_available_at` says when the *dataset* became usable as an instrument.
  Merging them hides every pre-2024 model release from any consumer modelling a
  pre-2024 world, because Epoch's database postdates AlphaGo by eight years.

## Contributing

Community feedback is never auto-merged; it goes through human review. All text
must be ASCII. Data in `data/raw/` is immutable -- if a source changes, run the
adapter again and produce a new dump.

Before opening a PR, run the checks under Quick start. CI runs the same ones.

## Ecosystem

- **pdoom1** -- the game. Consumes events and applies its own balance overrides.
- **pdoom1-website** -- public site and game stats.
- **pdoom-dashboard** -- analytics. Dormant since 2025-11.

## State of the build

`Data Integrity` is the workflow that matters, and it is green. It runs the
invariant checks, the rebuild assertions and the tests, and it has no write
access.

Two other workflows can commit to this repository and are **deliberately
restricted to manual dispatch**. `scripts/validation/check_workflow_disarm.py`
fails the build if that ever changes without a deliberate decision.
`Development Documentation CI/CD` is red against a known ASCII backlog; see
`CLAUDE.md` for why clearing it carelessly is worse than leaving it red.

## Licence

MIT.
