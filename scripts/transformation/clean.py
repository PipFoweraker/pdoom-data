#!/usr/bin/env python3
"""
Generalized data cleaning pipeline for the transformed zone.

This script implements the cleaning layer of the data lake:
    data/raw/* → data/transformed/validated/* → data/transformed/cleaned/*

Operations:
- Deduplication (by ID, by content similarity)
- Normalization (dates, text, URLs)
- ASCII conversion (smart quotes, dashes, accents)
- Validation fixes (fill missing fields where possible)
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import Counter
import unicodedata

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.logger import get_logger

logger = get_logger('data_cleaning')


class DataCleaner:
    """Generalized data cleaning for transformed zone."""

    def __init__(self, source_dir: Path, output_dir: Path, data_type: str = "jsonl"):
        """
        Initialize data cleaner.

        Args:
            source_dir: Directory containing validated data
            output_dir: Directory for cleaned output
            data_type: Data format ('jsonl' or 'json')
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.data_type = data_type

        self.stats = {
            'total_records': 0,
            'duplicates_removed': 0,
            'fields_normalized': 0,
            'ascii_conversions': 0,
            'validation_fixes': 0
        }

        logger.info(f"Initialized DataCleaner")
        logger.info(f"  Source: {self.source_dir}")
        logger.info(f"  Output: {self.output_dir}")
        logger.info(f"  Format: {self.data_type}")

    def deduplicate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate records.

        Deduplication strategy:
        1. By ID (exact match)
        2. By content similarity (future enhancement)

        Args:
            records: List of records to deduplicate

        Returns:
            Deduplicated list of records
        """
        seen_ids: Set[str] = set()
        unique_records = []

        for record in records:
            record_id = record.get('id')

            if not record_id:
                logger.warning(f"Record missing ID, keeping anyway: {record.get('title', 'UNKNOWN')[:50]}")
                unique_records.append(record)
                continue

            if record_id in seen_ids:
                self.stats['duplicates_removed'] += 1
                logger.debug(f"Removing duplicate ID: {record_id}")
                continue

            seen_ids.add(record_id)
            unique_records.append(record)

        logger.info(f"Deduplication: {len(records)} -> {len(unique_records)} records ({self.stats['duplicates_removed']} duplicates removed)")
        return unique_records

    def normalize_date(self, date_str: str) -> str:
        """
        Normalize date to ISO 8601 format.

        Args:
            date_str: Date string in various formats

        Returns:
            ISO 8601 formatted date string
        """
        if not date_str:
            return date_str

        # Already ISO 8601? Return as-is
        if re.match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?$', date_str):
            return date_str

        # Try common formats
        common_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
        ]

        for fmt in common_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # If we can't parse it, return original
        logger.warning(f"Could not normalize date: {date_str}")
        return date_str

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL (remove tracking params, standardize format).

        Args:
            url: URL string

        Returns:
            Normalized URL
        """
        if not url:
            return url

        # Remove common tracking parameters
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']

        if '?' in url:
            base, params = url.split('?', 1)
            param_pairs = [p for p in params.split('&') if p.split('=')[0] not in tracking_params]

            if param_pairs:
                url = base + '?' + '&'.join(param_pairs)
            else:
                url = base

        return url.strip()

    def ascii_convert(self, text: str) -> str:
        """
        Convert non-ASCII characters to ASCII equivalents.

        Smart quotes → straight quotes
        Em/en dashes → hyphens
        Accented characters → base characters

        Args:
            text: Text potentially containing non-ASCII

        Returns:
            ASCII-compatible text
        """
        if not text or text.isascii():
            return text

        # Track if we made changes
        original = text

        # Smart quotes to straight quotes
        replacements = {
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...', # Ellipsis
            '\u00a0': ' ',  # Non-breaking space
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Decompose accented characters (é → e)
        # NFKD = Compatibility Decomposition
        text = unicodedata.normalize('NFKD', text)

        # Remove combining characters (accents)
        text = ''.join(c for c in text if not unicodedata.combining(c))

        # Fallback: replace remaining non-ASCII with '?'
        text = text.encode('ascii', errors='replace').decode('ascii')

        if text != original:
            self.stats['ascii_conversions'] += 1

        return text

    def normalize_text(self, text: str) -> str:
        """
        Normalize text fields.

        - Strip whitespace
        - Convert to ASCII
        - Normalize line endings

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return text

        # Strip leading/trailing whitespace
        text = text.strip()

        # Normalize line endings to \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Convert to ASCII
        text = self.ascii_convert(text)

        return text

    def clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean a single record.

        Args:
            record: Record to clean

        Returns:
            Cleaned record
        """
        cleaned = record.copy()

        # Normalize text fields
        text_fields = ['title', 'text', 'abstract', 'description']
        for field in text_fields:
            if field in cleaned and isinstance(cleaned[field], str):
                cleaned[field] = self.normalize_text(cleaned[field])
                if cleaned[field] != record.get(field):
                    self.stats['fields_normalized'] += 1

        # Normalize dates
        if 'date_published' in cleaned:
            original = cleaned['date_published']
            cleaned['date_published'] = self.normalize_date(original)
            if cleaned['date_published'] != original:
                self.stats['fields_normalized'] += 1

        # Normalize URLs
        if 'url' in cleaned:
            original = cleaned['url']
            cleaned['url'] = self.normalize_url(original)
            if cleaned['url'] != original:
                self.stats['fields_normalized'] += 1

        # Normalize sources array
        if 'sources' in cleaned and isinstance(cleaned['sources'], list):
            cleaned['sources'] = sorted(list(set(
                self.normalize_url(s) for s in cleaned['sources'] if s
            )))

        # Normalize tags array (lowercase, sorted, unique)
        if 'tags' in cleaned and isinstance(cleaned['tags'], list):
            cleaned['tags'] = sorted(list(set(
                t.lower().strip() for t in cleaned['tags'] if t
            )))

        # Normalize authors array (unique, sorted)
        if 'authors' in cleaned and isinstance(cleaned['authors'], list):
            cleaned['authors'] = sorted(list(set(
                a.strip() for a in cleaned['authors'] if a
            )))

        return cleaned

    def load_jsonl(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load records from JSONL file."""
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error on line {line_num}: {e}")
        return records

    def load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load records from JSON file (array or dict)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Convert dict to list of records
            return list(data.values())
        else:
            raise ValueError(f"Unexpected JSON structure in {file_path}")

    def save_jsonl(self, records: List[Dict[str, Any]], file_path: Path):
        """Save records to JSONL file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            for record in records:
                json.dump(record, f, ensure_ascii=True)
                f.write('\n')

    def save_json(self, records: List[Dict[str, Any]], file_path: Path):
        """Save records to JSON file (array)."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=True)

    def clean_directory(self):
        """Clean all files in source directory."""
        logger.info("="*80)
        logger.info("STARTING DATA CLEANING")
        logger.info("="*80)

        # Find all data files
        if self.data_type == 'jsonl':
            data_files = list(self.source_dir.glob('**/*.jsonl'))
        else:
            data_files = list(self.source_dir.glob('**/*.json'))
            # Exclude metadata files
            data_files = [f for f in data_files if not f.name.startswith('_')]

        logger.info(f"\nFound {len(data_files)} files to clean")

        for data_file in data_files:
            logger.info(f"\nProcessing: {data_file.relative_to(self.source_dir)}")

            # Load records
            if self.data_type == 'jsonl':
                records = self.load_jsonl(data_file)
            else:
                records = self.load_json(data_file)

            logger.info(f"  Loaded {len(records)} records")
            self.stats['total_records'] += len(records)

            # Deduplicate
            records = self.deduplicate(records)

            # Clean each record
            cleaned_records = []
            for record in records:
                cleaned = self.clean_record(record)
                cleaned_records.append(cleaned)

            # Save cleaned records
            relative_path = data_file.relative_to(self.source_dir)
            output_path = self.output_dir / relative_path

            if self.data_type == 'jsonl':
                self.save_jsonl(cleaned_records, output_path)
            else:
                self.save_json(cleaned_records, output_path)

            logger.info(f"  Saved {len(cleaned_records)} cleaned records to {output_path}")

        # Print summary
        logger.info("\n" + "="*80)
        logger.info("CLEANING COMPLETE")
        logger.info("="*80)
        logger.info(f"\nStatistics:")
        logger.info(f"  Total records processed: {self.stats['total_records']}")
        logger.info(f"  Duplicates removed: {self.stats['duplicates_removed']}")
        logger.info(f"  Fields normalized: {self.stats['fields_normalized']}")
        logger.info(f"  ASCII conversions: {self.stats['ascii_conversions']}")
        logger.info(f"  Validation fixes: {self.stats['validation_fixes']}")
        logger.info(f"\nOutput directory: {self.output_dir}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Clean validated data')
    parser.add_argument('--source', type=str, required=True, help='Source directory (validated data)')
    parser.add_argument('--output', type=str, required=True, help='Output directory (cleaned data)')
    parser.add_argument('--format', type=str, default='jsonl', choices=['jsonl', 'json'], help='Data format')

    args = parser.parse_args()

    cleaner = DataCleaner(
        source_dir=Path(args.source),
        output_dir=Path(args.output),
        data_type=args.format
    )

    cleaner.clean_directory()


if __name__ == '__main__':
    main()
