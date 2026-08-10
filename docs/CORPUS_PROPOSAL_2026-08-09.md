# The timeline_events corpus: what it is, and what to do about it

    TO        Pip, as architect
    FROM      pdoom-data seat
    DATE      2026-08-09
    DECISION  Six asks below. Nothing is implemented; this is a proposal.
    STATUS    condition: dirty | attention: blocked on Pip
    SUPERSEDES  nothing. First document on this question.
    PAGE 1 OF 9

## Core message

Every number in the brief I was given is either wrong or measures the wrong
thing. The corpus is not 1,166 bad records; it is 1,166 good bibliographic
records wearing a fabricated event costume, and the projection that dresses
them throws away the authors, dates, DOIs and categories it was handed while
adding a randomly drawn quote attributed to nobody. The schema failure that
`pdoom-data#65` reports is real but cosmetic: it is one extra key and one empty
array, fixable in an afternoon, and fixing it would certify nothing. Meanwhile
four records still carry live academic email addresses on the public site.

## The asks

Each answerable yes or no. Reasoning starts on page 3.

| # | Ask | YES | NO |
|---|---|---|---|
| A1 | Redact the four records still publishing live email addresses this week, ahead of everything else here. | [ ] | [ ] |
| A2 | Stop publishing `safety_researcher_reaction` and `media_reaction` on the 1,166 bulk records, rather than keeping them behind the website's placeholder badge. | [ ] | [ ] |
| A3 | Split the collection: `timeline_events` keeps the 28 events, a new `research_corpus` carries the 1,166 papers in the candidate feed's shape. | [ ] | [ ] |
| A4 | Freeze `all_events.json` byte-for-byte as a named compatibility feed until both consumers migrate, rather than changing it under them. | [ ] | [ ] |
| A5 | Retire `event_v1` as the published contract for this collection instead of bending the data to pass it. | [ ] | [ ] |
| A6 | Report the headline as two numbers, "28 events, 1,166 research references", rather than one. | [ ] | [ ] |

A1 stands alone and I would act on a yes immediately. A2 through A6 are one
decision in five parts; a yes to A3 without A4 is the dangerous combination and
I would rather have a no to both.

## The eight facts this rests on

All measured today against the working tree at `b378d21`. Commands on page 3.

**One.** The corpus is 1,194 records: 28 hand-authored, 1,129 arXiv, 37 Distill.
`--check` on the producer passes, so the served file is reproducible.

**Two.** The 1,166 schema failures are exactly three defects and none of them is
a content defect: an undeclared `source_id` key against `additionalProperties:
false` (1,166 records), an empty `tags` array against `minItems: 1` (1,166), and
a description over 1,000 characters (24). Nothing else fails. `event_v1` does
not test any of the things that are actually wrong.

**Three.** All 24 over-length descriptions are over-length *because* of the PII
redaction. `[email address redacted]` is longer than the address it replaced.
24 of 24, no exceptions.

**Four.** `safety_researcher_reaction` on all 1,166 bulk records is one of five
canned strings chosen by `random.choice` seeded on the record id
(`scripts/enrichment/transform_enriched.py:210-242`). `media_reaction` is one of
three. Both are rendered publicly, inside quotation marks, on pdoom1.com.

**Five.** For a bulk record, 6 of the 12 published fields carry no information
about that record. Distinct values across all 1,166: `category` 1, `tags` 1,
`pdoom_impact` 1, `impacts` 2, `safety_researcher_reaction` 5,
`media_reaction` 6. Within the 1,129 arXiv records alone, `impacts` and
`media_reaction` drop to 1 and 3; the extra values are the Distill population's,
and they are constant within it too. Against 1,166 distinct titles and 1,166
distinct source URLs.

**Six.** 995 of 1,166 descriptions (85.3%) are a section heading and a rule, no
prose. 756 are literally `1 Introduction\n---------------`. The cause is that
the raw dump carries no abstract field for any of its 6,549 records, so the
generator fell through to "first paragraph of the extracted PDF", which for an
arXiv PDF is the first heading.

