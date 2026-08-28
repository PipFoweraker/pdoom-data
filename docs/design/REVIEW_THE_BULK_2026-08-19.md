# Reviewing the 1,166: what it would mean, and the cheapest thing that works

    TO          Pip, as architect
    FROM        pdoom-data seat
    DATE        2026-08-19
    DECISION    Six asks below. Nothing is implemented. No human field is set.
    STATUS      condition: dirty | attention: blocked on Pip
    SUPERSEDES  nothing. Downstream of docs/CORPUS_PROPOSAL_2026-08-09.md,
                whose six asks are still unticked.
    PAGE 1 OF 6

## Core message

The 2026-07-24 feedback asked for "at least one human eyeball involved in the
system that reviews and promotes it". The 93 watch-list atoms now have that
system. The 1,166 bulk records, which are already public, still have none, and
they are the larger gap.

But "review the 1,166" is not one job, it is four, and three of them should not
be done by a human at all. Description quality is already measured and is a
defect in our own extractor, so a human reading those descriptions would be
grading our code and calling it a corpus. Whether papers belong in a collection
called `timeline_events` is one ruling, not 1,166, and it is already drafted as
ask A3 in the corpus proposal. Schema conformance is one extra key and one empty
array. **Exactly one question has real per-record variance and no mechanical
answer: is this paper worth carrying in an AI-safety reference corpus.** That
question is the input to A3 rather than a consequence of it, which is why it can
be answered before anything else is ruled.

The corpus proposal already proposed the instrument, on its page 9, and offered
to prepare it "on request". Ten days later it has not happened, because it was
made contingent on a word that has not come. **The design change that matters is
to make the sample not need a ruling to exist.** It is an hour of machine time,
zero of yours, and it is discardable if you rule against the whole corpus.

## The asks

Each answerable yes or no. Reasoning starts on page 2.

| # | Ask | YES | NO |
|---|---|---|---|
| B1 | Prepare the sample without waiting on A1-A6: fetch real abstracts for a seeded random 100 of the 1,129 arXiv records into a new immutable raw dump, and generate one static review sheet. | [ ] | [ ] |
| B2 | Ask exactly one question per record, three keys, no typing anywhere in the fast lane. | [ ] | [ ] |
| B3 | Size the sample at 100 rather than 50 or 1,166. | [ ] | [ ] |
| B4 | Land verdicts in `data/curated/corpus_review/` and publish a POPULATION claim with its interval at `api/meta/corpus_review.json`. Write nothing into `all_events.json`. | [ ] | [ ] |
| B5 | Do not attempt a full 1,166 pass before A3 is ruled. | [ ] | [ ] |
| B6 | Do not build a new review tool. Generate a sheet; reuse the interaction model already measured in `pdoom1/tools/art_review/serve_review.py`. | [ ] | [ ] |

B1 is the only one that costs anything before you sit down, and what it costs is
machine time. B2, B3, B5 and B6 are constraints on a thing that does not exist
yet, so a NO to any of them is free today and expensive in a fortnight.

## What is new since 2026-08-09, so this is not a re-run

The corpus proposal measured the corpus. This document measures the *selection*,
and the finding changes what a review is for.

**The 1,166 bulk records are exactly the tier-A records of the alignment_research
quality scoring, and tier A is exactly the arXiv-or-Distill records. Both set
equalities are exact, zero exceptions in either direction.** The scoring config
has eight terms; the source bonus is 3 points and the other seven sum to 6.5
against a 7.0 threshold, so **no paper can reach tier A without being on arXiv or
Distill, and every paper on arXiv or Distill reaches it.** Not one of the other
seven terms moved a single tier-A decision.

The full selection chain, end to end, is now documented and contains no
relevance judgement at any step:

    9,378  records fetched from StampyAI/alignment-research-dataset
    6,549  after an upstream filter: date >= 2016, 11 named sources,
           full-text match on any of seven keywords -- alignment, safety,
           interpretability, robustness, capabilities, x-risk, existential --
           and min_text_length 100
    1,166  after quality_tier == "A", which is provably "the URL is arxiv.org
           or distill.pub"
    1,166  served publicly as timeline events

