# Printing: not owned here

**The canonical reference is `PipFoweraker/coordination` ->
`PRINT_AND_PROCESS_REFERENCE.md`.** Tooling is
`coordination/tools/walkpack/build_walkpack.py`. One renderer, one place.

`tools/print/packet.css` and `tools/print/TEMPLATE.html` were deleted on
2026-08-02 (Pip, `pdoom-data#55` A4; coordination seat, `coordination#2` A1).
They were a parallel print renderer built here on 2026-07-31, one of three that
three repositories produced independently on the same day. The walkpack tool
already carries things a fresh template does not: the boxed full-date print
stamp, the staleness line, per-job duplex and A4 via SumatraPDF, and the
decisions-on-the-cover block.

To be clear about blame, since this repo's check-in overstated it: the
coordination reference did not exist until 2026-08-01, after this stack was
built. The duplication was a missing registry, not a missed document.
`coordination` is that registry.

---

## What survives: the reference-code convention

The coordination seat ruled this **kept and made canonical there**, not binned
with the CSS. It is reproduced here only as the source text for that port
(`coordination#2` A1). **When the port lands in
`PRINT_AND_PROCESS_REFERENCE.md` section 2, delete this file.**

### The convention

Every item on a printed sheet carries a short, stable reference code in the
left gutter: `Q1`, `D3`, `S2`, `W1`, `R4`.

Not numbering for its own sake. Someone dictating a response to paper needs a
token they can say aloud. *"Q3, my answer is..."* survives automatic speech
recognition intact; *"the third paragraph under the second heading"* does not.

The prefix encodes the kind of item, so the code alone says what sort of
response it wants:

| Prefix | Meaning |
|---|---|
| `Q` | needs a decision from the reader |
| `D` | a decision already made, presented for confirmation |
| `S` | shipped, informational |
| `W` | waiting on someone else |
| `R` | re-entry checklist item |
| `A` | an ask, where the sheet is a memo rather than a status pack |

**Codes are stable within one sheet only.** A global scheme makes one code mean
two things across two sheets, which is worse than no code. The sheet's memo ID
disambiguates.

### Why it is worth keeping

Independent convergence, which is why the coordination seat took it rather than
discarding it with the renderer: Pip has answered `R1`-`R10`, `D1`-`D7`,
`K1`-`K8` and `W1`-`W5` in dictation across three days, arrived at from the
other direction. A single spoken letter-plus-digit is the highest-surviving
token class in a transcription loop, and spoken issue numbers are among the
lowest -- three different tickets once transcribed as "HQ 15".

### Related writing rules, offered with it

- State the cost of a late answer, not only the question. The reader is
  triaging what to think about on a walk.
- Order by decision cost, not by topic.
- No live link as the only route to information. Paper cannot be clicked.
- Include the counts. "140 accept, 64 unsure, 2 privacy" beats "mostly
  accepted" to someone who cannot query anything.
- Say what is **not** worth doing, and why. That is the part a reader cannot
  reconstruct.
