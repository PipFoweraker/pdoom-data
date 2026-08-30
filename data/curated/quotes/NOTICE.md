# If you have found your own words in this directory

This is a **research index**, not a publication queue, and it is worth being
clear about the difference.

## What this directory is

`quotes.jsonl` holds short passages about the difficulty of AI safety that
someone thought might suit a screen in a game called p(Doom)1. Most of them,
right now, belong to people who have not been asked. Each record carries the
author's name, a link to where it was published, the date, and a field saying
what basis exists for using it.

For most records that field currently reads `not_yet_asked`. That means exactly
what it says: **found, not asked, not used.**

## What is actually in the game

Nothing from here, unless it carries a named basis: either a licence that
permits it, or a person who said yes.

That is not a promise, it is a build step. `scripts/build/project_quotes.py`
emits `data/serveable/api/quotes/approved.jsonl`, which is the file the game
reads, and it copies across only records with a permission basis. There is no
flag to make it emit anything else. The withheld records appear in that build's
lineage as an id and a status, **with no text**, because printing the words we
are declining to publish would republish them.

## Why the candidates are visible at all

Because the alternative is a private list, and a private list of people's words
is worse. Here you can see the exact passage, what it is being considered for,
and that nobody has used it. It is also how this repository works generally:
judgement is recorded where it can be checked rather than held on one machine.

## If you would rather not be in it

Say so and it will be honoured, without needing a reason.

- Open an issue at <https://github.com/PipFoweraker/pdoom-data/issues>, or
- write to the address on the repository owner's GitHub profile.

The record will be set to `withdrawn`, which is a permanent state: the gate
refuses to serve it, and the row stays in the file carrying the reason so that
nobody who never saw your message can quietly reinstate it later. If it had
already reached the game, it comes out in the next build.

You can also ask for something narrower, and all of these are supported:

- **a correction**, if the quote is inaccurate or the link is wrong
- **a different attribution**, including initials or full anonymity
- **a note that your views have changed**, carried beside the quote
- **removal from one placement but not another**

## The standing position

These are real people's words about a real problem, quoted because they said
something true and hard to say better. Being asked should feel like being
asked, not like being notified.