"Capabilities" and "robustness" as free-text keywords are why the tail is wide:
they match most of modern machine learning. The step that looks like quality
control is a domain check. **Nobody, machine or human, has ever asked of any of
these 1,166 records whether it is relevant.** That is the gap, stated precisely,
and it is narrower and more answerable than "review 1,166 records".

---

    PAGE 2 OF 6

## 1. What reviewing 1,166 records would even mean

Four candidate questions. Three of them a human should not be asked.

**Description quality: already measured, and reviewing it grades our extractor.**
`api/meta/dataset_quality.json` is the canonical figure and should be quoted
from there: 989 of 1,194 descriptions are under 60 characters, 82.8 percent.
Re-measured against the bulk population alone today, those same 989 records are
84.8 percent of the 1,166, and **0 of the 28 hand-authored records are among
them**. 848 bulk descriptions are exactly 30 characters long, and the modal
value is the literal string `1 Introduction` followed by a rule.

There is nothing for a human to judge here. The cause is known and is in our
code: the raw dump carries no abstract, so `transform_enriched.py` fell through
to the first paragraph of extracted PDF, which for an arXiv PDF is the first
heading. A reviewer reading these would be scoring our own extraction failure.
That is not a metaphor about the check rule, it is the rule: `pdoom1#1075`,
clause 2, do not derive what to look for from the system you are checking.

**Schema conformance: one key and one empty array.** Re-measured today with
`jsonschema` against `config/schemas/event_v1.json`: 1,166 records fail, and the
failures are `additionalProperties` on an undeclared `source_id` (1,166),
`minItems` on an empty `tags` array (1,166), and `maxLength` on a description
over 1,000 characters (24). Removing `source_id` alone leaves 1,166 still
failing on `tags`. This reproduces `pdoom-data#65` and the corpus proposal's
fact two exactly. It is an afternoon of work and it certifies nothing about
whether the records belong.

**Inclusion in `timeline_events` at all: one ruling, not 1,166.** `Fixing Weight
Decay Regularization in Adam` did not happen to anyone. Every bulk record fails
the same way for the same reason, so per-record review cannot discriminate. This
is ask A3, and it is already on your desk.

**Worth carrying in a reference corpus: the only question with real variance.**
Whether `Interpretability in the Wild: a Circuit for Indirect Object
Identification in GPT-2 small` and `RL-IoT: Reinforcement Learning to Interact
with IoT Devices` belong in the same collection is a judgement, it differs
record by record, and no scanner can settle it. The corpus proposal put its
best guess at roughly a half wanted, a third weakly adjacent, a sixth off-topic,
from a sample of 40 titles it read itself, and flagged that as the one number a
second reader could move by a factor of two.

**So the reviewable question is that last one, and it must be asked against the
paper, not against our record of it.** The record we publish is damaged in a way
that correlates with nothing about the paper's merit. The abstract comes from
arXiv, which is outside this system, satisfying clause 1 as well.

## 2. The cheapest interaction that works

The constraint is not politeness, it is measured. From the first mass art review
on 2026-08-14, re-derived from `pdoom1/tools/art_review/review_log.jsonl`: 470
distinct assets judged in 23.1 minutes, 20.3 per minute, one every 2.9 seconds.
Final verdicts discard 274, keep 195, remix 1. **Harvest tags used: zero.**
Corpus-wide since, 2 harvest tags across 7,944 judged assets, 0.03 percent. The
diagnosis in `pdoom1/docs/art/HARVEST_PASS_PROPOSAL.md` is worth copying
verbatim rather than paraphrasing: *"The tool asks for the tag at the wrong
moment ... harvesting competes with sweeping for the same seconds. It loses,
every time, because fate is urgent and harvest is not. This is a TIMING problem,
not a discipline problem."*

`shelf`, the one verdict that required a typed reason, was used twice and both
were later changed to something else.

The minimum viable interaction, therefore:

**One question, stated on the sheet, in words.** The art review added per-block
purpose text at your own ask on 2026-08-14, with the reason on the commit: a
reviewer facing unlabelled items cannot tell what judgement is being asked for.
The question here is one sentence and it goes at the top of every screen:
*"Would you want this paper in an AI-safety reference corpus?"*

**Three keys, exclusive, one axis.** `y` yes, `n` no, `?` unsure. Not four:
`shelf` is the verdict nobody wants mid-sweep, and `remix` has no analogue for a
paper. `?` is not a failure mode, it is the honest answer for a paper outside
your field, and its count is itself a finding.