**Seven.** The raw dump carries, for all 1,129 arXiv records, fields the served
projection discards: `authors` (1,124), `date_published` (1,129), `categories`
(1,129), `doi` (99), `journal_ref` (93), `url`, and full `text` at a median of
47,996 characters. Licence is MIT on all 1,129.

**Eight.** Four records still publish live email addresses:
`arxiv_6d9c643dc346070e`, `arxiv_18def41ad9ebddf1`, `arxiv_b92f2e30b3f18ed7`,
`arxiv_95b381a292b906e9`. Six addresses. PDF extraction inserted a space inside
each domain, and the redactor's pattern has no whitespace tolerance.

---

    PAGE 2 OF 9

## What breaks downstream, measured rather than assumed

**pdoom1 is insulated and does not know it.** The game reads
`godot/data/historical_events.json`, a vendored snapshot dated 2026-08-03 with
1,194 records. There is no fetch of any kind;
`godot/autoload/event_service.gd:14-16` states that re-syncing is a build-time
act. So nothing I do here reaches the game until someone deliberately copies a
file. That is the single most important cost fact in this document, and it is
the opposite of what "most-consumed file in the ecosystem" implies.

When the game does re-sync, two unit tests fail on a shrunk corpus:
`godot/tests/unit/test_event_retime.gd:124` asserts more than 1,100 transformed
events, and `:97-119` asserts every override key exists in the corpus. Eleven of
the 24 promotion-pass overrides are `arxiv_*` or `distill_*` ids, promoted by
renaming them past the flavour gate. A cut that deletes the bulk population
therefore deletes eleven events Pip's own promotion pass chose. Separately,
changing the pool size forks the RNG stream and needs a release boundary.

**pdoom1-website fails open, which is worse than failing loud.** Sync is a
filesystem read of the sibling clone
(`scripts/sync/sync-events.py:77`) on a 03:00 UTC cron, committing under
`[skip ci]`. There is no count floor anywhere: the website's own schema says
`minProperties: 1`, so a corpus of one record validates. A silent shrink from
1,194 to 28 would deploy, would change the public "Total Events" tile at
`public/events/index.html:722`, and would alert nobody. Deleted records do not
404; `sync-events.py` contains no unlink, so their pages stay published, stay in
`sitemap.xml`, and stop receiving privacy fixes. That is the failure already
documented as E-0 in `pdoom1-website/docs/TECH_DEBT.md` for 1,000 orphaned
`alignmentforum_*` pages. Doing it again on purpose would be indefensible, and
it is why A4 is on the list.

**The website already disbelieves the reactions.** `sync-events.py:665-697`
renders a "Placeholder - Needs Real Quote" badge, and
`public/data/events-sync-summary.json` records `events_with_placeholders: 1194`.
The consumer built a warning label because the producer shipped fiction. That is
a consumer paying for a producer's decision, which is precisely the boundary
ADR-001 exists to police.

## Where I am least confident

Three places, and I would rather name them than have them found.

The topical-relevance judgement on page 5 is mine, on a sample of 40, and it is
an opinion. It is the only number in this document that a second reader could
reasonably move by a factor of two.

I have not established what a "research reference" is worth to anyone. The
recommendation assumes the 1,129 papers have standalone value as a bibliography.
That is plausible - they include MMLU, universal adversarial perturbations, the
IOI circuit paper, Loeb's theorem for bounded agents - but nobody has asked for
a bibliography, and I may be rescuing something that should be deleted.

The four residual addresses are what my scanner found. A different scanner would
find a different number, and the history in `scripts/privacy/redact_emails.py`
is four consecutive bugs in this exact area. I would not report the corpus clean
on the strength of my own pattern.

---

    PAGE 3 OF 9

## 1. How this was measured, so you can re-run it

Everything below is read-only. I did not run `clean_events.py` at all, did not
write to `data/serveable/`, and did not touch `data/raw/`.

The producer's own check passes, which is what makes the rest trustworthy:

    python scripts/build/project_timeline_events.py --check
    # records 1194 / hand authored 28 / bulk research 1166 / CHECK OK

