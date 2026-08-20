# Session 2026-08-21: wood to bronze, honestly

Running log. Times are AEST (UTC+10), wall clock, recorded as work happened
rather than reconstructed afterwards.

**Goal, as set by Pip 06:5x:** move every served collection from wood to
bronze -- "but only honestly, robustly and destructively tested and carefully
advanced".

**The named hazard, stated before starting.** Bronze is three predicates:
`has a schema`, `validates`, `every record has a source`. The first two are
both passed by committing `{"type": "object"}` as the schema file. That is a
vacuous pass: the collection would report BRONZE having gained nothing a
consumer can rely on. Any schema written today has to be derived from the
records as measured, and has to be shown to REJECT things, not merely to
accept what is already there.

## Log

| time | entry |
|---|---|
| 05:54 | Session start. Repo on `feat/maturity-ladder`, 45 commits behind `origin/main`. |
| 06:10 | Both local branches verified already merged (PR #66, PR #82). Deleted. On `main`, level, clean. |
| 06:2x | `check_all.py`: 22 gating checks pass. CI green on `f63f425`. |
| 06:3x | Watch list measured: 110 atoms, 0 triaged, 64 clean and rateable. `README.md` counts stale (says 93/19/7; actual 110/24/14). |
| 06:4x | pdoom1's hand-carried `historical_events.json` still carries the two mojibake titles (pdoom1#1163). Upstream here is repaired. |
| 06:58 | Ladder read in full. Bronze predicates identified. Vacuous-schema hazard named above. |
| 07:00 | **timeline_events failure diagnosed: three causes, not 1,166 problems.** 1,166 records fail on `source_id` (an undeclared property, `additionalProperties: false`) AND on `tags: []` against `minItems: 1`; 24 more on `description` `maxLength`. All 1,194 carry a source. |
| 07:01 | **candidates: 6 of 3,434 carry no source at all.** `p_sources` fails regardless of schema. Not schema-hackable. |
| 07:02 | The 6 split three ways, checked against `raw.jsonl` (upstream Epoch CSV, not the adapted form): 4 blank upstream (`Yi-Large`, `GPT-5.2`, `GPT-5.1-Codex`, `Midjourney V1`); 1 adapter defect (`Eagle 2` has `Link = arxiv.org/abs/2501.14818`, dropped by `epoch_models.py:133` `value.startswith("http")`); 1 upstream column error (`EXAONE 4.5` has an author list in `Link`, correctly rejected). |
| 07:03 | reviewed: 518/518 carry a source; 526 reviews, every one naming `Pip Foweraker`; verdicts accept/unsure/reject only. Reachable honestly today. |
| 07:05 | Full field census done on all 3,434 candidates: 23 universal fields, 1 optional enrichment field, no record carrying an undeclared key. Schema will be derived from this, not from intent. |
| 07:03 | Wrote `config/schemas/candidate_v1.json`, derived from the census. First run against the corpus: **3,434 of 3,434 fail**. Four disagreements, three of them mine. |
| 07:04 | Corrected three: `_provenance` entries carry `evidence_count` (all 3,434); airr confidence has a fourth level `very_low` (1,197); `privacy` is a real fourth verdict (2 records, both Pip's). Failures drop to 19. |
| 07:05 | **The remaining 19 were a defect in MY pattern, not a clean result.** `^https?://[^ ]+$` excludes spaces but not newlines, so newline-joined URL pairs passed. Tightened; the true count is **65 candidates, 11 reviewed**. |
| 07:06 | Tightened again: the negated-whitespace class with a `$` anchor still accepted a URL with one trailing newline, because Python's `re` treats `$` as end-or-before-final-newline and ECMA-262 (which JSON Schema specifies) does not. Replaced with a form that depends on neither anchor semantics nor the host engine. |
| 07:08 | `tests/test_schema_gates.py`: 57 must-fire, 14 must-not-fire. Passes first run. |
| 07:09 | **Did not believe the first run.** Meta-test: swapped in a vacuous `{"type": "object"}` schema, a loosened one, and one with a single constraint removed. All three must go red. |
| 07:10 | Meta-test found the gate failing for the WRONG reason on the vacuous schema -- a `KeyError` three frames down rather than a finding. Fixed: vacuity is now reported in words. Vacuous 34 misses, loosened 16, single `-SA` deletion 2. |
| 07:11 | Built `normalise_urls()` in `project_candidates.py`. Dry run over the served feed BEFORE rebuilding: 67 records change, **0 lose a URL**, 64 gain one, sourceless count unchanged at 6. |
| 07:12 | `project_candidates.py --check` goes red on the pending change, exit 1, as it should. (Read the exit code wrongly at first -- `$?` after a pipe is `tail`'s status, not the script's. Same species as trusting an `ssh` exit code.) |
| 07:13 | `tests/test_url_normalisation.py`: 17 cases, idempotence, and a corpus-wide assertion that no record loses a URL. Destructively verified by breaking the splitter three ways; all three go red. |
| 07:14 | Rebuilt `candidates` and `reviewed`. Wired `candidate_v1.json` into the ladder for both -- deliberately one schema, not two, because a second file would be a copy and a copy becomes a variant. |
| 07:15 | **`reviewed` reported GOLD, skipping two rungs. Did not bank it.** |
| 07:16 | Two ladder predicates were passing vacuously. `p_evidence` selected on `founded` OR `occurred_at` and then only inspected `founded`, so any collection not using `founded` counted nothing and returned ok. `p_contract_test` searched `scripts/validation/` -- **which contains the ladder itself**, whose predicate label is the string "consumer-contract test exists" and whose `COLLECTIONS` dict names all four collections. |
| 07:17 | **Checked whether my own comment caused it. It did not.** Replayed the original predicate against `HEAD`'s `check_maturity.py`: it matched itself for all four collections. `p_contract_test` **could not fail for any collection from the day L4 shipped**. `frontier_labs` was never gold, and this seat reported it as gold to Pip at 06:58 this morning. |
| 07:17 | Fixed both. `p_contract_test` now searches `tests/test_*.py` only and **runs** the test, requiring exit 0. `p_evidence` recognises two evidence forms and FAILS when it can measure neither, per the module's own "unknown is not a pass". |
| 07:18 | Audited the other eleven predicates the same way. Two more were weak: `p_no_bare_opinion` scanned `recs[:500]`, leaving 85% of candidates unread while reporting on all of them; `p_privacy_ci` matched the substring "privacy" anywhere in the workflow, which a comment satisfies. Both fixed. |
| 07:20 | **The regression test recursed.** `p_contract_test` now RUNS matching tests, and `tests/test_maturity_predicates.py` contains the words "contract" and "maturity", so it matched itself and spawned Python until killed by hand. Two independent guards added: skip any test importing `check_maturity`, and an env-var re-entry guard. |
| 07:21 | `tests/test_maturity_predicates.py`: 17 cases over 7 of 15 predicates, with the other 8 **named as untested** rather than left as a silent gap. |
| 07:22 | Full `check_all.py`: **25 gating checks pass**, 8 rebuild checks byte-identical. |

## Where the ladder actually stands

| collection | at 06:58 | at 07:22 | why it moved |
|---|---|---|---|
| `timeline_events` | WOOD | WOOD | unchanged; blocker now diagnosed precisely |
| `candidates` | WOOD | WOOD | bronze predicates 1 and 2 now pass; blocked on 6 sourceless records |
| `reviewed` | WOOD | **SILVER** | genuine: schema, validation, sources, producer, byte-check, lineage |
| `frontier_labs` | GOLD | **SILVER** | **correction, not a regression** -- its gold rested on a predicate that could not fail |

**Net honest movement: one collection up two rungs, one collection down one
rung to where it always was.** The demotion is the more valuable half.

## What is still blocking each rung

**`candidates` -> bronze: 6 records carry no source.** Not schema-hackable and
not a code fix. Three different causes, and they want three different answers:
4 are blank in Epoch's own CSV (`Yi-Large`, `GPT-5.2`, `GPT-5.1-Codex`,
`Midjourney V1`) and no source exists to cite; 1 is an adapter defect
(`epoch_ai:eagle_2`, whose `Link` is `arxiv.org/abs/2501.14818` and is dropped
by `epoch_models.py:133` for lacking a scheme); 1 is an upstream column error
(`EXAONE 4.5` has an author list where the URL goes). The adapter fix does not
reach the current feed, because raw dumps are immutable and the fix only lands
at the next re-ingest.

**`reviewed` and `frontier_labs` -> gold: a consumer-contract test.** Now a real
requirement rather than a substring, so it has to be written.

**`timeline_events` -> bronze: three causes, one of which is not a code fix.**
1,166 records carry an undeclared `source_id` and an empty `tags` array against
`minItems: 1`; 24 more exceed `maxLength` on `description`. Declaring
`source_id` is a contract change to a schema pdoom1 consumes. The empty `tags`
cannot be fixed by loosening `minItems` without making the field meaningless,
and cannot be fixed by tagging 1,166 records, which `540556c` explicitly ruled
against. This one is a design decision, not a task.
