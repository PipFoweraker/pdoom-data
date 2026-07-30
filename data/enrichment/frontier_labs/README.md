# Frontier AI labs

Organisations that develop frontier AI systems, with founding dates carried
alongside the evidence for them.

Built by `scripts/build/project_frontier_labs.py` into
`data/serveable/api/frontier_labs/`. Schema:
`config/schemas/frontier_labs_v1.json`.

Consumers: pdoom1 (engine integration, game issue #962) and pdoom1-website,
whose `scripts/calculate-game-stats.py` currently derives `frontier_labs_count`
from a hardcoded list. Filed as pdoom-data#37.

---

## What counts as "frontier"

This is the contestable part of the deliverable, so it is stated here rather
than left implicit in whoever typed the rows.

**A definition based on current capability would be wrong for this dataset.**
The collection feeds a timeline that runs from 2000 to the present, so it needs
organisations that *were* at the frontier at some point, not only those at it
today. A rule that excluded DeepMind-in-2015 or Google-Brain-in-2012 would be
useless for the thing it is for.

So inclusion is a disjunction, and which branch applied is recorded per row in
`inclusion_basis`.

### A. `epoch_frontier_model` -- mechanical

Credited on at least one model flagged `Frontier model` in the Epoch AI
notable-models database, with a publication date in 2000 or later, and not
purely academic.

This is a query, not a judgement. Epoch's flag is era-relative -- it marks the
1958 Perceptron as frontier for its time -- which is exactly the property the
timeline needs. Epoch AI's database is CC-BY-4.0 and is already ingested at
`data/raw/epoch_ai/`.

### B. `editorial` -- judgement, with a stated reason

Included although the mechanical rule did not select it. Every such row must
carry `inclusion_reason` naming *what the rule missed*.

**This branch is not a convenience.** Epoch's frontier flag is sparse: 123 of
1,034 rows in the ingested dump carry it. Its absence is therefore not evidence
that an organisation is not frontier. The decisive case is **DeepSeek**, which
has no flagged row in the dump at all despite V3 and R1 being unambiguously
frontier on release. A mechanical-only rule would have shipped a frontier-labs
dataset with no DeepSeek in it. Mistral, Alibaba, Cohere and Anthropic-adjacent
newer labs are further examples.

Two rows are deliberately borderline rather than quietly omitted:

- **Hugging Face** is arguably infrastructure, not a frontier lab. It is
  included so the boundary of the rule is visible *in the data*, where a
  disagreeing consumer can filter it, rather than hidden in a decision nobody
  recorded.
- **Safe Superintelligence** has released no model and so cannot appear in a
  model database by construction. Filter on `epoch_frontier_models` being null
  if you want only shipping labs.

### Counting: read `lab_kind` before you count rows

`frontier_labs_count` is not `len(labs)`. The collection deliberately mixes:

| `lab_kind` | Example |
|---|---|
| `dedicated_ai_lab` | DeepMind, Mistral AI, DeepSeek |
| `corporate_division` | Google Brain, Tencent AI Lab, ByteDance Seed |
| `corporate_parent` | Google, Microsoft, Amazon, NVIDIA |
| `research_institute` | Allen Institute for AI, Peng Cheng Laboratory |
| `research_collective` | EleutherAI |

Counting every row double-counts Google (which appears as Google, Google
Research, Google Brain, DeepMind and Google DeepMind, each with its own
founding date and its own end). That redundancy is intentional -- collapsing
them would destroy the merger and lineage facts -- but it means the consumer
must choose a filter. We do not choose one for you; that is the fact/opinion
firewall applied to counting.

**Two rows will inflate a naive count of currently-active frontier labs:**

- **Tencent AI Lab** was disbanded into the Hunyuan team on 2026-03-20
  (`status: merged`).
- **01.AI** stopped pre-training its own models in 2025-03 and now builds on
  DeepSeek's. It remains an operating company, so `status` is still `active`;
  the change is recorded in `status_date` and `notes`.

---

## Dates, and why several of them are null

The standing rule in this repo is **never guess a date**. `null` is ungated and
honest; a fabricated clock is indistinguishable from a real one later. Every
non-null `founded` carries `founded_evidence` with the URL that was read and
the verbatim sentence containing the date.

**Three rows have `founded: null` on purpose.**

- **Google Research** -- the only date available is an *uncited* Wikipedia
  infobox value. Google Research appears to be an organisational label that
  accreted rather than being founded: renamed to Google AI in 2018 and back,
  with the Brain team moving into and out of it.
- **Inspur** -- four mutually inconsistent dates circulate (1945, 1983, 1989,
  1998) because "Inspur" is not one organisation. Whoever consumes this row
  must first decide which entity is meant.
- **Adept AI** -- no source states a founding date. The widely repeated "2022"
  traces to the phrase "founded two years ago" in an article datelined
  2024-06-28. The well-evidenced public launch (2022-04-26) is in
  `founded_alternatives`, labelled as a launch.

### `evidence_strength` grades the source class, not the confidence

`registry` > `first_party` > `press` > `secondary` > `none`. This is
deliberately mechanical, because "how sure am I" is not a property of the
evidence. Mistral AI scores `registry` (French government SIREN 952418325);
Hugging Face scores `secondary`, because no first-party page states a founding
year and Wikipedia's own citation does not confirm the date when followed
through.

### `founded_contested` and `founded_alternatives`

Where founded / incorporated / announced / emerged-from-stealth are different
events, all of them are recorded and labelled. A consumer wanting "when did
this lab become publicly visible" should read `founded_alternatives`, not
`founded`.

This structure converged on a subset of Wikidata's statement model -- value
plus qualifiers plus references, with contested values coexisting rather than
one overwriting the others. Read their model before extending this one.

---

## Traps found while building this, recorded so nobody re-finds them

- **DeepMind's September/November ambiguity runs the opposite way to the usual
  telling.** Companies House shows entity 07386350 incorporated 2010-09-23
  under the shelf-company name `FRIARS 2022 LIMITED`, renamed DeepMind
  Technologies Limited on 2010-11-15. September is "a legal entity exists" and
  may be the shelf company's registration rather than any act by the founders.
  November is "DeepMind exists", and is what `founded` records.
- **Compaq CRL was not founded by Compaq.** DEC founded it in 1987 as DEC's
  Cambridge Research Laboratory; Compaq inherited it in 1998 and HP in 2002.
  The Epoch dump's org string flattens a three-parent lineage.
- **Stability AI's founding date misrepresents it.** Incorporated 2019-11-04,
  but with essentially no public AI-lab activity until Stable Diffusion in
  2022-08. Anyone comparing `founded` across labs will over-age Stability by
  about three years.
- **Qwen is not in DAMO Academy.** Alibaba moved DAMO's language and vision
  teams into Alibaba Cloud's Tongyi Lab in late 2022. The DAMO row is not the
  right home for Qwen.
- **Two reverse-acquihires are not acquisitions.** Character.AI (Google, 2024)
  and Adept (Amazon, 2024) both had founders hired and technology licensed
  without equity changing hands, and both continued operating. `status` stays
  `active` for each, with the event in `notes`. `parent_org` is null because no
  acquisition is evidenced.
- **Decoy corporate records, rejected and recorded.** UK Companies House lists
  `REKA AI LTD.` (14242489, incorporated 2022-07-19, Altrincham) whose date is
  temptingly close but whose office, size and profile do not match the
  Sunnyvale lab. A wrong SIREN (952481660) for Mistral circulates in secondary
  write-ups. Both are named in the relevant rows' `notes` so the next person
  does not adopt them.
- **MERL's name has a four-year gap.** It was called ITA from 1996 to 2000,
  which matters when matching on organisation name across a time series.

---

## Layout

    research/*.json      what was read. Each row carries URL and verbatim
                         quote. An evidence record: do not edit to change a
                         verdict.
    curation_table.json  the judgement calls -- id, lab_kind, inclusion_basis,
                         aliases, and the reason for each editorial inclusion.

Split so evidence and judgement can be reviewed separately. The projection
asserts both directions: a researched organisation missing from the curation
table fails the build rather than being silently dropped, and a curation entry
for something nobody researched fails too.

## Rebuilding

    python scripts/build/project_frontier_labs.py           # build
    python scripts/build/project_frontier_labs.py --check   # assert committed

`data/serveable/` is a build output; never hand-edit it. `--check` asserts the
committed feed is byte-identical to a fresh build. `LINEAGE.json` deliberately
carries no wall-clock stamp -- a `built_at` field is exactly what made the
candidate feed's rebuild-idempotence claim false.

## Deliberately not here

No game impacts, no rarity, no salience, no `game_facing` flag. Promotion to
the game is the consumer's call. Per ADR-001's stated direction and pdoom-data#34,
pdoom1's resource model belongs in an export profile, not the shared schema.

Reserved for later without a breaking change, via the `extra` escape hatch:
`funding_total`, `headcount_band`, `notable_models`, `safety_team_presence`,
`jurisdiction`.

## Known incompleteness

The inclusion rule's mechanical branch is only as good as the Epoch dump's
coverage, which skews toward language models with published compute figures.
Image, video, speech and robotics labs are under-represented, and the editorial
branch has not been systematically swept for them. Adding an inclusion basis
drawn from a governance instrument -- for example a frontier-safety-commitment
signatory list -- would be the natural third branch.