Schema conformance, which is the claim in `pdoom-data#65`:

    python -c "import json,io,jsonschema,collections; \
    d=json.load(io.open('data/serveable/api/timeline_events/all_events.json',encoding='utf-8')); \
    s=json.load(io.open('config/schemas/event_v1.json',encoding='utf-8')); \
    V=jsonschema.Draft7Validator(s); \
    c=collections.Counter(e.validator for k,v in d.items() for e in V.iter_errors(v)); \
    print(c)"

That returns `additionalProperties: 1166, minItems: 1166, maxLength: 24`. The
1,166 figure in `pdoom-data#65` is correct. What it means is not what the issue
implies, and section 3 is about that.

Field variety, which is the measurement I had not seen anywhere:

    python -c "import json,io; \
    d=json.load(io.open('data/serveable/api/timeline_events/all_events.json',encoding='utf-8')); \
    b=[v for k,v in d.items() if k.startswith(('arxiv_','distill_'))]; \
    print(len(b),'bulk records'); \
    [print(' ',f,len(set(json.dumps(v.get(f),sort_keys=True) for v in b))) for f in \
    ['category','impacts','tags','pdoom_impact','media_reaction', \
     'safety_researcher_reaction','description','title','sources']]"

The external anchor, per the rule in CLAUDE.md that a check must take an input
from outside the system it is checking: an arXiv identifier encodes the month of
first posting independently of the `year` field, and the raw dump's `url` field
carries it. 1,089 of 1,129 agree. 40 disagree. Of those, 23 are exactly one year
later, which is consistent with a journal publication year, and I would not call
those wrong so much as undefined. But 12 records carry a `year` **earlier** than
the preprint's own identifier, which is impossible under any reading. Example:
`arxiv_7b1fcae71ae04aa5` is dated 2020 against `arxiv.org/abs/1711.00694`.

Worth stating plainly: the `year` field agrees with the raw dump's
`date_published` on 1,166 of 1,166. So this is not a transformation bug in this
repository. It is an error inherited from the upstream StampyAI dataset and
republished without ever being checked against a second source. The check cost
about four lines.

## 2. What the corpus actually is

Three populations, and treating them as one is most of the confusion.

**28 hand-authored events.** Every field distinct per record. All 28 validate
against `event_v1`. These are real events with real sources: the OpenAI board
crisis, Project Maven, the FTX Future Fund collapse, the UK AISI rename. They
are what the collection's name promises.

**1,129 arXiv papers.** Real papers, real titles, real URLs, correct upstream
provenance with an MIT licence. 1,129 distinct titles, 1,129 distinct source
URLs, no duplicates. The titles survived extraction well: only three are
damaged, all by the same `?` fallback (`Parametric Bounded L?b's Theorem`,
`No?regret Learning`, `Inverse Scaling: When Bigger Isn?t Better`).

**37 Distill articles.** Same shape, and every one is `legendary` because
`transform_enriched.py:136-137` returns `legendary` unconditionally for
`source == 'distill'`. So `legendary` in this corpus means "came from
distill.pub". `pdoom-data#51` established this and it holds.

---

    PAGE 4 OF 9

### The description failure, classified

I partitioned all 1,166 bulk descriptions into mutually exclusive classes,
first match wins. This is the distribution the brief asked for.

| class | n | % of bulk |
|---|---|---|
| B: section heading and a rule, no prose | 995 | 85.3 |
| C: raw PDF dump, truncated at 1,000 chars | 95 | 8.1 |
| E: other, mostly PDF title-page fragments | 54 | 4.6 |
| A: HTML or CSS markup | 14 | 1.2 |
| D: short fragment under 60 chars | 8 | 0.7 |

`pdoom-data#51` reported "756 of them are literally `1 Introduction`". Measured
today: **756 exactly, and 938 counting the four near-identical variants** -
`I Introduction` (84, the digit 1 read as a capital I by the extractor),
`1. Introduction` (63), `Introduction` (35). The issue's number is right and
understates the mode by 24%.

Real records, quoted rather than described:

    arxiv_2831a92843a5e489   description: "1 Introduction\n---------------"
    arxiv_b750fa887406a883   description: "### \n1 Contributions"
    distill_46959ccf83a5e89d description: "![](images/multiple-pages.svg)"

