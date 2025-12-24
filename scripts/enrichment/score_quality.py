#!/usr/bin/env python3
"""
Quality Scoring for Alignment Research Records

This script scores alignment research records to identify high-quality,
game-worthy events using a non-destructive metadata approach.

The scoring system uses multiple signals to tier records:
- A tier (7.0+): Game-ready, high-impact research
- B tier (4.0-6.9): Good quality, may need light curation
- C tier (2.0-3.9): Background material
- D tier (0-1.9): Newsletters, link posts, low-value

Output is stored separately from source data, linked by source_id.
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.logger import get_logger

logger = get_logger('enrichment_scoring')


# Newsletter/linkpost detection patterns
NEWSLETTER_PATTERNS = [
    r'\[AN #\d+\]',           # Alignment Newsletter [AN #123]
    r'alignment newsletter',   # Plain text reference
    r'newsletter',
    r'linkpost',
    r'link post',
    r'\[linkpost\]',
    r'links for \w+',          # "Links for December"
    r'weekly.*digest',
    r'monthly.*roundup',
    r'weekly.*review',
    r'monthly.*review',
    r'^links:',                # Title starts with "Links:"
]


# Scoring weights configuration
SCORING_CONFIG = {
    'source_arxiv': 3,
    'source_distill': 3,
    'has_authors': 1,
    'not_newsletter': 2,
    'text_length_5k': 1,
    'text_length_10k': 1,
    'year_pre_2020': 1,
    'has_tags': 0.5
}

# Tier thresholds
TIER_THRESHOLDS = {
    'A': 7.0,
    'B': 4.0,
    'C': 2.0,
    'D': 0.0
}


def is_newsletter(title: str, text: str = '') -> bool:
    """
    Detect if a record is a newsletter or linkpost.

    Args:
        title: Record title
        text: Record text (first portion checked)

    Returns:
        True if detected as newsletter/linkpost
    """
    title_lower = title.lower()
    text_sample = text[:500].lower() if text else ''

    for pattern in NEWSLETTER_PATTERNS:
        if re.search(pattern, title_lower, re.IGNORECASE):
            return True
        # Check text only for strong patterns
        if pattern in [r'\[AN #\d+\]', 'alignment newsletter']:
            if re.search(pattern, text_sample, re.IGNORECASE):
                return True

    return False


def score_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a single alignment research record.

    Args:
        record: Alignment research record from StampyAI

    Returns:
        Scoring result with source_id, score, tier, and signals
    """
    score = 0.0
    signals = {}

    # Extract fields safely
    source = record.get('source', '')
    title = record.get('title', '')
    text = record.get('text', '')
    authors = record.get('authors', [])
    tags = record.get('tags', [])
    date_published = record.get('date_published', '')
    record_id = record.get('id', '')

    # Source signals (arxiv and distill are high-quality venues)
    signals['source'] = source
    if source == 'arxiv':
        score += SCORING_CONFIG['source_arxiv']
    elif source == 'distill':
        score += SCORING_CONFIG['source_distill']

    # Author signals
    has_authors = len(authors) > 0 if isinstance(authors, list) else bool(authors)
    signals['has_authors'] = has_authors
    if has_authors:
        score += SCORING_CONFIG['has_authors']

    # Newsletter detection
    is_nl = is_newsletter(title, text)
    signals['is_newsletter'] = is_nl
    if not is_nl:
        score += SCORING_CONFIG['not_newsletter']

    # Text length signals
    text_length = len(text) if text else 0
    signals['text_length'] = text_length
    if text_length > 5000:
        score += SCORING_CONFIG['text_length_5k']
    if text_length > 10000:
        score += SCORING_CONFIG['text_length_10k']

    # Year signal (historical content is rarer and more valuable)
    year = ''
    if date_published:
        try:
            year = date_published[:4]
            if year.isdigit() and int(year) <= 2019:
                score += SCORING_CONFIG['year_pre_2020']
        except (IndexError, ValueError):
            pass
    signals['year'] = year

    # Tags signal
    has_tags = len(tags) > 0 if isinstance(tags, list) else bool(tags)
    signals['has_tags'] = has_tags
    if has_tags:
        score += SCORING_CONFIG['has_tags']

    # Determine tier
    if score >= TIER_THRESHOLDS['A']:
        tier = 'A'
    elif score >= TIER_THRESHOLDS['B']:
        tier = 'B'
    elif score >= TIER_THRESHOLDS['C']:
        tier = 'C'
    else:
        tier = 'D'

    return {
        'source_id': record_id,
        'quality_score': round(score, 1),
        'quality_tier': tier,
        'signals': signals,
        'title_preview': title[:80] if title else ''
    }


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load records from a JSONL file."""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error on line {line_num}: {e}")
    return records


def run_scoring(input_path: Path, output_path: Path, source_dump: str = None):
    """
    Run quality scoring on all records and save results.

    Args:
        input_path: Path to input JSONL file
        output_path: Path to output JSON file
        source_dump: Optional source dump identifier
    """
    logger.info("=" * 80)
    logger.info("STARTING QUALITY SCORING")
    logger.info("=" * 80)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    # Load records
    logger.info("\nLoading records...")
    records = load_jsonl(input_path)
    logger.info(f"Loaded {len(records)} records")

    # Score each record
    logger.info("\nScoring records...")
    scored_records = {}
    tier_counts = Counter()
    tier_ids = {'A': [], 'B': [], 'C': [], 'D': []}

    for i, record in enumerate(records):
        if (i + 1) % 1000 == 0:
            logger.info(f"  Scored {i + 1}/{len(records)} records...")

        result = score_record(record)
        source_id = result['source_id']
        tier = result['quality_tier']

        scored_records[source_id] = result
        tier_counts[tier] += 1
        tier_ids[tier].append(source_id)

    # Build output structure
    output = {
        '_metadata': {
            'version': '1.0.0',
            'created': datetime.utcnow().isoformat() + 'Z',
            'source_file': str(input_path.name),
            'source_dump': source_dump or str(input_path.parent.name),
            'total_records': len(records),
            'scoring_config': SCORING_CONFIG,
            'tier_thresholds': TIER_THRESHOLDS
        },
        'records': scored_records,
        'tier_summary': {
            tier: {
                'count': tier_counts[tier],
                'ids': tier_ids[tier]
            }
            for tier in ['A', 'B', 'C', 'D']
        }
    }

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=True)

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("SCORING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\nTotal records scored: {len(records)}")
    logger.info("\nTier Distribution:")
    for tier in ['A', 'B', 'C', 'D']:
        count = tier_counts[tier]
        pct = (count / len(records) * 100) if records else 0
        logger.info(f"  {tier}: {count:5d} ({pct:5.1f}%)")

    logger.info(f"\nOutput saved to: {output_path}")

    # Sample records from each tier for spot-checking
    logger.info("\n" + "-" * 80)
    logger.info("SAMPLE RECORDS BY TIER (for spot-checking)")
    logger.info("-" * 80)

    for tier in ['A', 'B', 'C', 'D']:
        ids = tier_ids[tier][:3]  # First 3 from each tier
        logger.info(f"\n{tier}-tier samples:")
        for source_id in ids:
            result = scored_records[source_id]
            title = result['title_preview']
            score = result['quality_score']
            signals = result['signals']
            logger.info(f"  [{score:4.1f}] {title[:60]}")
            logger.info(f"         src={signals['source']}, len={signals['text_length']}, "
                       f"authors={signals['has_authors']}, newsletter={signals['is_newsletter']}")

    return output


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Score alignment research records for quality tiering'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Input JSONL file with alignment research records'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output JSON file for quality scores'
    )
    parser.add_argument(
        '--source-dump',
        type=str,
        help='Source dump identifier (default: input directory name)'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    run_scoring(input_path, output_path, args.source_dump)


if __name__ == '__main__':
    main()
