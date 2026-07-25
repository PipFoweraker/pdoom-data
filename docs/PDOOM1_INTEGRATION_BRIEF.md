# pdoom1 Integration Brief

Status as of 2026-07-25. Written for pdoom1 agents to investigate during the
game architecture workshop. Canonical copy lives here; a shorter action-
oriented version sits in `pdoom1/docs/PDOOM_DATA_CONTRACT_BRIEF.md`.

**Everything described here is on the branch `feat/forward-fill-adapters`,
unpushed at time of writing.** Nothing on `main` has changed.

---

## 1. What is new, in one paragraph

pdoom-data now has a second, additive feed: **3,434 candidate records**
covering the 2023-2026 gap, built from Epoch AI model releases, LessWrong and
EA Forum posts, and tagged against the MIT AI Risk Repository taxonomy. It is
a *candidate* feed, not an event feed: nothing in it has been reviewed by a
human, and nothing should reach players until it has. The existing
`all_events.json` is untouched.

---

## 2. Where things are

    data/serveable/api/candidates/all_candidates.jsonl   3,434 candidates
    data/serveable/api/candidates/LINEAGE.json           full build accounting
    data/serveable/api/timeline_events/all_events.json   UNCHANGED, 1,194 events
    config/sources.json                                  source registry + dates
    config/salience_profiles/default_v1.json             the scoring profile
    data/raw/mit_airr/dumps/<ts>/taxonomy_domain.json    7 domains, 24 subdomains
    data/raw/mit_airr/dumps/<ts>/taxonomy_causal.json    Entity x Intent x Timing
    docs/CONSUMER_GUIDE.md                               the full contract
    docs/ADAPTER_SPEC.md                                 how sources get in

---

## 3. The thing most likely to change game design: two gates, not one

Every record carries four clocks. **Two of them gate visibility and they are
not interchangeable.**

| Gate | Test | Question it answers |
|------|------|---------------------|
| Fact visibility | `published_at <= game_date` | Can the player know this happened? |
| Dataset unlock | `source_available_at <= game_date` | Can the player have this SOURCE as a research instrument? |

Combining them into one test hides every pre-2024 model release from every
pre-2024 player, because Epoch AI's database did not exist until 2024-06 even
though AlphaGo was public in 2016. Worked example from the real data:

    2016-12-31 ->   290 facts knowable | sources unlocked: lesswrong, eaforum, arxiv
    2020-06-30 ->   479 facts knowable | sources unlocked: lesswrong, eaforum, arxiv
    2024-12-31 ->  2087 facts knowable | + epoch_ai, openalex, aiid, mit_airr

The second column is a mechanic that falls out of metadata for free: a
dataset becoming available is itself a datable event that changes what the
player's org can see. AIID launches 2020-11-18, MIT AIRR 2024-08, OpenAlex
2022-01. **Which gate drives which mechanic is a pdoom1 decision** and
deliberately not encoded here.

Caveat to respect: some dates are `medium` confidence with the weakness
stated in `config/sources.json`. EA Forum is pinned to year start and is
therefore early by up to eleven months. Read the `confidence` field before
building anything that depends on a date being exact. A `null` clock means
ungated and unknown, never "now".

---

## 4. Answer to issue #26 (the tier field ask)

The ask was: expose the A/B/C/D tier per event so the game can filter feed
salience. Here is why the answer is not a straight yes.

**The existing tier system is inverted.** It scores provenance and length:

    source_arxiv: 3, source_distill: 3, has_authors: 1, not_newsletter: 2,
    text_length_5k: 1, text_length_10k: 1, year_pre_2020: 1, has_tags: 0.5
    thresholds: A >= 7.0