And one from class C, `arxiv_4a1054779386836e`, "Energetics of the brain and AI",
which shows four separate defects in one string:

    "Technical Report STR 2016-2 ? February 2016   \n \n \n \n \n \n
     ENERGETICS OF THE BRAIN AND AI \n \n \n \nAnders Sandberg \n ...
     ... brain emulation energy re- \nquirements. ... billions of neural fir-
     \nings. ... we  should expect de novo  AI to make use of \ndifferent,
     potentially very compressed and fast, pr ocesses. \nACM  Computing..."

The `?` was a bullet character. `re- \nquirements` and `fir- \nings` are
unrepaired hyphenation. `pr ocesses` is a column-extraction split; 87 of the 95
class-C records have three or more such splits. The trailing `...` is the
truncator at `transform_enriched.py:203-204`, `description[:997] + '...'`, which
is why 71 descriptions are exactly 1,000 characters long.

### Two failure modes I do not think anyone has named

**The `?` fallback is in the producer.** `transform_enriched.py:201` reads
`description.encode('ascii', 'replace').decode('ascii')`. That is the exact
construct CLAUDE.md forbids, in the sentence warning that
`legacy/2025-09_prototype/fix_ascii.py` "would shred every tree diagram". It has
been shredding this corpus since 2024-12-24. 44 records carry an intra-word `?`
where a `fi`, `fl` or diacritic used to be: `classi?cation`, `ef?ciency`,
`Polit?cnica de Val?ncia`, `Moore?s`. 96 occurrences. The seat that wrote the
landmine into CLAUDE.md and the code that violates it are the same repository.

**The corpus is a PII surface by construction.** Publishing unparsed PDF text
means publishing PDF front matter, and academic front matter is contact details.
42 records already carry a redaction tombstone covering 75 addresses. Four
records still carry six live addresses, listed on page 1. The redactor's pattern
at `scripts/privacy/redact_emails.py:73-74` requires a dot immediately after the
domain's first token; the extraction inserted a space (`uni -tuebingen.de`,
`louisville. edu`, `cbs .dk`), so it matched nothing. This is the fifth bug of
this species in that file, and it is the same lesson its own docstring teaches:
the damage that makes the descriptions unreadable is the damage that defeats the
scanner. I have not fixed it. It is `A1`.

---

    PAGE 5 OF 9

### What the projection threw away

This is the finding that changed my recommendation, so I want it explicit. The
raw dump at `data/raw/alignment_research/dumps/2025-12-24_063313/data.jsonl`
carries fifteen fields per arXiv record. The served projection carries thirteen,
of which six are constant. Set difference:

    DROPPED: _provenance, authors, author_comment, categories, converted_with,
             date_published, doi, journal_ref, primary_category, source_type,
             text, url
    ADDED:   impacts, rarity, pdoom_impact, safety_researcher_reaction,
             media_reaction, category

Every dropped field is a fact. Every added field is either a game mechanic or an
invention. The projection is not merely lossy; it is lossy in the exact
direction ADR-001 forbids. `authors` on 1,124 records was replaced by
`safety_researcher_reaction` drawn from a five-element list by a seeded dice
roll. That sentence is the whole problem in one line.

The dropped metadata is good. Primary categories are `cs.LG` 404, `cs.AI` 305,
`cs.CY` 83, `cs.CL` 74, `cs.RO` 56, `cs.CV` 55, across 39 distinct categories.
All 1,129 URLs are in the modern arXiv identifier form, so the arXiv API can
return an abstract for every one of them keyed on data already in the repo.

### Is the selection any good? My judgement, attributed

I drew a reproducible random sample of 40 arXiv titles (`random.seed(20260809)`)
and read them. This paragraph is my opinion and should be read as one.

Roughly half are papers a serious AI-safety bibliography would want: `Measuring
Massive Multitask Language Understanding`, `Interpretability in the Wild: a
Circuit for Indirect Object Identification in GPT-2 small`, `Understanding
Learned Reward Functions`, `Universal adversarial perturbations`, `Parametric
Bounded Loeb's Theorem`, `Modeling Transformative AI Risks (MTAIR)`. Perhaps a
third are general ML with a safety adjacency that is real but weak: `Fixing
Weight Decay Regularization in Adam`, `Stabilizing Transformers for
Reinforcement Learning`. Perhaps a sixth are off-topic: `Counterfactual
Explanation with Multi-Agent Reinforcement Learning for Drug Target Prediction`,
`Learning Visuo-Haptic Skewering Strategies for Robot-Assisted Feeding`,
`Finding the unicorn: Predicting early stage startup success`.

