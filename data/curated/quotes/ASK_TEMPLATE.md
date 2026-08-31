# Asking for permission

The sourcing research found that for LessWrong, the Alignment Forum, pre-2022
EA Forum posts, most personal blogs, books and podcasts, **there is no licence
and asking is the only lawful route**. It also found that asking well is the
single cheapest form of risk reduction available, and it costs one email.

This file exists so sending one takes five minutes rather than an hour.

## What every ask must contain, and why

Drawn from the 2026-08-30 sourcing brief. Each item is here because leaving it
out is a known failure.

1. **Who is asking and what the project is**, in one line.
2. **The tone of the thing.** They are consenting to a CONTEXT, not to a reuse.
   A dark and often funny game is a different proposition from a documentary,
   and saying so plainly is the difference between consent and a surprise.
3. **The exact quote, verbatim, as it would appear.** Never paraphrased.
4. **Where it appears, described concretely.** "On the screen shown when a
   player's run ends" is the fact that matters, and burying it is how people
   end up feeling misled by a technically accurate request.
5. **How they will be credited**, and an offer to change it.
6. **An easy no.** Explicitly: no reason needed, no awkwardness.
7. **What they can ask for later**: correction, re-attribution, anonymity, a
   note that their views have changed, or withdrawal.
8. **What happens by default.** No reply means NO USE. Never "if I don't hear
   back I'll assume it's fine."

## The template

> Subject: Permission to quote you in a game about AI safety
>
> Hi [NAME],
>
> I'm Pip Foweraker. I'm building p(Doom)1, a free and source-available game
> about running an AI safety organisation: you manage researchers, money and
> attention, and you usually lose. It is not finished.
>
> When a player's run ends, I'd like to show a short real quote about why this
> problem is genuinely hard, the way Call of Duty puts a line about the
> difficulty of war on its death screen. The point is to tell someone who has
> just lost that this is hard for everyone who has ever tried it, and that
> trying again is the reasonable thing to do. Most players will not already be
> convinced the problem is difficult. That is who the quotes are for.
>
> I would like to use this, of yours:
>
> > [EXACT QUOTE]
>
> From [TITLE], [DATE]: [URL]
>
> It would appear on that end-of-run screen, credited as "[CREDIT LINE]", with
> the source shown next to it so a player can go and read the whole thing.
>
> **Please feel free to say no.** You do not need a reason and it will not be
> awkward. If you would rather I used a different passage, or credited you
> differently, or used initials or no name at all, any of those are fine.
>
> If you do say yes, you can change your mind at any point afterwards. You can
> ask for a correction, a different attribution, a note that your views have
> changed, or removal altogether, and it comes out in the next build. There is
> a public record of every quote and its status here, including this one:
> https://github.com/PipFoweraker/pdoom-data/tree/main/data/curated/quotes
>
> If I don't hear back, I won't use it.
>
> Thanks either way, and thanks for writing the thing in the first place.
>
> Pip

## Notes on particular asks

**Two permissions, not one.** Quotes from 80,000 Hours transcripts need both
the speaker and 80,000 Hours, whose terms are explicitly restrictive. That
covers the Stuart Russell and Chris Olah candidates. Ask the speaker first: a
yes from them makes the second ask a formality.

**Co-authored.** The two Embedded Agency quotes are Scott Garrabrant AND Abram
Demski. Both must be asked, and it is one email each rather than one between
them.

**Ask about several at once.** The list is grouped by author for this reason.
Karnofsky, Cotra, Ngo, Yudkowsky and Garrabrant each have two or three
candidates, and asking about all of them in one message is less work for them
than two messages a fortnight apart.

**A warm introduction still needs an easy no.** Where an ask arrives through a
mutual acquaintance it carries social weight a cold email does not, so the
line about no being fine matters more rather than less.

## When a reply arrives

Set `permission.basis` to `granted` and fill in `granted_by`, `granted_at`,
`granted_via` and `context_shown_to_author`. That last one is the paragraph
describing the end-of-run screen; the gate refuses a grant without it, because
a yes given without being told where it goes is not a yes for that place.

On a no, set `basis` to `refused` and record the reason. The row stays in the
file permanently so that nobody who never saw the refusal can reinstate it.

Then capture an archive snapshot of the source, add a placement, and it will
project into the served file on the next build.
