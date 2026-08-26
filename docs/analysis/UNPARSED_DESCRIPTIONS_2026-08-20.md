# The 1,166 unparsed descriptions: triage, what is retrievable, and what to say

    TO          Pip, as architect
    FROM        pdoom-data seat
    DATE        2026-08-20
    DECISION    Five asks on page 1. Nothing was fixed. No data zone was written.
    STATUS      condition: measured | attention: needs a ruling on C1 and C3
    SUPERSEDES  nothing. Sits beside docs/design/REVIEW_THE_BULK_2026-08-19.md,
                which asked whether the 1,166 are worth carrying. This one asks
                what it would cost to make them legible, which is a different
                question and mostly a cheaper one.
    PAGE 1 OF 7

## Core message

The 1,166 bulk records are damaged in five distinct ways, not one, and the split
matters because they have different cures and wildly different costs. **1,003 of
them carry a section heading where a summary should be. 111 carry the first page
of a PDF, truncated mid-word. 22 carry the title back to you with a prefix. 13
carry a stylesheet. 17 are something else, and only 13 records in the whole 1,166
- one percent - carry a description a reader would call adequate.**

The good news is unambiguous and it is the finding that should change the plan.
**Nothing is lost. All 1,129 arXiv records carry a well-formed, unique arXiv
identifier in their source URL, and all 37 Distill records carry a unique live
URL. Zero records have no route back.** Eight arXiv identifiers were fetched from
the public API and eight returned real abstracts of 834 to 1,558 characters, real
titles, real posting dates and a primary category. Four Distill URLs were fetched
and four returned HTTP 200 with structured front matter carrying a description.

The second piece of good news is the licence, and it is the opposite of what I
expected going in. arXiv's own API terms of use say, verbatim, *"You are free to
use descriptive metadata about arXiv e-prints under the terms of the Creative
Commons Universal (CC0 1.0) Public Domain Declaration"*, and the footnote defines
descriptive metadata as *"fields such as title, abstract, authors, identifiers,
and classification terms"*. **Abstracts are CC0. The ShareAlike exclusion in
ADAPTER_SPEC does not bite here**, because the per-paper licence - which does
vary, and six of eight sampled were arXiv's non-exclusive-distribute rather than
Creative Commons - governs the e-print, not the metadata. Distill's own reuse
notice says *"Diagrams and text are licensed under Creative Commons Attribution
CC-BY 4.0"*. Neither source needs the link-and-summarise fallback.

The cost is also smaller than the last document assumed. The arXiv API accepts
batched identifier lists: **one request returned five abstracts, so 1,129 records
is roughly twelve requests and under a minute of wall clock at arXiv's own
one-request-per-three-seconds limit**, not the hour estimated on 2026-08-19. That
changes the shape of the argument for sampling: the fetch is no longer the
expensive part of anything.

## The asks

| # | Ask | YES | NO |
|---|---|---|---|
| C1 | Run the fetch for all 1,129 arXiv records, not a sample of 100. It is twelve requests and it costs you nothing. | [ ] | [ ] |
| C2 | Treat the fetched metadata as `CC0-1.0` on the strength of the two first-party quotes above, recorded in `config/sources.json` with evidence. | [ ] | [ ] |
| C3 | Fix `generate_description()` in `scripts/enrichment/transform_enriched.py` before re-projecting anything - it is the `?` fallback CLAUDE.md forbids, shipped and public. | [ ] | [ ] |
| C4 | Delete the fabricated `safety_researcher_reaction` and `media_reaction` on the 1,166, rather than repairing them. See page 6. | [ ] | [ ] |
| C5 | Do not repair descriptions in place until `pdoom-data#65` / ask A3 rules on whether these records belong here at all. | [ ] | [ ] |

C1 and C2 are unblocked today. C3 is a code fix with a one-day cost. C4 is the
only one that changes what a consumer sees, and it is a deletion. C5 is a
constraint, free to say yes to now and expensive to discover later.

---

    PAGE 2 OF 7

## 1. The triage, enumerated

