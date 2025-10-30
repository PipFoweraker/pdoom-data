# Funding Event Dump Spaces Documentation

## Overview

This system provides organized dump spaces for collecting funding event data from multiple sources through web crawling and manual extraction. It integrates with the raw data zone from the broader data structure.

## Directory Structure

```
data/raw/funding_sources/
|-- sff/                              # Survival & Flourishing Fund
|   |-- dumps/                        # Timestamped automatic extractions
|   |   `-- YYYY-MM-DD_HHMMSS/       # Each dump in timestamped directory
|   |       |-- data.json             # Extracted data
|   |       `-- _metadata.json        # Extraction metadata
|   |-- manual/                       # Manual extracts and corrections
|   `-- README.md                     # Source-specific documentation
|-- open_philanthropy/
|-- ai2050/
|-- macroscopic/
|-- givewiki/
|-- cooperative_ai/
|-- catalyze_impact/
`-- _templates/                       # Templates for new sources
    |-- SOURCE_README.md              # README template
    |-- metadata_schema.json          # Metadata schema
    |-- data_schema.json              # Common data schema
    `-- _metadata.json                # Example metadata file
```

## Supported Funding Sources

1. **SFF** - Survival & Flourishing Fund
2. **Open Philanthropy** - Open Philanthropy Project
3. **AI2050** - Schmidt Sciences AI2050
4. **Macroscopic** - Macroscopic
5. **GiveWiki** - GiveWiki database
6. **Cooperative AI** - Cooperative AI Foundation
7. **Catalyze Impact** - Catalyze Impact

## Metadata Standard

Every dump includes a `_metadata.json` file with the following structure:

```json
{
  "extraction_date": "2025-10-31T14:30:00Z",
  "source_name": "sff",
  "source_url": "https://...",
  "extraction_method": "web_scrape|manual|api",
  "extractor_version": "1.0.0",
  "data_format": "json|csv|html",
  "record_count": 150,
  "extraction_notes": "...",
  "fields_extracted": ["grant_id", "recipient", "amount", "date"],
  "extraction_status": "complete|partial|failed"
}
```

### Required Fields

- `extraction_date`: ISO 8601 timestamp of extraction
- `source_name`: Must match one of the valid sources
- `source_url`: URL where data was extracted from
- `extraction_method`: How data was extracted (web_scrape, manual, api)
- `data_format`: Format of extracted data
- `extraction_status`: Status of extraction (complete, partial, failed, pending)

### Optional Fields

- `extractor_version`: Version of extraction script/tool
- `record_count`: Number of records extracted
- `extraction_notes`: Any notes about the extraction
- `fields_extracted`: List of fields extracted
- `errors`: List of errors encountered
- `warnings`: List of warnings

## Common Data Schema

Preliminary schema for funding events:

```json
{
  "grant_id": "string (unique identifier)",
  "source": "string (source name)",
  "recipient_name": "string",
  "recipient_type": "individual|organization|institution",
  "amount": "number (in specified currency)",
  "currency": "string (ISO 4217, default: USD)",
  "grant_date": "date (ISO 8601)",
  "grant_type": "string",
  "focus_area": "string",
  "description": "string",
  "source_url": "string",
  "extracted_at": "datetime (ISO 8601)"
}
```

### Required Data Fields

- `grant_id`: Unique identifier for the grant
- `source`: Source organization name
- `recipient_name`: Name of recipient
- `amount`: Grant amount
- `grant_date`: Date grant was awarded

### Optional Data Fields

- `recipient_type`: Type of recipient entity
- `currency`: Currency code (defaults to USD)
- `grant_type`: Category of grant
- `focus_area`: Research or focus area
- `description`: Description of grant purpose
- `source_url`: Link to original announcement
- `extracted_at`: Timestamp of extraction
- `duration_months`: Grant duration
- `tags`: Additional categorization
- `notes`: Additional observations

## Tools and Scripts

### 1. Setup Script

**Location**: `scripts/setup/create_dump_spaces.py`

**Purpose**: Creates directory structure for all funding sources

**Usage**:
```bash
python scripts/setup/create_dump_spaces.py
```

**What it does**:
- Creates all 7 funding source directories
- Creates dumps/ and manual/ subdirectories
- Creates .gitkeep files for empty directories
- Sets up _templates directory

### 2. Dump Helper Script

**Location**: `scripts/extraction/new_dump.py`

**Purpose**: Creates timestamped dump directory for new extraction

**Usage**:
```bash
python scripts/extraction/new_dump.py --source <source> --method <method>
```

**Examples**:
```bash
# Create dump for manual SFF extraction
python scripts/extraction/new_dump.py --source sff --method manual

