# Print packet style guide

> **SUPERSEDED, pending deletion. Do not build on this.**
>
> The canonical reference is `PipFoweraker/coordination` ->
> `PRINT_AND_PROCESS_REFERENCE.md`, with tooling at
> `coordination/tools/walkpack/build_walkpack.py`. This file was written on
> 2026-07-31 in ignorance of it, and is one of three print systems three
> repositories built independently that day.
>
> Deletion is pending only on coordination#2 ask A1. Until then it is kept so
> the reference-code convention below can be compared against theirs rather
> than lost silently.
>
> **What this file got wrong**, measured against the canonical reference:
> it advertises "A4 or Letter" where the queue default is Letter and AU work
> must pass `paper=A4` per job; it has no boxed `PRINTED` timestamp, so a
> reprint cannot be distinguished from an original -- a failure that cost Pip
> re-answered questions on 2026-07-31; no staleness line; no `supersedes:`;
> and no hand-typed `PAGE n OF m`, which the canonical reference calls
> load-bearing because Chromium cannot generate page numbers and a clipped
> stack must reveal a missing page. It also treats sides as a preference when
> the reference makes it a correctness rule: checklists and runsheets print
> **simplex**, because a back face hides half the checklist on a clipboard.

For documents that get **printed, carried, annotated and dictated against**.
Pip reads these on walks, away from screens, on a clipboard. Screen rendering is
the secondary case, and the design is optimised accordingly.

Stylesheet: `tools/print/packet.css`
Skeleton: `tools/print/TEMPLATE.html`
Worked example: the 2026-07-31 session review packet.

---

## The one rule that makes these work

**Every item carries a short, stable reference code in the left gutter.**

`D1`, `Q3`, `S2`, `W1`, `R4`. Not decoration and not numbering-for-its-own-sake:
someone dictating a response to a sheet of paper needs a token they can say
aloud. *"Q3, my answer is..."* is unambiguous when it comes back to a screen.
"The third paragraph under the second heading" is not.

Prefixes encode the kind of item, so the code alone says what the response is
for:

| Prefix | Meaning |
|---|---|
| `Q` | needs a decision from the reader |
| `D` | a decision already made, presented for confirmation |
| `S` | shipped, informational |
| `W` | waiting on someone else |
| `R` | re-entry checklist item |

Codes are stable **within one sheet only**. Do not try to make them global; a
packet is a snapshot, and a code that means two things across two sheets is
worse than no code.

## Tokens

    --paper    #FCFCFB   warm-neutral ground
    --ink      #16201E   near-black, faint green-slate bias
    --ink-soft #4A5652   secondary text, rules, filled ticks
    --rule     #C9CFCC   structural rules
    --marine   #1E4F52   the accent: section structure, reference codes
    --flag     #9A6A18   muted ochre, ONLY for items needing a decision

The neutrals carry a slight hue bias toward the accent so they read as chosen
rather than as an unconsidered mid-grey.

**`--flag` is rationed.** It marks items that need a human decision and nothing
else. If everything is flagged, nothing is, and the reader loses the one signal
the sheet exists to carry.

## Type

No webfonts. The Artifact CSP blocks font CDNs, and a silent fallback on a
document that is about to be printed is worse than a considered system stack.

    body      Charter / Bitstream Charter / Cambria / Georgia
    labels    system sans, uppercase, letter-spaced, small
    ids/paths ui-monospace / Cascadia Mono / Consolas

Serif for body text because these are read at arm's length, outdoors, on paper,
where serifs hold up better than a screen-tuned sans. Sans is reserved for
labels, reference codes and table headers, so a glance distinguishes structure
from content.

Measure stays near 68ch. Headings get `text-wrap: balance`.

## Print behaviour

- **Tokens are overridden wholesale inside `@media print`**, so components never
  need print-specific rules. Pure black on pure white: no ink spent on
  background fills, maximum contrast in sunlight, and no surprise when a printer
  renders a tint badly.
- **`@page { margin: 17mm 15mm 18mm; }`** so the page supplies its own margins
  and the reader does not have to configure the browser dialog.
- **`break-inside: avoid` on every `.item`.** A question split across a page
  break is a question that gets answered wrong.
- **`break-after: avoid` on `h2`**, so a section heading never strands itself at
  the foot of a page.
- **10.5pt body.** Smaller than screen because print resolution carries it, and
  fewer sheets means a lighter clipboard.
- **The print bar is `display: none`** in print.

## Components

`.item` is the workhorse: a two-column grid with the reference code in the
gutter. Everything else composes inside its `.body-col`.

`.tick` is a real bordered box, not a checkbox glyph or an emoji. Glyphs render
inconsistently across printers and some drop out entirely; a CSS box always
prints.

`.ruled` gives ruled lines under an open question. They serve two purposes at
once: somewhere to write, and a visual cue that a response is expected.

`.clipboard` puts *Reviewed / Date / Sheet n of m* under the masthead, with
`.fill` underlines to complete by hand.

`.callout` for a single important consequence. `.callout.warn` for the ones with
a cost attached. Use sparingly; a page of callouts is a page with no emphasis.

## Writing for a printed sheet

- **State the cost of a late answer**, not just the question. The reader is
  deciding what to think about on a walk and needs to triage.
- **Order by decision cost, not by topic.** The expensive-if-late question goes
  first.
- **No live links as the only route to information.** Paper cannot be clicked.
  Reference an issue number, then say enough that the item stands alone.
- **Include the counts.** `140 accept, 64 unsure, 2 privacy` beats "mostly
  accepted", especially when the reader cannot query anything.
- **Say what is NOT worth doing** and why. A recommendation to skip something is
  as useful as a recommendation to do it, and it is the part a reader cannot
  reconstruct.

## Reuse

Copy `tools/print/packet.css` into a `<style>` block in the artifact HTML.
Do not `<link>` it: published artifacts run under a CSP that blocks external
stylesheets, and it will fail silently.

For Artifact publishing, omit `<!doctype>`, `<html>`, `<head>` and `<body>` --
the page content is wrapped at publish time. Set a `<title>`.
