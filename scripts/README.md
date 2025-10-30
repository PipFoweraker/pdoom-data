# Data Pipeline Scripts

## Overview

This directory contains all scripts for the data pipeline, including migration, validation, and utility functions.

## Directory Structure

```
scripts/
|-- migration/           # Data migration between zones
|   |-- migrate.py      # Main migration script
|   |-- config.json     # Default configuration
|   `-- README.md       # Migration documentation
|-- validation/         # Data validation
|   `-- validate_funding.py  # Funding data validator
`-- utils/              # Shared utilities
    |-- logger.py       # Structured logging
    `-- file_ops.py     # Safe file operations
```

## Quick Start

### Migrate Data from Raw to Validated

```bash
cd scripts/migration
python migrate.py
```

### Validate Data Files

```bash
cd scripts/validation
python validate_funding.py --directory ../../data/raw/funding_sources
```

### Run Tests

```bash
cd tests
python test_migration.py
```

## Components

### Migration Scripts

Located in `migration/`, these scripts handle data movement between zones:

- **migrate.py**: Main migration orchestrator
  - Idempotent processing (safe to rerun)
  - Atomic file operations
  - Comprehensive logging
  - Validation before and after
  - See `migration/README.md` for details

### Validation Scripts

Located in `validation/`, these scripts validate data quality:

- **validate_funding.py**: Validates funding data
  - Schema compliance
  - Required field checks
  - Data type verification
  - Business rule validation

### Utility Modules

Located in `utils/`, these provide shared functionality:

- **logger.py**: Structured logging
  - JSON and human-readable logs
  - Rotating file handlers
  - Metadata support

- **file_ops.py**: Safe file operations
  - Atomic copy/move
  - Checksum verification
  - Platform-aware operations
  - Backup/restore support

## Configuration

Most scripts accept configuration via JSON files or command line arguments.

Example configuration:
```json
{
  "source_dir": "data/raw/funding_sources",
  "dest_dir": "data/transformed/validated",
  "required_columns": ["grant_id", "amount", "date", "source"],
  "operation": "copy"
}
```

## Safety Features

All scripts implement safety features:

- [YES] **Idempotent**: Safe to rerun without duplicates
- [YES] **Atomic Operations**: No partial writes
- [YES] **Checksum Verification**: Detect corruption
- [YES] **Comprehensive Logging**: Full audit trail
- [YES] **Validation**: Quality checks before processing
- [YES] **Error Handling**: Fail safely without data loss

## Logging

All scripts log to `logs/` directory:

- Human-readable: `logs/[component]/[component].log`
- JSON structured: `logs/[component]/[component].json`
- Logs auto-rotate at 10MB
- 5 backup files retained

## Development

### Adding New Scripts

1. Place in appropriate subdirectory
2. Follow existing patterns for logging and error handling
3. Add tests in `tests/`
4. Update this README
5. Document in relevant `docs/` files

### Code Style

- Python 3.7+
- ASCII-only content
- Comprehensive docstrings
- Type hints where appropriate
- Follow existing patterns

## Documentation

- Pipeline architecture: `docs/DATA_ZONES.md`
- Operational procedures: `docs/RUNBOOK.md`
- Field definitions: `docs/DATA_DICTIONARY.md`
- Data flow: `docs/LINEAGE.md`

## Support

For issues or questions:

1. Check documentation in `docs/`
2. Review logs in `logs/`
3. Examine source code
4. Open GitHub issue