Full enumeration of all 1,166 bulk records, not a sample. Categories are assigned
by one classifier with an explicit precedence order, so the counts sum exactly.
The classifier is reproduced on page 7.

| # | Category | Count | arXiv | Distill | What it actually is |
|---|---|---:|---:|---:|---|
| 1 | Section heading only | 1,003 | 998 | 5 | A setext heading and its underline rule, nothing else. Modal value is the literal string `1 Introduction` followed by fifteen dashes, 756 times. |
| 2 | PDF page dump, truncated | 111 | 111 | 0 | Title block, author list, affiliations, sometimes reaching an abstract, cut at 997 characters plus an ellipsis. Carries PDF layout damage throughout. |
| 3 | Title echoed back | 22 | 16 | 6 | The literal string `Research publication: ` followed by the record's own title, verbatim, in all 22 cases. Zero information beyond the title field. |
| 4 | Markup artifact | 13 | 0 | 13 | A CSS block or an image placeholder captured as prose. Seven are the single string `![](images/multiple-pages.svg)`. |
| 5 | PDF title page, untruncated | 4 | 4 | 0 | Cover-page text short enough to escape truncation. Author names and institution names, no prose. |
| 6 | **Adequate** | **13** | **0** | **13** | The Distill article's own opening paragraph. Complete sentences, informative, correctly the thing a description should be. |
| 7 | Genuinely empty | 0 | 0 | 0 | None. Confirms `dataset_quality.json`. |
| | **Total** | **1,166** | **1,129** | **37** | |

**Adequate is 13 records, 1.1 percent, and every one of them is Distill.** Not one
of the 1,129 arXiv records has a usable description. That is a cleaner and more
damning statement than "82.8 percent are under 60 characters", and it is the one
to use.

### Reconciling with the published figure

`api/meta/dataset_quality.json` reports 989 descriptions under 60 characters
corpus-wide. That is consistent with the table and the join is exact: of the 989,
**977 are section headings, 7 are markup artifacts and 5 are title echoes.** The
published figure is right and should keep being quoted, but note that it
*undercounts* the heading damage: **26 section headings are 60 characters or
longer** and so are invisible to a length threshold. Length was a good proxy and
it is 97 percent accurate here; the structural classifier is the better one.

## 2. What is actually wrong, in one line of code

The cause is not mysterious and it is not upstream. It is
`scripts/enrichment/transform_enriched.py`, lines 191 to 208:

    description = record.get('abstract', '')
    if not description:
        text = record.get('text', '')
        paragraphs = text.split('\n\n')
        description = paragraphs[0] if paragraphs else text[:500]
    description = description.strip()
    description = description.encode('ascii', 'replace').decode('ascii')
    if len(description) > 1000:
        description = description[:997] + '...'
    if len(description) < 20:
        description = f"Research publication: {record.get('title', 'Unknown')}"

Every category in the table above is a branch of that function. The `abstract`
key is never present, so every record falls through to the first paragraph of
extracted PDF text, which for an arXiv PDF converted to markdown is the first
heading. The 111 are the branch where the first paragraph was long. The 22 are
the under-20-characters branch. The 13 markup artifacts are Distill articles whose
first block is a `<style>` element.

---

    PAGE 3 OF 7

**Line 201 is the `?` fallback that CLAUDE.md forbids by name.** The landmine
section says never run `legacy/2025-09_prototype/fix_ascii.py` because its `?`
fallback would shred every tree diagram, and requires an explicit substitution map
that errors on unmapped characters. `encode('ascii', 'replace')` is exactly that
fallback, it is in a shipped enrichment transform rather than a legacy script, and
its output is public. This is the same class of finding as the CLAUDE.md
self-correction on 2026-08-10: the warning was written about the tool nobody runs
while the tool everybody runs did the same thing.

Measured consequences of line 201 alone, across the 1,166:

- **93 descriptions contain a `?` that was a real character**, 7 of them the
  three-character sequence `???` where an em dash used to be.
- **5 titles are shredded.** Not 3. The 2026-08-19 note said 3; the count is 5 and
  all five were confirmed against arXiv rather than inferred. See page 5.
