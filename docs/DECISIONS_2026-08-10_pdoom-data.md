# pdoom-data -- decision sheet, Mon 2026-08-10

**There are no open pull requests in `pdoom-data`.** All three merged this
morning and `main` is green on both workflows. **Nothing on this sheet is
blocked on another seat.** The asks are at the front; the reasoning is behind
them.

---

## THE ASKS -- one line each, yes or no

**A1. Split the corpus?** `timeline_events` keeps the 28 real events;
a new `research_corpus` carries the 1,166 arXiv records; `all_events.json` is
frozen byte-for-byte until both consumers migrate. **YES / NO / DISCUSS**

**A2. Remove `safety_researcher_reaction` and `media_reaction` from the
producer?** They are a dice roll over five and three fixed strings, published as
what named researchers think. **YES / NO / DISCUSS**

**A3. Delete rather than import `#4`-`#9`, `#17`, `#18`, `#19`?** Nine issues,
none started, none with a consumer, three of them older than any producer this
repo has. **YES / NO**

**A4. `#32` -- two privacy-flagged records still need a human decision.**
Do you want them in front of you this week? **YES / NO**

**A5. The git-history rewrite: has the rule you were forming landed?**
Deferred by you on 2026-08-09 pending a general rule, not pending this repo.
**LANDED / STILL FORMING**

**A6. Are the four workshop bets still scored Saturday 2026-08-16?**
`pdoom-data`'s was re-scoped mid-workshop to cover all three repos.
**YES / MOVE**

**Struck since Sunday, needs no answer:** the empty-commit push probe. The
question answered itself this morning -- see below.

---

## WHAT LANDED TODAY

**`#74` -- the ASCII backlog is cleared.** Nineteen files, 1,175 substitutions.
`Development Documentation CI/CD` is green on `main` for the first time. The
warning in `CLAUDE.md` saying not to clear it **was stale by eleven days**: the
job it protected was commented out on 2026-07-30, and a commented job cannot run
whether the gate above it is red or green.

**`#69` -- the transcoding gate**, which catches the corruption species that
injects plausible printable characters and passes every other check.

**`#72` -- the privacy fix, and its guard.** Ten records in the public zone plus
306 occurrences in `data/transformed/`, a tracked zone no redaction run had ever
listed. The scan now runs in CI, gating on an independently written scanner
rather than on the redaction pattern, **and it has been observed going red**
(run `31342812917`) because a green guard proves nothing.

**The push trigger answered itself.** Merging `#74` fired two `push` runs on
`main`, both green. So the subscription is alive and the 2026-08-06 silence was
transient -- most likely the same platform window in which `pdoom1-website` had
six workflows cancelled that evening. **No probe needed.**

**Jira export delivered**, ahead of 14:30. 39 open issues, eight epics, tiers
11/15/13, commit `de583d1`. Three issues were closed rather than exported
because today's merges completed them and `Closes pdoom-data#30` is not a form
GitHub honours without the owner.

---

## THE TWO THINGS WORTH YOUR ATTENTION, AND WHY

**The corpus.** `docs/CORPUS_PROPOSAL_2026-08-09.md`, printed behind this sheet.
The measured position: **995 of 1,166 descriptions are a section heading rather
than a description**, the raw dump carries authors, dates, DOIs and full text
that the projection throws away to make room for invented fields, and **the dump
contains no abstracts at all**, which is why the descriptions are what they are.

**`#65`'s headline is true and misleading, and this is the correction that
matters most.** It says 1,166 of 1,194 events fail `event_v1`. They do. The
failures are an undeclared key, an empty array, and 24 over-length descriptions
-- **and all 24 are over-length because the redaction string is longer than the
address it replaced.** `event_v1` is not testing anything that is wrong. The
corpus could be made fully schema-valid in an afternoon without changing any
record's meaning. **If that reaches Jira as "1,166 records are broken" it will be
worked as an emergency it is not.**

**The invented quotes.** `safety_researcher_reaction` on all 1,166 bulk records
is `random.choice` over five strings seeded on the record id, and
`pdoom1-website` renders it publicly **inside quotation marks**. `media_reaction`
likewise, over three. The website independently built a "Placeholder - Needs Real
Quote" badge for all 1,194 -- **a consumer paying for a producer's decision**,
which is the ADR-001 boundary exactly. **No gate in this estate would ever have
caught this**, because every gate asks whether a value is well formed and none
asks whether it is true.

---

## NOT THIS SEAT'S, FLAGGED ONLY

**`pdoom1-website` has 5 open PRs**, four of them from the weekend, all waiting
on you. They are not printed here: printing another seat's pack from this one is
the duplicate-pack failure the pen ruling exists to prevent.
