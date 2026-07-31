# ADR-008: Provenance and annotation model - copy W3C, do not reinvent

- **Status:** Accepted (Pip, 2026-07-31)
- **Date:** 2026-07-31

## Context

Three requirements arrived together and turned out to be one structure.

**A traceability stack.** Pip's framing: *"this is the game's mechanical
implementation of this event, curated by these opinions and this decision(s)
that accepted/promoted it to attention from the dataset and then into the game
engine in such and such a fashion."*

**A contribution loop.** People encounter events through pdoom1-website and
through the game, form opinions, and feed them back; that should inform both the
dataset's selectors and the game's developers.

**Without polluting the dataset.** pdoom-data is itself a research corpus. The
worry was that community reaction would degrade it.

The fog in all three came from one word. **"Event" was doing three jobs:** a
thing that happened, what someone thinks about it, and what an audience did with
it. The first is an immutable sourced fact; the second is a contestable authored
opinion; the third is a fact about the audience rather than about the event.

## Decision

### 1. Three record types, joined by id. Never one record type with more fields.

| Layer | Nature | Mutability |
|---|---|---|
| **Fact** | a thing that happened, with sources | immutable |
| **Annotation** | what someone thinks about a fact | append-only, always attributed |
| **Reception** | what an audience did with a fact | append-only, pseudonymous |

### 2. The anti-pollution rule: reference, don't embed

An annotation or a reception record **points at** a fact. It is never a field on
the fact. The test, in the same family as the fact/opinion firewall test:

> **Delete every annotation and every reception record. Is the dataset still
> complete and correct?**
> Yes means they were never pollution. No means something got embedded that
> should have been referenced.

This is the wiki-article-versus-talk-page distinction, and it dissolves the
pollution worry structurally rather than by discipline.

It also reframes the goal. Reception data is **not a compromise tolerated beside
the real dataset** -- "what people thought about AI-safety events, over time, as
they happened" is a research corpus in its own right, and one almost nobody has.
It is only pollution when stored in the wrong place.

### 3. Copy W3C vocabularies. Do not adopt the full standards.

Pip's ruling: *"copying rather than adopting where possible ... troubleshooting
will then let us rely on their known solution sets also. We don't need to
reinvent this particular wheel."*

- **Provenance: W3C PROV-O.** Use its terms and relations verbatim as field
  names -- `Entity`, `Activity`, `Agent`, `wasDerivedFrom`, `wasGeneratedBy`,
  `wasAttributedTo`. Do **not** adopt RDF, triple stores or SPARQL.
- **Annotations: W3C Web Annotation Data Model.** Use `target`, `body`,
  `creator`, `created`, `motivation` (`assessing`, `classifying`, `commenting`,
  `questioning`) verbatim. Do **not** adopt JSON-LD framing or the full protocol.

**Why copy rather than invent:** when something goes wrong, "PROV-O
wasDerivedFrom cycle" is a searchable question with existing answers. A
home-grown `derived_from_ref` is a question only we can answer, forever.

**Why copy rather than fully adopt:** an RDF stack is a large operational
commitment for a repository whose consumers read JSON files. The standards' value
here is their *conceptual model and naming*, which is free; their serialisation
and tooling is the expensive part and buys us nothing today.

**Cheap insurance, and it should be taken:** ship a static JSON-LD `@context`
mapping our field names onto the real PROV-O and Web Annotation IRIs. Costs one
file that nothing has to read. Buys the option of lifting the data into genuine
PROV tooling later **without renaming a single field**. Skipping this is what
would make "copy" a trap rather than a shortcut.

### 4. Every hop names an agent

The provenance chain runs:

    fact ingested     agent: adapter            when: dump timestamp
      -> surfaced     agent: salience profile   when: build
      -> reviewed     agent: named human        when: verdict timestamp
      -> exported     agent: export profile     when: pack build
      -> implemented  agent: pdoom1 developer   when: game commit   [pdoom1 owns]

