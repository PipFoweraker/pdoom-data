# corpus_review

Human judgements about whether individual bulk records are worth carrying.
Curated zone: **not reproducible**. Delete it and someone has to decide again.

## The one question

    Would you want this paper in an AI-safety reference corpus?

It is the only question asked, and the reason it is the only one is worked out
in `docs/design/REVIEW_THE_BULK_2026-08-19.md` section 1. The other three
candidate questions about the 1,166 bulk records are not for a human:
description quality is a defect in our own extractor, schema conformance is one
key and one empty array, and belonging in `timeline_events` is one ruling
rather than 1,166.

The question is stored **verbatim** in `frame.json` and again on **every row**
of `verdicts.jsonl`. A verdict whose question has to be reconstructed from
context is not evidence of anything.

## The four answers, and the fifth state that is not an answer

| value | means |
|---|---|
| `yes` | worth carrying |
| `no` | not worth carrying |
| `unknown` | looked at it and could not tell |
| `skip` | deliberately passed over without judging |
| *(no row at all)* | **NOT YET REVIEWED** |

`unknown` and `skip` are stored as themselves and are never folded into `no`,
never folded into each other, and never folded into absence. A paper outside
the reviewer's field is an honest `unknown`, and how many there are is a
finding rather than a gap.

**Not-yet-reviewed is an absence, never a value.** Nothing writes a token
meaning "unreviewed", because a token can be read as a judgement and an
absence cannot. Any consumer of this directory must treat a missing record as
missing rather than as a soft no.

`retracted` appears in the log and is not an answer either. It is an undo: it
removes a record from the state projection, returning it to NOT YET REVIEWED,
while leaving both the original judgement and the retraction in the log.

## Layout of one pass

    <pass_id>/frame.json      the sample frame. Written BEFORE anything was
                              fetched and before any key was pressed: the seed,
                              the population and its exclusions, n, the drawn
                              ids, and the question. A frame chosen after
                              seeing verdicts is not a frame.
    <pass_id>/verdicts.jsonl  APPEND-ONLY, one row per keypress. The source of
                              truth. Rows carry `target`, `body`, `creator`,
                              `created`, `motivation` -- field names copied
                              verbatim from W3C Web Annotation per ADR-008 --
                              plus the previous value, so revisions survive
                              rather than overwrite.
    <pass_id>/state.json      a PROJECTION of the log, last row per target
                              wins. Safe to delete; rebuilt on the next
                              keypress. Never edit it: the log is the record.

Log before state, always. In the 2026-08-14 art review 394 of 470 judged
assets were later found orphaned from the state file, and the 470 claim
survived only because it was counted from the append-only log.

Every row carries `creator` and a `created` stamp **with an explicit UTC
offset**. ADR-001 forbids anonymous verdicts and `--by` is required, so there
is no path that produces an unattributed row.

## Running a pass

    # machine time, no ruling required, sets no human field
    python scripts/review/prepare_corpus_review.py --n 150 --seed 20260824

    # the sitting
    python scripts/review/serve_corpus_review.py --by "Your Name"

    # counts, at any time, writing nothing
    python scripts/review/serve_corpus_review.py --summary

The abstracts the reviewer reads are fetched from arXiv into
`data/raw/arxiv_abstracts/dumps/<timestamp>/`, whose `data.jsonl` is gitignored
like every other raw dump and re-fetchable from the seed in `frame.json`. They
come from arXiv rather than from our own record on purpose: `pdoom1#1075`
clause 2 says do not derive what to look for from the system you are checking,
and our published `description` for these records is unparsed PDF text.

## What a pass does NOT do

It writes nothing to `data/serveable/`, nothing to `all_events.json`, and no
per-record field on any bulk record. `check_maturity.py` refuses
`{salience, importance, rarity, score, tier, quality, verdict, rating,
pdoom_impact}` as bare opinions by name, and adding one here would move the
collection away from gold while looking like an improvement. The judgements
live here, joined by id, and ADR-008's test applies: delete every one of them
and the dataset is still complete and correct.

A pass of n records supports a claim about the population with an interval on
it. It does not support "the corpus has been reviewed". Those are different
sentences and only the first one is paid for.
