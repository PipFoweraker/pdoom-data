# Legacy prototype modules (2025-09)

Twelve modules moved here from the repository root on 2026-07-30. **Nothing was
deleted.** Git history is preserved through the move; `git log --follow` on any
file still works.

## Why they were moved, and why not deleted

Every one of these was last touched on 2025-09-14. A reference check found that
each is referenced by something -- so "dead code" would be the wrong label --
but the references are almost entirely **to each other and to documentation**.
They form a closed cluster that the current pipeline under `scripts/` never
calls.

That distinction matters. An earlier audit recorded "9 dead root .py modules";
measuring it found 0 with zero references and 12 in a self-referential cluster.
Deleting on the strength of the first description would have removed working
code that a doc still points at.

They are here rather than gone because nobody has established what, if
anything, still depends on them at runtime, and the cost of keeping them is one
directory.

## What is in here

| Module | Role in the 2025-09 design |
|---|---|
| `event_data_structures.py` | shared dataclasses the event modules import |
| `funding_events.py` | hand-authored funding events |
| `institutional_decay_events.py` | hand-authored institutional events |
| `organizational_events.py` | hand-authored organisational events |
| `technical_breakthrough_events.py` | hand-authored technical events |
| `game_integration_helpers.py` | shaping for the game; imports the four above |
| `setup_script.py` | scaffolding, imports the event modules |
| `setup_clean.py` | scaffolding variant; CI greps it for the VERSION string |
| `purify_historical_data.py` | one-shot historical cleanup |
| `dev_metrics.py` | writes `dev_metrics.db` |
| `version_manager.py` | bumps `VERSION` and appends to `DEVBLOG.md` |
| `fix_ascii.py` | **see the warning below** |

## Warning: do not run `fix_ascii.py`

It replaces non-ASCII characters with `?`. Roughly 20 files in `docs/` fail the
ASCII gate, and their failures are box-drawing characters, arrows and emoji --
which means running this to "fix the ASCII errors" would shred every tree
diagram in the documentation into rows of question marks.

If ASCII remediation is needed, use an explicit substitution map that **errors
on an unmapped character** rather than falling back to `?`. There is a worked
example of that approach in the 2026-07-30 session history; it was used to fix
9 glyphs in `weekly-data-refresh.yml` and it refuses to write when it meets a
character nobody has decided about.

Note also that clearing the ASCII gate has a side effect: it is the only thing
currently keeping the `documentation-publish` job in `documentation-ci.yml`
from running. That job is de-armed as of 2026-07-30, but read the comment there
before re-enabling anything.

## Live references that were repointed

Two things outside this directory still reach into it, and both were updated in
the same commit as the move:

- `pre-commit-hook.sh` suggests `setup_script.py` in an error message
- `.github/workflows/documentation-ci.yml` greps `setup_clean.py` for the
  current version string

`validate_ascii.py` was **not** moved. It stays at the repository root because
`documentation-ci.yml` invokes it as the ASCII gate.

## If you are deciding what to do with this directory

The question to answer first is whether the hand-authored event modules here
are the origin of the 28 curated events in `all_events.json`. If they are, this
directory is provenance and should stay. If the events were authored elsewhere
and these modules only ever generated them once, the directory is a candidate
for deletion after a release tag.

Nobody has checked. That check is the prerequisite, not a formality.
