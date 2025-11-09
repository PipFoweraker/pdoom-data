# Serveable Data Zone

**Purpose**: Production-ready, optimized data for consumption by applications, APIs, and dashboards.

---

## Overview

This directory contains the final layer of the data lake architecture. Data here has been:

1. ✅ Validated against schemas
2. ✅ Cleaned and normalized
3. ✅ Enriched with derived fields (where applicable)
4. ✅ Optimized for consumption (indexed, formatted, compressed)

## Directory Structure

```
serveable/
├── api/                    # API-ready formats (JSON, REST-friendly)
│   └── timeline_events/    # Game timeline events
└── analytics/              # Analytics-ready formats (future)
```

## Data Sources

### Timeline Events (`api/timeline_events/`)

**Source**: `data/raw/events/` → cleaned by `scripts/transformation/clean_events.py`

**Schema**: [config/schemas/event_v1.json](../../config/schemas/event_v1.json)

**Documentation**: [docs/EVENT_SCHEMA.md](../../docs/EVENT_SCHEMA.md)

**Contents**:
- `all_events.json` - Complete dataset (all 28 events)
- `by_year/{year}.json` - Events grouped by year
- `by_category/{category}.json` - Events grouped by category
- `event_index.json` - Lightweight event index
- `manifest.json` - API metadata and file paths
- `stats.json` - Summary statistics

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
python scripts/transformation/clean_events.py
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

- [DATA_ZONES.md](../../docs/DATA_ZONES.md) - Three-zone architecture
- [EVENT_SCHEMA.md](../../docs/EVENT_SCHEMA.md) - Event schema details
- [DATA_PUBLISHING_STRATEGY.md](../../docs/DATA_PUBLISHING_STRATEGY.md) - Public publishing

---

**Last Updated**: 2025-11-09
**Maintainers**: pdoom-data team