**No typing in the fast lane at all.** No tags, no second axis, no required
reason, no free text on any of the three keys. A note key exists, opens after
the fact, and never blocks. Expect it to be used a handful of times and design
as if it will be used zero.

**Decided records leave the working set.** This is what actually produces the
pace, more than the keystroke count: `serve_review.py` moves decided cells out
of the live flow into a collapsed archive and the arrow keys walk live cells
only, so the queue shortens as you work.

**Log before state, always.** Every keystroke appends to a JSONL log before
anything else is written, and the state file is a projection of the log. This is
already the pattern in `scripts/review/triage_watch.py`, and it earned its keep
in the art review within four hours: 15 assets were revised mid-session, and
**394 of the 470 judged assets were later found orphaned from the state file.
The 470 claim survived only because it was counted from the append-only log.**

---

    PAGE 3 OF 6

**Screen budget.** A paper is not a thumbnail. The art review's 2.9 seconds
covers an image the eye takes in whole; here the unit is a title plus a
150-word abstract, and an honest estimate is 8 to 25 seconds. That is the single
largest reason not to size this at 1,166 (see page 4). One record per screen,
title large, abstract in full, the arXiv link live, and the record's own
published description shown small and clearly labelled as ours rather than
theirs, so the damage is visible without being what is judged.

**What is deliberately absent, and why each absence is measured rather than
tasteful:** no tag vocabulary (0 of 470, then 2 of 7,944), no typed reason on
any verdict (`shelf` used twice, both reversed), no second axis (the two-axis
model went unused in its first real outing), no rating scale (the mapping in
`triage_watch.py` already collapses status and rating into one keypress because
asking twice is asking twice).

## 3. Is a full review the right goal? Both sides.

### The case for reviewing all 1,166

Only a full pass yields per-record labels, and per-record labels are the only
thing that lets you **keep the good subset and drop the rest** - which the
corpus proposal itself names as the outcome neither Option 3 nor Option 4
covers. They are also the only thing that could replace pdoom1's hardcoded
`arxiv*` prefix match in `event_service.gd` with a field, which is what
`pdoom-data#26` asked for. A sample cannot produce a field. It produces a
sentence.

A full pass is also the only thing that answers the 2026-07-24 feedback on its
own terms. "At least one human eyeball involved in the system that reviews and
promotes it" is a claim about every record, and a 100-record sample leaves 1,066
records that no eyeball has seen. If the point is to be able to say the corpus
is reviewed, a sample cannot say it.

And the cost is not as large as it looks, *if* the batch axis is built. The
arXiv primary category is a real axis: the corpus proposal measured 39 distinct
primary categories with `cs.LG` 404, `cs.AI` 305, `cs.CY` 83, `cs.CL` 74,
`cs.RO` 56, `cs.CV` 55, so six decisions would cover about 977 of 1,129 records.
The art review's set-winner button is the precedent and its leverage is stated
in `serve_review.py`: *"ONE winner per axis, not a verdict per image - which is
why ~7 judgements retire ~1.5 GB here."* Judge the axis, not the item.

### The case for sampling

A full pass is 1,166 records at 8 to 25 seconds. That is 2.6 to 8.1 hours. It is
not a 23-minute sitting and it will not become one, because the unit of
judgement is a paragraph of prose. Presented as a sitting it will be started and
abandoned, and an abandoned pass is worse than none: it leaves a partial human
layer that looks like a verdict.

More decisively, **a full pass is work that a NO to A3 throws away entirely.**
If you rule that this repository's output is the game's corpus and nothing else
- which the corpus proposal names as the ruling that would flip it to Option 3 -
then 1,166 per-record labels on a bibliography being deleted are pure cost. The
sample is the input to that ruling. It is the wrong order to spend eight hours
labelling records in order to decide whether to keep them.

The category-axis argument also has a hole in it today: **the raw dump that
carries `primary_category` is not on this machine.** Only its `_metadata.json`
survives at `data/raw/alignment_research/dumps/2025-12-24_063313/`; the 28MB
dump that is present holds 1,000 alignmentforum records and joins to zero of the
1,166. So the batch axis costs a full 1,129-record arXiv fetch before its first
keystroke, and the fetch is the same fetch the sample needs anyway - just 11
times larger.

