# CLAUDE.md - AI Assistant Context for pdoom-data

This file provides essential context for AI assistants (Claude, GPT, etc.) working with this repository.

## Repository Purpose

**pdoom-data** is the centralized data hub for the P(Doom) game ecosystem. It provides:
- Historical AI safety timeline events (1,000+ events)
- Game-ready event data with impacts, rarity, and reactions
- Data transformation pipelines
- Schemas and validation

## Critical Architecture Decision: Game/Data Boundary

**READ THIS FIRST**: See [docs/ARCHITECTURE_DECISION_RECORDS.md](docs/ARCHITECTURE_DECISION_RECORDS.md) for ADR-001.

### The Layered Model

```
pdoom-data provides:        pdoom1 provides:
--------------------        ----------------
- Historical facts          - Impact overrides (balance tuning)
- Default game impacts      - Rarity overrides
- Default rarity            - Event chains & triggers
- Flavor text/reactions     - Scenario assignments
- Community feedback        - Dialogue trees
                            - Probability curves
```

### Key Rules

1. **pdoom-data events are game-ready** - They include impacts, rarity, reactions as sensible defaults
2. **pdoom1 can override anything** - Game team owns balance and mechanics
3. **Never put trigger conditions here** - "Appears after turn 50" belongs in pdoom1
4. **Never put event chains here** - "Event A unlocks B" belongs in pdoom1
5. **Facts are immutable** - Title, year, description, sources don't change
6. **Impacts are defaults** - pdoom1 can tune `cash: +10` to `cash: +15`

## Quick Reference

### Repository Structure

```
pdoom-data/
  data/
    raw/                  # Immutable source data (never auto-modify)
    transformed/          # Validated/cleaned/enriched
    serveable/            # Production-ready (consumers fetch from here)
      api/timeline_events/
        all_events.json   # 1,028 events ready to use
  config/schemas/         # JSON schemas for validation
  scripts/                # Transformation pipelines
  tools/                  # Event Browser, utilities
  docs/                   # Documentation (start with DOCUMENTATION_INDEX.md)
```

### Common Tasks

| Task | Command/Location |
|------|------------------|
| Validate events | `python scripts/validation/validate_alignment_research.py` |
| Clean events | `python scripts/transformation/clean.py` |
| Transform to timeline | `python scripts/transformation/transform_to_timeline_events.py` |
| Browse events visually | Open `tools/event_browser.html` in browser |
| Find documentation | Start at `docs/DOCUMENTATION_INDEX.md` |

### Event Schema (v1)

Required fields for timeline events:
- `id` (snake_case, unique)
- `title`, `year`, `description`
- `category` (technical_research_breakthrough, funding_catastrophe, etc.)
- `impacts` (array of {variable, change, condition})
- `sources` (array of URLs)
- `tags`, `rarity`, `pdoom_impact`
- `safety_researcher_reaction`, `media_reaction`

Full schema: `config/schemas/event_v1.json`

## What NOT to Do

1. **Don't add game logic** - No "if player has X, then Y" conditions
2. **Don't modify raw/ directly** - Use transformation pipelines
3. **Don't use non-ASCII** - All text must be ASCII-compatible
4. **Don't auto-merge community feedback** - It goes through human review
5. **Don't create event chains** - Those belong in pdoom1

## Ecosystem Context

```
pdoom-data (you are here)
    |
    +--> pdoom1-website (PostgreSQL, displays events)
    |
    +--> pdoom1 (game, consumes events, adds overrides)
    |
    +--> pdoom-dashboard (analytics, visualizations)
```

## Auto-Approved Commands

The following are pre-approved for this repository:
- `python scripts/validation/*.py`
- `python scripts/transformation/*.py`
- `python -m json.tool`
- `git add`, `git commit`, `git push`, `git pull`, `git fetch`
- `gh issue list`, `gh issue view`

## Key Documentation

Start here:
1. [DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) - Navigation hub
2. [ARCHITECTURE_DECISION_RECORDS.md](docs/ARCHITECTURE_DECISION_RECORDS.md) - Key decisions
3. [EVENT_SCHEMA.md](docs/EVENT_SCHEMA.md) - Event data structure
4. [DATA_ZONES.md](docs/DATA_ZONES.md) - Data lake architecture
5. [REPO_NAVIGATION.md](REPO_NAVIGATION.md) - Cross-repo context

## Open Issues Priority

Check `gh issue list` for current work. Key labels:
- `priority:critical` - Do first
- `grant-readiness` - Important for funding
- `pipeline` - Data transformation work

---

**Last Updated**: 2024-12-24
