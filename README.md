# pdoom-data: AI Safety Data Lake

**Production-grade data infrastructure for AI safety research, timeline events, and funding information.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data Quality](https://img.shields.io/badge/Data%20Quality-100%25%20Validated-brightgreen)]()
[![Events](https://img.shields.io/badge/Events-1%2C028-blue)]()
[![Weekly Updates](https://img.shields.io/badge/Updates-Weekly-orange)]()

---

## Quick Start

**For Developers**: [5-Minute Integration Guide](docs/QUICK_START_INTEGRATION.md)

**For Data Engineers**: [Complete Integration Guide](docs/INTEGRATION_GUIDE.md)

**For Navigation**: [Documentation Index](docs/DOCUMENTATION_INDEX.md)

---

## Overview

pdoom-data provides a curated, validated, and production-ready data lake for AI safety information. Data flows through a three-zone architecture (raw → transformed → serveable) with automated pipelines, comprehensive validation, and full provenance tracking.

### What's Inside

**1,028 Timeline Events** (28 manual + 1,000 alignment research)
- Hand-curated AI safety events (2016-2025)
- Automated alignment research extraction (2020-2022)
- Schema-validated with complete source attribution
- Organized by year, category, and rarity

**Alignment Research Dataset** (1,000+ records)
- Research papers, blog posts, forum discussions
- 30+ sources (ArXiv, Alignment Forum, LessWrong, EA Forum)
- Automated weekly extraction with delta detection
- Enriched with metrics and derived fields

**Funding Data** (In Progress)
- Survival and Flourishing Fund (SFF) grants
- Grant amounts, recipients, project descriptions
- Historical funding patterns

---

## Data Collections

### Timeline Events (`data/serveable/api/timeline_events/`)

**Status**: Production Ready | **Events**: 1,028 | **Schema**: event_v1.json

Two datasets available:

1. **Manual Curated Events** (28 events, 2016-2025)
   - Organizational crises, technical breakthroughs, funding events
   - Full source attribution and metadata
   - Files: `all_events.json`, `by_year/`, `by_category/`

2. **Alignment Research Events** (1,000 events, 2020-2022)
   - Generated from StampyAI Alignment Research Dataset
   - Research papers, forum posts, blog articles
   - Files: `alignment_research/alignment_research_events.json`, `by_year/`

**Use Cases**:
- Game timeline system with event impacts
- Research dashboard and visualization
- Historical analysis of AI safety field
- Training data for AI safety models

### Alignment Research (`data/raw/alignment_research/`)

**Status**: Weekly Updates | **Records**: 1,000+ | **Sources**: 30+

- Automated extraction from Hugging Face dataset
- Schema validation and quality checks
- Cleaning pipeline (deduplication, ASCII conversion)
- Enrichment pipeline (metrics, topics, safety relevance)

### Funding Data (`data/raw/funding/`)

**Status**: In Development | **Sources**: SFF, Open Philanthropy

- Grant amounts and recipients
- Project descriptions and outcomes
- Funding patterns over time

---

## Architecture

### Three-Zone Data Lake

```
RAW ZONE                TRANSFORMED ZONE              SERVEABLE ZONE
(Immutable)             (Validated/Cleaned/Enriched)  (Production-Ready)

data/raw/               data/transformed/             data/serveable/
├── events/             ├── validated/                ├── api/
├── alignment_research/ ├── cleaned/                  │   └── timeline_events/
└── funding/            └── enriched/                 └── analytics/
```

**Pipeline Stages**:
1. **Raw**: Immutable source data with checksums
2. **Validated**: Schema-validated against JSON schemas
3. **Cleaned**: Deduplicated, normalized, ASCII-compliant
4. **Enriched**: Derived fields, metrics, categorization
5. **Serveable**: Optimized for consumption (indexed, formatted)

**Automation**: GitHub Actions runs pipeline on data changes

See [DATA_ZONES.md](docs/DATA_ZONES.md) for architecture details.

---

## Integration

### Quick Integration (5 Minutes)

**pdoom1-website** (PostgreSQL + FastAPI):
```bash
git submodule add https://github.com/PipFoweraker/pdoom-data.git data/pdoom-data
python scripts/import_events.py  # Import 1,028 events to PostgreSQL
# API endpoint: GET /api/events?year=2024&category=technical_research_breakthrough
```

**pdoom (Godot Game)**:
```bash
cp pdoom-data/data/serveable/api/timeline_events/*.json res://data/events/
# Load events with EventLoader.gd, apply impacts to game variables
```

**pdoom-dashboard** (React/TypeScript):
```typescript
const { events } = useEvents({ year: 2024, category: 'technical_research_breakthrough' });
// Display interactive timeline with filtering
```

See [QUICK_START_INTEGRATION.md](docs/QUICK_START_INTEGRATION.md) for complete setup guides.

---

## Data Quality

### Standards

- Rigorous sourcing with complete attribution
- JSON Schema validation on all datasets
- ASCII-only encoding for universal compatibility
- Comprehensive extraction and transformation logs
- Idempotent pipelines (safe to re-run)
- Full version control and lineage tracking

### Quality Metrics (Current)

| Metric | Value |
|--------|-------|
| Total Events | 1,028 |
| Schema Validation Pass Rate | 100% |
| ASCII Compliance | 100% |
| Source Attribution Complete | 100% |
| Duplicate Records | 0 |

---

## Automation

### GitHub Actions Workflows

**1. Weekly Data Refresh** ([weekly-data-refresh.yml](.github/workflows/weekly-data-refresh.yml))
- Extracts new alignment research every Monday at 2am UTC
- Validates extracted data
- Commits to repository

**2. Automated Pipeline** ([data-pipeline-automation.yml](.github/workflows/data-pipeline-automation.yml))
- Triggers on raw data changes
- Runs full pipeline: validate -> clean -> enrich -> transform -> manifest
- Auto-commits processed data

**3. Documentation CI** ([documentation-ci.yml](.github/workflows/documentation-ci.yml))
- Validates documentation quality
- Checks ASCII compliance
- Tests JSON validity

---

## Tools

### Event Browser

**Interactive browser for reviewing and annotating events**

Open `tools/event_browser.html` in your browser to:
- Browse and filter 1,000+ timeline events
- Add custom metadata for game integration
- Tag events by impact level and game relevance
- Export metadata for use in pdoom1 and pdoom1-website

See [EVENT_BROWSER_GUIDE.md](docs/EVENT_BROWSER_GUIDE.md) for complete documentation.

---

## Documentation

### Essential Guides

| Document | Purpose | Audience |
|----------|---------|----------|
| [QUICK_START_INTEGRATION.md](docs/QUICK_START_INTEGRATION.md) | 5-minute integration | Developers |
| [INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) | Complete integration docs | Developers |
| [EVENT_SCHEMA.md](docs/EVENT_SCHEMA.md) | Timeline event schema | Developers |
| [EVENT_BROWSER_GUIDE.md](docs/EVENT_BROWSER_GUIDE.md) | Interactive event browser | Curators, Game Designers |
| [DATA_ZONES.md](docs/DATA_ZONES.md) | Architecture overview | Engineers |
| [RUNBOOK.md](docs/RUNBOOK.md) | Operations guide | Operators |
| [DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) | All documentation | All |

### For Integrators

See [CROSS_REPO_INTEGRATION_ISSUES.md](docs/CROSS_REPO_INTEGRATION_ISSUES.md) for ready-to-use GitHub issues to create in consuming repositories.

---

## Repository Structure

```
pdoom-data/
├── data/
│   ├── raw/                      # Immutable source data
│   │   ├── events/               # Manual curated events
│   │   ├── alignment_research/   # Research dataset
│   │   └── funding/              # Funding data
│   ├── transformed/              # Processed data
│   │   ├── validated/            # Schema-validated
│   │   ├── cleaned/              # Normalized, deduplicated
│   │   └── enriched/             # With derived fields
│   └── serveable/                # Production-ready
│       ├── MANIFEST.json         # Complete data catalog
│       └── api/
│           └── timeline_events/  # 1,028 events ready for use
├── tools/
│   └── event_browser.html        # Interactive event browser (open in browser)
├── config/
│   └── schemas/                  # JSON schemas
│       └── event_v1.json         # Timeline event schema
├── scripts/
│   ├── analysis/                 # Event analysis tools
│   ├── transformation/           # Data pipeline scripts
│   ├── validation/               # Schema validation
│   ├── publishing/               # Manifest generation
│   └── logging/                  # (Future) Log consolidation
├── docs/                         # Comprehensive documentation
└── .github/workflows/            # Automation
```

---

## Usage Examples

### Load All Events (Python)

```python
import json
from pathlib import Path

# Load manual events
with open('data/serveable/api/timeline_events/all_events.json') as f:
    manual_events = list(json.load(f).values())

# Load alignment research events
with open('data/serveable/api/timeline_events/alignment_research/alignment_research_events.json') as f:
    research_events = json.load(f)

all_events = manual_events + research_events
print(f"Loaded {len(all_events)} events")

# Filter by year
events_2024 = [e for e in all_events if e['year'] == 2024]
print(f"  {len(events_2024)} events in 2024")
```

### Query by Category (SQL)

```sql
-- After importing to PostgreSQL
SELECT id, title, year, rarity
FROM events
WHERE category = 'technical_research_breakthrough'
  AND year >= 2020
ORDER BY year DESC, rarity DESC
LIMIT 10;
```

### Load in Godot (GDScript)

```gdscript
# EventLoader.gd
var events = []

func _ready():
    var file = File.new()
    file.open("res://data/events/all_events.json", File.READ)
    var json = file.get_as_text()
    file.close()

    var result = JSON.parse(json)
    if result.error == OK:
        for event_id in result.result:
            events.append(result.result[event_id])

    print("Loaded ", events.size(), " events")
```

---

## Roadmap

### Completed

- Three-zone data lake architecture
- Timeline event schema and validation
- Alignment research integration (1,000 events)
- Automated weekly data extraction
- Complete transformation pipeline
- Serveable zone with manifest
- Integration documentation
- GitHub Actions automation

### In Progress

- Public communication strategy implementation
- Logs consolidation and public blog
- Additional funding data sources
- Data quality dashboard

### Planned

- Public data portal (web UI)
- API documentation auto-generation
- Community contribution guide
- Data visualization toolkit
- Machine learning training datasets

See [GitHub Issues](https://github.com/PipFoweraker/pdoom-data/issues) for detailed tracking.

---

## License

MIT License - Free for educational, research, and commercial use.

---

## Data Sources & Attribution

### Alignment Research
- **Source**: [StampyAI Alignment Research Dataset](https://huggingface.co/datasets/StampyAI/alignment-research-dataset)
- **License**: Various (see individual records)
- **Attribution**: Full source URLs included in each record

### Manual Events
- **Curated by**: pdoom-data team
- **Sources**: Public announcements, news articles, organizational updates
- **Attribution**: Complete source lists in each event

### Funding Data
- **Sources**: Survival and Flourishing Fund, Open Philanthropy (planned)
- **Attribution**: Links to original grant databases

---

## Repository Visibility

This repository is currently **private** during active development. A publishing workflow is configured to sync the serveable zone to a future public repository once data transformation pipelines are complete.

See [docs/DATA_PUBLISHING_STRATEGY.md](docs/DATA_PUBLISHING_STRATEGY.md) for details on the planned public data release strategy.

---

## Contributing

This repository is currently in active development. For questions or suggestions:

1. Check [DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)
2. Review existing [GitHub Issues](https://github.com/PipFoweraker/pdoom-data/issues)
3. Open a new issue with your question or proposal

This repository maintains strict ASCII-only content for agent compatibility. See [ASCII_CODING_STANDARDS.md](ASCII_CODING_STANDARDS.md) and [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).

---

## Support

**Documentation**: [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)

**Quick Start**: [docs/QUICK_START_INTEGRATION.md](docs/QUICK_START_INTEGRATION.md)

**Issues**: [GitHub Issues](https://github.com/PipFoweraker/pdoom-data/issues)

**Integration Help**: See issue templates in [CROSS_REPO_INTEGRATION_ISSUES.md](docs/CROSS_REPO_INTEGRATION_ISSUES.md)

---

**Last Updated**: 2025-11-24

**Maintained by**: pdoom-data team

**Version**: 0.2.0 (In Development)
