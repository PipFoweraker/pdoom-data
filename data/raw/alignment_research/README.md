# Alignment Research Dataset Integration

## Overview

This directory contains data extracted from the **StampyAI Alignment Research Dataset**, a comprehensive collection of AI alignment and safety research documents aggregated from 30+ sources.

## Dataset Information

**Source**: StampyAI/alignment-research-dataset
**Platform**: Hugging Face
**URL**: https://huggingface.co/datasets/StampyAI/alignment-research-dataset
**License**: MIT License
**Maintainer**: StampyAI / AI Safety Info
**Records**: 10,000 - 100,000 documents
**Time Range**: Varies by source (many from 2010s onwards)

## Data Sources Included

The dataset aggregates content from 30+ platforms including:

### Research Platforms
- ArXiv (AI safety papers)
- Distill
- Arbital

### Forums & Communities
- LessWrong
- Alignment Forum
- Effective Altruism Forum

### Organization Blogs
- DeepMind
- OpenAI
- Anthropic
- MIRI
- EleutherAI
- Gwern Branwen
- 10+ other researcher blogs

### Educational Content
- AGI Safety Fundamentals
- AI Safety Talks
- YouTube channels (AI Explained, Rob Miles AI, etc.)

### Curated Collections
- Stampy's FAQ (aisafety.info)
- Google Sheets managed documents

## Extraction Method

**Type**: API (Hugging Face Datasets Library)
**Authentication**: Optional (token recommended for higher rate limits)
**Method**: Streaming (memory-efficient)
**Frequency**: Weekly delta updates

### Initial Extraction
- Bulk download of all historical records matching filter criteria
- Stores in timestamped dump directory
- Creates comprehensive metadata file

### Weekly Updates
- Delta detection based on last extraction date
- Only fetches new/updated records
- Appends to separate timestamped dump
- Minimizes API calls and storage

## Data Structure

Each record contains:

### Required Fields
- `id` - Unique identifier
- `source` - Origin platform (arxiv, lesswrong, etc.)
- `title` - Document title
- `text` - Full text content
- `url` - Source URL
- `date_published` - ISO 8601 format

### Optional Fields
- `authors` - List of authors
- `abstract` - Paper/post abstract
- `doi` - Digital Object Identifier
- `categories` - Classification categories
- `tags` - User-defined tags
- `source_type` - Original format (latex, markdown, html, pdf)
- `alignment_text` - Alignment classification (pos/neg/unlabeled)
- `confidence_score` - Classification confidence (0-1)

## Extraction Script

**Location**: `extraction_script.py`

### Usage

#### Initial Full Extraction
```bash
# Test with small sample (dry run)
python extraction_script.py --mode full --limit 100 --dry-run

# Extract first 1000 records
python extraction_script.py --mode full --limit 1000

# Extract all records (may take hours)
python extraction_script.py --mode full
```

#### Weekly Delta Update
```bash
# Extract only new records since last run
python extraction_script.py --mode delta
```

### Configuration Options

The script supports filtering by:
- **Date range**: Only records published after specified date
- **Sources**: Specific platforms (arxiv, lesswrong, etc.)
- **Keywords**: Text search in content
- **Record limit**: For testing or partial extractions

### Environment Variables

```bash
# Optional: Higher rate limits with Hugging Face token
export HF_TOKEN="your_huggingface_token"
```

Get token from: https://huggingface.co/settings/tokens

## File Organization

```
alignment_research/
├── README.md                   # This file
├── extraction_script.py        # Main extraction script
├── _templates/
│   ├── _metadata.json         # Metadata template
│   └── data_schema.json       # Schema definition
└── dumps/
    ├── 2025-11-06_140000/     # Timestamped dumps
    │   ├── data.jsonl         # Extracted records (JSONL format)
    │   └── _metadata.json     # Extraction metadata
    └── 2025-11-13_020000/     # Delta update
        ├── data.jsonl
        └── _metadata.json
```

## Metadata Tracking

Each dump includes `_metadata.json`:

