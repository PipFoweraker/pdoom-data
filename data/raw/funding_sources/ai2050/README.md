# Schmidt Sciences AI2050 Funding Data

## Overview

This directory contains funding event data extracted from Schmidt Sciences AI2050.

## Directory Structure

```
ai2050/
|-- dumps/               # Timestamped automatic extractions
|   |-- YYYY-MM-DD_HHMMSS/
|   |   |-- data.json    # Extracted data
|   |   `-- _metadata.json  # Extraction metadata
|-- manual/              # Manual extracts and corrections
|   `-- YYYY-MM-DD_notes.txt
`-- README.md            # This file
```

## Data Source Information

- **Source Name**: Schmidt Sciences AI2050
- **Source URL**: https://ai2050.schmidtsciences.org/
- **Data Type**: Funding events, grants, awards
- **Update Frequency**: As announced
- **Extraction Method**: Manual extraction from announcements

## Extraction Workflow

### Automated Extraction

1. Run dump helper:
   ```bash
   python scripts/extraction/new_dump.py --source ai2050 --method manual
   ```

2. Extract data from source (script or manual)

3. Save data to timestamped directory

4. Fill in `_metadata.json` with extraction details

5. Validate dump:
   ```bash
   python scripts/extraction/validate_dump.py --source ai2050 --dump YYYY-MM-DD_HHMMSS
   ```

### Manual Extraction

1. Create timestamped directory in `manual/`

2. Extract data manually and save files

3. Document extraction process in notes file

4. Add metadata file for tracking

## Data Format

See `data/raw/funding_sources/_templates/metadata_schema.json` for expected format.

Expected fields:
- grant_id: Unique identifier
- recipient_name: Organization or individual name
- amount: Grant amount in USD
- currency: Currency code (ISO 4217)
- grant_date: Date of grant (ISO 8601)
- focus_area: Research area or topic
- description: Brief description of grant
- source_url: Original source URL

## Notes

- All data in this directory is immutable (append-only)
- Do not modify files after creation
- For corrections, create new dump with updated data
- Archive superseded data to `data/raw/_archive/`

## Contact

For questions about this data source or extraction issues, see project documentation.