So the selection is a decent AI-safety-and-adjacent reading list with a wide
tail, not junk. I put weight on this because it inverts the obvious conclusion.
The instinct on reading 756 copies of `1 Introduction` is that the import is
worthless. The import is fine. The projection is what is worthless.

## 3. What "we have 1,194 events" is actually claiming

A count is a claim about a population, and the claim has three parts: that the
members exist, that they are of the named kind, and that they are distinct
instances of it. This number passes the first, fails the second, and passes the
third only on a technicality.

They exist. 1,194 records, reproducible from source, `--check` green, distinct
ids, distinct titles, distinct source URLs, no duplicates. That part is sound and
better than I expected.

They are not events. 1,166 of them are documents about events, or more often
documents about methods, which is a further step removed. `Fixing Weight Decay
Regularization in Adam` did not happen to anyone. The word is doing the work
here: `pdoom-data#47` already names `event` as meaning three different things,
and this is the cost of that. A count is only meaningful once the noun is.

They are distinct instances of a kind, but the kind is heterogeneous in a way
the number conceals. Adding 28 hand-researched events, each with a
human-written description and per-record sources, to 1,166 machine-derived
bibliography entries with six constant fields, and reporting a single total,
implies the members are commensurable. They differ by three or four orders of
magnitude in embodied attention.

**What a consumer is entitled to assume from "1,194 events".** Reading it
cold, I would assume: 1,194 discrete happenings, each with a description of what
happened, each editorially reviewed to the standard the first ten I clicked
suggested, differentiated enough that `rarity` and `category` mean something.
Every one of those is false for 97.7% of the collection. `category` has one
value. `rarity` is a length threshold on a field that was discarded before
publication (`pdoom-data#51`, correlation with the published description length
r = -0.0065). The reactions are dice rolls.

The honest reading is: **28 events, and 1,166 references to research
literature.** That is not a smaller claim, it is a different one, and A6 is
whether to make it.

---

    PAGE 6 OF 9

### The ADR-001 test, applied field by field

The test is: could a disagreeing consumer ignore this field, or would they have
to fork? For the six constant fields on bulk records:

`impacts` and `pdoom_impact` are already tracked as a breach by `pdoom-data#34`
and `vibey_doom` is unarguably one game's vocabulary. pdoom1 has since gone
further: `pdoom1/docs/decision-cards/2026-08-02_pdoom-data-contract.md:159-170`
explicitly removes `rarity`, `impacts`, `pdoom_impact` and `source_id` from what
it wants, on the grounds that "assigning intermediary magnitudes is an ADR-grade
balance act. It cannot live in a facts repo." The consumer these fields exist to
serve has asked for them to be withdrawn. That resolves `pdoom-data#34` in the
direction it proposed, with the beneficiary's consent on file.

`safety_researcher_reaction` and `media_reaction` are the harder case, and the
one I want a ruling on rather than a default. ADR-001 currently blesses them:
"Flavor text | safety_researcher_reaction, media_reaction | Content, not
mechanics". But ADR-001 was written on the assumption that flavour text is
written. A pseudo-random draw from a five-element list, published inside
quotation marks on a public page under the heading "safety researcher reaction",
is not flavour text. It is an unattributed assertion about what a class of real
people thinks, generated by a dice roll, and it fails the test in the strongest
possible form: a consumer who disagrees cannot ignore it, because it has already
been rendered on a page under their name. CLAUDE.md's own line is "No anonymous
verdicts. Every review names its reviewer." These are anonymous verdicts with
nobody behind them at all.

I am not proposing to attribute them, because there is nobody to attribute them
to. A2 proposes deleting them from the bulk records.

## 4. Options

Five, including the null. Costs are my estimates and should be read as such.

### Option 0: disclose and do nothing

Add a `known_defect` note to the manifest and a warning to the consumer guide.