- 48 descriptions carry the literal marker `[email address redacted]`, a leftover
  of the PII redaction pass, served publicly inside a field labelled description.

Two more damage classes that line 201 did not cause, both measured on the same
pass and both absent from all 28 hand-authored records:

- **114 titles end in a spurious full stop.** arXiv titles do not. Confirmed by
  the probe: ours reads `No?regret Learning in Dynamic Stackelberg Games.`, arXiv
  reads `No-Regret Learning in Dynamic Stackelberg Games`.
- **12 titles contain an embedded newline**, a preserved PDF line wrap, for
  example `Towards Automated Circuit Discovery\nfor Mechanistic Interpretability`.

## 3. What is retrievable, and from where

### The route back exists for every record

| Route | Records | Result |
|---|---:|---|
| `sources[0]` is `https://arxiv.org/abs/<id>` and the id parses | 1,129 / 1,129 | 100 percent. All 1,129 ids are distinct; no collisions, no old-style `cs/0701001` forms, no version suffixes. |
| `sources[0]` is a `distill.pub` URL | 37 / 37 | 100 percent, all 37 distinct. |
| No id and no source URL | **0** | Nothing is lost. |

Every bulk record carries exactly one source URL. Not one carries zero, and not
one carries two.

### The arXiv API works, tested on eight

Eight identifiers were fetched from `export.arxiv.org/api/query`, one at a time,
three seconds apart, with an honest User-Agent naming the repository and a contact
address. Chosen deliberately: the five suspected shredded titles and two of the
twelve impossible years, so the probe doubles as a check rather than only a
capability test.

**Eight of eight returned `OK`** with an abstract of 834 to 1,558 characters, a
title, a `published` timestamp, an `updated` timestamp and an
`arxiv:primary_category`. A ninth request with five identifiers in one `id_list`
returned all five in 14,126 bytes, so batching works and the per-entry cost is
about 2.8 KB.

**Cost of the full arXiv fetch, derived from measurement rather than guessed:**
1,129 identifiers at 100 per request is 12 requests; arXiv's terms require no more
than one request every three seconds on a single connection, so **36 seconds of
wall clock and roughly 3.2 MB**. At a more conservative 50 per request it is 23
requests and 70 seconds. The 2026-08-19 estimate of "an hour of machine time" is
high by two orders of magnitude, and that is the fact that undercuts the sampling
argument: the fetch was never the expensive part.

---

    PAGE 4 OF 7

One implementation trap, observed: **`id_list` does not preserve order.** The
five-id request returned them shuffled. Join on the identifier in each entry's
`<id>` element, never on position.

### The licence, read first-party, and it is better than feared

ADAPTER_SPEC rule 1 says the SPDX must be read from a first-party page and never
inferred, so two pages were read.

`https://info.arxiv.org/help/api/tou.html`, under "Things that you can (and
should!) do", verbatim:

> Retrieve, store, transform, and share descriptive metadata about arXiv e-prints.

and, in the terms proper:

> You are free to use descriptive metadata about arXiv e-prints under the terms of
> the Creative Commons Universal (CC0 1.0) Public Domain Declaration.

with footnote 1, verbatim:

> Descriptive metadata includes information for discovery and identification
> purposes, and includes fields such as title, abstract, authors, identifiers, and
> classification terms.

`https://info.arxiv.org/help/license/index.html`, under "Metadata license":

> A Creative Commons CC0 1.0 Universal Public Domain Dedication will apply to all
> metadata.

The prohibition is narrow and does not touch us: *"Store and serve arXiv e-prints
(PDFs, source files, or other content) from your servers"*. We would store the
abstract, which the footnote names as metadata, and we would not store the PDF.

