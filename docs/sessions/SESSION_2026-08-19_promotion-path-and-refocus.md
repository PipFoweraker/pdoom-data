# Session: the promotion path, and being told to stay in my own repo

**Wed 2026-08-19, pdoom-data seat.** Written to be read later, not now.

---

## The correction that shaped the session

Pip asked, mid-morning: *"this feels like a lot of coordination stuff, are we the
right convo or repo to be doing these things? should we be focused on the things
relating to this repo and then asking others to do other things"*

He was right and it was not marginal. Four agents had just been fired at DKIM,
the walkpack print ledger, the *wa* collector and a website funding page. **None
of the four is pdoom-data's work.** `CLAUDE.md` routes cross-repo ops, printing
and capture to `coordination`, and site and publishing to `pdoom1-website`.

Measured across the whole weekend, the honestly-ours work was the scan payloads,
the claim gate, the watchlist atom layer and the triage writer. The printing,
capture, cards, gallery, strategy, budget and campaigns were not. **This seat did
them because it was the seat in front of him**, which is exactly the failure the
estate register names from the other side: the seats exist on paper and the work
goes to whoever is available.

Two handovers were written and pushed --
`HANDOVER_2026-08-17_to-coordination-seat.md` and `..._to-website-seat.md` --
each saying plainly that agents were already running, that their output would
land uncommitted, and that it is the receiving seat's to review rather than
inherit.

## What was built here afterwards, and it is all in this repo

### The promotion path, and the decision inside it

The Watch mechanic had no output. 93 atoms sat in `data/curated/watchlist/` with
no route to any consumer, which makes a published monthly decision a private
opinion.

**The obvious destination was the wrong one, twice.** `event_v1` *requires*
`impacts`, `rarity`, `pdoom_impact`, `safety_researcher_reaction` and
`media_reaction`, with `additionalProperties: false`, so a record cannot be
partly conformant. Promoting an atom through it means inventing a cash delta and
a rarity tier for a real-world event -- the `#34` breach, multiplied by 93. And
`all_events.json` has exactly one producer, which was hard won: that zone had
none, was hand-edited because it could not be rebuilt, and `clean_events.py` once
collapsed it from 1,194 records to 28.

So accepted atoms serve at **`api/watch/accepted.jsonl`** in a neutral shape:
what happened, when, who said so, who decided. No weightings. A consumer wanting
an event to cost thirty cash computes that itself, which is ADR-001's own test.

**Three gates: a date, a source, a named decider.** Nineteen of the 93 have null
dates on purpose; three are flagged UNVERIFIED. Those can be accepted by you and
still not be servable, and when that happens **the build prints the reason**
rather than dropping them. Proven with two test acceptances, one clean and one
with a null date -- one served, one blocked -- then both reverted, because a
`watch_status` this seat invented is not yours.

It currently serves zero records. That is correct; nothing is triaged.

### A wrong number caught before it was published

A draft funding page carried *"801 of 1,194 event descriptions literally begin
Introduction"*.

Measured: **35 begin with it.** What is true is that **970 -- 81.2 percent --
contain the word somewhere**, a different and weaker claim. **801 is 81 percent
with the decimal lost.** Wrong count and wrong predicate, in the passage a
sceptical funder is most likely to check against a JSON file we publish.

The 989-under-60-characters figure was right: 82.8 percent of the corpus.

So the counts stopped being prose. `scripts/analysis/dataset_quality.py` measures
the served corpus and writes `api/meta/dataset_quality.json`; `--check` fails the
build if it stops matching. Sabotage-tested, gating in `check_all`. It carries
three predicates separately with a note that they are different claims and have
been confused before -- because that confusion is what produced the error.

### The `#34` measurement

The issue argued the case well and nobody had counted it. Posted as a comment.

Four of the five game-facing fields are on all 1,194 records; `pdoom_impact` is
on **seven**. And the impact variables split into two populations that are not
the same problem:

    vibey_doom   1,193     |  ethics_risk  16
    research     1,187     |  cash         15
    papers       1,176     |  reputation   15
                           |  stress       13

The small group tracks the 28 hand-authored records -- real editorial judgement.
The large group is **a template stamped across the 1,166 bulk import**.
`vibey_doom` on an arXiv preprint nobody assessed is not a sensible default; it
is a field with a value in it. `rarity` says the same: **1,076 of 1,194 are
"rare"**, which carries almost no information.

**This makes the ruling cheaper than it looked.** The counter-argument -- that
impacts-in-core keeps pdoom1 zero-build -- applies fully to 28 records and
barely at all to 1,166. A split moving only the templated bulk would remove
`vibey_doom` from the shared artefact while leaving every human judgement where
it is.

There is an accident worth keeping: the Watch collection had to be neutral
*because* `event_v1` would have forced 93 invented rarity tiers. The new
collection could not be conformant without committing the thing `#34` exists to
undo.

## Capture, which is not ours but was urgent

**Every recording from 2026-08-19 is empty.** Five files, 257 bytes each,
byte-identical, valid M4A headers with no audio stream at all. `ffprobe` reports
zero streams. Last capture with real audio is `20260818_221541`.

Same failure shape as the fortnight: the recorder reported success -- a file
appeared, right name, right timestamp, valid header -- while capturing nothing. A
directory listing looks entirely healthy.

Three files were marked **personal** and not processed, in
`~/DeskVoiceRecordings2026/SENSITIVITY.md`, which records classification only --
never content, never quotes. One is a private conversation naming third parties;
75 seconds were sampled before its nature was apparent, the clip was deleted and
no transcript reached disk.

## State at close

All four repos clean and pushed. `check_all` green: 13 gating checks, 8 rebuild.
Two new served collections, both gated.

**Outstanding and genuinely ours:** the scan remainder that the scanners named
but could not reach; the 1,166 unparsed descriptions, which is the
dataset-maintenance job the funding page now describes as having a known size;
and the human review stage for the event pipeline, which the Watch tooling now
half-provides.

**Blocked on you, and cheap:** thirty minutes triaging 93 atoms and ten clearing
66 pull-quotes. Until then `api/watch/accepted.jsonl` serves zero records and
every drafted campaign stays unpostable -- by design, because null is not
consent.
