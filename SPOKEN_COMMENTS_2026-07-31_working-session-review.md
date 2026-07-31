# Spoken comments -- pdoom-data working session review, 2026-07-31

Source: capture `2026-07-31_141036__e05c8a27` (3:07), transcribed on-device
(faster-whisper `small.en`, audio never uploaded). Reviewing the sheet dated
**30 July 2026, 12:00 start**.

**Status:** EXTRACTED BY CLAUDE, not yet re-read by Pip. Verify item labels
against the original sheet before acting -- ASR does not reliably distinguish
Q/D/S/W prefixes.

## Needs Pip's call -- open questions he asked back

- **Q1** *(underlined three times)*: **which domains it bears on, why it
  mattered, and what it is evidence of** -- specifically around
  *"forward-propagating 'general capability uplift'?"*
- **Q2** -- *"is correct, there is..."*, then: **does AI need a second axis?**
  Possibly an **implementation axis** -- upstream vs downstream sociological
  impact. His example: *"can we [attribute] suicides from depression [to an]
  LLM?"* Proposed cut: **risk vs crime and criminals; government; law and order;
  social/local; interpersonal.**
- **Q3** documentation published: *"I've forgotten the purpose of this. I suspect
  it's been superseded -- please check that and advise."*
- **Q4** legacy modules: **yes**, there was a first pass.

## Rulings

| Item | Ruling |
|---|---|
| D1, D2, D3 | yes -- D3 *"I agree with the additional note on the sanity check"* |
| D4 | yes -- **make it explicit in relation to the heads-up**, and **remind Pip to double-check in ~a fortnight** |
| D5 | yes -- *"we add slowly over time"*; **find another 40 or 50 before 7 [Aug?]** and **add that to Jira** |
| D6 | yes, shipped |
| S1-S4 | yes |
| S5 | **unsure** -- *"I believe it's been done, waiting on other people"* |
| W1, W2, W3 | **come back to me** on all three |

> The spoken date was *"before the 7th of July"*, which is in the past. Almost
> certainly **7 August**. Confirm before the Jira ticket is written.

## General comment on the state of the repository

Verbatim, because the framing matters:

> *"Let's codify these stats but make them invisible by default. Let's make them
> shift to an orchestrator... keeps my analytics addiction [in check]. I don't
> want to be checking these every day -- I probably want to do it once or twice
> a month or once or twice a fortnight. But otherwise, like website analytics, I
> want them tracked but mostly hidden from my day-to-day updates."*

Design consequence: **stats stay collected, stop being surfaced.** Daily views
should not carry them; an orchestrator-level periodic view should.

Also liked, as-is: *"candidates root files, CI green is good, branches, open PRs,
served collections."* -- with one change: **split "served collections" into
sub-categories.** The transcript cuts off mid-sentence at *"frontier labs isn't
going to..."*, so that thought is **incomplete** -- worth asking him to finish it.