**So the SPDX for a fetched-abstract dump is `CC0-1.0`, not the paper's own
licence.** This matters because the paper's own licence is genuinely mixed and
would have been a problem. Eight per-paper licences were read from arXiv's
OAI-PMH interface, which exposes a `<license>` element the Atom API does not
carry at all: **six of eight were `http://arxiv.org/licenses/nonexclusive-distrib/1.0/`
and two were CC BY 4.0.** arXiv offers CC BY-SA 4.0 as one of four submission
options, so some of the 1,129 certainly carry it, and had the abstract been
governed by the e-print licence, `validate_candidate()` would have been right to
refuse the dump. It is not, so it will not, and no per-record licence lookup is
needed. Record the CC0 evidence once, per source, with the two quotes above.

### The local dumps do not help, and this settles an open question

The 2026-08-19 note flagged a contradiction it could not referee: the
2025-12-24 dump's `_metadata.json` lists `abstract` among `fields_extracted`,
while the corpus proposal says no dump carries an abstract. Both surviving dumps
were opened and counted.

| Dump | `data.jsonl` | Records | Carry `abstract` | Join to the 1,166 |
|---|---|---:|---:|---:|
| `2025-11-06_103900` | present | 100 | **0** | **0** |
| `2025-11-06_104039` | present | 1,000 | **0** | **0** |
| `2025-12-24_063313` | **absent** | - | - | - |

All 1,100 present records are `source: alignmentforum`. **`fields_extracted` is a
statement of intent, not of content: no record in either dump has an `abstract`
key at all, and neither dump joins to a single one of the 1,166 served records.**
The corpus proposal was right and the dump metadata is wrong. The fetch is
necessary, and the dump metadata should be corrected or annotated so the next
reader does not spend the same half hour.

---

    PAGE 5 OF 7

## 4. Confirming the two claims carried over from 2026-08-19

Both bear on these records, so both were re-derived independently rather than
copied.

**Twelve impossible years: CONFIRMED, exactly 12.** Defining impossible as the
record's `year` being strictly earlier than the year encoded in its own arXiv
identifier - a paper cannot be dated before it was posted - the count is 12 of
1,129. All twelve are listed on page 7. Two were checked against the arXiv API,
which is an input from outside this system: `1802.05250` was published 2018-02-14
and our record says 2016; `2005.10297` was published 2020-05-20 and our record
says 2017. A further 28 records carry a `year` *later* than their identifier's
year, which is not impossible - a journal version or a revision explains it - and
those are deliberately excluded from the 12.

**Three shredded titles: REFUTED. The count is five, and all five were verified
against arXiv rather than judged by eye.**

| Ours | arXiv | What the `?` replaced |
|---|---|---|
| `Parametric Bounded L?b's Theorem ...` | `Parametric Bounded Lob's Theorem ...` (o-umlaut) | U+00F6 |
| `Action-Conditional $?$-VAE ...` | `Action-Conditional $(beta)$-VAE ...` | Greek small beta |
| `No?regret Learning in Dynamic Stackelberg Games.` | `No-Regret Learning in Dynamic Stackelberg Games` | a dash, plus a spurious full stop and a case change |
| `... in the Machiavelli?Benchmark` | `... in the MACHIAVELLI Benchmark` | a space, plus an injected newline |
| `Inverse Scaling: When Bigger Isn?t Better` | `Inverse Scaling: When Bigger Isn't Better` | a typographic apostrophe |

39 titles contain a `?` in total. The other 34 read as genuine question marks -
`"Why Should I Trust You?"`, `When Will AI Exceed Human Performance?` - and were
not fetched. The honest statement is therefore **five confirmed shredded, 34
believed genuine and unverified**, not "five of 39".

Note the second-order damage the table exposes: two of the five carry a *second*
defect the `?` hid, a trailing full stop and an injected newline. Repairing only
the `?` would leave both.

**A third claim, offered as a correction rather than a confirmation.** Four of the
37 Distill records have a `year` that disagrees with the year in their URL path -
all four are Circuits-thread articles at `distill.pub/2020/circuits/...` published
in 2021. The URL prefix names the thread, not the article. **These are not
errors** and should not be added to any defect count.

## 5. Recoverability, per category, with mechanism and cost

"Review time" below means human minutes. It is zero for every category except the
one where the question is editorial, and that is the whole point of the table.

