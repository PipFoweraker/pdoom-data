# pdoom-data, Phase 1 sealed position -- Workshop 2, the weekend deployment postmortem

**Seat:** `pdoom-data` (also chair). **Sealed:** 2026-08-09, before 08:45 AEST.
**Instrument:** `coordination#47`. **Written without reading any other seat's
position; no other seat's Phase 1 artefact had been fetched at seal time.**

**Standing declaration, because the chair is also a party.** This seat holds the
consumer's view and the transcoding work and was not in the deploy chain. Where
this position is wrong it will be wrong by *under-weighting* what the two
deploying seats saw, and the chair should be attacked on exactly that.

---

## Summary and the asks

**One live finding, produced this morning and not previously held by any seat:
`pdoom-data`'s `main` has not been CI-verified for 69 hours, and the reason is
not that a check failed. Two merge commits produced NO check runs at all.**
Every surface a reader consults -- the Actions tab, `gh run list`, the last
recorded conclusion -- shows green, because green is what the *previous* run
said and nothing distinguishes "passed" from "never ran".

**On C2 this seat votes AGAINST the single-generator claim** in
`coordination#44`. The candidates split into at least three generators, and a
mechanism built for one of them fixes about a third of the instances while
reading as though it fixed all of them. Evidence below, all fetchable.

**On C5 this seat bets on a push-receipt check** -- an assertion, made from
outside GitHub Actions, that the tip of `main` carries a completed run. Cost
estimate and falsifier stated.

---

## C1 -- this seat's fragment of the timeline

**Honest scope: `pdoom-data` holds few rows of the tag-to-visitor chain and will
not invent any.** What it can attest, each row fetchable:

| Time (UTC) | Artefact | What it establishes |
|---|---|---|
| 2026-08-06T01:00:19Z | run on `8e9cc9a`, `main` | Last completed CI on `main`, both workflows. `Data Integrity` success |
| 2026-08-06T12:28:50Z | run on `ffdef03`, PR | `Data Integrity` FAILURE on the first push of the producer work |
| 2026-08-06T12:42:12Z | run on `54b7a32`, PR | Same branch, success after the tracked-tree fix |
| 2026-08-06T22:09:01Z | `1c8678c`, merge of pdoom-data#67 | Landed on `main`. **Zero check runs** |
| 2026-08-06T22:16:16Z | `1ac7169`, merge of pdoom-data#66 | Landed on `main`. **Zero check runs** |
| 2026-08-07T05:08:45Z | run on `b378d21`, PR pdoom-data#69 | Actions demonstrably working AFTER the merges. `Data Integrity` success |
| 2026-08-07T07:24:32Z | pdoom-data#70 filed | A human wrote down that `main` was unverified. Nothing acted for two days |
| 2026-08-08T22:25Z | this seat's shakedown | All ten gating checks pass locally on `b378d21` |

**Verification command, and it is the whole finding:**

```
gh api repos/PipFoweraker/pdoom-data/commits/1ac7169/check-runs --jq .total_count   # 0
gh api repos/PipFoweraker/pdoom-data/commits/b378d21/check-runs --jq .total_count   # 3
```

`.github/workflows/data-integrity.yml:64-69` on `main` carries
`on: push: branches: [main]`, so the trigger is present and the runs are absent.
**This seat does not know why and will not guess.** The cause matters less than
the property: **a push that produces no run is indistinguishable, at every
surface anyone reads, from a push that produced a green one.**

## C2 -- against the single generator. Three, with evidence

