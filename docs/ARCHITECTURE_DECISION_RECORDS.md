# Architecture Decision Records (ADR)

This document records significant architectural decisions for the pdoom-data repository and the broader P(Doom) ecosystem. These decisions should be referenced by developers, contributors, and AI assistants working across the ecosystem.

---

## ADR-001: Game/Data Boundary - Layered Event Architecture

**Date**: 2024-12-24
**Status**: Accepted
**Deciders**: PipFoweraker, pdoom-data team

### Context

The P(Doom) ecosystem serves multiple consumers:
- **pdoom1** (the game) - needs game-ready events with impacts, rarity, reactions
- **pdoom-dashboard** - needs event data for visualization and analytics
- **pdoom1-website** - needs event data for community features and history display
- **Future consumers** - research tools, other games, public APIs

We needed to decide: **Where do game mechanics live?** Options considered:
1. All game data in pdoom-data (single source of truth)
2. All game data in pdoom1 (separation of concerns)
3. Layered approach (defaults in pdoom-data, overrides in pdoom1)

### Decision

**We adopt a layered architecture** where pdoom-data provides game-compatible defaults and pdoom1 can override or extend as needed.

```
LAYER 1: Core Event Data (pdoom-data - immutable facts)
---------------------------------------------------------
| id, title, year, description, category, tags, sources |
---------------------------------------------------------
                           |
                           v
LAYER 2: Game-Compatible Metadata (pdoom-data - sensible defaults)
------------------------------------------------------------------
| impacts, rarity, pdoom_impact, reactions (safety/media)        |
------------------------------------------------------------------
                           |
                           v
LAYER 3: Community Metadata (pdoom-data - separate files)
---------------------------------------------------------
| Player feedback, corrections, suggestions (quarantined) |
---------------------------------------------------------
                           |
                           v
LAYER 4: Game Overrides (pdoom1 - game-specific tuning)
-------------------------------------------------------
| Per-event impact overrides, rarity adjustments       |
-------------------------------------------------------
                           |
                           v
LAYER 5: Game Extensions (pdoom1 - game-only mechanics)
-------------------------------------------------------
| Event chains, trigger conditions, dialogue trees,    |
| scenario assignments, balancing curves               |
-------------------------------------------------------
```

### Boundaries

#### What BELONGS in pdoom-data:

| Data Type | Examples | Rationale |
|-----------|----------|-----------|
| Historical facts | title, description, year, sources | Immutable truth |
| Categorization | category, tags | Shared taxonomy |
| Default game impacts | `{"variable": "cash", "change": 10}` | Usable out-of-box |
| Default rarity | common/rare/legendary | Sensible starting point |
| Flavor text | safety_researcher_reaction, media_reaction | Content, not mechanics |
| Editorial assessment | pdoom_impact | Expert opinion, not game balance |

#### What BELONGS in pdoom1:

| Data Type | Examples | Rationale |
|-----------|----------|-----------|
| Impact overrides | Tuning cash from +10 to +15 | Game balance |
| Rarity overrides | Making an event legendary for gameplay | Game design |
| Trigger conditions | "Only appears after turn 50" | Game mechanics |
| Event chains | "Event A unlocks Event B" | Narrative design |
| Scenario assignments | "Event X only in Hard mode" | Difficulty tuning |
| Dialogue/choices | Player response options | Game UI |
| Probability curves | How rarity maps to appearance chance | Balancing |

#### What STAYS SEPARATE (Community Layer):

| Data Type | Location | Rationale |
|-----------|----------|-----------|
| Player feedback | pdoom-data/community/ | Quarantined for moderation |
| Suggested corrections | pdoom-data/community/ | Human review required |
| Community notes | pdoom1-website DB | Displayed but not merged |

### Consequences

**Positive:**
- pdoom-data events are immediately usable (no assembly required)
- Game team can iterate on balance without touching data repo
- Dashboard and website get consistent data
- Clear ownership: facts = data team, gameplay = game team
- Community can contribute historical facts without game design knowledge
- Multiple games could consume same events with different mechanics

**Negative:**
- Some duplication if pdoom1 overrides many defaults
- Need to document which layer owns what
- Consumers must understand merge order (defaults + overrides)

**Risks mitigated:**
- Coupling: Game changes don't require data repo PRs
- Bottlenecks: Teams can work in parallel
- Confusion: Clear documentation of boundaries

### Implementation

1. **pdoom-data**: Continue current schema (already has game-compatible fields)
2. **pdoom1**: Create `data/event_overrides/` directory for per-event tuning
3. **pdoom1**: Create `data/game_extensions/` for chains, triggers, scenarios
4. **Both**: Reference this ADR in CLAUDE.md and REPO_NAVIGATION.md

### Override Merge Logic (for pdoom1)

When loading events, pdoom1 should:

```python
def load_event(event_id):
    # Layer 1+2: Get base event from pdoom-data
    base_event = fetch_from_pdoom_data(event_id)

    # Layer 4: Apply game overrides if present
    if override := load_override(event_id):
        base_event = deep_merge(base_event, override)

    # Layer 5: Attach game extensions
    base_event['extensions'] = load_extensions(event_id)

    return base_event
```

### Related Documents

- [EVENT_SCHEMA.md](EVENT_SCHEMA.md) - Current event schema definition
- [DATA_ZONES.md](DATA_ZONES.md) - Data lake architecture
- [ECOSYSTEM_OVERVIEW.md](ECOSYSTEM_OVERVIEW.md) - Multi-repo architecture
- pdoom1: `docs/EVENT_OVERRIDE_SYSTEM.md` (to be created)

---

## ADR-002: Nondestructive Metadata Pattern

**Date**: 2024-11-24
**Status**: Accepted
**Deciders**: pdoom-data team

### Context

When annotating events (for game relevance, quality review, community feedback), we needed to decide whether to modify source events or keep annotations separate.

### Decision

**All annotations are stored in separate metadata files, never modifying source events.**

```
data/serveable/api/timeline_events/
  all_events.json           <- Source events (never modified by annotations)
  all_events_metadata.json  <- Annotations (separate file)
```

### Rationale

- Preserves data integrity
- Allows experimentation without risk
- Supports multiple reviewers with different metadata
- Easy rollback by deleting metadata
- Version control of annotations separately from events
- Community feedback can be stored without touching curated data

### Implementation

- Event Browser tool exports metadata separately
- Merge happens at consumption time, not storage time
- Community feedback uses same pattern (quarantine table)

---

## ADR-003: ASCII-Only Data Requirement

**Date**: 2024-11-09
**Status**: Accepted

### Decision

All text data in pdoom-data must be ASCII-compatible. No smart quotes, em dashes, non-ASCII characters.

### Rationale

- Consistent display across all platforms
- Prevents encoding issues in game engine
- Simplifies validation and testing
- Better compatibility with AI/LLM processing

### Implementation

- Validation scripts enforce ASCII compliance
- Pre-commit hooks check for non-ASCII characters
- Documentation in ASCII_CODING_STANDARDS.md

---

## Future ADRs

Reserved for future decisions:
- ADR-004: API versioning strategy
- ADR-005: Event ID namespace conventions
- ADR-006: Multi-game support architecture

---

**Last Updated**: 2024-12-24
**Maintainer**: pdoom-data team