| # | Category | n | Recoverable | Mechanism | Requests | Review time |
|---|---|---:|---|---|---:|---|
| 1 | Section heading | 1,003 | Yes, fully | Fetch abstract by id; substitute | ~10 (batched, shared) | 0 |
| 2 | PDF dump, truncated | 111 | Yes, fully | Same fetch; the real abstract replaces the page scrape entirely | shared | 0 |
| 3 | Title echo | 22 | Yes, fully | Same fetch for the 16 arXiv; page fetch for the 6 Distill | shared + 6 | 0 |
| 4 | Markup artifact | 13 | Yes | Distill front-matter `description` and `<d-abstract>` | 13 | 0 |
| 5 | PDF title page | 4 | Yes, fully | Same fetch | shared | 0 |
| 6 | Adequate | 13 | N/A - already good | Leave alone; strip the `???` mojibake | 0 | 0 |
| 7 | Empty | 0 | - | - | 0 | 0 |
| | **Total** | **1,166** | **1,153 repairable, 13 already fine, 0 lost** | | **~12 arXiv + 37 Distill** | **0** |

**Every category is machine-recoverable and none of it needs a human reader.**
That is the honest answer to "how much of this is fixable", and it is why this
document's asks are mostly about sequencing rather than resourcing.

---

    PAGE 6 OF 7

The two caveats that keep that number honest. First, **the 100 percent is on the
route, not on the retrieval**: 8 of 8 arXiv identifiers and 4 of 4 Distill URLs
resolved, which is a probe and not a census. Withdrawn papers and dead links will
exist. The expected shortfall is small and it is not knowable without the fetch,
so it should be reported as a count after Phase 1 rather than estimated now.
Second, **abstracts contain non-ASCII** - the very first probe returned
`Lob's theorem` with an o-umlaut - so the ASCII gate applies to the repair as much
as it applied to the damage, and the repair must use an explicit substitution map
that errors on unmapped characters. Reaching for `encode('ascii', 'replace')`
would reproduce the original defect exactly, in a commit whose message says it is
fixing it.

## 6. The thing next to the descriptions that is worse than the descriptions

While enumerating, one field pair was measured that nobody has asked about and
that changes what the funding page can honestly claim.

`generate_reactions()`, twelve lines below `generate_description()`, seeds
`random` on the record id and picks from a hardcoded list. So every one of the
1,166 records carries a `safety_researcher_reaction` drawn from five canned
strings and a `media_reaction` drawn from six. Measured on the served file: **five
distinct safety reactions across 1,166 records, and 363 arXiv preprints publicly
asserting `media_reaction: "Peer-reviewed publication"`.**

arXiv is a preprint server. 363 records claim peer review that did not
necessarily happen, in a field that reads as editorial commentary, attributed to
nobody, generated by a seeded random number generator. **Zero of the 28
hand-authored records are affected.** By ADR-001's own operative test this is not
a borderline case: a consumer who disagreed would have to fork. It is also
squarely the `#34` breach, and it is worse than the descriptions because a broken
description is visibly broken while `"Peer-reviewed publication"` is plausible,
which is the transcoding lesson from `coordination#10` in a different costume.

The cure is not a better generator. It is C4: delete both fields on the 1,166.
That is a one-line change in the projection, it needs no fetch, it needs no
ruling on whether the records belong, and it removes a false public claim today.

## 7. The phased plan, cheapest first

**Phase 0 - now, zero cost.** This document, plus an issue carrying the table on
page 2. Do not touch `data/serveable/`. If anything is regenerated, it is
`dataset_quality.json` through its existing producer
`scripts/analysis/dataset_quality.py`, adding the structural counts beside the
length counts - one producer, already gated, no second writer.

**Phase 1 - the fetch. 12 requests, 36 seconds, no ruling required.** An adapter
per ADAPTER_SPEC writing one immutable dump to
`data/raw/arxiv_metadata/dumps/<UTC timestamp>/` with `data.jsonl`, `raw.jsonl`,
`_metadata.json` and `MANIFEST.sha256`. Licence block `CC0-1.0` with the two
first-party quotes as evidence and `verified_at: 2026-08-20`. Half a day of
engineering, then it never needs doing again. **Nothing downstream changes.**