# Create dump for web scraping Open Philanthropy
python scripts/extraction/new_dump.py --source open_philanthropy --method web_scrape

# Create dump for API extraction from AI2050
python scripts/extraction/new_dump.py --source ai2050 --method api
```

**What it does**:
- Creates timestamped directory (YYYY-MM-DD_HHMMSS)
- Creates _metadata.json with template
- Creates empty data.json file
- Validates source name

### 3. Validation Helper Script

**Location**: `scripts/extraction/validate_dump.py`

**Purpose**: Validates dump directory structure and content

**Usage**:
```bash
python scripts/extraction/validate_dump.py --source <source> --dump <timestamp>
```

**Example**:
```bash
python scripts/extraction/validate_dump.py --source sff --dump 2025-10-30_225651
```

**What it validates**:
- Directory structure exists
- _metadata.json exists and is valid JSON
- All required metadata fields present
- Metadata values are valid
- data.json exists and is valid JSON
- Record count matches between metadata and data
- Files use ASCII encoding only

## Workflows

### Manual Extraction Workflow

1. Create new dump directory:
   ```bash
   python scripts/extraction/new_dump.py --source sff --method manual
   ```

2. Extract data from source manually and save to `data.json`

3. Update `_metadata.json` with:
   - source_url
   - record_count
   - fields_extracted
   - extraction_notes
   - extraction_status (change to "complete")

4. Validate the dump:
   ```bash
   python scripts/extraction/validate_dump.py --source sff --dump <timestamp>
   ```

5. Data is ready for migration to transformed zone

### Automated Extraction Workflow (Future)

1. Scheduled scraper runs `new_dump.py`
2. Scraper extracts and saves data to `data.json`
3. Scraper fills metadata automatically
4. Validation runs automatically
5. Triggers migration pipeline
6. Logs and schedules next run

## Integration with Data Pipeline

### Current Integration

- **Issue #1**: Uses directory structure created there
- Dumps land in `data/raw/funding_sources/`
- Follow append-only principles from raw data zone

### Future Integration

- **Issues #3-9**: Each investigation populates its dump space
- Migration scripts can process dumps to `data/transformed/`
- Eventually flows to `data/serveable/` for production use

## Example Dump

An example dump is provided to demonstrate the structure. You can find examples in the dumps directories with timestamped folders (format: YYYY-MM-DD_HHMMSS).

This demonstrates:
- Proper metadata structure
- Sample funding event records
- Valid JSON formatting
- ASCII-only content

## ASCII Compliance

All files must use ASCII-only characters (0-127):
- No Unicode quotes or special characters
- Use standard ASCII quotes and apostrophes
- Ensures agent compatibility and cross-platform reliability
- All scripts validate ASCII compliance

## Best Practices

1. **Timestamps**: Always use UTC time for consistency
2. **Immutability**: Never modify dumps after creation
3. **Corrections**: Create new dump with corrected data
4. **Documentation**: Fill in all metadata fields completely
5. **Validation**: Always validate before considering dump complete
6. **Version Control**: Use git for tracking changes to scripts
7. **Naming**: Use lowercase with underscores for consistency

## Troubleshooting

### Validation Fails

- Check JSON syntax in _metadata.json and data.json
- Verify all required fields are present
- Ensure ASCII-only characters used
- Check record_count matches data array length

### Directory Not Found

- Run setup script: `python scripts/setup/create_dump_spaces.py`
- Check source name is valid
- Verify base directory path

### Unicode Errors

- Review files for non-ASCII characters
- Use ASCII quotes: " and '
- Avoid em-dashes, smart quotes, emojis
- Re-save files with ASCII encoding

## Future Enhancements

Potential improvements for this system:

1. Automated web scrapers for each source
2. Scheduled extraction jobs
3. Duplicate detection across dumps
4. Automated migration to transformed zone
5. Dashboard for monitoring extractions
6. API for accessing dump metadata
7. Schema evolution tracking
8. Data quality metrics

## Questions and Support

For questions about:
- Data sources: See individual source README.md files
- Extraction issues: Check validation output
- Schema questions: Review _templates/data_schema.json
- Integration: See DATA_ARCHITECTURE.md

## License

MIT License - See repository LICENSE file for details.