**Cost** half a day. **Forecloses** nothing. **Who agrees** nobody.
**Downstream** nothing changes.

**Why it is on the list.** It is the honest baseline and this repository has a
documented failure mode of choosing it by accident: CLAUDE.md's own example is
`pdoom1-website/docs/TECH_DEBT.md` recording E-0 with numbers that matched a
later measurement exactly, and nothing happening. **Why I do not recommend it.**
It leaves fabricated quotes on a public site under real researchers' professional
description, and it leaves four addresses published. Writing that down does not
un-publish it. Document versus mechanism, and this is a mechanism problem.

### Option 1: repair in place

Keep one collection of 1,194. Re-derive descriptions from the raw `text` and the
arXiv API, populate `tags` from `categories`, restore `authors` and `doi`,
delete or attribute the reactions, and widen `event_v1` to match.

**Cost** I estimate three to five days. The abstract re-derivation is the bulk
of it: 1,129 arXiv API calls at the polite rate is about an hour of wall clock,
plus a day building and checking the join, plus a day on the schema and the
producer. **Forecloses** the split. Once these are all one collection with one
good schema, separating them later is a breaking change made twice.
**Who agrees** you, plus a courtesy note to pdoom1-website because record
content changes under a live sync. **Downstream** the website's pages regenerate
with real abstracts, which is a visible improvement; pdoom1 is unaffected until
it re-vendors.

**The case for it** is that it is the only option that makes the existing
headline true, and it improves every consumer without asking any of them to do
anything. **The case against** is that it dignifies the category error. At the
end you have 1,194 well-formed records of which 1,166 are still not events, and
the word `event` is still doing three jobs (`pdoom-data#47`). You have spent five
days making a wrong claim well-supported.

---

    PAGE 7 OF 9

### Option 2: re-derive the whole collection from source

Discard the current projection. Build a new one from the raw dump plus the arXiv
API, choosing the shape fresh.

**Cost** I estimate one to two weeks, mostly because "choosing the shape fresh"
is the expensive part and it means re-litigating the contract with pdoom1.
**Forecloses** little, but it spends the decision budget on a design exercise
rather than on the corpus. **Who agrees** you and pdoom1, because a fresh shape
is a new contract. **Downstream** everything, at once.

**The case for it** is that it is the only option that fixes the year errors,
the `?` shredding, the PII surface and the shape in one pass, from a source that
is on disk and reproducible. **The case against** is that `pdoom-data#58`
already told me what the constraint is, and it is your attention, not the code.
A two-week rebuild that lands a new contract on pdoom1 unbidden spends the scarce
resource. It also re-opens questions pdoom1 has already answered in writing.

### Option 3: shrink to what survives a quality bar

Publish only records that pass a stated bar. The natural bar is "has a
human-written description", which gives 28. A more generous bar, "is promoted by
pdoom1's own promotion pass or is hand-authored", gives about 63.

**Cost** two days, most of it on the migration path. **Forecloses** the
bibliography permanently; deleted records are gone from the served zone.
**Who agrees** you, pdoom1 and pdoom1-website, because both break.
**Downstream** this is the expensive one and I measured it rather than guessing.

pdoom1: two unit tests go red
(`godot/tests/unit/test_event_retime.gd:124` and `:97-119`), eleven of the 24
records your own promotion pass chose are `arxiv_*` or `distill_*` ids and would
be deleted, and the RNG stream forks, which needs a release boundary and a
version bump. pdoom1-website: no schema or count check catches it
(`minProperties: 1`), so a 03:00 cron would deploy it silently under `[skip ci]`;
roughly 1,100 event pages become orphans rather than 404s, stay in
`sitemap.xml`, and stop receiving privacy fixes, reproducing the E-0 failure in
`pdoom1-website/docs/TECH_DEBT.md` deliberately.

**The case for it** is that it is the only option whose headline is defensible
without a footnote, and `pdoom-data#64` records you already accepted metric F,
"28 schema-valid events". **The case against** is that it destroys 1,129
correctly-provenanced MIT-licensed bibliographic records to fix a labelling
problem, and it breaks the two consumers to do it.

