# Transformed Data Zone

## Purpose

This zone contains data in various stages of processing and transformation, from validated to enriched.

## Subdirectories

### validated/

Schema-validated data from raw zone:
- All required fields present
- Data types correct
- Format validated
- Ready for cleaning

### cleaned/

Normalized and deduplicated data:
- Duplicates removed
- Consistent formats
- Null values handled
- Quality issues resolved

### enriched/

Analysis-ready data with derived fields:
- Calculated fields added
- Categorizations applied
- Aggregations available
- Denormalized views

## Data Flow

```
raw -> validated -> cleaned -> enriched -> serveable
```

Each stage is reproducible from the previous stage.

## Key Principles

- **Reproducible**: Can be regenerated from raw data
- **Script-Driven**: All transformations via scripts, no manual edits
- **Validated**: Quality checks at each stage
- **Logged**: All operations recorded

## Operations

**Allowed**:
- [YES] Read data
- [YES] Process via scripts
- [YES] Delete and regenerate

**Not Allowed**:
- [NO] Manual file edits
- [NO] Direct writes without logging
- [NO] Skipping validation steps

## Regenerating Data

Safe to delete and regenerate at any time:

```bash
# Clear all transformed data
rm -rf data/transformed/validated/*
rm -rf data/transformed/cleaned/*
rm -rf data/transformed/enriched/*

# Clear processing state
rm logs/migration/.migration_state.json

# Reprocess from raw
python scripts/migration/migrate.py
```

## Documentation

- See `docs/DATA_ZONES.md` for zone architecture
- See `docs/LINEAGE.md` for transformation logic
- See `docs/RUNBOOK.md` for procedures