And on the sizing: **50 records already separates the corpus proposal's own two
decision thresholds.** At n=50, an observed 50 percent gives a 95 percent
interval of [36.9, 63.1] and an observed 20 percent gives [11.5, 32.8]. Those do
not overlap, so n=50 answers "Option 4 or Option 3" outright. n=100 narrows the
half-width from 13.1 to 9.2 percentage points and buys the thing n=50 does not:
enough resolution to place a bar rather than only to pick a side.

---

    PAGE 4 OF 6

### Recommendation on this question

**Sample, at n=100, explicitly as a decision instrument and not as a quality
certificate.** 100 records at 8 seconds is 13 minutes; at a conservative 25
seconds, 42 minutes. Either fits a sitting. The full pass stays available and
gets cheaper, not more expensive, if the sample says the bibliography is worth
keeping - because the same fetch that serves the sample serves the category axis.

The honest limit, stated so it is not discovered later: **this produces a
sentence about the population, with a name and an interval on it. It does not
produce a per-record field, and it does not let anyone say the corpus has been
reviewed.** It lets someone say, truthfully and citably, what fraction of it a
named person judged worth carrying, and how confident that estimate is. Those
are different claims and the second is the one we can afford.

## 4. Where the verdict lives, and what a consumer sees

These records are already served. `all_events.json` has exactly one producer,
`scripts/build/project_timeline_events.py`, which was hard won and passes
`--check` in CI. Nothing here writes to it, and nothing here writes to
`data/serveable/api/timeline_events/` at all.

**The judgement is an annotation, and ADR-008 already specifies the shape.**
Three record types joined by id - fact, annotation, reception - with the rule
that opinions reference a fact and are never fields on it, field names copied
verbatim from W3C Web Annotation (`target`, `body`, `creator`, `created`,
`motivation`), and `motivation: assessing` for exactly this. Its own test: delete
every annotation, is the dataset still complete and correct? Yes, and that is the
point. A hop with no agent is prohibited, so `creator` is required, which is the
same rule as `--by` in `triage_watch.py` and the same rule as ADR-001's no
anonymous verdicts.

So, three artefacts and no more:

**`data/curated/corpus_review/<pass_id>/verdicts.jsonl`** - append-only, one row
per keystroke, `{target, body, creator, created, motivation}` plus the previous
value so revisions survive. Human zone: not reproducible, delete it and someone
decides again. This is the only place a human field is set, and this document
sets none.

**`data/curated/corpus_review/<pass_id>/frame.json`** - the sample frame, written
*before* the sitting: the seed, the population it was drawn from, n, the fetch
dump it is joined to, and **the question asked, verbatim**. Written first
because a sample frame chosen after seeing verdicts is not a sample. It is also
what makes the whole thing re-derivable by someone who does not trust it.

**`data/serveable/api/meta/corpus_review.json`** - the served output, built by a
new producer with `--check`, gated in `check_all` like every other projection.
It carries the population claim and its uncertainty, not 1,166 silent labels:
the question verbatim, the reviewer's name, the date, n, the counts of yes / no
/ unsure, the Wilson interval, the seed, and the frame it was drawn from. It sits
beside `dataset_quality.json` rather than inside it, because that file's charter
is counts with no judgement and this is a judgement with a name on it.

The 100 individual verdicts are served alongside as an annotation sidecar joined
by `id`, per ADR-002's non-destructive pattern, so a consumer can read the actual
judgements rather than trusting an aggregate. Note the warning ADR-002 needs:
the existing `all_events_metadata.json` is that pattern gone wrong - 28 records
of `impact_level`, no producer, no author, zero references anywhere. An
annotation with no creator and no producer is what this must not become, and the
`--check` plus the required `creator` are the two mechanisms that prevent it.

**What a consumer sees.** Nothing changes in `all_events.json`, so nothing
breaks on the day: `pdoom1-website`'s 03:00 sync reads the same bytes, and
`pdoom1` reads a vendored snapshot and would not notice either way. What changes
is that a new file exists which the website's funding and about copy can quote,
in place of the number it currently has no basis for. That is the concrete
consumer-visible effect, and it is small on purpose.

---

    PAGE 5 OF 6

