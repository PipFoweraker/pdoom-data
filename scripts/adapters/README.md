# scripts/adapters/

One module per external source. Full contract: `docs/ADAPTER_SPEC.md`.

    _base.py          shared plumbing; do not put source logic here
    epoch_models.py   Epoch AI notable models (bulk CSV)
    forum_posts.py    LessWrong + EA Forum (GraphQL, metadata only)
    mit_airr.py       MIT AI Risk Repository (reference taxonomy, not events)

## Adding a source, shortest path

1. Read the terms on a **first-party page** and write the licence block by
   hand. If you cannot find the terms, the adapter does not ship -- record the
   attempt in `config/sources.json` instead. `validate_candidate()` will
   refuse any dump whose SPDX contains `-SA`.
2. Add the source to `config/sources.json` with a `source_available_at` date
   **and an evidence entry naming what you read**. If you cannot verify a
   date, use `null`. Never guess: a fabricated clock is indistinguishable
   from a real one six months later and silently corrupts the in-game gating.
3. Write `fetch()` and `normalise()` as separate functions. Re-normalising a
   stored dump must never require a network call.
4. Add the `source_id` to `SOURCES` in `scripts/build/project_candidates.py`.
   Adapters do not enter the feed just by existing; that is deliberate.

## Things that have already bitten someone

**ASCII is enforced, including in your escape tables.** Writing a character
map with literal smart quotes fails the repo's own gate. Use `\uXXXX`
sequences. If you generate the table programmatically, note that some tools
normalise escapes back into literals on write -- check with
`grep -P '[^\x00-\x7F]'` afterwards, do not assume.

**Never open an existing file with `encoding="ascii"` for writing.** Python
truncates on open and only then raises on the offending byte, so a file with
any pre-existing non-ASCII is destroyed before the error appears. This ate
`_base.py` once and `docs/DOCUMENTATION_INDEX.md` once. Write to a temp file
and `os.replace()`.

**Ids must be unique and stable.** `slugify()` stripped trailing `+`, so
PointNet++ and PointNet collapsed onto one id. `write_dump()` now refuses
duplicates outright, but think about what makes your source's key distinct
before relying on a slug.

**Dumps are immutable.** Re-running an adapter writes a *new* timestamped
directory. Never edit or delete one. The diff between consecutive dumps of
the same source is evidence about how the upstream changed, and that is data
worth keeping. The single exception is a privacy tombstone.

**Signals are time series, not scalars.** Use `_base.signal()`. A citation
count differs in 2019 and 2026, and the game clock decides which applies.

## Verifying your work

    python scripts/adapters/<yours>.py --dry-run
    python scripts/validation/check_invariants.py
    grep -rP '[^\x00-\x7F]' scripts/adapters/<yours>.py