### Option 4: change what the field means. RECOMMENDED

Split by kind rather than by quality.

`timeline_events` keeps the 28 events and means events. A new collection,
`research_corpus`, carries the 1,129 papers and 37 articles in the shape the
candidate feed already uses: `id`, `title`, `authors`, `published_at`,
`source_urls`, `license`, `_provenance`, `content_sha256`,
`salience_tier_by_profile`, `summary`, `reviews`. Descriptions are re-derived
from the arXiv API into `summary`; where the API returns nothing, `summary` is
null rather than a section heading. The six invented fields do not exist in the
new collection. `all_events.json` is frozen byte-for-byte as
`all_events_v1_frozen.json`, kept building and kept checked, with a deprecation
date, until both consumers have migrated.

**Cost** I estimate four to six days: two for the new projection and its
`--check`, one for the abstract fetch and its join, one for the frozen
compatibility feed and its guard, one to two for docs, the glossary entry
`pdoom-data#47` wants, and the consumer notices. **Forecloses** the single
headline number, permanently. **Who agrees** you now; pdoom1 and
pdoom1-website at migration time, not at build time, which is the point of the
freeze. **Downstream** nothing breaks on the day, because nothing changes on the
day. Both consumers move when they choose.

---

    PAGE 8 OF 9

**Why this shape and not another.** I am not inventing it. The candidate feed at
`data/serveable/api/candidates/all_candidates.jsonl` already carries exactly
these fields across 3,434 records, including `salience_tier_by_profile` with A
172 / B 687 / C 1,717 / D 858, and `salience_basis_by_profile` recording the
method that produced each tier. That is the ADR-001-compliant shape, it works,
and `timeline_events` is the last collection in the repository still on the
pre-ADR shape. The proposal is to stop having two shapes rather than to design a
third. It also delivers, for free, the thing pdoom1 asked for in
`pdoom-data#26` and again in its own K1 note: a salience tier on the corpus, so
`_is_flavour_event`'s hardcoded `arxiv*` prefix match in
`event_service.gd:384-388` can be replaced by reading a field.

## 5. Recommendation, and the case against it

**Recommend Option 4, plus A1 executed immediately and independently.**

The case for, in one paragraph. The corpus's problem is not quality, it is
kind, and every option except 4 answers a quality question. The evidence that it
is a kind problem rather than a quality problem is that the good data was
present and was discarded: 1,124 author lists, 1,129 dates, 99 DOIs, all thrown
away to make room for a dice-rolled quote. Option 4 is the only one that returns
those, and it is the only one whose downstream cost on the day is zero, because
freezing the old feed converts a breaking change into a scheduled one. It costs
about the same as Option 1 and leaves the vocabulary correct rather than merely
the schema.

**The case against, which I think is genuinely strong.**

It adds a collection to a repository whose problem is arguably too many
collections, and `pdoom-data#64` records that "record sets: 4" is a live
candidate headline metric. Option 4 makes that metric 5 by doing work, which is
precisely the gaming failure that issue's own text warns about: "Four is also a
number that grows by adding collections, which is a new way to game it." I would
be inflating a metric you are considering adopting, in the same week, and I do
not have a clean answer to that.

Two collections is two producers, two `--check` paths, two schemas and two
deprecation clocks, in a repository that got into this state because one file
had no producer at all. The frozen feed in particular is a liability: a build
output nobody is allowed to change but everybody keeps building, which is a
description of something that rots. Option 3 has none of that; it ends with
fewer moving parts than it started with, and "28 events" needs no footnote,
where "28 events and 1,166 research references" needs one every time.

And the honest version of my confidence: I am recommending building a
bibliography that no consumer has asked for. pdoom1 asked for salience tiers on
events. pdoom1-website renders event pages. Neither asked for
`research_corpus`. I believe it has value, and I have argued that on page 5 from
a sample of 40 titles that I read myself, but that is an inference about future
demand and it is the weakest link in this document. If you think nobody will
ever want the bibliography, Option 3 is correct and Option 4 is five days spent
gold-plating a deletion.

