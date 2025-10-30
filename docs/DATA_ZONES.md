# Data Zone Architecture

## Overview

This repository implements a three-zone data architecture designed to maintain data integrity, enable safe transformations, and provide production-ready datasets for consumption.

## Zone Definitions

### Raw Zone (`data/raw/`)

**Purpose**: Immutable landing zone for source data

**Characteristics**:
- **Never Modified**: Data in this zone is append-only and immutable
- **Authoritative Source**: Single source of truth for all downstream processing
- **Complete Audit Trail**: All ingested data is retained with timestamps
- **Organized by Source**: Data organized by originating system or provider

**Directory Structure**:
```
data/raw/
|-- funding_sources/          # Funding data organized by source
|   |-- sff/                 # Survival & Flourishing Fund
|   |-- open_philanthropy/   # Open Philanthropy
|   |-- ai2050/              # Schmidt Sciences AI2050
|   |-- macroscopic/         # Macroscopic
|   |-- givewiki/            # GiveWiki
|   |-- cooperative_ai/      # Cooperative AI Foundation
|   `-- catalyze_impact/     # Catalyze Impact
`-- _archive/                # Historical/superseded data
```

**Policies**:
- Only automated ingestion processes write to this zone
- Files are named with timestamps: `source_YYYY-MM-DD.json`
- Never delete files - move to `_archive/` if superseded
- Maintain complete lineage from source to ingestion

**Access**:
- Read: All processes
- Write: Ingestion processes only
- Delete: Never (archive instead)

### Transformed Zone (`data/transformed/`)

**Purpose**: Intermediate processing stages

**Characteristics**:
- **Validated Data**: Schema-validated and quality-checked
- **Cleaned Data**: Normalized, deduplicated, and corrected
- **Enriched Data**: With derived fields and calculations

**Directory Structure**:
```
data/transformed/
|-- validated/    # Schema-validated, structurally sound
|-- cleaned/      # Normalized and deduplicated
`-- enriched/     # With derived fields and aggregations
```

**Policies**:
- Data flows: raw -> validated -> cleaned -> enriched
- Each stage is idempotent and reproducible
- All transformations are script-driven (no manual edits)
- Failed transformations are logged and halt processing

**Access**:
- Read: All processes
- Write: Transformation pipelines only
- Delete: Safe to recreate from raw data

### Serveable Zone (`data/serveable/`)

**Purpose**: Production-ready, optimized data for consumption

**Characteristics**:
- **Analytics-Ready**: Optimized for dashboards and analysis
- **API-Ready**: Formatted for direct API serving
- **Performance-Optimized**: Indexed, compressed, or pre-aggregated

**Directory Structure**:
```
data/serveable/
|-- analytics/    # For dashboards and analysis tools
`-- api/          # API-ready formats (JSON, etc.)
```

**Policies**:
- Generated from transformed zone only
- Optimized for specific use cases
- May include aggregations and summaries
- Safe to regenerate at any time

**Access**:
- Read: Applications, APIs, dashboards
- Write: Publishing pipelines only
- Delete: Safe to recreate from transformed data

## Data Flow

```
[External Source]
     |
     v
[data/raw/]           <- Ingestion (immutable)
     |
     v
[data/transformed/    <- Validation
 validated/]
     |
     v
[data/transformed/    <- Cleaning & normalization
 cleaned/]
     |
     v
[data/transformed/    <- Enrichment & derivation
 enriched/]
     |
     v
[data/serveable/]     <- Publishing (optimized)
     |
     v
[Applications/APIs]
```

## Zone Transition Rules

### Raw -> Transformed

**Process**: Migration script with validation
**Script**: `scripts/migration/migrate.py`
**Operations**:
1. Validate source data against schema
2. Copy (not move) to validated zone
3. Log all operations
4. Track checksums for idempotency

**When to Run**:
- After new data arrives in raw zone
- When schema or validation rules change
- On-demand for reprocessing

### Transformed -> Serveable

**Process**: Publishing pipeline
**Operations**:
1. Apply optimizations (indexing, compression)
2. Generate format-specific outputs
3. Create aggregations and summaries
4. Verify output integrity

**When to Run**:
- After successful transformation
- When publishing requirements change
- On schedule for regular updates

## Maintenance Procedures

### Adding New Data Sources

1. Create subdirectory in `data/raw/funding_sources/`
2. Update ingestion documentation
3. Configure validation rules for source
4. Test with sample data
5. Document source-specific considerations

### Reprocessing Data

1. Clear transformed and serveable zones (backup if needed)
2. Run migration script: `python scripts/migration/migrate.py`
3. Verify logs for errors
4. Run publishing pipeline
5. Validate outputs

### Archiving Old Data

1. Identify data to archive (superseded, outdated)
2. Move from raw zone to `data/raw/_archive/`
3. Document reason for archival
4. Keep for audit trail - never delete

### Recovery Procedures

If data corruption detected:

1. Stop all processing pipelines
2. Identify last known good state
3. Clear affected zones
4. Restore from raw zone (always authoritative)
5. Rerun transformations
6. Validate outputs before resuming

## Monitoring and Alerting

### Key Metrics

- Files processed per hour
- Validation failure rate
- Average processing time
- Disk space utilization
- Error frequency by type

### Alert Conditions

- Validation failures exceed threshold
- Disk space below 20% free
- Processing time exceeds SLA
- Checksum mismatches detected
- File corruption detected

## Best Practices

1. **Never Modify Raw Data**: Always transform through pipelines
2. **Log Everything**: Complete audit trail of all operations
3. **Validate Early**: Catch issues at ingestion, not consumption
4. **Test Transformations**: Use sample data before production runs
5. **Document Changes**: Update schemas and docs with data changes
6. **Monitor Continuously**: Track metrics and set up alerts
7. **Backup Before Changes**: Especially for destructive operations
8. **Use Checksums**: Verify integrity at every stage
9. **Fail Safely**: Halt on errors, don't corrupt good data
10. **Keep It Simple**: Avoid complex transformations in single step

## Troubleshooting

### Validation Failures

1. Check logs in `logs/validation/`
2. Examine failing records
3. Verify schema is current
4. Check for data format changes
5. Update validation rules if legitimate

### Migration Stuck

1. Check logs in `logs/migration/`
2. Verify disk space available
3. Check file permissions
4. Review `.migration_state.json` for processed files
5. Manually reset state if needed

### Performance Issues

1. Check file sizes and counts
2. Monitor system resources
3. Consider batch processing
4. Optimize transformations
5. Add indexing or compression

## References

- See `RUNBOOK.md` for step-by-step operational procedures
- See `DATA_DICTIONARY.md` for field definitions
- See `LINEAGE.md` for data flow documentation
- See `scripts/migration/README.md` for migration tool usage
