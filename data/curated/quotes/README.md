# quotes

Real people's real words about AI safety, and the basis on which the game may
show them.

**Curated zone: not reproducible.** A permission is a conversation someone had.
Delete this and it has to be had again.

## The one rule

**Nothing is servable until a named basis says it may be.** A quote is born in
`not_yet_asked`, which is an absence rather than a permission, and
`scripts/validation/check_quote_permissions.py` refuses to let an absence
become a display.

This is the same rule as ADR-001 pointed at quotations rather than at verdicts.
It is here in this shape because the alternative already happened: 1,194 served
events carried invented reaction text attributed to unnamed safety researchers,
for months (pdoom-data#92, #76). A corpus of real quotes has that same failure
mode with a real person on the other end of it.

## The six states, and which two are permission

| basis | servable | means |
|---|---|---|
| `licence` | yes | A public licence permits it. Named, with a URL. |
| `granted` | yes | A person said yes, to this quote, for this placement. |
| `not_yet_asked` | no | The default. An absence. |
| `asked_no_reply` | no | **Silence is not consent.** |
| `refused` | never | They said no. Permanent. |
| `withdrawn` | never | They said yes and later said no. Permanent. |

`refused` and `withdrawn` rows stay in this file forever, carrying their
reason. A refusal that is deleted is a refusal the next person overturns
without ever knowing it happened.

## What the sourcing brief established

Researched 2026-08-30, from the primary terms of each platform.

**LessWrong and the Alignment Forum grant no third-party reuse right at all.**
Their terms license MIRI to operate the site; that licence does not extend to
anyone else, and there is no per-post Creative Commons option. These are the
two most quote-dense sources for this subject and **neither can ever rest on a
licence.** Only a person saying yes will do. The gate enforces this by
platform, so it cannot be filled in wrongly by accident.

**The EA Forum is split by date.** CC BY 4.0 is mandatory from 2022-12-01.
Earlier posts are ordinary copyright unless that author added a licence clause
to that specific post. The date is load-bearing and the gate checks it.

**arXiv has no site-wide licence.** Abstracts are released as CC0 metadata and
are quotable. Full text is whatever the author chose, the modal choice grants
no reuse right at all, and two of the six options are share-alike.

**Distill is CC BY**, though the version varies by article. **gwern.net is
CC0.** Zvi Mowshowitz's Substack carries a bespoke attribution licence. Those
are the exceptions among personal blogs; most default to ordinary copyright
with no statement, which means ask.

**Fair use is not the shortcut it looks like.** A quote placed atmospherically
on a death screen adds no commentary and is therefore not transformative, which
is the factor that usually carries a fair-use argument. `Harper and Row v.
Nation Enterprises` (1985) turned on roughly 300 words and still went against
the quoter. UK fair dealing is narrower again and may not reach a balancing
test at all.

## Context collapse is the ethical risk, separately from the legal one

A 2018 forum comment appearing on a 2026 death screen has lost its thread, its
audience, and possibly the author's current view. The term is Marwick and boyd
(2011). `context_note` records what the person was actually talking about, and
`context_shown_to_author` records what we told them about where it would
appear, because **consent is to a context and not merely to a reuse.** A yes
given without being shown the death screen is not a yes for the death screen.

Moral rights make this a legal question too, not only a courteous one: the
right to be correctly attributed and to object to derogatory treatment survives
any licence, and is broader outside the United States.

## A person can always change their mind

`id` is stable forever precisely so that a request years later to correct,
re-attribute or withdraw can be executed without re-deriving which line in the
game belongs to whom. Set `basis` to `withdrawn`, record the reason, and the
gate does the rest.
