# Data Zone Architecture

## Overview

This repository implements a four-zone data architecture designed to maintain data integrity, enable safe transformations, and provide production-ready datasets for consumption.

> **Updated 2026-07-30: a Curated zone was added.** The document below still
> describes three zones in places; the sections that have not caught up are
> accurate about Raw, Transformed and Serveable, and silent about Curated.
> Read this section first.

### Why a fourth zone

The original three zones distinguish data by *how processed* it is. They have
no way to say **who decided**. Machine-derived enrichment and human judgement
were both landing in `data/enrichment/`, which meant a reviewer's verdict and a
tagger's output sat in the same place and looked alike.

That matters here more than in most repositories, because the fact/opinion
firewall is the thing this data hub sells. If a human judgement cannot be
located by zone, it cannot be audited, attributed, or filtered out by a
consumer who disagrees.

### The zones, and the progression

    Raw        immutable dumps, exactly as ingested. Re-running an adapter
               produces a NEW dump; nothing is ever edited in place.
                 |
                 |  validate, clean, standardise
                 v
    Transformed  machine-derived only. Deduplication, ASCII normalisation,
               derived fields, taxonomy tags. Reproducible from Raw by
               running code -- no human is in the loop.
                 |
                 |  a person decides something
                 v
    Curated      HUMAN JUDGEMENT. Review verdicts, inclusion calls, editorial
               reasons, hand-researched records. Everything here is an
               opinion with an author, or a fact a person went and found.
               NOT reproducible by re-running code: if you delete it, it is
               gone, and someone has to decide again.
                 |
                 |  project, conform to a published schema, validate
                 v
    Serveable    build output. Byte-identical to a fresh projection, asserted
               by --check. Never hand-edited. What consumers fetch.

This maps onto the standard lake progression as
Raw -> Curated -> Conformed -> Served, with two local deviations worth naming:

- **Conforming is not a zone here, it is the projection step.** Schema
  conformance happens on the way into Serveable, enforced by
  `config/schemas/*.json` plus a `--check` that asserts the committed output
  matches a fresh build. Giving it a directory would create a second producer
  writing to the same place, which is precisely the failure that left this
  repo with `MANIFEST.json` saying 28 events while `all_events.json` said
  1,194.
- **Transformed sits between Raw and Curated** rather than being folded into
  cleansing, because machine-derived enrichment must stay separable from human
  judgement. That separation is the whole point of the new zone.

### What lives in Curated (`data/curated/`)

    human_review/     attributed review verdicts. Every entry names its
                      reviewer; there are no anonymous verdicts.
    frontier_labs/    hand-researched organisation records, split into
                      research/ (what was read, with verbatim quotes) and
                      curation_table.json (the judgement calls). Split so
                      evidence and judgement can be reviewed separately.

`data/enrichment/` retains `airr_tags/` and `alignment_research/`, which are
machine-derived and belong on the Transformed side of the line.

### Rules for Curated

1. **Everything carries an author.** A verdict, tier override or inclusion
   decision without a named person is a bug, not a default.
2. **It is not reproducible.** Raw can be re-fetched and Transformed can be
   re-derived. Curated cannot. Treat deletion as data loss.
3. **Evidence and judgement stay separate where practical.** A research record
   states what was read; a curation record states what was decided about it.
   Editing the former to change the latter destroys the audit trail.
4. **Promotion out of Curated does not launder an opinion into a fact.** The
   `reviewed` collection carries its reviewer attribution all the way to the
   consumer, and its LINEAGE says in words that acceptance is an attributed
   opinion and not an endorsement.

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
