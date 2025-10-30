# Data Pipeline Runbook

## Purpose

This runbook provides step-by-step operational procedures for managing the data pipeline, including routine operations, troubleshooting, and recovery procedures.

## Prerequisites

- Python 3.7 or higher
- Read access to data directories
- Write access to logs directory

## Daily Operations

### Check Pipeline Status

```bash
# Check recent logs
tail -n 50 logs/migration/migration.log

# Check for errors
grep ERROR logs/migration/migration.log | tail -n 20

# Check processing state
cat logs/migration/.migration_state.json | python -m json.tool
```

### Run Standard Migration

```bash
# Copy new files from raw to validated
python scripts/migration/migrate.py \
  --config scripts/migration/config.json

# Check results
echo "Check logs/migration/ for detailed results"
```

### Validate Data Quality

```bash
# Run validation on a directory
python scripts/validation/validate_funding.py \
  --directory data/transformed/validated \
  --schema config/schemas/funding_data_v1.json
```

## Common Tasks

### Process New Data Source

**Scenario**: New funding data has been added to raw zone

**Steps**:

1. Verify data location:
   ```bash
   ls -lh data/raw/funding_sources/[source_name]/
   ```

2. Run migration:
   ```bash
   python scripts/migration/migrate.py \
     --source data/raw/funding_sources/[source_name] \
     --dest data/transformed/validated/[source_name]
   ```

3. Check logs:
   ```bash
   tail -f logs/migration/migration.log
   ```

4. Verify output:
   ```bash
   ls -lh data/transformed/validated/[source_name]/
   ```

### Reprocess Existing Data

**Scenario**: Validation rules changed, need to reprocess

**Steps**:

1. Clear processed state:
   ```bash
   # Backup current state
   cp logs/migration/.migration_state.json \
      logs/migration/.migration_state.json.bak
   
   # Clear state for specific files
   python -c "
   import json
   with open('logs/migration/.migration_state.json', 'r') as f:
       state = json.load(f)
   # Remove specific files from state
   state['processed_files'] = {}
   with open('logs/migration/.migration_state.json', 'w') as f:
       json.dump(state, f, indent=2)
   "
   ```

2. Run migration again:
   ```bash
   python scripts/migration/migrate.py
   ```

3. Verify reprocessing:
   ```bash
   grep "Processing file" logs/migration/migration.log | tail -n 20
   ```

### Archive Old Data

**Scenario**: Need to archive superseded data

**Steps**:

1. Identify files to archive:
   ```bash
   find data/raw/funding_sources -name "*2023*" -type f
   ```

2. Move to archive:
   ```bash
   mkdir -p data/raw/_archive/2023
   mv data/raw/funding_sources/*/2023-* data/raw/_archive/2023/
   ```

3. Document archival:
   ```bash
   echo "Archived 2023 data on $(date)" >> data/raw/_archive/ARCHIVE_LOG.txt
   ```

### Clean Up Logs

**Scenario**: Log files growing too large

**Steps**:

1. Check log sizes:
   ```bash
   du -sh logs/*
   ```

2. Archive old logs:
   ```bash
   tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/
   mv logs_archive_*.tar.gz ~/backups/
   ```

3. Logs will auto-rotate, but can manually clear if needed:
   ```bash
   # Keep only last 100 lines of each log
   for log in logs/*/*.log; do
     tail -n 100 "$log" > "$log.tmp"
     mv "$log.tmp" "$log"
   done
   ```

## Troubleshooting

### Migration Fails with "Validation Error"

**Symptoms**: Migration exits with validation errors

**Diagnosis**:
```bash
# Check validation logs
grep "Validation failed" logs/migration/migration.log

# Get details on failed file
grep -A 10 "ERROR.*validation" logs/migration/migration.log
```

**Resolution**:

1. Examine the failing file:
   ```bash
   cat [failing_file] | python -m json.tool
   ```

2. Check schema requirements:
   ```bash
   cat config/schemas/funding_data_v1.json
   ```

3. Options:
   - Fix source data in raw zone (create new version)
   - Update schema if requirements changed
   - Add data cleaning step

### Files Not Being Processed

**Symptoms**: Migration completes but files not in destination

**Diagnosis**:
```bash
# Check if already processed
cat logs/migration/.migration_state.json | grep [filename]

# Check for skip messages
grep "already processed" logs/migration/migration.log
```

