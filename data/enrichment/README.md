# Enrichment Data

This directory contains quality scoring metadata for alignment research records.
The enrichment system uses a **nondestructive metadata pattern** - source data
is never modified; scoring results are stored as separate overlay files.

## Purpose

The raw alignment research dataset contains 6,500+ records of varying quality.
The enrichment system scores each record to identify high-quality, game-worthy
events without losing any source data.

## Files

### `alignment_research/quality_scores_YYYY-MM-DD.json`

Quality scores for each alignment research record.

**Structure:**
```json
{
  "_metadata": {
    "version": "1.0.0",
    "created": "2024-12-24T...",
    "source_dump": "dumps/2025-12-24_063313",
    "total_records": 6549,
    "scoring_config": {...},
    "tier_thresholds": {...}
  },
  "records": {
    "<source_id>": {
      "source_id": "4e3806e28ffb49e...",
      "quality_score": 8.5,
      "quality_tier": "A",
      "signals": {
        "source": "arxiv",
        "text_length": 25000,
        "is_newsletter": false,
        "has_authors": true,
        "year": "2019",
        "has_tags": true
      },
      "title_preview": "Attention Is All You Need"
    }
  },
  "tier_summary": {
    "A": {"count": 1166, "ids": [...]},
    "B": {"count": 3966, "ids": [...]},
    "C": {"count": 1375, "ids": [...]},
    "D": {"count": 42, "ids": [...]}
  }
}
```

## ID Linking

Records are linked through the existing ID chain:

```
Source Record (raw JSONL)      Enrichment Metadata          Timeline Event (serveable)
-------------------------      -------------------          --------------------------
id: "4e3806e28ffb49e..."  -->  source_id: same          --> source_id: same
source: "arxiv"                                              id: "arxiv_4e3806e28..."
```

The `source_id` is the StampyAI hash from the original HuggingFace dataset.
This ID is persistent and immutable, allowing full traceability.

## Scoring System

### Signals and Weights

| Signal | Points | Detection |
|--------|--------|-----------|
| Source = arxiv | +3 | Academic papers |
| Source = distill | +3 | High-quality ML explainers |
| Has authors | +1 | Attribution present |
| NOT newsletter/linkpost | +2 | Excludes aggregation posts |
| Text length > 5000 | +1 | Substantive content |
| Text length > 10000 | +1 | Long-form content |
| Year <= 2019 | +1 | Historical (rarer, more valuable) |
| Has tags | +0.5 | Categorized content |

**Maximum possible score: 12.5**

### Newsletter Detection Patterns

The system detects and deprioritizes:
- `[AN #123]` - Alignment Newsletter
- `newsletter`, `linkpost`, `link post`
- `weekly digest`, `monthly roundup`
- Aggregation/summary posts

### Tier Thresholds

| Tier | Score | Description |
|------|-------|-------------|
| A | 7.0+ | Game-ready, high-impact (arxiv/distill papers) |
| B | 4.0-6.9 | Good quality forum content |
| C | 2.0-3.9 | Background material |
| D | 0-1.9 | Newsletters, linkposts, low-value |

## Usage

### Running the Scorer

```bash
python scripts/enrichment/score_quality.py \
  --input data/raw/alignment_research/dumps/2025-12-24_063313/data.jsonl \
  --output data/enrichment/alignment_research/quality_scores_2024-12-24.json
```

### Transforming Enriched Data

```bash
python scripts/enrichment/transform_enriched.py \
  --scores data/enrichment/alignment_research/quality_scores_2024-12-24.json \
  --source data/raw/alignment_research/dumps/2025-12-24_063313/data.jsonl \
  --output data/serveable/api/timeline_events/enriched_alignment_research \
  --tiers A
```

To include B-tier as well:
```bash
--tiers A,B
```

## Current Results (2024-12-24)

| Tier | Count | Percentage | Description |
|------|-------|------------|-------------|
| A | 1,166 | 17.8% | 1,129 arxiv + 37 distill papers |
| B | 3,966 | 60.6% | Forum posts with good content |
| C | 1,375 | 21.0% | Shorter content, newsletters |
| D | 42 | 0.6% | Pure linkposts/aggregation |

### A-Tier by Year

| Year | Count |
|------|-------|
| 2016 | 53 |
| 2017 | 60 |
| 2018 | 205 |
| 2019 | 200 |
| 2020 | 211 |
| 2021 | 223 |
| 2022 | 190 |
| 2023 | 24 |

## Design Decisions

1. **Nondestructive**: Source JSONL is never modified; metadata is overlay
2. **Versioned**: Timestamped files allow re-scoring without losing history
3. **Regenerable**: Scoring is deterministic and can be re-run
4. **Linked**: `source_id` provides traceability to original records
5. **Tiered**: Multiple quality levels support different use cases

## Related Documentation

- [ARCHITECTURE_DECISION_RECORDS.md](../../docs/ARCHITECTURE_DECISION_RECORDS.md) - ADR-002 on nondestructive metadata
- [EVENT_SCHEMA.md](../../docs/EVENT_SCHEMA.md) - Timeline event schema
- [QUICK_START_INTEGRATION.md](../../docs/QUICK_START_INTEGRATION.md) - Integration guide
