# One number to drive to zero -- design v0.1, for argument

**Written by the `pdoom-data` seat, 2026-08-10, at Pip's request.** *"I like one
number that I try to drive to zero on my hygiene reports, ideally with the
sub-numbers of failures easily accessible so I can track them."*

**This is a proposal, not a build.** Nothing here is implemented. `coordination`
holds the cross-repo ground and should mark it up before anyone writes code.

---

## The asks, and two of them decide whether the number is honest

**Q1. Is the number OPEN CONTRADICTIONS -- places where the estate asserts
something that is not true right now?** Alternative below. **YES / NO / OTHER**

**Q2. Do suppressions count against the number?** If an accepted-drift entry
makes a finding vanish, the number reaches zero with the defects still there.
**My strong recommendation: suppressions are counted, dated, and EXPIRE.**
**COUNTED / NOT COUNTED**

**Q3. Does it gate, or only report?** Recommendation: **gate on new findings,
report the backlog.** A permanently red gate is ignored within a fortnight.
**GATE ON DELTA / REPORT ONLY / GATE ON ALL**

**Q4. Who owns the aggregate?** Each repo emits its own findings; `coordination`
sums them. **CONFIRM COORDINATION AGGREGATES / OTHER**

---

## The number: OPEN CONTRADICTIONS

**Definition, and it is deliberately narrow: a place where this estate states
something, and the thing it states is not true right now, checkable by machine.**

Not "issues". Not "tech debt". Not a quality score. **A contradiction has a
claimant and a referent, and a machine can fetch both and compare them.** That
is what makes it countable, arguable, and drivable to zero.

**Why not a score.** A weighted score cannot be driven to zero honestly -- it
asymptotes, and the weights become the argument instead of the defects. Worse,
a score hides composition: 40 points could be one catastrophe or forty
trivialities. **You asked for sub-numbers precisely to avoid that, and a raw
count with buckets gives it for free.**

**Why not "open issues".** GitHub already counts those and the count is not
actionable -- 13 of `pdoom-data`'s 39 are tier 3 and 9 should arguably be
deleted. **An open issue is work not done. A contradiction is a lie being told
right now.** Only the second belongs in a hygiene number.

## The evidence this definition is not invented

**Every instance below is real, from the last four days, and each is one line of
the same shape.** This is the test of whether the definition earns its keep --
it was derived from these, not fitted to them afterwards.

| The claim | The referent | Days wrong |
|---|---|---|
| `manifest.json`: 28 events | `all_events.json`: 1,194 | 274 |
| `PDOOM-4` epic: **Done** | `pdoom-data#24`, its work, open and critical | 196 |
| `CLAUDE.md`: the ASCII red guards a live job | that job, commented out | 11 |
| `CLAUDE.md`: SumatraPDF not installed on this seat | it had been, since 07-31 | 4 |
| redaction tombstone: this file is clean | ten records still carrying addresses | 8 |
| `check_all.py`: "run this and nothing else" | two of five rebuild checks absent | ~4 |
| `sync-game-version`: green | the website, unchanged | ~240 |

**Seven instances, five subsystems, one shape.** Note that **not one of them was
found by the check that owned the ground.** They were found by a person or by a
second, differently-written observer -- which is the estate's own two-clause
rule, and the reason this number is worth having at all.

## Sub-numbers: the eight classes, already ruled

Workshop 2 (`coordination#47`) settled these against three seats' independent
evidence, so the buckets do not need re-litigating:

    1  Disarmed              exit code discarded; assertion cannot fail
    2  Unverified assertion  reports an outcome it never observed
    3  Mis-aimed referent    observes real state of the WRONG object
    4  Wrong property        right object, irrelevant property measured
    5  Knowing allowlist     sees the defect and is configured to permit it
    6  Expired premise       true at t0, false at t1, no write between
    7  Composite premise     two fresh sources of different vintages, paired
    8  Absent                no check ran at all

**Report the total, and the eight beneath it.** Class 5 is the one to watch on a
dashboard, for the reason in Q2.

## The failure mode this design must survive, and it is Q2

**The number will be gamed, and not dishonestly.** Someone under pressure adds
an accepted-drift entry, the finding disappears, the number improves, and
nothing changed. **That is not hypothetical here.** `check_invariants.py` held
three true, documented, printed divergences for nine months and exited 0 the
whole time, and `config/reference_drift.json` now carries **19** accepted
entries, one of which I added today.

**So the rule I would fight for: a suppression is a finding of class 5, counted
in the total, with a mandatory `expires_on`.** An expired suppression is a
finding whether or not anyone renews it. The number then measures *"things we
are living with"* rather than *"things we have not yet hidden"*, and it can
still be driven to zero -- by fixing or by deliberately re-dating, in a commit,
with a name on it.

**The cost, stated honestly: the number starts high and goes UP before it goes
down**, because 19 existing suppressions become 19 findings on day one. **A
hygiene number that starts at zero is measuring nothing.**

## Shape of the mechanism -- sketch only

Each repo owns its own detection and emits a file in one agreed shape.
`coordination` fetches and sums. **Reference, do not copy** (`coordination#15`):
the aggregate holds no findings of its own, only pointers.

    # per repo, e.g. pdoom-data/data/hygiene/findings.jsonl
    {"class": 6, "claim": "data/serveable/.../manifest.json:total_events=28",
     "referent": "all_events.json record count=1194",
     "first_seen": "2025-11-09", "suppressed_until": null,
     "check": "scripts/validation/check_invariants.py"}

Three properties worth arguing about now rather than after it is written:

**Every finding names the check that produced it.** A finding nobody owns is a
finding nobody fixes.

**Every finding carries `first_seen`.** Age is the most useful sub-number you are
not currently asking for -- *274 days* is a different fact from *274 findings*,
and the oldest contradiction is usually the most embarrassing and the cheapest
to fix.

**No finding is created by the aggregator.** If `coordination` can mint findings,
the aggregate becomes a claimant, and this whole exercise is about claimants that
are not checked.

## What this is NOT, so scope does not creep

**Not a linter.** Style, coverage and complexity are not contradictions.

**Not an issue tracker.** A contradiction is fixed or suppressed; it does not get
groomed, prioritised or assigned a sprint.

**Not a per-repo score to compare seats against each other.** The instant it
ranks seats it starts producing the behaviour it exists to detect.

## Open questions for `coordination` specifically

1. **Where does the aggregate live and what publishes it?** A file, an issue, a
   printed line on the daily sheet? Pip reads paper first.
2. **Cadence.** Recomputed per push, per day, or per printed report? The
   monitoring rule says state has to be pushed, not polled.
3. **Does the Jira layer emit too?** `PDOOM-4` is a real finding and it lives in
   neither GitHub nor a repo. If Jira is in scope, that changes who can detect.
4. **Does a seat's own prose count as a claimant?** `CLAUDE.md` produced two of
   the seven instances above. I think yes, and I think it is the hardest part.
