# Consumer Guide

For anyone building on pdoom-data: another game, a research tool, a
visualisation, a dashboard. Including future maintainers of pdoom1.

The short version: **take the facts, and decide deliberately whether you want
the opinions.** This repository is built so you never have to fork it in order
to disagree with it.

---

## 1. Facts versus opinions

Every field in a served record is one or the other, and they are kept
structurally apart on purpose.

| Kind | Fields | How to treat it |
|------|--------|-----------------|
| **Fact** | `title`, `occurred_at`, `published_at`, `source_available_at`, `actors`, `source_urls`, `signals`, `license`, `content_sha256` | Derived from the world. Any consumer computes the same value. |
| **Opinion** | `salience_by_profile`, `salience_tier_by_profile`, `reviews` | Someone's judgement. Named, versioned, or attributed, never anonymous. |

The design test used throughout this repo:

> If another consumer disagreed with this value, would they have to fork the
> data, or could they just ignore a field?

Fork means it is on the wrong side of the boundary. Ignore means it is safe to
ship. That is why there is deliberately **no bare `salience` field** and **no
`game_facing` flag**: a bare number reads as a property of the record rather
than as one weighting among many, and a repo-level promotion flag would be
this project deciding what belongs in *your* product.

---

## 2. Salience profiles

`salience_by_profile` maps a profile id to a score:

```json
"salience_by_profile":      {"default_v1": 0.9902},
"salience_tier_by_profile": {"default_v1": "A"},
"salience_basis_by_profile": {"default_v1": {
    "method": "karma:identity", "raw_score": 913.0,
    "topical_relevance": 1.0, "percentile_within": "kind=forum_post,year=2026",
    "group_size": 600, "shrinkage": 0.98 }}
```

`default_v1` is defined in `config/salience_profiles/default_v1.json`,
including its method, its parameters, and an explicit `known_weaknesses` list.
Read that file before trusting the number.

**To use a different weighting**, add your own profile file. The build applies
every profile it finds and emits all of them side by side. You do not need
permission, a fork, or a discussion. Records gain a key; nothing else changes.

The raw inputs are always present in `signals` as dated observations, so you
can ignore every profile and compute your own ranking from scratch:

```json
"signals": {"karma": [{"observed_at": "2026-07-24T23:51:57Z", "value": 913}]}
```

Signals are time series rather than scalars because citation counts and karma
keep accruing. If you need "what was known at time T", read the observation at
or before T rather than the latest value.

---

## 3. Human reviews, and how to inherit or ignore them

`reviews` is a list of attributed judgements:

```json
"reviews": [
  {"reviewer": "pip", "verdict": "accept", "tier_override": "A",
   "note": "landmark", "at": "2026-07-25T11:02:00Z", "layer": "human_review_2026-07-25.json"}
]
```

Attribution is the whole point. Three postures are all first-class:

- **Inherit** a reviewer's judgement, because curating a corpus by eye is
  expensive and someone else already did it. Filter to
  `reviews[].reviewer == "pip"` and take the accepts.
- **Filter** to reviewers you trust, or require agreement between two.
- **Ignore** reviews entirely and curate from the facts yourself.

None of these requires modifying the data. An unattributed verdict would have
made a single person's taste indistinguishable from a source-derived property,
which is exactly the trap this structure avoids.

`review_status` is a *factual* statement about whether any review exists
(`unreviewed`, `needs_privacy_review`, `reviewed`). It is not a verdict.

---

## 4. Two temporal gates, not one

Records carry four clocks. Two of them gate visibility, and they answer
different questions:

| Gate | Test | Question |
|------|------|----------|
| Fact visibility | `published_at <= your_date` | Could someone know this had happened? |
| Dataset unlock | `source_available_at <= your_date` | Could someone have this source as a research instrument? |

**Do not combine these into a single test.** Epoch AI's model database did not
exist until 2024-06, but AlphaGo was public in 2016. Testing both at once
hides every pre-2024 model release from every pre-2024 consumer.

`ingested_at` is audit metadata and should never drive user-facing behaviour.
A `null` clock means ungated and unknown, never "now".

Availability dates live in `config/sources.json`, each with an `evidence`
block naming what was read and a `confidence` rating. Some are marked medium
or low with the weakness stated. Check the confidence before building a
mechanic that depends on the date being exact.

---

## 5. Obligations

Most of this guide is permissive. These parts are not.

**Honour tombstones.** `data/raw/_tombstones/` lists records removed because
they should not have been ingested, typically concerning private individuals
or personal circumstances. Tombstones record the id, date, and reason category
and deliberately never record the content. If you cached a record that later
gains a tombstone, delete your copy. This is the one non-optional obligation
here, and it exists because a corpus assembled from public forums will contain
memorials, harassment reports, and health disclosures about real people who
never volunteered to appear in anyone's product.

**Carry the licence.** Every record has a `license` block with the SPDX
identifier, the attribution string, and the terms URL that was actually read.
Obligations travel with the record, not with the repo.

- Most content is CC-BY-4.0 and requires attribution.
- Some is `NOASSERTION` with a `reuse_basis` field. For the forums this reads
  `facts_and_link_only`: bibliographic metadata and a hyperlink are stored,
  **no post text**, so no licence grant is relied upon. If you intend to
  retain or display post text, that is your decision to research, not one this
  repo has made for you.
- ShareAlike sources are excluded from this repo by policy, and
  `validate_candidate()` mechanically refuses to write a dump whose SPDX
  contains `-SA`.

**Credit the upstream sources, not just this repo.** The `citation` field in
each licence block carries the form the source asked for.

---

## 6. What is deliberately not here

Game mechanics. No trigger conditions, no event chains, no dialogue, no
scenario assignments, no probability curves. See ADR-001.

One historical exception you should know about: the older `all_events.json`
feed carries an `impacts` array using pdoom1's resource vocabulary
(`cash`, `stress`, `burnout_risk`, `vibey_doom`). That predates this boundary
being drawn and is the one place where one game's model sits in the shared
artefact. The candidate feed does not repeat the mistake; per-game mappings
belong in export profiles.

---

## 7. Reproducing the build

```
python scripts/build/project_candidates.py
```

Output under `data/serveable/api/candidates/` is derived and disposable.
Delete it, re-run, and you should get identical bytes. `LINEAGE.json` records
the input dumps with their hashes, the profiles applied, the review layers
merged, the realised tier cut points, and every dropped record with a reason.

There is no silent truncation anywhere in the pipeline: every input record is
either present in the output or listed in `dropped_records` with a cause. If
you find a record that is neither, that is a bug worth reporting.
