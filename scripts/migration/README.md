# Migration Scripts

## Overview

This directory contains scripts for migrating data between zones with validation, logging, and safety features.

## Main Script: migrate.py

The migration script safely copies or moves data from raw zone to transformed zone with full validation and logging.

### Features

- **Idempotent**: Safe to rerun, tracks processed files by checksum
- **Atomic Operations**: Uses temp files and atomic moves to prevent corruption
- **Validation**: Validates data before and after migration
- **Logging**: Comprehensive JSON and human-readable logs
- **Backup**: Creates backups before overwriting existing files
- **Platform-Aware**: Works on Windows, Mac, and Linux

### Basic Usage

```bash
# Copy files from raw to validated zone (default config)
python migrate.py

# Use custom configuration
python migrate.py --config custom_config.json

# Process specific source
python migrate.py \
  --source data/raw/funding_sources/sff \
  --dest data/transformed/validated/sff

# Move instead of copy
python migrate.py --operation move
```

### Configuration

Configuration can be provided via JSON file (config.json) or command line arguments.

**Configuration File (config.json)**:
```json
{
  "source_dir": "data/raw/funding_sources",
  "dest_dir": "data/transformed/validated",
  "backup_dir": "data/_backups",
  "log_dir": "logs/migration",
  "required_columns": ["grant_id", "amount", "date", "source"],
  "validation_schema": "config/schemas/funding_data_v1.json",
  "fail_on_warning": false,
  "create_backups": true,
  "operation": "copy"
}
```

**Command Line Arguments**:
- `--config PATH`: Path to configuration file
- `--pattern GLOB`: File pattern to process (default: `*`)
- `--source PATH`: Override source directory
- `--dest PATH`: Override destination directory
- `--operation {copy,move}`: Operation type

### How It Works

1. **Scan**: Finds all files matching pattern in source directory
2. **Check State**: Calculates checksums and checks if already processed
3. **Validate Source**: Validates source data against schema
4. **Backup**: Creates backup of destination if it exists
5. **Copy/Move**: Atomically copies or moves file to destination
6. **Validate Destination**: Validates copied/moved data
7. **Update State**: Records file as processed with metadata
8. **Log**: Records all operations with timestamps and checksums

### Processing State

The migration maintains state in `.migration_state.json` to enable idempotent operations:

```json
{
  "processed_files": {
    "data/raw/funding_sources/sff/2024-01-15.json": {
      "checksum": "a3b2c1d4...",
      "processed_at": "2025-10-30T14:25:12Z",
      "dest_path": "data/transformed/validated/sff/2024-01-15.json",
      "metadata": {
        "size_bytes": 12345,
        "modified_timestamp": 1635432123.456
      }
    }
  },
  "last_updated": "2025-10-30T14:25:12Z"
}
```

Files are only reprocessed if:
- Not in state file
- Checksum has changed
- State file is manually cleared

### Error Handling

**Validation Failures**:
- Source validation failure: File skipped, error logged
- Destination validation failure: Operation rolled back if possible

**File Operation Failures**:
- Disk space check before operations
- Checksum verification after copy
- Backup restoration on critical failures

**State Corruption**:
- State file backed up before updates
- Can be manually reset if corrupted
- Safe to delete and reprocess

### Logs

Logs are written to two formats:

**Human-Readable** (`logs/migration/migration.log`):
```
2025-10-30 14:25:12 - migration - INFO - Processing file: data/raw/funding_sources/sff/2024-01-15.json
2025-10-30 14:25:13 - migration - INFO - Copy successful: checksum a3b2c1d4...
```

**JSON** (`logs/migration/migration.json`):
```json
{
  "timestamp": "2025-10-30T14:25:12Z",
  "level": "INFO",
  "message": "Processing file",
  "file": "data/raw/funding_sources/sff/2024-01-15.json",
  "checksum": "a3b2c1d4..."
}
```

### Common Operations

**Reprocess All Data**:
```bash
# Clear state
rm logs/migration/.migration_state.json

# Run migration
python migrate.py
```

**Process New Files Only**:
```bash
# State file ensures only new files processed
python migrate.py
```

**Process Specific Source**:
```bash
python migrate.py \
  --source data/raw/funding_sources/sff \
  --dest data/transformed/validated/sff
```

**Validate Without Processing**:
```bash
# Use validation script directly
python ../validation/validate_funding.py \
  --directory data/raw/funding_sources/sff
```

### Troubleshooting

**Files Not Being Processed**:
- Check if already in `.migration_state.json`
- Verify file matches pattern
- Check logs for skip messages

**Validation Failures**:
- Review validation errors in logs
- Check data against schema
- Verify required fields present

**Performance Issues**:
- Use `--pattern` to process subset
- Check disk I/O performance
- Review log file sizes

### Exit Codes

- `0`: Success (all files processed)
- `1`: Failure (one or more files failed)

### Safety Features

- **No Modification of Raw Data**: Raw zone is read-only
- **Atomic Operations**: No partial writes
- **Checksum Verification**: Detects corruption
- **Backup Before Overwrite**: Can restore on failure
- **Comprehensive Logging**: Full audit trail
- **Idempotent**: Safe to rerun
- **Fail-Safe**: Errors stop processing, don't corrupt data

## Related Documentation

- Main documentation: `docs/DATA_ZONES.md`
- Operational procedures: `docs/RUNBOOK.md`
- Field definitions: `docs/DATA_DICTIONARY.md`
- Data flow: `docs/LINEAGE.md`