**Phase 2 - the free check, and it is free because Phase 1 already paid.** Join
the fetched titles and dates to the served records and report disagreements. This
independently tests the 12 impossible years, the 5 shredded titles, the 114
trailing full stops and the 12 embedded newlines against an input from outside
this repository, satisfying both clauses of `pdoom1#1075`. Machine only, no
writes, and it delivers a correction list whether or not anyone ever presses a
key. **Phases 1 and 2 together are the cheapest useful thing and they are
unblocked today.**

---

    PAGE 7 OF 7

**Phase 3 - the relevance sample, which is `REVIEW_THE_BULK`'s ask B1 and is now
cheaper than it was.** Because Phase 1 fetched all 1,129 rather than 100, the
`primary_category` axis exists for free, so the sample and the category batch pass
are no longer alternatives. 13 to 42 minutes of your time, per that document's
estimate, which this one does not contest.

**Phase 4 - delete the fabricated reactions.** C4. One line in
`scripts/build/project_timeline_events.py`, plus a `--check` run. Independent of
everything above and of ask A3. If only one thing on this page happens, this is
the one with the best ratio of harm removed to effort.

**Phase 5 - repair the descriptions in place.** Fix `generate_description()`
first (C3: explicit substitution map, error on unmapped, no `?` fallback), then
re-project through the single existing producer. **This is the phase that must
wait**, because a NO on ask A3 deletes these records and throws the work away.
One day of engineering, zero review minutes.

**Phase 6 - the 37 Distill records, separately.** Different licence (CC BY 4.0,
attribution required, so the record must carry it), different structure (front
matter JSON with a `description`, plus `<d-abstract>`), different failure mode
(stylesheets and image placeholders rather than PDF scrape), and 13 of the 37 are
already fine and must be left alone. 37 page fetches, but Distill pages are large
- one measured at 3.9 MB - so budget tens of megabytes and fetch politely. One
caveat found on the pages themselves: the CC BY 4.0 notice is qualified by
*"unless noted otherwise. The figures that have been reused from other sources
don't fall under this license"*, and two of the four sampled pages carried
CC-BY-NC and CC-BY-SA strings for individual figures. Text only, and the
qualification goes in the licence block.

## What the funding page should say

The one paragraph this document exists to produce.

> The honest version is short and it is stronger than the vague one. Say that the
> collection holds 1,194 records, that 28 were written by hand and 1,166 were
> imported in bulk from arXiv and Distill in late 2025, and that **the import
> captured the wrong text: only 13 of the 1,166 carry a description a reader would
> call adequate, and 1,003 carry a section heading - most often the literal words
> "1 Introduction" - where a summary should be.** Then say the part that makes it
> a maintenance job rather than a confession: **nothing is lost. Every one of the
> 1,166 records carries a working link back to its source, the abstracts are
> available under CC0, and the fetch is about twelve API requests.** The work the
> money pays for is not re-collecting the data; it is the judgement that follows -
> deciding which of these papers belong in an AI-safety reference corpus at all,
> which is roughly six hundred editorial decisions no script can make - plus the
> engineering to repair a text pipeline that has been silently replacing
> characters it could not encode with question marks, and the removal of
> auto-generated commentary that currently tells 363 preprints they were
> peer-reviewed. Do not claim the corpus is reviewed, because it is not; claim
> that the defects are measured, published at
> `data/serveable/api/meta/dataset_quality.json`, and individually costed.

Two notes on what that paragraph deliberately does **not** do. It does not quote
the 82.8 percent figure, because "82.8 percent of descriptions are under 60
characters" invites the reply that short is not the same as broken; "13 of 1,166
are adequate" cannot be read down. And it does not promise a fixed corpus, because
ask A3 is unruled and the corpus may be deleted rather than repaired - which is a
legitimate outcome and a funding page that has promised repair cannot take it.