**Resolution**:

1. Files may already be processed (idempotent behavior)
2. If need to reprocess, clear from state:
   ```bash
   # Edit .migration_state.json to remove file entry
   ```

### Disk Space Issues

**Symptoms**: Migration fails with "Insufficient disk space"

**Diagnosis**:
```bash
df -h
du -sh data/*
```

**Resolution**:

1. Clean up old backups:
   ```bash
   rm -rf data/_backups/[old_date]
   ```

2. Archive and compress old logs:
   ```bash
   tar -czf old_logs.tar.gz logs/
   rm -rf logs/*.log.*
   ```

3. Move serveable data to external storage if needed

### Checksum Mismatches

**Symptoms**: "Checksum mismatch" errors in logs

**Diagnosis**:
```bash
grep "Checksum mismatch" logs/migration/migration.log
```

**Resolution**:

1. This indicates file corruption during copy
2. Check disk health:
   ```bash
   # On Linux
   sudo smartctl -a /dev/sda
   ```

3. Retry the operation:
   ```bash
   # Clear state and rerun
   python scripts/migration/migrate.py
   ```

4. If persists, investigate storage system

### Permission Errors

**Symptoms**: "Permission denied" errors

**Diagnosis**:
```bash
ls -la data/raw/
ls -la data/transformed/
```

**Resolution**:
```bash
# Fix permissions
chmod -R u+rw data/
chmod -R u+rw logs/

# If using shared system, check group permissions
```

## Recovery Procedures

### Recover from Data Corruption

**If transformed data is corrupted**:

1. Stop all processing
2. Remove corrupted data:
   ```bash
   rm -rf data/transformed/validated/*
   rm -rf data/transformed/cleaned/*
   ```

3. Clear processing state:
   ```bash
   rm logs/migration/.migration_state.json
   ```

4. Reprocess from raw:
   ```bash
   python scripts/migration/migrate.py
   ```

5. Verify checksums in logs

**If raw data is corrupted**:

1. Raw data should never be corrupted (immutable)
2. If it is, restore from source system
3. Reingest from original source
4. Document incident

### Rollback Failed Migration

**Steps**:

1. Check for backups:
   ```bash
   ls -lh data/_backups/
   ```

2. Restore from backup:
   ```bash
   cp -r data/_backups/[timestamp]/* data/transformed/validated/
   ```

3. Restore processing state:
   ```bash
   cp logs/migration/.migration_state.json.bak \
      logs/migration/.migration_state.json
   ```

4. Investigate failure before retrying

## Monitoring

### Key Metrics to Track

**Daily Checks**:
- Number of files processed
- Validation failure rate
- Processing time per file
- Disk space utilization

**Weekly Checks**:
- Log file sizes
- Backup integrity
- Schema version currency
- Processing performance trends

### Setting Up Alerts

Create a monitoring script (example):

```bash
#!/bin/bash
# monitor_pipeline.sh

# Check for recent errors
ERROR_COUNT=$(grep -c ERROR logs/migration/migration.log)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "ALERT: $ERROR_COUNT errors in migration log"
fi

# Check disk space
DISK_USAGE=$(df -h /home | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: Disk usage at ${DISK_USAGE}%"
fi

# Check if migration ran recently
LAST_RUN=$(stat -c %Y logs/migration/migration.log)
NOW=$(date +%s)
HOURS_SINCE=$(( ($NOW - $LAST_RUN) / 3600 ))
if [ $HOURS_SINCE -gt 24 ]; then
    echo "ALERT: No migration in $HOURS_SINCE hours"
fi
```

## Pre-flight Checks

Before running migrations on production data:

- [ ] Backups are current
- [ ] Sufficient disk space (>20% free)
- [ ] No other migrations running
- [ ] Schema files are current
- [ ] Test with sample data first
- [ ] Review recent error logs

## Post-Migration Validation

After completing migration:

- [ ] Check log file for errors
- [ ] Verify file counts match expectations
- [ ] Spot-check sample files
- [ ] Verify checksums logged correctly
- [ ] Confirm disk space still adequate
- [ ] Update documentation if needed

## Contact Information

For issues not covered in this runbook:

1. Check logs in `logs/` directory
2. Review documentation in `docs/`
3. Examine source code in `scripts/`
4. Open issue on GitHub repository

## Version History

- v1.0 (2025-10): Initial runbook with migration procedures
