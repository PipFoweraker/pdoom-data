# ADR-009: Funding data - atoms here, aggregates in the consumer

- **Status:** Accepted (Pip, 2026-08-22)
- **Date:** 2026-08-22

## Context

pdoom1-website's dashboard recalibration ("The Uncalibrated Instrument",
2026-08-22) deleted a hand-entered "AI safety investment 2018-2025" panel and
recorded that it knew of no machine-readable source for it. That claim was made
without checking this repository, which has had `data/raw/funding_sources/`
scaffolded for ai2050, catalyze_impact, cooperative_ai, givewiki, macroscopic,
open_philanthropy and sff since 2025-10. The scaffold holds zero real grant
records. See pdoom-data#94.

Probes run 2026-08-22 from the Windows seat, with HTTP status recorded:

| source | status | finding |
|---|---|---|
| survivalandflourishing.fund | 200 | Per-round pages 2019 to 2026, server-rendered |
| manifund.org/api/v0/projects | 200, keyless | 100/page, cursor `?before=`, history to 2023 |
| metaculus.com/api/posts/ | 403 | "available to authenticated users ... use your API token" |
| openphilanthropy.org/grants/ | 301 | to coefficientgiving.org/funds/ ; renamed Nov 2025 |

Three measurements decided this ADR.

**Stated money and moved money differ by more than an order of magnitude.**
Manifund's newest 100 projects on 2026-08-22 sum to $9,039,076 of
`funding_goal` and $502,800 of `txns`, with 9 of 100 projects carrying any
transaction at all. Both numbers are defensible answers to "how much AI safety
funding is on Manifund".

**Sources say so themselves.** SFF's recommendation pages state: "Some of the
grants below might not happen if they are logistically difficult or
time-consuming for the Funders". A recommendation is not a disbursement.

**Coverage moves independently of the world.** Coefficient Giving (as Open
Philanthropy) runs from about 2015, SFF from 2019, Manifund from 2023. A series
assembled from the sources that exist rises across 2017-2026 substantially
because more funders were onboarded. Plotted without coverage stated, that is a
source-onboarding artifact wearing the costume of a trend.

## Decision

### 1. pdoom-data ingests grant atoms. It does not publish a total.

An atom is one funder's one stated allocation to one recipient on one date,
with its source URL. Apply ADR-001's test: a consumer who disagrees that a
grant counts as AI safety ignores the cause field and keeps the record. A
consumer who disagrees with our definition of "total AI safety investment" must
recompute, and can only do so if the atoms are here.

### 2. Any aggregate is namespaced by its definition, or it is not served.

Following the `salience_by_profile.default_v1` precedent, never a bare `total`.
Preferred form is to serve no aggregate at all and let the dashboard sum with a
filter it states on the panel.

### 3. Store the source's own field, never a normalised `amount`.

`recommended_usd`, `funding_goal_usd`, `transacted_usd` are different facts.
Collapsing them into `amount` destroys the distinction that the 18x Manifund
gap and SFF's own caveat both turn on. A record carries which kind it is.

### 4. Every funding collection carries coverage metadata.

Funders included, date range per funder, and what is known to be missing.
History is patchy because the funding history was patchy; that is publishable.
Silent patchiness is not. A consumer cannot state a denominator it cannot read.

### 5. Conflict of interest is a field, not a footnote.

Pip has a live Manifund campaign (coordination,
`STRATEGY_2026-08-14_manifund-26-days.md`). Ruled 2026-08-22: our own campaign
is INCLUDED in the dataset, and carries a machine-readable
`related_party: true` with the relationship named. A disclosure that lives only
in prose is a copy, and copies go stale - see the printer-facts section of
CLAUDE.md for this repo's own worked example.

### 6. Metaculus is the first credentialed source, and that is a real cost.

No adapter in this repo reads a token today; `grep` for
`getenv|API_KEY|TOKEN` across `scripts/adapters/` returns nothing. Metaculus
requires one. Consequences: a CI secret, and a fetch workflow that must NOT
re-arm either of the deliberately de-armed committing workflows. The token
gates fetching only; a Metaculus community forecast is an attributed published
number, which ADR-001 permits as a fact about an opinion.

## Consequences

- The dashboard's "AI safety investment" panel becomes buildable, but only as
  "recommended USD, named funders, stated coverage", never as "AI safety
  investment".
- `data/raw/funding_sources/` gains real dumps. Its existing SFF investigation
  report stays where it is: `data/raw/` is immutable, so the correction is
  pdoom-data#94 plus this ADR, not an edit.
- A check on funding totals must take an input from outside the pipeline that
  produced them, per pdoom1#1075. Cross-check a computed round total against
  the funder's own published figure; do not verify our sum with our parser.

## Related

- ADR-001 (facts here, opinions attributed), ADR-008 (provenance)
- pdoom-data#94, pdoom1-website "The Uncalibrated Instrument" 2026-08-22