## How this was measured

Read-only throughout. **Nothing was written to `data/serveable/`, `data/raw/`,
`data/curated/` or `data/enrichment/`.** Scripts and probe output live in a
scratchpad outside the repository. Network use was 8 single-id arXiv Atom
requests, 1 five-id Atom request, 8 arXiv OAI-PMH licence requests, 3 arXiv
help-page reads and 5 Distill page reads, each at least 3 seconds apart, with
User-Agent `pdoom-data-triage/0.1 (+https://github.com/PipFoweraker/pdoom-data;
pip@beacongcr.org)`. That is 25 requests total, no bulk download.

The classifier, in precedence order, applied to every one of the 1,166:

    empty              description strips to nothing
    markup             starts with '![' or '<', or contains a CSS declaration
    heading            1 to 3 short lines followed by a rule of 3+ '-' or '='
    title echo         starts with 'Research publication: '
    pdf truncated      ends with '...'
    other              everything else, all 17 of which were read individually

Counts of derived defects were taken with independent one-line passes rather than
by reusing the classifier, per `pdoom1#1075` clause 2. Description length figures
reconcile to `dataset_quality.json` exactly (989 = 977 + 7 + 5) and are not a
second measurement of the same thing.

The twelve records whose `year` precedes their arXiv identifier's posting month:

    arxiv_f2ac3447dea6aeca  year 2016  arxiv 1802.05250  (published 2018-02-14, verified)
    arxiv_7065ba6b881fd64f  year 2017  arxiv 1802.01636
    arxiv_0e8afc013c84e4e7  year 2017  arxiv 2005.10297  (published 2020-05-20, verified)
    arxiv_eb789c40c7c9d84c  year 2018  arxiv 1901.10513
    arxiv_0f27b954a6dd7471  year 2018  arxiv 1901.00064
    arxiv_b9a647ad554c990a  year 2019  arxiv 2001.00496
    arxiv_1405aec1edf8be7e  year 2019  arxiv 2002.00941
    arxiv_117d259472867be5  year 2019  arxiv 2003.01709
    arxiv_44744bf31057f3d2  year 2019  arxiv 2002.04833
    arxiv_1eda22f5f61402fa  year 2019  arxiv 2001.00078
    arxiv_dfe1a69ce0a50944  year 2019  arxiv 2001.00463
    arxiv_673f5a66b8253c07  year 2020  arxiv 2101.07691

## Where I am least confident

**The retrieval rate is a probe, not a census.** 8 of 8 and 4 of 4 is encouraging
and it is not 1,166 of 1,166. Withdrawn arXiv papers exist. Report the real number
after Phase 1 and do not let this document's "nothing is lost" harden into a claim
about retrieval when it is a claim about routes.

**I have not proven that a fetched abstract makes a good game description.** An
arXiv abstract is 800 to 1,500 characters of dense technical prose. It is
unambiguously better than `1 Introduction`, and it may still be the wrong shape
for whatever consumes this. That is a separate question from whether the data is
recoverable, and I have only answered the second.

**The category boundary between 1 and 5 is mine.** Four records were placed in
"PDF title page, untruncated" rather than "heading" or "PDF dump" by reading them.
A different reader might place them differently. The count is 4, so it cannot move
any conclusion, but it is the one place in the table where judgement entered.

## Reading list

    docs/design/REVIEW_THE_BULK_2026-08-19.md     the selection chain, asks B1-B6
    docs/CORPUS_PROPOSAL_2026-08-09.md            asks A1-A6, still unticked
    docs/ADAPTER_SPEC.md                          licence block, four clocks, dump layout
    data/serveable/api/meta/dataset_quality.json  the canonical counts
    scripts/enrichment/transform_enriched.py      lines 191-241, the cause
    scripts/build/project_timeline_events.py      the one producer, --check
    https://info.arxiv.org/help/api/tou.html      CC0 metadata, rate limits
    https://info.arxiv.org/help/license/index.html  per-paper licence options
    pdoom-data#65, #58, #34, #26