**One slot deliberately left empty.** `check_maturity.py` looks for a `maturity`
key in each collection's `LINEAGE.json` and no LINEAGE in this repository has
one. That is the designed place for a collection to self-report its rung, and
filling it for `timeline_events` is the natural follow-on. It should follow the
sample rather than lead it, because writing a rung before the judgement exists
is writing a claim before the evidence, which is the whole failure mode this
repository keeps re-finding.

## 5. What I would NOT build, and why

This repository's standing preference is mechanisms over documents, and its
matching failure is tools nobody uses. Six things I would not build, each
refused on a measurement rather than a taste.

**A new triage tool.** `scripts/review/triage_watch.py` exists and works. For
100 records the right surface is a generated static sheet, not a program: one
HTML file with the abstracts already in it, three keys, an export. The art
review's own history is the argument - three generations of surface, and the one
that carried the 470-asset session was a local server whose entire job was to
write a log. If a sitting is 13 to 42 minutes, a tool that takes two days to
build has to be used twenty times to pay for itself, and this pass runs once.

**A per-record field on the bulk records.** Not `salience`, not `quality`, not
`review_status`, not `game_facing`. ADR-001's operative test settles it: a
consumer who disagreed with our tier would have to fork. It is also the field
`check_maturity.py` already refuses by name - its `BARE_OPINION` set is
`{salience, importance, rarity, score, tier, quality, verdict, rating,
pdoom_impact}` - so adding one would move the collection further from gold while
appearing to improve it.

**A widened `event_v1`.** Bending the schema to admit `source_id` and empty tags
makes 1,166 records pass a contract they still do not belong to. It converts a
visible failure into an invisible one, which is this repository's most-repeated
mistake, and `pdoom-data#65` explicitly declines to prejudge it for that reason.

**A second axis, a tag vocabulary, or a rating scale.** Measured: 0 harvest tags
in 470 assets, 2 in 7,944. There is no version of this that survives contact
with a fast lane. If tags are wanted they are a separate later pass with its own
question, which is the ruling `HARVEST_PASSES` already encodes: a pass is a
question, not a filter.

**The category-axis batch pass, yet.** It is the right mechanism and I would
build it the day A3 comes back yes. Today it needs a 1,129-record fetch and 39
rulings to answer a question that 100 records answer well enough to decide with,
and it is only worth anything if the bibliography is being kept.

**Anything at all on the other 5,383 records.** The alignment_research corpus
holds 6,549 records: 2,190 alignmentforum, 1,767 lesswrong, 1,426 eaforum, plus
the 1,166 served. The 5,383 unserved ones are not a review problem because
nobody has published them. Reviewing them would be inventing work.

## 6. The first concrete step

**Fetch the abstracts. One command, an hour of machine time, no ruling required,
and it delivers a check even if the review never happens.**

Specifically: draw a seeded random 100 from the 1,129 arXiv records, write
`frame.json` recording the seed and population before anything is fetched, pull
each abstract from the arXiv API keyed on the identifier already in the record's
`sources` URL, and land the result as a new immutable dump under
`data/raw/arxiv_abstracts/dumps/<timestamp>/` with the usual `_metadata.json`.
Then generate one static sheet from it.

Three reasons this is the right first step rather than a proposal to do the
first step:

**It costs you nothing and needs no answer.** The corpus proposal's page 9
offered exactly this and made it conditional. Ten days on, the condition is what
failed, not the idea. Made unconditional it is an hour of a machine's time and a
file that can be deleted.

**It is a check before it is a review.** The fetched titles and dates are an
input from outside this system, so joining them to the served records
independently tests two claims already on file: the 12 records whose `year`
precedes their own arXiv identifier's posting month, and the 3 titles the `?`
fallback shredded. That check exists whether or not anybody ever presses a key,
and it satisfies both clauses of `pdoom1#1075` - the abstracts are external, and
the sample is drawn from the record list rather than from anything the current
projection decided.

---

    PAGE 6 OF 6

**It converts the expensive resource.** `pdoom-data#58` says the constraint is
your attention, not the corpus size. Everything above is arranged so that the
machine spends an hour and you spend 13 to 42 minutes, once, on the only
question a machine cannot answer.

