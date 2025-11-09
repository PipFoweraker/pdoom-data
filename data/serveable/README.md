# Serveable Data Zone

**Purpose**: Production-ready, optimized data for consumption by applications, APIs, and dashboards.

---

## Quick Start

1. **Explore available data**: Check [MANIFEST.json](MANIFEST.json) for complete dataset catalog
2. **Integration guide**: See [docs/INTEGRATION_GUIDE.md](../../docs/INTEGRATION_GUIDE.md)
3. **Event schema**: Review [docs/EVENT_SCHEMA.md](../../docs/EVENT_SCHEMA.md)

## Overview

This directory contains the final layer of the data lake architecture. Data here has been:

1. ✅ Validated against schemas
2. ✅ Cleaned and normalized
3. ✅ Enriched with derived fields (where applicable)
4. ✅ Optimized for consumption (indexed, formatted, compressed)

**Current Status**: 1,028 timeline events ready for game integration

## Directory Structure

```
serveable/
├── MANIFEST.json           # Complete catalog of all serveable data
├── api/                    # API-ready formats (JSON, REST-friendly)
│   └── timeline_events/    # Game timeline events (1,028 events)
│       ├── all_events.json           # Manual curated events (28)
│       ├── by_year/                  # Manual events by year
│       ├── by_category/              # Manual events by category
│       ├── alignment_research/       # Research events (1,000)
│       │   ├── alignment_research_events.json
│       │   └── by_year/              # Research events by year
│       └── manifest.json             # Timeline events metadata
└── analytics/              # Analytics-ready formats (future)
```

## Data Sources

### Timeline Events (`api/timeline_events/`)

**Two datasets available:**

#### 1. Manual Curated Events (28 events)
**Source**: `data/raw/events/` → `scripts/transformation/clean_events.py`

**Files**:
- `all_events.json` - All 28 manual events
- `by_year/{year}.json` - Events by year (2016-2025)
- `by_category/{category}.json` - Events by category
- `event_index.json` - Lightweight lookup
- `manifest.json` - Metadata
- `stats.json` - Statistics

#### 2. Alignment Research Events (1,000 events)
**Source**: `data/raw/alignment_research/` → cleaning → enrichment → transformation

**Files**:
- `alignment_research/alignment_research_events.json` - All 1,000 events
- `alignment_research/by_year/{year}.json` - Events by year (2020-2022)

**Schema**: [config/schemas/event_v1.json](../../config/schemas/event_v1.json)

**Documentation**: [docs/EVENT_SCHEMA.md](../../docs/EVENT_SCHEMA.md)

**Usage**:
```python
import json

# Load all events
with open('data/serveable/api/timeline_events/all_events.json') as f:
    events = json.load(f)

# Load events for specific year
with open('data/serveable/api/timeline_events/by_year/2024.json') as f:
    events_2024 = json.load(f)
```

## Data Characteristics

### Quality Guarantees

All data in the serveable zone:

- ✅ Passes schema validation
- ✅ Has complete attribution (sources, citations)
- ✅ Is ASCII-compliant
- ✅ Has proper metadata (version, timestamp)
- ✅ Is idempotent (safe to regenerate)

### Freshness

Data is regenerated when:
- New events are added to raw zone
- Schema changes
- Cleaning logic improves
- Manual regeneration requested

To regenerate:
```bash
# Manual events
python scripts/transformation/clean_events.py

# Alignment research events (full pipeline)
python scripts/transformation/clean.py --source data/transformed/validated/alignment_research/latest --output data/transformed/cleaned/alignment_research/latest --format jsonl
python scripts/transformation/enrich.py --source data/transformed/cleaned/alignment_research/latest --output data/transformed/enriched/alignment_research/latest --format jsonl
python scripts/transformation/transform_to_timeline_events.py --source data/transformed/enriched/alignment_research/latest --output data/serveable/api/timeline_events/alignment_research

# Update manifest
python scripts/publishing/generate_manifest.py
```

## Integration

### For Game Developers

See [docs/INTEGRATION_GUIDE.md](../../docs/INTEGRATION_GUIDE.md) for:
- Database import scripts (PostgreSQL)
- API endpoint examples (FastAPI)
- Godot/GDScript integration
- React/TypeScript dashboard integration

### Quick Load Example

```python
import json
from pathlib import Path

# Load all events (manual + research)
serveable_dir = Path("data/serveable/api/timeline_events")

# Manual events
with open(serveable_dir / "all_events.json") as f:
    manual_events = list(json.load(f).values())

# Research events
with open(serveable_dir / "alignment_research/alignment_research_events.json") as f:
    research_events = json.load(f)

all_events = manual_events + research_events
print(f"Loaded {len(all_events)} total events")

# Filter by year
events_2024 = [e for e in all_events if e['year'] == 2024]
print(f"  {len(events_2024)} events in 2024")
```

## Operations

**Allowed**:
- ✅ Read data
- ✅ Regenerate from raw/transformed zones
- ✅ Update via transformation pipelines

**Not Allowed**:
- ❌ Manual edits (always use pipelines)
- ❌ Direct writes without validation

## Related Documentation

- **[MANIFEST.json](MANIFEST.json)** - Complete data catalog
- **[INTEGRATION_GUIDE.md](../../docs/INTEGRATION_GUIDE.md)** - Game integration guide
- [DATA_ZONES.md](../../docs/DATA_ZONES.md) - Three-zone architecture
- [EVENT_SCHEMA.md](../../docs/EVENT_SCHEMA.md) - Event schema details
- [DATA_PUBLISHING_STRATEGY.md](../../docs/DATA_PUBLISHING_STRATEGY.md) - Public publishing

---

**Last Updated**: 2025-11-09
**Maintainers**: pdoom-data team
