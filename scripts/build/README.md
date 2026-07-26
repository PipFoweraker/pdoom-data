# scripts/build/

    project_candidates.py    bronze dumps -> the candidate feed

## The one rule

**`data/serveable/` is a build output. Never hand-edit it.**

The repo lost this property once and paid for seven months: `manifest.json`
claimed 28 events while `all_events.json` held 1,194, because two different
producers wrote to the serveable zone and nothing rebuilt or compared. That
is the entire reason this directory exists.

To assert the property:

    python scripts/build/project_candidates.py --check

Exits 1 if committed output has drifted from a fresh build. The feed must
match byte for byte; `LINEAGE.json` is compared with `built_at` removed,
because it is a wall-clock stamp that changes every run by design. Demanding
equality there would make the gate permanently red and therefore ignored,
which is worse than having no gate.

## What the build does, and where each input lives

    data/raw/<source>/dumps/<latest>/data.jsonl   bronze records
    data/raw/_tombstones/*.jsonl                  privacy removals
    config/sources.json                           source-level facts, clocks
    config/salience_profiles/*.json               every profile is applied
    data/enrichment/human_review/*.json           attributed verdicts
    data/enrichment/airr_tags/*.json              machine risk-domain tags

Source-level facts are resolved **here**, not stamped by adapters. Correcting
a date must never require re-downloading an 11 MB dump.

## Invariants this build maintains

- **No silent truncation.** Every input record is either in the output or in
  `LINEAGE.json -> dropped_records` with a reason. If you add filtering, add
  it to the drop log too.
- **Opinions stay namespaced.** No bare `salience`, no `game_facing`. A bare
  number reads as a property of the record; an unattributed verdict makes one
  person's taste look like a fact. Both force a disagreeing consumer to fork
  rather than ignore a field.
- **Tombstoned ids never reach the feed.**

`scripts/validation/check_invariants.py` asserts all of these.

## Statistical gotchas already found here

**Percentile within a group hands a perfect 1.0 to the top member of any
group**, however small. A 2001 decision-tree model outranked Alignment Faking
on the strength of one comparison. Percentiles are shrunk toward 0.5 in
proportion to group size (`SHRINKAGE_K`); if you add a new grouping, keep it.

**Substring matching on short tokens is noise.** `"ai" in text` matches
"training", "domain", "explain". Relevance terms are word-boundary regexes.

**Some sources are on-topic by construction.** Every row of an AI-models
database is about AI whether or not the model's *name* contains a keyword.
See `kinds_always_relevant` in the profile.