"A-tier" therefore decodes as *"is a long arXiv paper with named authors"*,
which is exactly why the `hist_arxiv` deck floods the feed at full salience
(game issue #630). Exposing that field as-is would hand pdoom1 a filter whose
high values mean *least* game-salient.

**What exists instead**, on the candidate feed:

```json
"salience_by_profile":      {"default_v1": 0.9902},
"salience_tier_by_profile": {"default_v1": "A"},
"salience_basis_by_profile": {"default_v1": {
    "method": "karma:identity", "raw_score": 913.0,
    "topical_relevance": 1.0, "percentile_within": "kind=forum_post,year=2026",
    "group_size": 600, "shrinkage": 0.98}}
```

Salience is estimated *importance*, computed from external signals: training
compute for model releases, karma for forum posts, citations for papers.
Percentile within (kind, year), shrunk toward the mean for small groups, times
a topical relevance factor. Tier bands are quantiles: A is the top 5%, B the
next 15%, C the next 30%, D the remainder. Current distribution over 3,434
records: **A 172, B 687, C 1717, D 858**.

It is deliberately namespaced by profile rather than emitted as a bare
`salience` field, because it is a weighting *choice*, not a property of the
record. If pdoom1 wants different weights, add a file to
`config/salience_profiles/` and the build emits your profile alongside the
default. You never need to fork records to disagree.

**Recommendation for the workshop:** threshold on
`salience_tier_by_profile` for the feed-flood fix, and treat the old
`all_events.json` tiering as unusable for salience until those 1,166 arXiv
records are rescored or moved.

---

## 5. Facts versus opinions

Every field is one or the other, kept structurally apart so pdoom1 can take
the facts and ignore the judgements, or inherit them deliberately.

| Kind | Fields |
|------|--------|
| Fact | `title`, the four clocks, `actors`, `source_urls`, `signals`, `license`, `content_sha256` |
| Opinion | `salience_by_profile`, `reviews`, `airr_tags_by_layer` |

The test used throughout: *if another consumer disagreed, would they have to
fork the data or just ignore a field?* Fork means it is on the wrong side.

There is deliberately **no `game_facing` flag**. Whether a record belongs in
pdoom1 is pdoom1's call, not this repo's.

### Reviews are attributed

```json
"reviews": [{"reviewer": "pip", "verdict": "accept", "tier_override": "A",
             "note": "landmark", "at": "2026-07-25T11:02:00Z"}]
```

Filter to `reviewer == "pip"` and take the accepts to inherit his curation
cheaply; or filter to reviewers you trust; or ignore reviews and curate from
facts. `review_status` is factual (does any review exist), not a verdict.

**As of writing, zero records have been reviewed.** The review pass has not
run yet. Do not ship candidate records to players before it does.

---

## 6. Risk taxonomy tags

`airr_tags_by_layer` carries an inferred MIT AI Risk Repository domain:

```json
"airr_tags_by_layer": {"machine_v1": {
    "domain": "7. AI System Safety, Failures, & Limitations",
    "margin": 0.41, "tokens_used": 31, "confidence": "medium"}}
```

Seven domains, 24 sub-domains, plus a causal taxonomy of Entity (AI / Human /
Other) x Intent (Intentional / Unintentional / Other) x Timing (Pre- /
Post-deployment / Other). Full vocabulary in the `mit_airr` dump. Licence
CC-BY-4.0; the MIT team is aware and supportive, and this is the taxonomy
pdoom1 intends to use as an in-game reference function.

**Accuracy warning.** Tags come from a token-statistics classifier trained on
AIRR's own labelled descriptions. It scores 82.3% top-1 on held-out
descriptions against a 26% baseline, but candidates are short titles and
performance there is materially worse and **unmeasured**. It misfiled
"SolidGoldMagikarp" and "The Rise of Parasitic AI" as Privacy & Security when
both are system-safety findings. Only 878 of 3,135 tags reach `medium`
confidence; ~300 records are deliberately untagged. Use `very_low` and `low`
tags as a starting filter, never as a label shown to players.

---

## 7. Consumption protocol

Decided: **pdoom1 fetches at build time and vendors a copy into its own
repo.** Consequences worth designing around:

- Additive fields are non-breaking; pdoom1 upgrades when it chooses.
- Pin the vendored copy to a tag or commit and record which one. The monthly
  cycle will cut versioned releases; do not track a moving target mid-sprint.
- `data/serveable/**` stays committed so it is raw-fetchable from GitHub.
- The build is reproducible: `python scripts/build/project_candidates.py
  --check` exits 1 if committed output has drifted from a fresh build.

### One obligation that is not optional

**Honour tombstones.** `data/raw/_tombstones/` lists records removed because
they should not have been ingested, typically concerning private individuals.
Tombstones record id, date and reason category and never the content. If
pdoom1 has vendored a record that later gains a tombstone, delete it. A corpus
scraped from public forums contains memorials, harassment reports and health
disclosures about real people; the privacy screen has already flagged 23 such
records including one memorial that scored in the top ten by salience.

---

## 8. The boundary, restated

| Belongs in pdoom-data | Belongs in pdoom1 |
|-----------------------|-------------------|
| Historical facts, clocks, sources | Trigger conditions, event chains |
| External signals (karma, compute, citations) | Impact vectors and balance tuning |
| Shared taxonomy tags | Which gate drives which mechanic |
| Attributed editorial judgements | Dialogue, scenarios, probability curves |

**Known violation, pre-existing:** `all_events.json` carries `impacts` using
pdoom1's resource vocabulary (`cash`, `stress`, `burnout_risk`, `vibey_doom`)
in the shared schema, blessed by ADR-001. That is one game's model sitting in
the shared artefact and is the one thing another developer would have to fork
around. The candidate feed does not repeat it; per-game mappings belong in
export profiles (`data/enrichment/profiles/<game>.json`), which is a proposed
pattern and not yet built.

---

## 9. Open questions for the workshop

These are genuine forks where pdoom-data is deliberately not deciding:

1. **Does the dataset-unlock gate become a visible mechanic?** Sources
   becoming available is a free, dated, real-world progression axis. Is that a
   research-tool unlock, a Situational Awareness modifier, or ignored?
2. **What salience threshold fixes the feed flood?** A-only is 5% of records.
   A+B is 25%. Does the threshold move with player Situational Awareness, as
   issue #26 suggests?
3. **Does pdoom1 inherit Pip's review verdicts wholesale, or re-review?**
   Inheriting is free and immediate; re-reviewing costs hours but lets the
   game apply its own "is this fun" filter, which is a different question from
   "is this important".
4. **Does the AIRR taxonomy become a player-visible categorisation** (risk
   domains as a research tree, say) or an internal filter only? If
   player-visible, the tag confidence problem above becomes urgent.
5. **What happens to the 1,166 arXiv records in `all_events.json`?** Options
   discussed: rescore them under a salience profile, move them to a separate
   literature feed, or leave them and filter at the game layer.
6. **Which pdoom1 resource variables should an export profile map to?** This
   determines what a `profiles/pdoom1.json` would look like if the impacts
   move out of the shared schema.

---

## 10. What not to do

- Do not consume `all_candidates.jsonl` as finished game events. Zero records
  are reviewed.
- Do not read the old A/B/C/D tiers as salience. They measure provenance.
- Do not combine the two temporal gates into one test.
- Do not treat `very_low` confidence AIRR tags as labels.
- Do not expect `main` to contain any of this yet.