The final hop is deliberately not ours. pdoom-data records the chain to the
boundary and exposes a stable id; pdoom1 references it back. Neither repository
needs to own the other's half.

**A hop with no agent is prohibited.** That is where accountability disappears.
The live counterexample is the A/B/C/D tier score: it has no recorded author and
no rationale, and as a result nobody noticed for months that it ranks provenance
and length rather than importance.

### 5. Reception is pseudonymous microdata

- **Per-person granularity, not aggregate.** One row per respondent.
  Pre-aggregation destroys the analysis and cannot be undone later.
- **Per-person does not mean per-identified-person.** Rows carry a stable
  pseudonymous id, not an identity.
- **In-game reactions carry no player identity at all.** pdoom1 is maximally
  privacy-respecting; the game side has no identity to leak.

Retrofitting anonymity onto collected data is the expensive direction, so this is
settled before anything is built rather than after.

### 5a. Attribution is opt-in, and the preference persists

Pip's ruling: *"opt in attributions through the chains but with persistent
preference memory seems best overall for managing these things and also legally
and morally complies."*

- **Default is pseudonymous.** A contributor is a stable pseudonymous id unless
  they choose otherwise.
- **Attribution is opt-in, per contributor, and remembered.** The preference is
  stored once and applied to every subsequent contribution across every channel,
  rather than asked each time. Asking repeatedly produces both consent fatigue
  and inconsistent records for the same person.
- **Nobody is required to be identified.** Pip contributes under his real name
  by choice; that is a personal decision and is not the default for anyone else.

**The consequence that must be stated to contributors at opt-in time:** a
preference change applies **prospectively only**. Once a record has been
published with attribution, copies already taken cannot be recalled -- that is a
property of publishing, not a gap in our implementation. The existing tombstone
mechanism removes a record from *our* copy and records that a removal happened;
it cannot reach a copy someone else already holds.

Saying so plainly at the point of consent is the difference between informed
opt-in and a promise we cannot keep.

### 5b. The bar is institutional usability, not minimum compliance

Pip's framing, paraphrased: this data is no good if a collaborator at an
institution cannot use it because pdoom-data has a poor standing on data ethics.

That sets the target above "technically lawful". The properties a researcher's
institution will look for, and which we should therefore be able to evidence:

- a stated lawful basis and a real consent record, not an assumed one
- data minimisation -- in-game reactions carry no identity because they do not
  need one, not because we stripped it later
- a documented withdrawal path, with its limits stated honestly (see 5a)
- provenance sufficient to answer "where did this row come from and who agreed
  to it being here", which is what ADR-008 point 4 already requires

These are cheap to build in now and expensive to retrofit, which is the whole
argument for settling them before the first contribution is collected.

### 6. Channels stay separate. Never sum them.

Website contributions are deliberated and low-volume; in-game reactions are
reflexive and high-volume. **Summing them destroys the deliberated signal with
the reflexive one** -- forty considered comments vanish into ten thousand clicks.
Keep them as distinct annotation sets with distinct `motivation` values and let
each consumer weight them.

This is ADR-007's grading-not-gating stance applied to contributions: we grade
the source, the consumer chooses the weighting.

## Consequences

- Queries need a join. Accepted; the fact corpus stays clean and citable.
- Annotations become independently publishable, which was not previously true.
- Community feedback still never auto-merges. It is input to the next review
  pass, not a change to any record.
- The glossary (#47) must define `fact`, `annotation`, `reception`, `assessment`
  and `motivation` once, rather than three times in three schemas.

## Not yet decided

- Whether the AIRR taxonomy needs a second axis for events about capability,
  funding or institutions rather than harm. Pip: AIRR is fine for now.
- The concrete schemas. Blocked on #43 and pdoom1 DQ-21.

## Related

- ADR-007 (anti-corruption layer)
- ADR-001 (game/data boundary), ADR-002 (nondestructive metadata)
- #39 (declaring epistemic status), #43, #47, #48, #49
- pdoom1 ADR-0015, pdoom1#1052
