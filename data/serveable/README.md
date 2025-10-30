# Serveable Data Zone

## Purpose

Production-ready, optimized data for consumption by applications, APIs, and dashboards.

## Subdirectories

### analytics/

Data optimized for dashboards and analysis:
- Pre-aggregated views
- Denormalized for query performance
- Time-series formatted
- Statistical summaries

### api/

Data formatted for direct API serving:
- JSON formatted
- Paginated where appropriate
- Versioned schemas
- Documented endpoints

## Key Principles

- **Production-Ready**: Optimized and tested
- **Performant**: Indexed and cached where needed
- **Versioned**: Schema versions tracked
- **Documented**: API contracts defined

## Operations

**Allowed**:
- ✅ Read data
- ✅ Regenerate from transformed zone
- ✅ Update via publishing pipeline

**Not Allowed**:
- ❌ Manual edits
- ❌ Direct writes without validation

## Regenerating Data

Safe to regenerate from transformed/enriched:

```bash
# Clear serveable data
rm -rf data/serveable/analytics/*
rm -rf data/serveable/api/*

# Republish from enriched zone
# (Publishing pipeline to be implemented)
```

## Documentation

- See `docs/DATA_ZONES.md` for zone architecture
- See `docs/LINEAGE.md` for data flow