**What would change my mind.** A ruling that the repository's output is the
game's corpus and nothing else. Under that reading the 1,129 papers are pure
cost and Option 3 wins on every axis. I do not think that is your reading -
`pdoom-data#58` says "data platform rather than a corpus" and
`pdoom-data#64`'s comment records "this is the thing that the repo is
differentiated on" about evidence-backed claims - but that is me inferring your
intent from a transcript, and you can overrule it in one word.

---

    PAGE 9 OF 9

## 6. The measurement that would settle it

If you do not want to decide from the above, one measurement discriminates
between Option 3 and Option 4 better than any argument in this document, and it
respects the constraint you named in `pdoom-data#58`, which is your attention
rather than the corpus size.

**Draw 50 of the 1,129 arXiv records at random with a recorded seed, fetch the
real abstract for each from the arXiv API, and rule on each one: "would I want
this in an AI-safety reference corpus - yes, no, unsure."** Attributed, one
named reviewer, using the review tooling that already exists. I estimate 45 to
60 minutes at the pace your existing review passes ran.

That gives a point estimate with a confidence interval on the only quantity that
separates the two options: what fraction of the 1,129 is worth carrying. Above
roughly 50% keep-rate, Option 4 is clearly right and the bibliography is real.
Below roughly 20%, Option 3 is right and I am gold-plating. In between, the
answer is a third thing neither option covers: keep the subset, delete the rest,
and the sample tells you where the bar goes.

It also satisfies both clauses of the check rule as stated in `pdoom1#1075` and
restored by `coordination#5`. The abstracts come from arXiv, which is outside
this system, so the judgement is made on the paper rather than on our damaged
extract of it - which matters, because judging these records on the descriptions
we currently publish would be judging our own extraction failure and calling it
a corpus failure. And the sample is drawn from the record list, not from
anything the current projection decided, so it cannot inherit the projection's
selection.

I can prepare the sample, the fetch and the review sheet without any ruling on
Options 0 through 4. Say the word and it is ready before you sit down to it.

## 7. Defects found, reported and not fixed

Per the brief, I fixed nothing. Five things want issues, and I will file them on
a yes to A1 or on request.

**One.** Four records publish live email addresses. `redact_emails.py:73-74`
cannot match an address containing whitespace, which is the normal output of PDF
extraction. Ids on page 1. This is the highest-urgency item in this document and
the only one I would act on before Monday if you would rather I did not wait.

**Two.** `transform_enriched.py:201` uses `encode('ascii', 'replace')`, the `?`
fallback CLAUDE.md forbids by name. 44 records damaged, 96 occurrences, 3 titles.

**Three.** `transform_enriched.py:255` defaults `year = 2020` when
`date_published` is absent, which is a guessed date and against the standing
rule. It happens to bite nothing today because the dump has a date on all 1,129
records, but it is a loaded gun in a producer.

**Four.** 12 records carry a `year` earlier than their own arXiv identifier's
posting month. Inherited from the upstream StampyAI dataset, not introduced
here, and never checked against the second source that was sitting in the same
record.

**Five.** `pdoom1-website` has no cardinality guard of any kind on this feed.
`minProperties: 1`, no count floor in `sync-events.py`, alert only on
`failure()`. Whatever you decide, a floor belongs there before anything in this
document is executed, and it belongs in the consumer rather than here, because a
producer cannot check its own output count against a consumer's expectation
without violating the second clause of the check rule.

## Reading list, if you want to check me

    data/serveable/api/timeline_events/all_events.json    the corpus
    scripts/build/project_timeline_events.py              the producer, --check
    scripts/enrichment/transform_enriched.py:130-260      where the fabrication is
    scripts/privacy/redact_emails.py:73                   the pattern that missed
    config/schemas/event_v1.json                          the contract it fails
    data/raw/alignment_research/dumps/2025-12-24_063313/  what was thrown away
    data/serveable/api/candidates/all_candidates.jsonl    the shape to copy
    pdoom1/godot/autoload/event_service.gd:14-16,384-412  vendored, and the gate
    pdoom1/docs/decision-cards/2026-08-02_pdoom-data-contract.md:159-170
    pdoom1-website/scripts/sync/sync-events.py:77,665-697
    pdoom-data#65, #64, #51, #47, #34, #26, #58
