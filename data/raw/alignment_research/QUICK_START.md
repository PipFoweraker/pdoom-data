# Alignment Research Dataset - Quick Start

**For quick reference - see [README.md](README.md) for full documentation**

## Extract Data

```bash
# Test extraction (10 records, dry run)
python extraction_script.py --mode full --limit 10 --dry-run

# Extract sample (100 records)
python extraction_script.py --mode full --limit 100

# Full extraction
python extraction_script.py --mode full

# Delta update (new records only)
python extraction_script.py --mode delta
```

## Validate Data

```bash
# Find latest dump
LATEST=$(ls -td dumps/*/ | head -n 1)

# Validate
python ../../../scripts/validation/validate_alignment_research.py "${LATEST}"
```

## Check Status

```bash
# View metadata
cat "${LATEST}_metadata.json" | python -m json.tool

# Count records
wc -l "${LATEST}data.jsonl"

# Sample record
head -n 1 "${LATEST}data.jsonl" | python -m json.tool
```

## Weekly Automation

GitHub Actions runs automatically every Monday at 2am UTC.

**Manual trigger**: Go to Actions tab → Weekly Data Refresh → Run workflow

## Files

- `extraction_script.py` - Main extraction script
- `README.md` - Full documentation
- `dumps/` - Timestamped extractions
- `_templates/` - Metadata templates

## Links

- **Integration Guide**: [docs/ALIGNMENT_RESEARCH_INTEGRATION.md](../../../docs/ALIGNMENT_RESEARCH_INTEGRATION.md)
- **Schema**: [config/schemas/alignment_research_v1.json](../../../config/schemas/alignment_research_v1.json)
- **Validation Script**: [scripts/validation/validate_alignment_research.py](../../../scripts/validation/validate_alignment_research.py)
- **HuggingFace Dataset**: https://huggingface.co/datasets/StampyAI/alignment-research-dataset

## Quick Stats

- **Initial Dataset**: 1,000 records (27MB)
- **Extraction Time**: 3.8 seconds
- **Validation Pass**: 100%
- **Update Frequency**: Weekly (automated)
- **Data Sources**: 30+ platforms
