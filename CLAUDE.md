# CLAUDE.md - context for AI assistants working in pdoom-data

> **Style and reasoning conventions live in `D:\Local_Code\CLAUDE.md`** and are
> already loaded alongside this file. They are deliberately NOT repeated here.
> Until 2026-07-30 this file duplicated 20,867 characters of that preamble
> verbatim -- about 5k tokens paid on every session, for content the model had
> already read. If you are tempted to paste general guidance in here, put it in
> the parent instead.
>
> This file is for what is true about **this repository** and nowhere else.

---

## What this repository is

The data hub for the P(Doom) game ecosystem. It holds historical AI-safety
events and candidate records, the pipelines that shape them, and the schemas
that let other repositories depend on them.

    pdoom-data (here)
        |
        +--> pdoom1-website   PostgreSQL, displays events, game stats
        +--> pdoom1           the game; consumes events, adds its own overrides
        +--> pdoom-dashboard  analytics (dormant since 2025-11)

## The one architectural rule that matters

**Facts here. Opinions attributed. Shaping in pdoom1.**

See `docs/ARCHITECTURE_DECISION_RECORDS.md` (ADR-001). The operative test, and
use it whenever you add a field:

> If another consumer disagreed with this value, would they have to fork the
> data, or could they just ignore a field?
> **Fork means it is on the wrong side of the boundary.**

Consequences you will actually hit:

- No bare `salience`. It is a weighting choice, so it is namespaced by profile:
  `salience_by_profile.default_v1`.
- No anonymous verdicts. Every review names its reviewer.
- No `game_facing` flag. Promotion is the consumer's call.
- No trigger conditions, no event chains, no probability curves. Those are
  pdoom1's.

**Known breach, tracked:** ADR-001 itself says events "are game-ready" with
`impacts` and `rarity` as defaults. That is the wrong side of the line and
#34 tracks moving it to an export profile. Do not add more fields of that kind
meanwhile.

## Zones

    data/raw/          immutable dumps. Re-running an adapter makes a NEW dump.
    data/transformed/  machine-derived only; reproducible by re-running code.
    data/enrichment/   machine-derived enrichment (airr_tags, alignment_research)
    data/curated/      HUMAN JUDGEMENT. Not reproducible. Delete it and someone
                       has to decide again.
    data/serveable/    build output. Byte-identical to a fresh projection.
                       NEVER hand-edit.

Full model, including how this maps onto Raw -> Curated -> Conformed -> Served:
`docs/DATA_ZONES.md`.

## Build and check

Every projection has a `--check` that asserts the committed output matches a
fresh build. Run them before believing anything.

    python scripts/build/project_candidates.py --check
    python scripts/build/project_frontier_labs.py --check
    python scripts/build/project_reviewed.py --check
    python scripts/validation/check_invariants.py
    python scripts/validation/check_workflow_disarm.py

All five run in CI via `.github/workflows/data-integrity.yml`, which is
read-only and therefore safe to have armed.

## Served collections

| Path | What it is |
|---|---|
| `api/timeline_events/all_events.json` | 1,194 events. 28 hand-authored, 1,166 bulk arXiv import whose descriptions are unparsed PDF text. |
| `api/candidates/all_candidates.jsonl` | 3,434 candidates, 2023-2026 forward-fill. Unreviewed unless `review_status` says otherwise. |
| `api/reviewed/all_reviewed.jsonl` | 140 human-accepted candidates, attributed. Not `event_v1` shape; not engine-ingestible without a mapping layer. |
| `api/frontier_labs/all_labs.json` | 46 organisations with founding dates and per-date evidence. |

## Landmines

Each of these is here because it already went wrong once.

**`clean_events.py` rewrites the serveable zone.** It once did so on any
invocation including `--help`, collapsing `all_events.json` from 1,194 records
to 28. It now refuses without `--write` and exits 2. Do not remove that guard,
and do not pass `--write` until the question of which producer is canonical for
the serveable zone is settled.

**Two workflows can commit to the repo and are deliberately de-armed.**
`data-pipeline-automation.yml` and `weekly-data-refresh.yml` run on
`workflow_dispatch` only. Until 2026-07-30 they were inert only because of a
YAML syntax error, which made "fix the broken CI" an instruction that would
have destroyed data. The repair and the de-arm landed together, and
`scripts/validation/check_workflow_disarm.py` now fails the build if either
regains an unattended trigger. Re-arming is a deliberate act: remove the entry
from `DISARMED` in the same commit that arms it.

**The ASCII backlog is CLEARED, 2026-08-10, and the reason it was safe is the
part worth keeping.** Nineteen files failed the gate on box-drawing, arrows and
emoji. This paragraph used to say clearing them would arm `documentation-publish`,
a job that appends to `DEVBLOG.md` with `echo >>` on every push to main so the
file grows without bound.

