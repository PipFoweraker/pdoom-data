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

## Two kinds of quote, and they are not the same object

**`difficulty`** is the Call of Duty shape. The player lost, and here is
someone saying why this problem is genuinely hard. The speaker is being agreed
with. Attribution and permission are the whole of it.

**`accountability`** places a named public figure's own words beside what
happened afterwards. The speaker is not being agreed with. It needs more, and
the gate enforces four things:

- **Verified against a PRIMARY source**, not against someone else's report of
  the quote. A misquote repeated accurately is still a misquote. Accuracy is
  the single biggest thing standing between this and a problem.
- **A link to the full context.** The answer to "you cropped me" is that the
  whole thing is one click away.
- **The outcome carries its own dated evidence.** Same rule as every date in
  `config/sources.json`, and it matters more here.
- **`speaker_status` recorded.** An executive speaking publicly about their own
  company is not a forum commenter, legally or ethically.

## The framing guard

`framing_text` is anything the GAME says in its own voice around a quote, and
it is the actual risk surface. Reproducing what somebody said is one thing.
Asserting what they knew or intended is another, and it is a much harder thing
to stand behind.

So the gate refuses game-voice framing containing `lied`, `knowingly`,
`deliberately`, `covered up`, `fraud`, `conspired` and their relatives. Give
the dated evidence and let the player do the arithmetic.

**This is not squeamishness, it is the stronger move.** A reader who works out
for themselves that a 2022 assurance did not survive contact with 2024 is more
convinced than one who is told what to think, and the position is far easier to
defend. The juxtaposition does the work; the epithet only adds exposure.

**The guard never touches the quote itself.** If the speaker used one of those
words, that is what they said, and it stands.

It is a drafting guard, not legal advice. The accountability tier warrants an
actual lawyer before anything ships, and Australian defamation law is the
relevant law here rather than the US assumptions most writing on this subject
carries.

## The Australian position, because that is the law that applies

Researched 2026-08-30. Most writing on quoting public figures assumes US law,
where `New York Times v Sullivan` makes a public figure prove actual malice.
**Australia has no equivalent**, and this seat publishes from Tasmania.

**Correction to a comfortable assumption: juxtaposition is not a shield here.**
Australian law reaches defamatory IMPUTATIONS arising from implication and
context, not only express statements. "I only quoted them accurately" answers
whether the quote is true; it does not answer what the screen as a whole
conveys to an ordinary player.

What the framing choice actually does is decide **which imputation** a court
finds, and the defences are imputation-specific. "They said something that did
not survive contact with events" is provable from two dated facts. "They
knowingly lied" requires proving what was in someone's head at the time, which
public statements almost never establish. That is the whole reason the framing
guard exists, and it is a real effect: it is just narrower than "safe".

Three defences do the work, and each has a build requirement:

- **s 25 justification.** Truth of the imputation. Rests entirely on quote
  accuracy, which is why primary-source verification is a hard gate.
- **s 31 honest opinion.** Needs the opinion to rest on "proper material"
  **stated or referenced in the same publication**. Evidence sitting in this
  repository that a player never sees does not count, which is why
  `sources_shown_in_product` is required. It is a UI obligation that only the
  data can record.
- **s 29A public interest.** Judged on whether the belief was REASONABLE, on
  what was actually done. In `Russell v ABC (No 3) [2023] FCA 1223`, the first
  full trial of this defence, **the ABC lost and paid over AUD 400,000** --
  decisively because it did not seek the subject's response. Hence
  `right_of_reply` is required. A declined or ignored request is fine, so long
  as it is documented. Silence from them is acceptable; silence from us is not.

**s 10A serious harm** is a real first gate: a niche game and an already very
public reputation make it contestable. **Corporations with 10 or more employees
cannot sue** (s 9), but s 9(3) preserves the individual's own action, so the
named executive simply sues personally and the corporate exclusion buys
nothing.

**Australia has no right of publicity.** That risk is genuinely low, lower than
a US-focused reader would assume. Defamation is the exposure; personality
rights are not.

**A complaint arrives as a letter first.** A concerns notice under s 12A is a
mandatory pre-litigation step, with 28 days to make an offer to make amends.
Responding well inside that window can end the matter, so the correction and
withdrawal paths in this schema are load-bearing rather than decorative.

**The dominant risk is cost, not merit.** Australian defence costs run from
about AUD 20,000 to 780,000 and there is no anti-SLAPP statute. Tasmania has
its own precedent in the Gunns 20 case, where the claims largely failed and the
chilling effect landed anyway.

Not legal advice. The accountability tier wants a paid hour with an Australian
defamation lawyer on the actual shortlist before anything ships.

## A person can always change their mind

`id` is stable forever precisely so that a request years later to correct,
re-attribute or withdraw can be executed without re-deriving which line in the
game belongs to whom. Set `basis` to `withdrawn`, record the reason, and the
gate does the rest.
