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

**Do not clear the ASCII backlog to make CI green.** About 20 files in `docs/`
fail the gate on box-drawing and arrows. That failure is the only thing keeping
the `documentation-publish` job from running, and that job appends to
`DEVBLOG.md` with `echo >>` on every push to main, so the file grows without
bound. Both are de-armed now, but the coupling is real. Also: never run
`legacy/2025-09_prototype/fix_ascii.py`, whose `?` fallback would shred every
tree diagram. Use an explicit substitution map that errors on unmapped
characters.

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
printer bug hours apart. **pdoom-data was one of the three.** The tooling in
`tools/print/` and `docs/PRINT_STYLE_GUIDE.md` is that duplication; it is
pending deletion (coordination#2, ask A1) in favour of
`coordination/tools/walkpack/build_walkpack.py`.

Facts from that reference worth having before you touch a printer from here:

- The Brother HL-L2460DW is a **host-based raster printer**. It accepts
  `image/urf` and `image/pwg-raster` only -- **no PDF, no PostScript, no PCL**.
  Sending a PDF to port 9100 prints a ream of ASCII garbage.
- **Use SumatraPDF** with `-print-to ... -silent -exit-when-done`. It is not
  installed on this seat.
- **`Start-Process -Verb Print` fails on this seat**: `.pdf` has no registered
  handler at all. Documented; do not rediscover it.
- **Verify on the spooler, not on the exit code**, and poll fast -- jobs drain
  in under five seconds and `JobCountSinceLastReset` reads 0 regardless. A
  single late poll looks identical to a failed print, and reporting "cannot
  print" on that basis has already cost Pip a walk to the machine.
- **Checklists and runsheets print simplex.** A back face hides half the
  checklist when the sheet is clipped.
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
