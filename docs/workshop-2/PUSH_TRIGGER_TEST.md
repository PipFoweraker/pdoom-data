# Push-trigger test -- pdoom-data `main`

**The ask: may an empty commit be pushed to `pdoom-data`'s `main`?** It is the
last untested half of the class-8 diagnosis from Workshop 2 (`coordination#47`).
**Run it yourself with the steps below, or say go and the seat runs it.**

## What is already known, so the test is not repeated work

**`main` had no CI for 69 hours and nothing showed red.** Two merge commits carry
zero check runs -- `1c8678c` (2026-08-06T22:09:01Z) and `1ac7169` (22:16:16Z) --
while PR head commits on the same days carry three each.

**Seven hypotheses are already eliminated.** Not a `GITHUB_TOKEN` push (both
merges show `committer_login: web-flow`, `actor_login: PipFoweraker`); no `paths:`
filter on the workflow; workflow `active`; the `on:` block byte-identical at the
last good run and at the failure; Actions enabled; repo public, not archived; and
`check_workflow_disarm.py` does not touch `data-integrity.yml`.

**Dispatch works and `main` is green on its own merits.** Run `31287938301`,
event `workflow_dispatch`, ref `main`, conclusion `success`, 2026-08-09 11:16.
**So the workflow, the runner and the tree are all fine.** `pull_request` fires,
`workflow_dispatch` fires. **Only `push` to `main` appears not to.**

**This test is the only remaining way to tell a dead event subscription from a
one-evening platform failure.** Nothing else distinguishes them.

## The steps

**Step 1 -- baseline, so the result is unambiguous.** Note the newest run before
touching anything.

    gh run list --repo PipFoweraker/pdoom-data --branch main --limit 3

Expect the newest to be the manual dispatch `31287938301`, and before it a gap
back to 2026-08-06T01:00:19Z.

**Step 2 -- the probe commit.** Empty, so it changes no file and no data.

    cd G:\Documents\Organising_Life\Code\pdoom-data
    git checkout main
    git pull --ff-only
    git commit --allow-empty -m "probe: does a push to main dispatch a run"
    git push

**Step 3 -- wait about 30 seconds, then ask the API, not the tab.**

    git rev-parse HEAD
    gh api repos/PipFoweraker/pdoom-data/commits/<that SHA>/check-runs --jq .total_count
    gh run list --repo PipFoweraker/pdoom-data --branch main --limit 3

**Ask the count, not the colour.** The whole defect is that a zero and a green
look identical on every page a person reads.

## Reading the result

**If the count is 1 or more -- the subscription is ALIVE.** The two zero-run
merges were then a transient failure on the evening of 2026-08-06, and there is a
correlation waiting: `pdoom1-website` had six workflows across four schedules go
`cancelled` between 18:29Z and 20:12Z the same evening (runs `31126296161`,
`31126044404`, `31125967449`, `31127433715`). **Next step in that case: check
GitHub's published incident history against both windows.** Neither repo could
have formed that hypothesis alone.

**If the count is 0 -- the subscription is DEAD**, and it is a configuration
question with an owner rather than a mystery. Check repo Settings -> Actions ->
General -> Actions permissions, then open GitHub Support citing both merge SHAs,
this probe SHA, and the successful dispatch `31287938301` as proof the workflow
itself runs.

**Either way, post the number into `coordination#47`.** It is the one open
question the workshop minute could not close, and it closes with a single integer.

## What it costs and what it cannot break

**An empty commit on `main` is permanent history and changes no file.** The
workflow it may trigger is read-only -- `permissions: contents: read` -- and takes
about 25 seconds. **Nothing in `data/serveable/` can be written by it.** The only
irreversible part is one line in `git log`, which is also the evidence.

## Why the seat did not just run it

**A write to `main` while you were absent by design.** The chair ruled at 10:15
that it was not a seat's call to make unattended and declined to reverse that at
11:22 when it became inconvenient. **The ruling is in the workshop record**, so
reversing it quietly would have cost more than the three days of silence already
had.
