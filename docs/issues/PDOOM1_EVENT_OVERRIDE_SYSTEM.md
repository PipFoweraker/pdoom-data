# GitHub Issue for pdoom1: Event Override System

**Copy this content to create an issue in the pdoom1 repository.**

---

## Title

Implement Event Override System (ADR-001 Compliance)

## Labels

`architecture`, `enhancement`, `data-integration`

## Body

## Overview

Implement the game-side of ADR-001 (Game/Data Boundary) as documented in pdoom-data. This enables the game to consume events from pdoom-data while maintaining full control over game balance and mechanics.

**Reference**: https://github.com/PipFoweraker/pdoom-data/blob/main/docs/ARCHITECTURE_DECISION_RECORDS.md

## Background

pdoom-data provides 1,028 timeline events with **sensible defaults** for game integration:
- Impact values (cash, stress, reputation, etc.)
- Rarity (common/rare/legendary)
- Flavor text (safety_researcher_reaction, media_reaction)

However, game balance and mechanics should be owned by the game team, not the data team. This issue implements the override layer that lets pdoom1 tune events without requiring changes to pdoom-data.

## The Layered Model

```
pdoom-data (Source)          pdoom1 (This Issue)
------------------          -------------------
Historical facts     --->   (consumed as-is)
Default impacts      --->   Override Layer (tune values)
Default rarity       --->   Override Layer (adjust for gameplay)
Reactions            --->   (consumed as-is, or override)
                            Game Extensions (chains, triggers, scenarios)
```

## Implementation

### 1. Create Override Directory Structure

```
pdoom1/
  data/
    events/
      overrides/           # Per-event tuning
        README.md          # How to use overrides
        example.json       # Template
      extensions/          # Game-only mechanics
        event_chains.json  # A unlocks B
        triggers.json      # Conditional appearance
        scenarios.json     # Mode assignments
      balancing/           # Global tuning
        rarity_curves.json # How rarity maps to probability
        difficulty.json    # Difficulty multipliers
```

### 2. Override Schema

```json
{
  "ai_sandbagging_research_2024": {
    "impacts": [
      {"variable": "cash", "change": -20},
      {"variable": "stress", "change": 15}
    ],
    "rarity": "legendary",
    "pdoom_impact": 8
  }
}
```

Only include fields you want to override. Missing fields use pdoom-data defaults.

### 3. Event Loader Logic

```python
def load_event(event_id: str) -> Event:
    # 1. Load base event from pdoom-data
    base = load_pdoom_data_event(event_id)

    # 2. Apply overrides if present
    if override := load_override(event_id):
        base = deep_merge(base, override)

    # 3. Attach extensions
    base.chain = load_chain(event_id)
    base.trigger = load_trigger(event_id)
    base.scenario = load_scenario(event_id)

    return base

def deep_merge(base: dict, override: dict) -> dict:
    """Override replaces base values, arrays are replaced entirely."""
    result = base.copy()
    for key, value in override.items():
        result[key] = value
    return result
```

### 4. Extension Schemas

**Event Chains** (`extensions/event_chains.json`):
```json
{
  "chains": [
    {
      "trigger_event": "openai_safety_team_exodus_2024",
      "unlocks": ["anthropic_hiring_spree_2024"],
      "delay_turns": 2
    }
  ]
}
```

**Triggers** (`extensions/triggers.json`):
```json
{
  "triggers": [
    {
      "event_id": "major_alignment_breakthrough",
      "conditions": {
        "min_turn": 50,
        "requires_research": 100,
        "probability": 0.1
      }
    }
  ]
}
```

**Scenarios** (`extensions/scenarios.json`):
```json
{
  "scenarios": {
    "hard_mode": {
      "include_events": ["funding_catastrophe_*"],
      "exclude_events": ["alignment_breakthrough_*"],
      "impact_multiplier": 1.5
    }
  }
}
```

### 5. Documentation

Create `docs/EVENT_OVERRIDE_SYSTEM.md`:
- How to add overrides
- When to override vs request pdoom-data change
- Extension system documentation
- Examples and templates

## Acceptance Criteria

- [ ] Override directory structure created
- [ ] Override schema documented
- [ ] Event loader supports overrides
- [ ] At least 3 example overrides created
- [ ] Event chain system implemented
- [ ] Trigger condition system implemented
- [ ] Scenario assignment system implemented
- [ ] Documentation complete
- [ ] CLAUDE.md updated with override guidance

## Benefits

1. **Fast iteration** - Game team can tune balance without data repo PRs
2. **Clear ownership** - Facts in pdoom-data, mechanics in pdoom1
3. **No coupling** - Data updates don't break game balance
4. **Extensibility** - Add game mechanics without touching source data

## Related

- pdoom-data ADR-001: https://github.com/PipFoweraker/pdoom-data/blob/main/docs/ARCHITECTURE_DECISION_RECORDS.md
- pdoom-data CLAUDE.md: https://github.com/PipFoweraker/pdoom-data/blob/main/CLAUDE.md
- Issue #24 (pdoom-data): Content pipeline demo

## Notes

This is a foundational architecture issue. Completing this unblocks:
- Rapid game balancing
- Custom scenarios and difficulty modes
- Event chain narratives
- Community modding (override files are moddable)

---

**Priority**: High (architecture foundation)
**Estimated effort**: Medium (structure + loader + docs)
