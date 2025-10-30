# Raw Data Zone

## Purpose

This is the **immutable landing zone** for all source data. Data in this zone is never modified after ingestion.

## Key Principles

- **Append-Only**: Add new data, never modify or delete
- **Authoritative Source**: Single source of truth for all downstream processing
- **Complete Audit Trail**: All ingested data retained with timestamps
- **Organized by Source**: Data organized by originating system

## Directory Structure

```
raw/
|-- funding_sources/          # Funding data by source organization
|   |-- sff/                 # Survival & Flourishing Fund
|   |-- open_philanthropy/   # Open Philanthropy
|   |-- ai2050/              # Schmidt Sciences AI2050
|   |-- macroscopic/         # Macroscopic
|   |-- givewiki/            # GiveWiki
|   |-- cooperative_ai/      # Cooperative AI Foundation
|   `-- catalyze_impact/     # Catalyze Impact
`-- _archive/                # Historical/superseded data
```

## File Naming Convention

Files should be named with timestamps to track when data was received:

- `source_YYYY-MM-DD.json` - Daily snapshot
- `source_YYYY-MM-DD_HH-MM-SS.json` - With time if multiple per day
- `source_YYYY-QN.json` - Quarterly data

Examples:
- `sff_2024-03-15.json`
- `open_philanthropy_2024-Q1.json`

## Policies

### What Goes Here
- Raw exports from source systems
- API responses from funding databases
- CSV downloads from grant portals
- Unmodified source data

### What Doesn't Go Here
- Transformed or cleaned data -> use `data/transformed/`
- Aggregated data -> use `data/transformed/enriched/`
- Production data -> use `data/serveable/`

### Operations

**Allowed**:
- [YES] Add new files
- [YES] Read files
- [YES] Copy files to other zones

**Not Allowed**:
- [NO] Modify existing files
- [NO] Delete files (move to `_archive/` instead)
- [NO] Manual data entry (use ingestion scripts)

## Archiving

When data is superseded:

1. Move to `_archive/` directory
2. Preserve original path structure
3. Document reason in `_archive/ARCHIVE_LOG.txt`
4. Keep indefinitely for audit trail

Example:
```bash
mv raw/funding_sources/sff/2023-old.json raw/_archive/2023/sff/
echo "2025-10-30: Archived old SFF data, replaced by corrected version" >> raw/_archive/ARCHIVE_LOG.txt
```

## Data Ingestion

Data should be ingested via automated processes:

1. Pull from source API or download portal
2. Save with timestamp in filename
3. Verify file integrity (checksum)
4. Log ingestion metadata
5. Never manually edit files

## Validation

Raw data is validated during migration to transformed zone, not at ingestion. This allows:

- Source data issues to be documented
- Validation rules to evolve
- Reprocessing with updated rules

## Security

- Read access: All team members
- Write access: Ingestion processes only
- Backup: Daily snapshots recommended

## Next Steps

After data lands in raw zone:

1. Run migration script: `python scripts/migration/migrate.py`
2. Data flows to `data/transformed/validated/`
3. Further processing in transformed zone
4. Eventually published to `data/serveable/`

## Documentation

- See `docs/DATA_ZONES.md` for complete zone architecture
- See `docs/RUNBOOK.md` for operational procedures
- See `docs/LINEAGE.md` for data flow details