What it does not do, and must not: it sets no `watch_status`, no rating, no
verdict and no human field of any kind. A frame with no verdicts is a prepared
sitting. A frame with verdicts this seat invented is a forgery.

## How this was measured

Read-only. Nothing was written to `data/serveable/`, `data/raw/` or
`data/curated/`. Run with `.venv-checks/bin/python`, which is the interpreter
that has `jsonschema`.

    # the selection chain, and the two set equalities
    .venv-checks/bin/python -c "import json; \
      d=json.load(open('data/serveable/api/timeline_events/all_events.json')); \
      q=json.load(open('data/enrichment/alignment_research/quality_scores_2024-12-24.json')); \
      A=set(q['tier_summary']['A']['ids']); \
      B={v['source_id'] for v in d.values() if 'source_id' in v}; \
      C={k for k,v in q['records'].items() if v['signals']['source'] in ('arxiv','distill')}; \
      print(A==B, A==C, len(A))"
    # -> True True 1166

    # schema conformance, reproducing pdoom-data#65
    .venv-checks/bin/python -c "import json,jsonschema,collections; \
      d=json.load(open('data/serveable/api/timeline_events/all_events.json')); \
      s=json.load(open('config/schemas/event_v1.json')); \
      V=jsonschema.Draft7Validator(s); \
      print(collections.Counter(e.validator for v in d.values() for e in V.iter_errors(v)))"
    # -> additionalProperties 1166, minItems 1166, maxLength 24

Description counts are quoted from `data/serveable/api/meta/dataset_quality.json`
per CLAUDE.md rather than retyped; the bulk-scoped restatement (989 of 1,166,
84.8 percent, and 0 of 28 hand-authored) is the same 989 records under a
different denominator, not a second measurement. Interval arithmetic is Wilson
with a finite-population correction against N = 1,129.

Art-review figures are from
`pdoom1/docs/art/audit_2026-08-13/SESSION_2026-08-14_first-mass-review.md`,
`pdoom1/docs/art/HARVEST_PASS_PROPOSAL.md`,
`pdoom1/tools/art_review/ORPHANS_2026-08-15.md` and
`pdoom1/tools/art_review/serve_review.py`.

## Where I am least confident

**The 8-to-25-second estimate is not measured, it is inferred**, and every
sizing argument on page 4 rests on it. Nobody has timed a human reading arXiv
abstracts under a three-key verdict. If the real figure is 5 seconds the full
pass is 97 minutes and the case for sampling weakens sharply; if it is 40
seconds even n=100 is a 67-minute sitting. The cheapest fix is to time the first
20 records of the sample and report the number, which costs nothing and would
make this paragraph obsolete.

**I assert that description quality needs no human and I have not proven the
converse.** It is conceivable that a reviewer reading 100 damaged descriptions
would notice a class of damage the classifier missed. I judge that unlikely
because the damage is a small number of mechanical causes, but it is a judgement.

**The dump metadata contradicts the corpus proposal and I cannot referee it.**
`data/raw/alignment_research/dumps/2025-12-24_063313/_metadata.json` lists
`abstract` among its `fields_extracted`; the corpus proposal's fact six states
the dump carries no abstract for any of its 6,549 records. The dump's
`data.jsonl` is not on this machine, so I could verify neither. If the abstracts
are in fact in that dump, B1's fetch is unnecessary and the whole first step is
a local join instead - which would make it cheaper, not more expensive, so it
does not change the recommendation. It does mean the first thing B1 should do is
look.

## Reading list

    docs/CORPUS_PROPOSAL_2026-08-09.md            asks A1-A6, still unticked
    data/serveable/api/meta/dataset_quality.json  the canonical counts
    data/enrichment/alignment_research/quality_scores_2024-12-24.json
    scripts/build/project_timeline_events.py      the one producer, --check
    scripts/build/project_watch_accepted.py       why promotion avoids event_v1
    scripts/review/triage_watch.py                the keyboard pattern to copy
    data/curated/watchlist/README.md              derived vs human fields
    docs/adr/ADR-008-provenance-and-annotation-model.md   the annotation shape
    scripts/validation/check_maturity.py          BARE_OPINION, the maturity slot
    pdoom1/tools/art_review/serve_review.py       the interaction model
    pdoom-data#65, #64, #58, #52, #51, #47, #34, #26