**That coupling was already dead when this warning was written and the warning
outlived it.** The job was de-armed on 2026-07-30 by being **commented out** --
`.github/workflows/documentation-ci.yml` lines 195-242, which is prose, not YAML.
A commented job cannot run whether the gate above it is red or green, so the red
was protecting nothing. **This is the stale-copy failure this file warns about
two sections below, committed by this file, about itself.** Check the workflow
before trusting a claim about the workflow.

Still true and still load-bearing: **never run
`legacy/2025-09_prototype/fix_ascii.py`**, whose `?` fallback would shred every
tree diagram. The 2026-08-10 clearance used an explicit substitution map that
**errors on unmapped characters**, keeps box-drawing at one ASCII character per
box character so tree alignment survives, and hand-corrected the three Python
files rather than substituting in them -- `check_evidence.py` carried en and em
dashes **inside the string literals that normalise en and em dashes**, so a
textual pass would have produced `replace("-", "-")` and silently disabled the
check while turning the file green. That is the whole argument for an explicit
map in one example.

**Never open an existing file with `encoding="ascii"` for writing.** Python
truncates on open, then raises on the first non-ASCII byte, destroying the file
before the error surfaces. This ate two files in one session. Write to a temp
file and `os.replace()`.

**On Windows, `Set-Content -Encoding utf8` writes a BOM.** PowerShell 5.1's
`utf8` means with-BOM, which will fail the ASCII gate on a file you only meant
to search-and-replace. Caught by `check_invariants.py` on 2026-07-30. Use
Python with `io.open(..., encoding="utf-8", newline="\n")`.

## Standing rules

- **Never guess a date.** `null` is ungated and honest; a fabricated clock is
  indistinguishable from a real one later. Every date in `config/sources.json`
  and in `data/curated/frontier_labs/` carries an evidence entry naming what was
  read.
- **Measure the claim before writing it down.** Every documented claim that got
  measured during the 2026-07 forward-fill turned out to be slightly wrong:
  rebuild idempotence was documented and false, `slugify()` silently merged
  PointNet and PointNet++, tagger accuracy was honest but its distribution
  shift severe. None were found by reading code; all were found by
  cross-checking two numbers that should agree.
- **A behavioural claim about a person is checkable by asking them.** In
  2026-07 a count of "1 note per 206 verdicts" was read as evidence a tool was
  badly designed, and the tool was rebuilt on that inference. Asked directly,
  the reviewer's account contradicted it. See the correction block in
  `docs/sessions/SESSION_2026-07-26_FORWARD_FILL.md`.
- **ASCII only.** Enforced by `validate_ascii.py`.
- **Licence enforcement is mechanical, not remembered.** `validate_candidate()`
  refuses any dump whose SPDX contains `-SA`.

## Cross-repo conventions are NOT owned here

**Before inventing any printing, dictation, memo or routing convention, read
`PipFoweraker/coordination` -> `PRINT_AND_PROCESS_REFERENCE.md`.** It is the
canonical file and it is maintained by the coordination seat.

This is not advice. On 2026-07-31 three repositories independently built print
and dictation tooling on the same day, and two independently debugged the same
printer bug hours apart. **pdoom-data was one of the three.** Its renderer was
deleted on 2026-08-02 (`pdoom-data#55` A4, `coordination#2` A1).

The cause was a missing registry, not a missed document -- the reference did
not exist until 2026-08-01, after the duplication happened. `coordination` is
that registry, and checking it first is the whole mechanism.

### Working conventions Pip has ruled on

**Sabbath is real and binding.** Sunday, sunrise to sunset, no work
notifications at all. Weekend quiet hours run Friday ~17:00 to Monday 06:00,
less strictly. Never design anything that depends on a response inside those
windows.

**Nothing prints before 06:00.** Paper should be in the tray before he is up.

**Density up; ministerial shape.** Denser prose, more paragraphs, fewer bullets
and splitting mechanisms. One front page carrying summary, key facts and the
exact asks -- one line each, answerable yes or no -- with reasoning behind it.
His words: *"treat me as a literate minister"*, and *"if the asks are at the
front and I have the context, I can answer them and move on."*

**Runsheet blocks carry duration, order AND wall-clock time.** All three. Wall
clock right-aligned or offset; duration and order left-aligned, so the two
kinds of information are distinguishable at a glance.

**For any finding, ask: document or mechanism?** Where the fix is a document,
ask what the mechanism version would cost, then take the trade-off
deliberately. Writing a lesson down does not install it. This repo has a clean
counter-example on file: `pdoom1-website/docs/TECH_DEBT.md` already documented
the orphaned-collection problem as E-0, with numbers matching a later
independent measurement exactly. Found, written down, not acted on. The failure
was never detection.

