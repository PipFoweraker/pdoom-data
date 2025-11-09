#!/usr/bin/env python3
"""
Generalized data enrichment pipeline for the transformed zone.

This script implements the enrichment layer of the data lake:
    data/transformed/cleaned/* → data/transformed/enriched/*

Operations:
- Extract temporal fields (year, quarter, month, decade)
- Calculate content metrics (word_count, reading_time, etc.)
- Categorize content (topic, safety_relevance, technical_level)
- Extract relationships (references, citations)
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.logger import get_logger

logger = get_logger('data_enrichment')


class DataEnricher:
    """Generalized data enrichment for transformed zone."""

    def __init__(self, source_dir: Path, output_dir: Path, data_type: str = "jsonl"):
        """
        Initialize data enricher.

        Args:
            source_dir: Directory containing cleaned data
            output_dir: Directory for enriched output
            data_type: Data format ('jsonl' or 'json')
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.data_type = data_type

        self.stats = {
            'total_records': 0,
            'temporal_fields_added': 0,
            'content_metrics_added': 0,
            'categorizations_added': 0,
            'relationships_extracted': 0
        }

        logger.info(f"Initialized DataEnricher")
        logger.info(f"  Source: {self.source_dir}")
        logger.info(f"  Output: {self.output_dir}")
        logger.info(f"  Format: {self.data_type}")

    def extract_temporal_fields(self, date_str: str) -> Dict[str, Any]:
        """
        Extract temporal fields from date string.

        Args:
            date_str: ISO 8601 date string

        Returns:
            Dict with year, quarter, month, decade
        """
        if not date_str:
            return {}

        try:
            # Parse date (handle various ISO 8601 formats)
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')

            year = dt.year
            month = dt.month
            quarter = (month - 1) // 3 + 1  # 1-4
            decade = (year // 10) * 10  # 2020, 2010, etc.

            return {
                'year': year,
                'quarter': f"Q{quarter}",
                'month': month,
                'decade': f"{decade}s"
            }

        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse date for temporal extraction: {date_str}")
            return {}

    def calculate_content_metrics(self, text: str) -> Dict[str, Any]:
        """
        Calculate content metrics from text.

        Args:
            text: Document text

        Returns:
            Dict with word_count, reading_time_minutes, paragraph_count, has_code
        """
        if not text:
            return {
                'word_count': 0,
                'reading_time_minutes': 0,
                'paragraph_count': 0,
                'has_code': False
            }

        # Word count
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)

        # Reading time (average 200-250 words per minute, use 225)
        reading_time_minutes = max(1, round(word_count / 225))

        # Paragraph count (split on double newlines)
        paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
        paragraph_count = len(paragraphs)

        # Has code? (look for code blocks or common code patterns)
        has_code = bool(
            re.search(r'```|`[^`]+`|def \w+\(|class \w+[:(]|import \w+|function \w+\(', text)
        )

        return {
            'word_count': word_count,
            'reading_time_minutes': reading_time_minutes,
            'paragraph_count': paragraph_count,
            'has_code': has_code
        }

    def categorize_safety_relevance(self, text: str, title: str = "") -> str:
        """
        Categorize safety relevance (High/Medium/Low).

        Args:
            text: Document text
            title: Document title

        Returns:
            Safety relevance category
        """
        combined = (title + " " + text).lower()

        # High relevance keywords
        high_keywords = [
            'alignment', 'existential', 'x-risk', 'doom', 'superintelligence',
            'mesa-optimization', 'inner alignment', 'outer alignment',
            'reward hacking', 'deceptive alignment', 'treacherous turn'
        ]

        # Medium relevance keywords
        medium_keywords = [
            'safety', 'robustness', 'interpretability', 'transparency',
            'fairness', 'bias', 'explainability', 'verification'
        ]

        high_score = sum(1 for kw in high_keywords if kw in combined)
        medium_score = sum(1 for kw in medium_keywords if kw in combined)

        if high_score >= 2:
            return 'High'
        elif high_score >= 1 or medium_score >= 3:
            return 'Medium'
        else:
            return 'Low'

    def categorize_technical_level(self, text: str, source: str = "") -> str:
        """
        Categorize technical level (Research/Tutorial/Overview).

        Args:
            text: Document text
            source: Document source

        Returns:
            Technical level category
        """
        # ArXiv papers are usually research
        if source == 'arxiv':
            return 'Research'

        text_lower = text.lower()

        # Research indicators
        research_indicators = [
            'theorem', 'proof', 'lemma', 'corollary',
            'methodology', 'experimental setup', 'we propose',
            'our contribution', 'novel approach'
        ]

        # Tutorial indicators
        tutorial_indicators = [
            'introduction to', 'beginner', 'how to',
            'step by step', 'tutorial', 'getting started',
            'for example', 'let\'s', 'first, second, third'
        ]

        research_score = sum(1 for ind in research_indicators if ind in text_lower)
        tutorial_score = sum(1 for ind in tutorial_indicators if ind in text_lower)

        if research_score > tutorial_score and research_score >= 2:
            return 'Research'
        elif tutorial_score > research_score and tutorial_score >= 2:
            return 'Tutorial'
        else:
            return 'Overview'

    def extract_topics(self, text: str, tags: List[str] = None) -> List[str]:
        """
        Extract primary topics from text and tags.

        Args:
            text: Document text
            tags: Existing tags

        Returns:
            List of topics
        """
        topics = set()

        # If we have tags, use them
        if tags:
            topics.update(tags[:5])  # Take first 5 tags

        # Extract topics from text (simple keyword matching)
        topic_keywords = {
            'interpretability': ['interpretability', 'explainability', 'transparency'],
            'alignment': ['alignment', 'value learning', 'reward modeling'],
            'robustness': ['robustness', 'adversarial', 'distribution shift'],
            'governance': ['governance', 'policy', 'regulation', 'coordination'],
            'capabilities': ['capabilities', 'scaling', 'performance'],
            'rl': ['reinforcement learning', 'rl', 'reward'],
            'llm': ['language model', 'llm', 'gpt', 'transformer']
        }

        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.add(topic)

        return sorted(list(topics))[:10]  # Max 10 topics

    def enrich_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single record.

        Args:
            record: Record to enrich

        Returns:
            Enriched record
        """
        enriched = record.copy()

        # Add _enriched metadata
        if '_enriched' not in enriched:
            enriched['_enriched'] = {
                'enrichment_date': datetime.utcnow().isoformat() + 'Z',
                'enrichment_version': '1.0.0'
            }

        # Extract temporal fields
        if 'date_published' in record:
            temporal = self.extract_temporal_fields(record['date_published'])
            if temporal:
                enriched.update(temporal)
                self.stats['temporal_fields_added'] += len(temporal)

        # Calculate content metrics
        text = record.get('text', '')
        if text:
            metrics = self.calculate_content_metrics(text)
            enriched.update(metrics)
            self.stats['content_metrics_added'] += len(metrics)

        # Categorize safety relevance
        title = record.get('title', '')
        if text or title:
            enriched['safety_relevance'] = self.categorize_safety_relevance(text, title)
            self.stats['categorizations_added'] += 1

        # Categorize technical level
        source = record.get('source', '')
        if text:
            enriched['technical_level'] = self.categorize_technical_level(text, source)
            self.stats['categorizations_added'] += 1

        # Extract topics
        tags = record.get('tags', [])
        topics = self.extract_topics(text, tags)
        if topics:
            enriched['primary_topics'] = topics
            self.stats['categorizations_added'] += 1

        return enriched

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

    def enrich_directory(self):
        """Enrich all files in source directory."""
        logger.info("="*80)
        logger.info("STARTING DATA ENRICHMENT")
        logger.info("="*80)

        # Find all data files
        if self.data_type == 'jsonl':
            data_files = list(self.source_dir.glob('**/*.jsonl'))
        else:
            data_files = list(self.source_dir.glob('**/*.json'))
            # Exclude metadata files
            data_files = [f for f in data_files if not f.name.startswith('_')]

        logger.info(f"\nFound {len(data_files)} files to enrich")

        for data_file in data_files:
            logger.info(f"\nProcessing: {data_file.relative_to(self.source_dir)}")

            # Load records
            if self.data_type == 'jsonl':
                records = self.load_jsonl(data_file)
            else:
                records = self.load_json(data_file)

            logger.info(f"  Loaded {len(records)} records")
            self.stats['total_records'] += len(records)

            # Enrich each record
            enriched_records = []
            for record in records:
                enriched = self.enrich_record(record)
                enriched_records.append(enriched)

            # Save enriched records
            relative_path = data_file.relative_to(self.source_dir)
            output_path = self.output_dir / relative_path

            if self.data_type == 'jsonl':
                self.save_jsonl(enriched_records, output_path)
            else:
                self.save_json(enriched_records, output_path)

            logger.info(f"  Saved {len(enriched_records)} enriched records to {output_path}")

        # Print summary
        logger.info("\n" + "="*80)
        logger.info("ENRICHMENT COMPLETE")
        logger.info("="*80)
        logger.info(f"\nStatistics:")
        logger.info(f"  Total records processed: {self.stats['total_records']}")
        logger.info(f"  Temporal fields added: {self.stats['temporal_fields_added']}")
        logger.info(f"  Content metrics added: {self.stats['content_metrics_added']}")
        logger.info(f"  Categorizations added: {self.stats['categorizations_added']}")
        logger.info(f"  Relationships extracted: {self.stats['relationships_extracted']}")
        logger.info(f"\nOutput directory: {self.output_dir}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Enrich cleaned data')
    parser.add_argument('--source', type=str, required=True, help='Source directory (cleaned data)')
    parser.add_argument('--output', type=str, required=True, help='Output directory (enriched data)')
    parser.add_argument('--format', type=str, default='jsonl', choices=['jsonl', 'json'], help='Data format')

    args = parser.parse_args()

    enricher = DataEnricher(
        source_dir=Path(args.source),
        output_dir=Path(args.output),
        data_type=args.format
    )

    enricher.enrich_directory()


if __name__ == '__main__':
    main()
