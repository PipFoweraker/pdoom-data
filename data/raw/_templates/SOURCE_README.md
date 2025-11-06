# [Source Name] Integration

## Overview

This directory contains data extracted from **[Source Name]**, [brief description of data source].

## Dataset Information

**Source**: [Source Name]
**Platform**: [Platform/Organization]
**URL**: [https://data.source.url]
**License**: [License Type]
**Maintainer**: [Maintainer/Organization]
**Records**: [Approximate count]
**Time Range**: [Date range of data]

## Data Sources Included

<!-- If applicable, list specific subsources -->

- Source 1
- Source 2
- Source 3

## Extraction Method

**Type**: [API | Web Scraping | Manual Download]
**Authentication**: [Required | Optional | Not Required]
**Method**: [Brief description]
**Frequency**: [One-time | Weekly | Daily | Real-time]

### Initial Extraction

[Description of initial extraction process]

### Weekly/Periodic Updates

[Description of update process]

## Data Structure

Each record contains:

### Required Fields
- `id` - [Description]
- `title` - [Description]
- `url` - [Description]
- `date` - [Description]

### Optional Fields
- `field1` - [Description]
- `field2` - [Description]

## Extraction Script

**Location**: `extraction_script.py`

### Usage

#### Initial Full Extraction
```bash
# Test with small sample (dry run)
python extraction_script.py --mode full --limit 100 --dry-run

# Extract first 1000 records
python extraction_script.py --mode full --limit 1000

# Extract all records
python extraction_script.py --mode full
```

#### Incremental Update
```bash
# Extract only new records since last run
python extraction_script.py --mode delta
```

### Configuration Options

The script supports filtering by:
- **Date range**: `--min-date YYYY-MM-DD`
- **Record limit**: `--limit N`
- [Other filters as applicable]

### Environment Variables

```bash
# Optional: Authentication token for higher rate limits / access
export [SOURCE]_API_TOKEN="your_token_here"
```

Get token from: [URL for getting token]

## File Organization

```
[source_name]/
├── README.md                   # This file
├── extraction_script.py        # Main extraction script
├── _templates/
│   ├── _metadata.json         # Metadata template
│   └── data_schema.json       # Schema definition
└── dumps/
    ├── [timestamp]/           # Timestamped dumps
    │   ├── data.jsonl         # Extracted records (JSONL format)
    │   └── _metadata.json     # Extraction metadata
    └── [timestamp]/           # Subsequent dumps
        ├── data.jsonl
        └── _metadata.json
```

## Metadata Tracking

Each dump includes `_metadata.json`:

```json
{
  "extraction_date": "[ISO 8601 timestamp]",
  "source_name": "[source_name]",
  "source_url": "[source URL]",
  "extraction_method": "[api|web_scrape|manual]",
  "extractor_version": "1.0.0",
  "data_format": "jsonl",
  "record_count": 0,
  "extraction_type": "full|delta",
  "last_extraction_date": null,
  "filters_applied": {
    "date_range": "YYYY-MM-DD to present",
    "other_filters": []
  },
  "extraction_status": "complete",
  "attribution": "[Attribution text]",
  "license": "[License]"
}
```

## Schema Validation

**Schema**: `config/schemas/[source_name]_v1.json`

All extracted data is validated against this schema before migration to the transformed zone.

## Attribution Requirements

### Citation

When using this data, please cite:

```
Dataset: [Dataset Name]
Source: [Source URL]
Maintained by: [Maintainer]
License: [License Type]

[Optional: Paper citation if applicable]
```

### License Compliance

This dataset is provided under the **[License Name]**, which allows:
- [Permission 1]
- [Permission 2]
- [Permission 3]

With the requirement of:
- [Requirement 1]
- [Requirement 2]

## Data Quality Notes

### Content Warnings
- [Any content warnings or biases to be aware of]

### Known Limitations
- [Limitation 1]
- [Limitation 2]
- [Limitation 3]

## Logging

Extraction logs are stored in `logs/[source_name]_extraction/`:
- **Console**: Human-readable progress updates
- **File**: Rotating log files (structured format)
- **JSON**: Machine-parseable logs for automation

## Rate Limits

<!-- If applicable -->

### [Platform] Rate Limits (per time window)

| Account Type | Requests | Downloads |
|--------------|----------|-----------|
| Anonymous | X | Y |
| Free (Authenticated) | X | Y |
| Paid | X | Y |

**Recommendation**: [Recommendation about rate limits]

## Troubleshooting

### Rate Limit Errors
```
Solution: [Solution description]
```

### Missing Fields
```
Solution: [Solution description]
```

### Authentication Errors
```
Solution: [Solution description]
```

### [Other common issues]
```
Solution: [Solution description]
```

## Integration with pdoom-data Pipeline

### Data Flow

```
[Data Source]
    ↓
[extraction_script.py]
    ↓
data/raw/[source_name]/dumps/[timestamp]/data.jsonl
    ↓
[scripts/migration/migrate.py]
    ↓
data/transformed/validated/
    ↓
[Future: Cleaning & Enrichment]
    ↓
data/serveable/
```

### Weekly Automation

<!-- If automated -->

GitHub Actions workflow runs every [day] at [time]:
- Executes delta extraction
- Validates data against schema
- Migrates to transformed zone
- Commits changes to repository

See: `.github/workflows/[source-name]-refresh.yml`

## Contact & Maintenance

**pdoom-data Maintainer**: [Maintainer]
**Dataset Maintainer**: [Original maintainer]
**Issues**: Report to pdoom-data GitHub issues
**Dataset Issues**: Report to [original source issue tracker]

## References

- **Dataset Homepage**: [URL]
- **Documentation**: [URL]
- **API Reference**: [URL]
- **Source Code**: [URL if applicable]

## Version History

- **v1.0.0** ([DATE]): Initial integration
  - [Feature 1]
  - [Feature 2]
  - [Feature 3]