```json
{
  "extraction_date": "2025-11-06T14:00:00Z",
  "source_name": "alignment_research",
  "source_url": "https://huggingface.co/datasets/StampyAI/alignment-research-dataset",
  "extraction_method": "api",
  "extractor_version": "1.0.0",
  "data_format": "jsonl",
  "record_count": 1543,
  "extraction_type": "full|delta",
  "last_extraction_date": "2025-10-30T...",
  "filters_applied": {
    "date_range": "2020-01-01 to present",
    "sources": ["arxiv", "alignmentforum", "lesswrong"],
    "keywords": ["alignment", "safety"]
  },
  "extraction_status": "complete",
  "huggingface_dataset_version": "main",
  "attribution": "StampyAI/AI Safety Info - MIT License"
}
```

## Schema Validation

**Schema**: `config/schemas/alignment_research_v1.json`

All extracted data is validated against this schema before migration to the transformed zone.

## Attribution Requirements

### Citation

When using this data, please cite:

```
Dataset: StampyAI Alignment Research Dataset
Source: https://huggingface.co/datasets/StampyAI/alignment-research-dataset
Maintained by: StampyAI / AI Safety Info
License: MIT License

Original Paper:
Kirchner, J. H., Smith, L., Thibodeau, J., McDonnell, K., and Reynolds, L.
"Understanding AI alignment research: A Systematic Analysis"
arXiv preprint arXiv:2206.02841 (2022)
```

### License Compliance

This dataset is provided under the **MIT License**, which allows:
- Commercial use
- Modification
- Distribution
- Private use

With the requirement of:
- Attribution to original authors
- Inclusion of license and copyright notice

## Data Quality Notes

### Content Warnings
- LessWrong posts are overweighted in the dataset
- Content may include discussions of existential risk and doom scenarios
- Be aware of potential bias when using for model training

### Known Limitations
- Not all sources updated at same frequency
- Some records may have missing optional fields
- Text quality varies by source (LaTeX conversions, HTML parsing, etc.)
- Delta detection relies on `date_published` field accuracy

## Logging

Extraction logs are stored in `logs/alignment_extraction/`:
- **Console**: Human-readable progress updates
- **File**: Rotating log files (structured format)
- **JSON**: Machine-parseable logs for automation

## Rate Limits

### Hugging Face API Limits (5-minute windows)

| Account Type | API Calls | File Downloads |
|--------------|-----------|----------------|
| Anonymous | 500 | 3,000 |
| Free (Authenticated) | 1,000 | 5,000 |
| PRO | 2,500 | 12,000 |
| Enterprise | 6,000+ | 50,000+ |

**Recommendation**: Use authentication token to avoid rate limiting.

## Troubleshooting

### Rate Limit Errors
```
Solution: Add HF_TOKEN environment variable or reduce extraction frequency
```

### Missing Fields
```
Solution: Check schema for optional vs required fields. Use try-except for optional fields.
```

### Memory Issues
```
Solution: Use streaming mode (default) or reduce batch size in script
```

### Duplicate Records
```
Solution: Delta mode checks last_extraction_date. Use --force-full to re-extract.
```

## Integration with pdoom-data Pipeline

### Data Flow

```
Hugging Face API
    ↓
[extraction_script.py]
    ↓
data/raw/alignment_research/dumps/[timestamp]/data.jsonl
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

GitHub Actions workflow runs every Monday at 2am UTC:
- Executes delta extraction
- Validates data against schema
- Migrates to transformed zone
- Commits changes to repository

See: `.github/workflows/weekly-data-refresh.yml`

## Contact & Maintenance

**pdoom-data Maintainer**: See repository owner
**Dataset Maintainer**: StampyAI / AI Safety Info
**Issues**: Report to pdoom-data GitHub issues
**Dataset Issues**: Report to https://github.com/StampyAI/alignment-research-dataset

## References

- **Dataset Repository**: https://github.com/StampyAI/alignment-research-dataset
- **Hugging Face Dataset**: https://huggingface.co/datasets/StampyAI/alignment-research-dataset
- **Original Paper**: https://arxiv.org/abs/2206.02841
- **Hugging Face Docs**: https://huggingface.co/docs/datasets/
- **StampyAI**: https://aisafety.info

## Version History

- **v1.0.0** (2025-11-06): Initial integration
  - Full extraction capability
  - Delta update mechanism
  - Schema validation
  - Comprehensive metadata tracking
  - Weekly automation
