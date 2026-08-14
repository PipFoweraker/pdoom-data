# Watch list

93 candidate events, one atom each, and the place where judgement about them
lives.

    data/raw/llm_event_scan/payloads/   what four machine scans SAID  (bronze, immutable)
    data/curated/watchlist/             what a human DECIDED          (this)
    posts, sheets, promotion            projections over a selection

Built by `scripts/build/project_watchlist.py`, checked in `check_all`.

## The mechanic this is built for

Pip's, in his words: a thing happens, it goes on **Watch** for the month, and
at month end it is decided and the decision is published with reasons.

`watch_status` is exactly that state:

| value | meaning |
|---|---|
| `null` | not yet triaged. **The default, and nothing may infer past it.** |
| `watching` | on the Watch list for this month |
| `accepted` | a named person accepted it into the curated set |
| `rejected` | a named person rejected it, with a reason |

`accepted` does **not** mean it is in a game. ADR-001: promotion is the
consumer's call. There is no `game_facing` flag here and there will not be one.

## Derived fields vs human fields

The split is the whole design.

**Derived** -- `id`, `slug`, `title`, `date`, `date_kind`, `description`,
`sources`, `why_it_matters`, `scan_confidence`, `scan_flags`, `scans`,
`primary_source_retrieved`, `possible_duplicate_of`. Owned by the build,
reproducible from the payloads, and what `--check` compares.

**Human** -- `watch_status`, `watching_since`, `decided_on`, `decided_by`,
`decision_note`, `rating`, `cleared_for`, `note`. Owned by a person.

**A rebuild carries every human field forward untouched.** That is not a
convenience, it is the difference between a layer you can put judgement into
and one that eats it. `--check` compares only the derived half, so a rated atom
still passes.

If an atom carrying a human decision ever vanishes from the payloads, the build
**refuses** rather than dropping the decision silently. Bronze is immutable so
that should be impossible, which is exactly why it is worth failing loudly.

## Rate once, and it percolates

    scripts/review/select_watch.py --status watching --rating A
    scripts/review/select_watch.py --platform bluesky --limit 3
    scripts/review/select_watch.py --needs-attention

`select_watch.py` writes nothing and holds no copy of any event. Set a rating
or a clearance on the atom and every selection follows. This is what the first
art-cull draft lacked: there, a judgement had to be applied by hand to each
platform's prose, and whichever copy got missed silently disagreed.

**A null `cleared_for` means "not yet ruled on", never consent.** `--platform`
selects nothing until someone rules, by design.

## Duplicates are flagged, never merged

Seven pairs are flagged in `possible_duplicate_of`. They are **not** merged,
because identity is a judgement: `kimi_k3` appears twice and those are two
genuinely different events, a model release and a sandbox escape.

Detection uses title similarity, date proximity, and -- the one that matters --
the **explicit cross-references the scanners wrote into their own flags**. The
export-control pair ("US applies export controls to a domestic frontier model"
and "US order bars foreign nationals from Fable 5 and Mythos 5") is the same
event and shares **zero** title tokens. No lexical measure will ever link them.
A human had already noticed and said so, so the detector reads that rather than
re-deriving it.

> The first version of the detector mixed descriptions into the similarity and
> reported **zero duplicates across 93 atoms**. Descriptions add tokens faster
> than they add agreement, so a 0.88 title match scored 0.36 and fell under the
> threshold. It looked like a clean bill of health. Titles only, now.

## What needs a human, in order

    scripts/review/select_watch.py --needs-attention

1. **7 duplicate pairs** to merge or separate.
2. **19 atoms with a null date.** Most are month-only; none were guessed.
3. **3 atoms with no source at all**, each flagged `UNVERIFIED` in its own
   payload. Two are reported White House actions, one is a GPT-5.6 file-deletion
   report.
4. **The tertiary-source problem.** 17 of the 20 incidents-and-funding records
   rest on Wikipedia, and the scanner said so unprompted. The four 2026 items
   there are the thinnest.
5. **Records naming private individuals or live litigation** carry flags that
   are not decoration. `suchir_balaji_death_2024` in particular involves a real
   death and a contested cause, and probably should not be a game event at all.

## Not in this layer

No `impacts`, no `rarity`, no `salience`, no `game_facing`. Nothing here shapes
an event for a consumer. If pdoom1 wants a weighting it belongs in an export
profile, per ADR-001 and `pdoom-data#34`.
