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
| `setup_script.py` | scaffolding -- **has never parsed, see below** |
| `setup_clean.py` | scaffolding variant; CI greps it for the VERSION string |
| `purify_historical_data.py` | one-shot historical cleanup |
| `dev_metrics.py` | writes `dev_metrics.db` |
| `version_manager.py` | bumps `VERSION` and appends to `DEVBLOG.md` |
| `fix_ascii.py` | **see the warning below** |

## `setup_script.py` has never been valid Python

Measured 2026-08-24 while acting on the seat-portability sweep. `ast.parse`
raises `SyntaxError: invalid syntax` at line 250 on the file as it stands, and
on every revision git has of it -- `b810351` of 2025-09-14, the commit that
introduced it, and `d475e7d` of 2026-07-31, the move into this directory. The
cause is `generate_integration_guide()` building its Markdown inside a `"""`
string that itself contains a fenced Python block with a `"""docstring"""` in
it, so the outer literal terminates on line 250 and the remainder of the file
is parsed as code.

The consequence was not academic. `pre-commit-hook.sh` told every developer
whose commit failed the ASCII gate to run this script to auto-fix the problem,
which it cannot do because it cannot start. That pointer is now gone, and the
hook says what to do instead.

This is also a correction to what the 2026-08-17 sweep recorded. It read line
479, `open("README.md", "w", encoding='ascii')`, as an instance of the
truncate-then-raise pattern CLAUDE.md forbids by name, and ranked it as a
file-destroying hazard aimed at whatever directory you were standing in. Two
things are wrong with that reading. The first is that `create_readme()` pipes
its content through `ensure_ascii_only()` first, which coerces anything left
over into `?` -- the same fallback that gets `fix_ascii.py` banned two sections
down -- so the write would never raise, it would SUCCEED and silently replace
the README of whichever repository the caller happened to be in. The second is
that neither can happen, because the module does not import. A loud
`SyntaxError` at import time is the cheapest possible failure and it is what
has been happening all along.

The remaining question about this directory is unchanged and still unanswered:
whether the hand-authored event modules are the provenance of the 28 curated
events. That a scaffolding script never ran is weak evidence they are not, but
it is evidence, and it is written down here rather than acted on.

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

- `pre-commit-hook.sh` suggested `setup_script.py` in an error message. Removed
  2026-08-24: the script has never parsed, so the suggestion was advice to run
  a file that cannot start. Nothing outside this directory reaches into it now.
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
