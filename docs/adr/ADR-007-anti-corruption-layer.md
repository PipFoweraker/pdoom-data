# ADR-007: Anti-corruption layer - pdoom-data never encodes a consumer's internal vocabulary

- **Status:** Accepted (Pip, 2026-07-31)
- **Date:** 2026-07-31
- **Supersedes in part:** ADR-001's position that events carry pdoom1-shaped `impacts`

## Context

pdoom-data ships `event_v1` records carrying `impacts: [{variable, change}]`,
`rarity` and `pdoom_impact`. Those field names and their value spaces are
pdoom1's internal mechanical vocabulary, embedded in a shared schema.

On 2026-07-13 pdoom1 accepted **ADR-0015**, which deprecates exactly that shape:

> No action or event definition carries a literal doom field. Effects target
> intermediary world-state variables ... doom is computed from world state each
> day tick.

Quoting Pip's ruling recorded there: *"hardcoding doom counters into things
seems really like a legacy design philosophy ... we should move more towards
downstream effects rather than single source-destination number bumps."*

So the shared schema now encodes a vocabulary its only consumer has abandoned.
That is not a one-off mistake to patch. It is the predictable outcome of having
encoded a consumer's internal vocabulary at all, and it will happen again on the
next revision unless the structure changes.

Two further facts made the cost concrete. pdoom1's replacement vocabulary does
not yet exist (ADR-0015 marks it "v1 vocabulary owed, DQ-21"), and two competing
drafts are in circulation there -- ADR-0015's four examples and
`RISK_SYSTEM.md`'s six risk pools. Had pdoom-data guessed, it would have been
inventing pdoom1's core mechanical language from outside pdoom1, which ADR-0015
point 2 explicitly treats as an ADR-grade act belonging to that repo.

## Decision

**pdoom-data expresses cross-boundary meaning in vocabularies it owns or that
are externally maintained and stable. It never encodes a consumer's internal
names.**

This is the Domain-Driven Design **anti-corruption layer** between bounded
contexts, applied at the data-hub boundary. Each side keeps its own ubiquitous
language; translation is explicit and lives on the consumer's side.

Concretely:

1. **Where a directional hint is wanted**, express it against an external
   taxonomy -- currently the MIT AI Risk Repository domains, which pdoom-data
   already tags against -- plus a direction and a confidence, attributed. Not
   against `deployment_pressure`, `Capability Overhang`, or any successor.
2. **The mapping table from our vocabulary to a consumer's lives with the
   consumer.** pdoom1 owns the translation from AIRR domain to whatever its
   intermediaries end up being called.
3. **Existing `impacts` / `rarity` / `pdoom_impact` fields become archival.**
   They are not deleted -- this repository is an archive of its own evolution
   and those fields record what the ecosystem believed in 2025 -- but nothing
   new is authored against them and no consumer should read them as current
   guidance. Tracked in #34 and #43.

## Why this is in the consumer's interest, not ours

The argument that matters is not tidiness. It is blast radius on rename.

If pdoom-data encodes `deployment_pressure` and pdoom1 later renames or splits
it, then every exported pack already in the wild **silently means the wrong
thing**. There is no error; the field still parses; the numbers are simply
attached to a concept that no longer exists. Stale copies are the dangerous
case, and a data hub's output is copied by definition.

If pdoom-data encodes an AIRR domain, pdoom1 edits one mapping table and every
historical pack remains correct. DQ-21 can then change as often as the game
design needs it to, which is the point -- the game should be free to revise its
mechanics without a schema negotiation.

## Consequences

- **pdoom-data cannot be blocked by pdoom1's vocabulary churn**, and pdoom1
  cannot be slowed by ours.
- **A third consumer becomes possible.** Another game or tool can read an AIRR
  domain without learning pdoom1's mechanics. This was not true before.
- **Translation cost moves to the consumer.** That is the intended trade: the
  side that owns the vocabulary owns the mapping into it.
- **Some fidelity is lost.** A hint expressed in a general taxonomy cannot be as
  precise as one written directly against the engine's variables. Accepted
  deliberately: precision that decays silently is worth less than coarseness
  that stays true.

## Adopting pdoom1's framing

ADR-0015 point 4 states the boundary better than pdoom-data's own documentation:

> The doom function is structure; intermediary pricing is numbers ... MtG
> framing: events are cards, the doom function is the rules.

pdoom-data ships cards. pdoom1 owns the rules. This wording is adopted verbatim
rather than paraphrased, so both repositories use one sentence for one idea.

## Related

- pdoom1 ADR-0015 (no printed doom deltas), pdoom1 DQ-21, pdoom1#1052
- ADR-001 (game/data boundary), partially superseded
- ADR-008 (provenance and annotation model)
- #34, #43, #47, #49