**A check must take at least one INPUT FROM OUTSIDE the system it is
checking.** Endorsed by Pip; canonical wording is `pdoom1#1075`, restored by
`coordination#5`. **Cite the source, do not paraphrase** -- this seat wrote it
here backwards as "output from inside" on 2026-08-02 and propagated the
inverted form into three repos and two printed sheets before it was caught.
The inversion is not cosmetic: the inverted form passes the exact failure the
rule was written to catch.

Two clauses, and a single-clause version passes one instance and fails the
other:

1. **Observe the system's actual state**, not a proxy for it. An `ssh` cleanup
   trusted on its exit code returns 0 on an SFTP-only host having executed
   nothing.
2. **Do not derive what to look for from that same system.** A board probe that
   built its candidate list from seeds the site had already seen could not see
   a newly drawn seed, by construction. Fix per `pdoom1-website#229`: read the
   expectation from an artifact a different repo produced.

Worked example from this repo, and note it cuts against the obvious fix: the
redaction tool's verifier used a silently broken pattern and reported clean
while ten records still carried addresses. Making detection and verification
share one function satisfies clause 1 and **violates clause 2** -- a defect in
the shared function is then invisible to both. What actually caught it was a
separately written scanner giving a different answer.

Related, same issue: monitoring by polling is not merely incomplete but
incapable. State has to be pushed.

### Do NOT copy printer facts into this file

This section used to hold a copy of the reference's printer facts. **That copy
went stale and was wrong for two days**, in the specific way `coordination#15`
predicts: a copy becomes a variant the moment either side changes.

What it claimed: *"SumatraPDF is not installed on this seat, winget failed with
exit 43, so there is currently no PDF path at all from this workstation."*

What was true: **SumatraPDF has been installed here since 2026-07-31 11:01.**
The winget exit 43 was almost certainly *already installed*, read as absence.
Another seat measured it and corrected the canonical file on 2026-08-04, while
this copy went on asserting the opposite.

The cost was not abstract. Believing it, this seat printed four days of memos as
plain text through `Out-Printer` -- **simplex Letter, no page numbers, no print
stamp** -- when a duplex-A4 stamped path was available the whole time. Pip's
complaint that *"this memo formatting is weird, consistently pdoom-data and
pdoom-data alone"* traces directly to this paragraph.

**Read the printer facts from `coordination/PRINT_AND_PROCESS_REFERENCE.md`
section 1 and its per-seat table. Do not restate them here.** If your machine
disagrees with that file, your machine is the evidence and the file is the
claim -- fix it there.

### How to print from this seat

Use coordination's renderer rather than writing one. It already handles the
stamps, page numbers, duplex and paper size, and it **refuses to print rather
than emitting an unstamped sheet**, which is the behaviour that caught this:

    python coordination/tools/walkpack/build_walkpack.py \
      --title "..." --decision "..." --sides duplex --paper A4 \
      --print "$queue" doc1.md doc2.md

Needs `markdown`, `pypdf` and `reportlab`. Resolve `$queue` at runtime by name
**or** driver -- see the reference; matching on driver alone returns nothing on
the other seat.

Two rules that are ours to remember rather than theirs to state:

- **Verify on the spooler, not the exit code**, and poll every ~400ms. Jobs
  drain in under five seconds, so a single late poll looks identical to a print
  that never happened -- which is how this seat once told Pip it could not
  print a job that had succeeded.
- **Checklists and runsheets print simplex**, reading documents duplex. A back
  face hides half a checklist clipped to a board.
- Every printed artifact carries a boxed `PRINTED <day> <date> <time> <tz>`, a
  staleness line, `supersedes:`, and hand-typed `PAGE n OF m` -- Chromium
  cannot generate page numbers, so they must be written into the source.
- **Qualify every issue reference with its repo** (`pdoom1#630`, not `#630`).
  A bare number costs Pip a context switch.

Routing: data contracts and standards live here. Game, release and league go to
`pdoom1`; site and publishing to `pdoom1-website`; cross-repo daily ops,
printing and capture to `coordination`.

## Where to look

    docs/DOCUMENTATION_INDEX.md   navigation hub, start here
    docs/DATA_ZONES.md            zone model
    docs/CONSUMER_GUIDE.md        the contract: facts vs opinions, obligations
    docs/ADAPTER_SPEC.md          how a source gets in
    docs/PDOOM1_INTEGRATION_BRIEF.md  what the game needs to know
    docs/sessions/                past session write-ups, newest most useful
    scripts/adapters/README.md    adding a source, and its traps
    scripts/build/README.md       why serveable is derived
    config/sources.json           source facts, with evidence per date
    legacy/2025-09_prototype/     moved from root 2026-07-30; read its README

## Pre-approved commands

    python scripts/**/*.py
    python -m json.tool
    git add / commit / push / pull / fetch
    gh issue list / view
