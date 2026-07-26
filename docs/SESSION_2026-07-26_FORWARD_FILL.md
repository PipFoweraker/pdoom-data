# Session: Forward-fill campaign and ingestion architecture

**2026-07-25 to 2026-07-26.** Merged to main as PR #28 plus follow-ups.

Starting state: repo dormant seven months, all four CI workflows failing, the
2023-2026 window holding 46 events against 200-224/year for 2018-2021, and the
game's playable range running out around 2019.

---

## 1. What the numbers actually were

The headline "1,194 events" decomposed on inspection:

| Measure | Value |
|---|---|
| Events in `all_events.json` | 1,194 |
| Of which hand-authored | **28** |
| Of which bulk arXiv/Distill imports | **1,166** |
| Distinct impact vectors | 30, but 1,129 records share one |
| Distinct `safety_researcher_reaction` strings | 33; top three cover 715 records |
| Records with exactly one source URL | 1,168 |

Descriptions on the imported records are unparsed PDF text with broken
ligatures and mojibake. The corpus was 28 curated events plus a paper dump
wearing an event costume.

**The A/B/C/D tier system was inverted.** Its scoring config weights
`source_arxiv: 3`, `has_authors: 1`, `text_length_5k: 1` and similar -- every
term measures provenance or length, none measures importance. "A-tier"
therefore decodes as *long arXiv paper with named authors*, which is exactly
why the `hist_arxiv` deck floods the game feed (pdoom1 issue #630). Issue #26
asked us to expose that field; doing so would have handed the game a filter
whose high values mean least salient.

---

## 2. What was built

**3,434 candidate records**, roughly **700 per year for 2023-2026** against a
target of 300-400, plus 670 backfilled pre-2023.

| Source | Records | Licence |
|---|---|---|
| Epoch AI notable models | 1,034 | CC-BY-4.0 |
| LessWrong, top 300/year | 1,200 | metadata + link only |
| EA Forum, top 300/year | 1,200 | metadata + link only |
| MIT AI Risk Repository | taxonomy + 2,574 labelled rows | CC-BY-4.0 |

Supporting architecture: adapter framework with mechanical licence
enforcement, source registry with evidence-backed availability dates, salience
profiles, attributed human review layer, a risk-domain tagger with measured
accuracy, a keyboard-driven review tool, and an invariants checker.

### Risk-domain coverage of the corpus

    1051  33.5%  7. AI System Safety, Failures, & Limitations
     618  19.7%  6. Socioeconomic and Environmental
     465  14.8%  2. Privacy & Security
     340  10.8%  5. Human-Computer Interaction
     279   8.9%  1. Discrimination & Toxicity
     238   7.6%  4. Malicious Actors & Misuse
     144   4.6%  3. Misinformation
     299   8.7%  untagged / abstained

Thin domains are the honest ingestion targets: Misinformation, Malicious
Actors, Discrimination. Worth noting the shape reflects *our sources* (two
rationalist-adjacent forums and a model database), not the field. A corpus
built from incident databases and policy trackers would tilt the other way.

---

## 3. Decisions, and the reasoning behind them

**Serveable is a projection, not a file you edit.** The repo lost this
property and paid for seven months: `manifest.json` said 28 events while
`all_events.json` said 1,194, because two producers wrote to the same zone and
nothing rebuilt or compared. `--check` now asserts it.

**Facts and opinions are structurally separate.** The operative test: *if
another consumer disagreed with this value, would they have to fork the data,
or could they just ignore a field?* Fork means wrong side of the boundary.
Hence no bare `salience` (it is a weighting choice, namespaced by profile) and
no `game_facing` flag (promotion is the consumer's call).

**Opinions are attributed, which enables inheritance as much as elision.**
Pip's framing: someone may be glad to inherit a human-eye value judgement
cheaply. Attribution makes inherit / filter / ignore all first-class.

**Four clocks, two gates.** `published_at` gates whether a fact is knowable;
`source_available_at` gates whether a dataset is available as an instrument.
Merging them hides every pre-2024 model release from every pre-2024 player,
because Epoch's database postdates AlphaGo by eight years. This fell out of a
test that returned zero visible records and looked like a bug in the data
before it turned out to be a bug in the question.

**Never guess a date.** Every entry in `config/sources.json` carries evidence
naming what was read, and a confidence rating that states its own weakness.
EA Forum is pinned to year start and is therefore early by up to eleven
months; the file says so.

**ShareAlike excluded mechanically, not by memory.** `validate_candidate()`
refuses any dump whose SPDX contains `-SA`. The concrete casualty is AIAAIC;
the escape hatch is link-and-summarise.

**Privacy via tombstone.** Raw dumps are immutable with exactly one exception.
Tombstones record id, date and reason category, never content, so the audit
trail survives the erasure. This is the classic erasure-versus-audit-log
problem and the standard resolution.

---

## 4. Bugs found, and what found them

| Bug | Consequence if unfixed | What surfaced it |
|---|---|---|
| No `.gitattributes` rule for `.jsonl` with `core.autocrlf=true` | Every dump checks out CRLF on a fresh clone; every `MANIFEST.sha256` verification fails on any other machine | A git warning during staging |
| `slugify()` stripped trailing `+` | PointNet++ and PointNet shared an id; a consumer keying by id loses one, a review lands on the wrong record | Tagger classified 3,135 records but wrote 3,133 tags |
| `"ai" in text` substring match | Matched "training", "domain", "explain"; topical relevance was near noise | Inspecting a skewed tier distribution |
| Percentile within group | Top member of any group scores 1.0; a 2001 decision-tree model outranked Alignment Faking | Sanity-checking the A band |
| `clean_events.py` ran on any invocation | Rewrote `all_events.json` from 1,194 to 28 | Audit agent ran it and had to `git restore` |
| Rebuild-idempotence claim | Documented but false; `LINEAGE.json` carries a wall-clock stamp | Testing the claim instead of asserting it |

**The pattern**: every claim that got measured turned out to be slightly
wrong. Nothing was caught by reading the code. Cross-checking two counts that
should agree found the id collision; running the idempotence claim found it
overstated; evaluating the tagger found the accuracy honest but the
distribution shift severe.

`scripts/validation/check_invariants.py` now encodes these as assertions.

---

## 5. Human review: the first pass

206 decisions in 20.6 minutes: **600 decisions/hour, 408 accepts/hour**. Whole
A band (172) plus 34 of B. 140 accept, 64 unsure, 2 privacy, **0 reject**.

The zero-reject result is not evidence the salience ordering works. It is
consistent with three different explanations -- A-tier really is all plausible,
`unsure` absorbed what `reject` was for, or the key legend was unclear (the
reviewer said as much). Those are indistinguishable from this data. A clean
pass with the improved legend would settle it.

**The important finding was not throughput.** 206 verdicts produced **1 note**.
The reviewer reported "lots of inspiration" that went nowhere, because writing
a note meant pressing `n` and breaking stride. Verdicts are cheap; the design
thinking is the scarce output, and the tool was optimised for the wrong one.

Fixed by inverting the interface: notes mode is now default, every letter
types into the note, and decisions live on punctuation that never occurs
mid-sentence (`` ` `` accept, `\` unsure, `]` reject, `[` privacy). A verdict
commits whatever note is buffered.

The reviewer's single note -- *"I need more context to understand the relevance
of things introduced by this model"* -- diagnosed a real defect. All 38 unsure
model-releases already carried Epoch's `notability_criteria` ("SOTA
improvement", "Highly cited", "Training cost") in `extra`, and the UI never
rendered it. The information needed was present and hidden.

**Reframe worth keeping**: the review pass doubles as a structured tech review
of a decade of the field. That changes what to optimise for -- salience
ordering is right for triage coverage and wrong for comprehension. A
chronological mode would serve the second use much better.

---

## 6. Deliberately not done

**CI remains broken, and that is currently protective.**
`data-pipeline-automation.yml` triggers on `data/raw/**` and runs
`clean_events.py`. Repairing the YAML without simultaneously de-arming the
triggers arms a data-clobbering auto-commit. The fix and the de-arm must land
in the same commit. A full 8-hour mechanical plan exists from an audit pass.

**No tombstones written.** Two privacy proposals came from the review, but the
reviewer described them as exploratory and wants to judge by reading full
text rather than from memory. Tombstoning deletes; it waits for a deliberate
call.

**OpenAlex adapter deferred.** Adding 1,000 more records before measuring
review throughput would have contradicted the argument for measuring first.

---

## 7. Open threads

Tracked as issues. In rough priority:

1. Lens Academy: a third, differently-trained salience opinion.
2. Chronological and thematic queue orderings.
3. Privacy review by full text; widen the screen using what it missed.
4. Mechanical uplift day, with the de-arm ordering constraint.
5. `source_available_at` precision for Epoch and EA Forum.
6. Export profile so pdoom1's resource model leaves the shared schema.
7. OpenAlex citation pass.
8. Test the disagreement-ordering hypothesis against salience ordering.