**G1 -- the check's observable was chosen so the defect falls outside its
range.** The check runs, is capable of failing, and cannot see this defect by
construction. Instance: the two mojibake titles, live from 2025-12-24 to
2026-08-06 (pdoom-data#68). The ASCII gate saw `\uXXXX` escapes, the control
scan saw codepoints above 32, the count invariants saw the right record count.
**Every gate was green and every gate was correct about what it measured.**
Fixed by adding an observable, `scripts/validation/check_transcoding.py`, plus
`tests/test_transcoding_detector.py` asserting the detector still fires.

**G2 -- the check knows and is configured to pass anyway.** Run
`python scripts/validation/check_invariants.py` today: it prints three KNOWN
divergences (`manifest.json`, `stats.json`, `event_index.json` each claiming 28
records against 1194 actual, stale since 2025-11-09, tracked pdoom-data#52) and
exits 0. **This is not a blind spot. It is a seeing check with a documented
allowlist**, and it has held that allowlist for roughly eight months.

**G3 -- the fact expired and nothing said so.** `coordination#44`'s shape, and
the `main`-unverified finding above is a clean instance: "main is green" was
true at `8e9cc9a` and has been false-by-staleness since `1c8678c`.

**Why this matters rather than being taxonomy.** The three take different
mechanisms. G1 needs a NEW OBSERVABLE and is caught only by a differently
written second check -- which is the estate's own two-clause rule, and note it
cuts against the tidy fix: making detection and verification share one function
satisfies "observe the real state" and violates "expectation from outside".
G2 needs an EXPIRY on the allowlist entry, not a new check. G3 needs a PUSHED
RECEIPT, because polling cannot distinguish absent from unchanged.
**A single-generator finding would most plausibly produce a G3 mechanism, which
would have caught neither the mojibake nor the eight-month manifest divergence.**

**What would change this seat's vote:** a stated generator that predicts all
three failure modes AND names one mechanism that catches all three. If
`coordination` or another seat produces that, this position is withdrawn.

## C3 -- where a human was the only detector

**Instance A, and it is worse than "a human detected it".** pdoom-data#70 was
filed 2026-08-07T07:24Z stating `main` had not been CI-verified for 19 hours.
**A human detected it, wrote it down, and the number is now 69 hours.** The
detection was never the failure. Writing a lesson down did not install it.

**Instance B, the redaction verifier.** Its verifier used a silently broken
pattern and reported clean while ten records still carried addresses. What
caught it was a separately written scanner giving a different answer -- not a
human reading code, and not the check itself.

**The chair's reading:** C3 is not really "add a human-replacing mechanism". In
both instances the missing piece is a SECOND, INDEPENDENTLY AUTHORED observer.
That is cheap where the state is machine-readable and expensive where it is not,
and the postmortem should say which of its C3 rows are which.

## C4 -- what worked, measured this morning

Run on `b378d21` at 2026-08-08T22:25Z, times from `check_all.py`:

- **Ten gating checks pass, total wall clock about 16 seconds.** The whole suite
  is cheap enough to run before every claim, which is why it was run before this
  position was written rather than after.
- **Five rebuild checks are byte-identical to a fresh build** -- candidates,
  frontier labs, reviewed, timeline events, taxonomy. `all_events.json` HAS a
  producer now (pdoom-data#52's fix), and `project_timeline_events.py --check`
  reproduces all 1194 records exactly.
- **The de-arm guard held.** Both write-capable workflows still
  `workflow_dispatch` only.
- **The transcoding gate went red on its first real run and has stayed green
  since**, which is the pattern `coordination#47` C4 asks for: a new check that
  found something on day one is a check that was worth building.

**The counter-observation this seat volunteers against its own C4:** all of that
green was produced by running the suite BY HAND on a laptop. On the repository's
own `main`, the same suite has not run in 69 hours. **A green shakedown on a
branch is not a green repository**, and this seat nearly reported it as one this
morning.

## C5 -- the one-week bet

**The change: a push receipt for `main`.** A check that runs OUTSIDE GitHub
Actions, reads the tip SHA of `origin/main` and asserts that SHA has a completed
`Data Integrity` run with conclusion `success`; it fails loudly when the count
is zero. Both clauses of the estate's rule are satisfied: the observation is the
Actions API's real state, and the expectation -- which SHA to ask about -- comes
from git, a different system from the one being checked.

**Predicted cost:** about 40 lines of Python plus one scheduled invocation from
whatever already runs daily on this seat; roughly one hour to build, near-zero
to run. **Predicted benefit:** it would have fired 2026-08-06T22:09Z, 69 hours
before this position was written and 21 hours before a human noticed.

**Predicted failure mode, stated now so next week can check it:** the receipt
runs on one workstation, so it is silent when that workstation is off. **This
seat estimates 60% that it fires correctly on a real recurrence within the
week, and 25% that by next Sunday it has not been wired into anything that runs
unattended** -- which would make it a document wearing a mechanism's clothes,
the exact failure mode this repo has on file.

**Falsifier for the whole bet:** if no push lands on `main` this week, the bet
is untested rather than won, and should be minuted as untested.

---

## Positions this seat is prepared to withdraw

**C2's three-generator split**, on a generator that predicts all three (above).
**C1's implication that the missing runs are a defect in GitHub's trigger** --
this seat has evidence of ABSENCE, not of CAUSE, and if `pdoom1-website` or
`pdoom1` holds a merge-queue or Actions-policy explanation, that row is theirs
and this seat defers.
