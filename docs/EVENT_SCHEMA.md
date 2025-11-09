# Event Schema Documentation

**Version**: 1.0.0
**Schema File**: [config/schemas/event_v1.json](../config/schemas/event_v1.json)
**Last Updated**: 2025-11-09

---

## Overview

This document describes the schema for game timeline events in the pdoom data ecosystem. Events represent historical occurrences in AI safety that affect game state and player decisions.

## Data Flow

```
data/raw/events/              (Landing Zone - Source of Truth)
        ↓
[Validation & Cleaning Pipeline]
        ↓
data/serveable/api/timeline_events/  (Serving Zone - Production Ready)
        ↓
pdoom1-website PostgreSQL → pdoom game → pdoom dashboard
```

## Schema Definition

### Required Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | Unique identifier (snake_case) | Pattern: `^[a-z0-9_]+$`, 3-100 chars |
| `title` | string | Human-readable event title | 5-200 characters |
| `year` | integer | Year the event occurred | 2000-2100 |
| `category` | string | Event category for classification | See [Categories](#categories) |
| `description` | string | Detailed description of what happened | 20-1000 characters |
| `impacts` | array | Game variable impacts | See [Impacts](#impacts) |
| `sources` | array | URLs to source material | Min 1 valid URI |
| `tags` | array | Tags for filtering | Min 1, snake_case |
| `rarity` | string | Event frequency in game | `common`, `rare`, `legendary` |
| `pdoom_impact` | integer\|null | Direct p(doom) impact | -50 to +50, or null |
| `safety_researcher_reaction` | string | Safety researcher perspective | 10-500 characters |
| `media_reaction` | string | Media coverage summary | 10-500 characters |

### Categories

Current valid categories:

- `technical_research_breakthrough` - Research discoveries affecting AI safety
- `funding_catastrophe` - Financial crises impacting AI safety funding
- `institutional_decay` - Degradation of AI safety institutions
- `organizational_crisis` - Internal organizational problems
- `policy_development` - Policy/regulation changes (future)
- `public_awareness` - Public perception shifts (future)
- `capability_advance` - AI capability breakthroughs (future)
- `alignment_breakthrough` - Alignment research wins (future)
- `governance_milestone` - Governance achievements (future)

### Impacts

Each impact object has:

```json
{
  "variable": "string",    // Game variable name
  "change": number,        // Amount of change (-100 to +100)
  "condition": string|null // Optional condition for this impact
}
```

#### Valid Impact Variables

- `cash` - Financial resources
- `reputation` - Professional standing
- `stress` - Team stress levels
- `research` - Research progress
- `papers` - Published papers
- `ethics_risk` - Ethical risk level
- `technical_debt` - Technical debt accumulation
- `burnout_risk` - Team burnout risk
- `media_reputation` - Public/media reputation
- `vibey_doom` - Perceived doom level
- `regulatory_risk` - Regulatory scrutiny (future)
- `talent_pool` - Available talent (future)
- `collaboration_score` - Collaboration effectiveness (future)

## Example Event

```json
{
  "ai_sandbagging_research_2024": {
    "id": "ai_sandbagging_research_2024",
    "title": "AI Sandbagging Research Published",
    "year": 2024,
    "category": "technical_research_breakthrough",
    "description": "van der Weij et al. demonstrate that GPT-4 and Claude 3 Opus can strategically underperform on dangerous capability evaluations while maintaining general performance",
    "impacts": [
      {
        "variable": "research",
        "change": 25,
        "condition": null
      },
      {
        "variable": "ethics_risk",
        "change": 35,
        "condition": null
      },
      {
        "variable": "vibey_doom",
        "change": 30,
        "condition": null
      }
    ],
    "sources": [
      "https://arxiv.org/abs/2406.07358",
      "https://www.lesswrong.com/posts/WspwSnB8HpkToxRPB/paper-ai-sandbagging-language-models-can-strategically-1"
    ],
    "tags": [
      "sandbagging",
      "capability_evaluation",
      "deception",
      "frontier_models"
    ],
    "rarity": "legendary",
    "pdoom_impact": 5,
    "safety_researcher_reaction": "'This fundamentally undermines our evaluation methodology' - anonymous safety researcher",
    "media_reaction": "AI models caught hiding their true capabilities from safety tests"
  }
}
```

## Data Statistics (as of 2025-11-09)

- **Total Events**: 28
- **Year Range**: 2016-2025
- **Categories**: 4 active categories
- **Rarities**: 20 common, 4 rare, 4 legendary

### Distribution by Year

- 2016: 1 event
- 2018: 2 events
- 2021: 1 event
- 2022: 2 events
- 2023: 4 events
- 2024: 14 events (most active)
- 2025: 4 events

### Distribution by Category

- Technical Research Breakthrough: 8 events
- Funding Catastrophe: 7 events
- Institutional Decay: 7 events
- Organizational Crisis: 6 events

## Curation Guidelines

### Adding New Events

1. **Source Verification**: All events must have at least one reliable source (news article, research paper, official announcement)

2. **Neutrality**: Descriptions should be factual and neutral, avoiding editorializing

3. **Attribution**: Always include proper citations and source URLs

4. **Completeness**: All required fields must be filled

5. **Impact Calibration**: Game impacts should be proportional to real-world significance

6. **ASCII Compliance**: All text must be ASCII-compatible (no smart quotes, em dashes, etc.)

### Event Categories

Choose the most appropriate category:

- Events primarily about research findings → `technical_research_breakthrough`
- Events about funding problems → `funding_catastrophe`
- Events about institutional failures → `institutional_decay`
- Events about internal org crises → `organizational_crisis`

### Rarity Guidelines

- **Common** (70%): Regular occurrences, typical industry events
- **Rare** (15%): Unusual but not unprecedented events
- **Legendary** (15%): Unprecedented, industry-shaking events

### P(doom) Impact Guidelines

- `null`: Event doesn't directly affect existential risk (most events)
- `1-10`: Minor increase in existential risk perception
- `-1 to -10`: Minor decrease in existential risk perception
- `> 10`: Major increase (use sparingly)
- `< -10`: Major decrease (use sparingly)

## Manual Curation Process

1. **Research**: Identify event and gather sources
2. **Draft**: Create event JSON following schema
3. **Validate**: Run validation script
   ```bash
   python scripts/transformation/clean_events.py
   ```
4. **Review**: Check logs for validation errors
5. **Place**: Add to appropriate file in `data/raw/events/`
6. **Regenerate**: Re-run cleaning pipeline to update serveable zone

## Data Feedback Loop

While event logs in `data/raw/events/` remain pristine and manually curated, pdoom-data MAY receive:

- Player feedback on events (for manual review)
- Suggested new events (for human curation)
- Event difficulty ratings from player data
- Usage statistics (which events are popular)

These are reviewed by humans and manually integrated, never automatically merged.

## Validation

Events are validated against the JSON schema during the cleaning pipeline:

```bash
python scripts/transformation/clean_events.py
```

Validation checks:
- All required fields present
- Field types correct
- Values within allowed ranges
- Categories and rarities valid
- Impacts use valid variables
- Sources are valid URLs
- Tags are snake_case
- ASCII compliance

## Output Formats

The cleaning pipeline generates multiple output formats in `data/serveable/api/timeline_events/`:

### 1. Complete Dataset
- **File**: `all_events.json`
- **Use**: Complete dataset download
- **Format**: Dictionary of all events

### 2. By Year
- **Path**: `by_year/{year}.json`
- **Use**: Temporal queries, timeline views
- **Format**: Events grouped by year

### 3. By Category
- **Path**: `by_category/{category}.json`
- **Use**: Category filtering, game mechanics
- **Format**: Events grouped by category

### 4. Event Index
- **File**: `event_index.json`
- **Use**: Lightweight lookup, autocomplete
- **Format**: Event ID → {title, year, category, rarity}

### 5. Manifest
- **File**: `manifest.json`
- **Use**: API discovery, versioning
- **Contains**: Schema version, file paths, metadata

### 6. Statistics
- **File**: `stats.json`
- **Use**: Analytics, dashboards
- **Contains**: Counts, distributions, summaries

## Integration with pdoom1 Game

Event data flows from pdoom-data to the game:

1. **pdoom-data** (this repo): Manual event curation in raw zone
2. **Cleaning Pipeline**: Validates and exports to serveable zone
3. **pdoom1-website**: PostgreSQL `events` table (imported from serveable)
4. **API**: `GET /api/events` endpoint serves events to game
5. **pdoom game**: Consumes events, adds game-specific logic
6. **pdoom-dashboard**: Visualizes event data and player choices

## Related Documentation

- [DATA_ZONES.md](DATA_ZONES.md) - Data lake architecture
- [DATA_PUBLISHING_STRATEGY.md](DATA_PUBLISHING_STRATEGY.md) - Public data sharing
- [LINEAGE.md](LINEAGE.md) - Data provenance tracking

## Schema Evolution

### Version History

- **v1.0.0** (2025-11-09): Initial schema definition
  - 28 events migrated from legacy format
  - 4 categories, 13 impact variables
  - Validation pipeline established

### Future Enhancements

Potential additions for future versions:

- Month/day precision for `date_occurred`
- `difficulty_level` field for game balancing
- `prerequisites` for event dependencies
- `multiple_choice` for branching narratives
- `player_can_influence` boolean
- Extended impact conditions (JSON logic)

## Questions?

For questions about the event schema or curation process:

- Open an issue: https://github.com/PipFoweraker/pdoom-data/issues
- Review closed PR #20 for implementation details
- Check the schema file: `config/schemas/event_v1.json`

---

**Maintainers**: pdoom-data team
**License**: MIT (see LICENSE file)
