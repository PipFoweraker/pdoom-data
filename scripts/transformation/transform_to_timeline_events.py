#!/usr/bin/env python3
"""
Transform alignment research data into game timeline events.

This script converts enriched alignment research records into the event schema
used by the pdoom game for its timeline event system.

Pipeline:
    data/transformed/enriched/alignment_research/*
        -> data/serveable/api/timeline_events/alignment_research/*
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.logger import get_logger

logger = get_logger('timeline_transformation')


class TimelineEventTransformer:
    """Transform alignment research records to timeline events."""

    def __init__(self, source_dir: Path, output_dir: Path):
        """
        Initialize transformer.

        Args:
            source_dir: Directory containing enriched alignment research
            output_dir: Directory for timeline events output
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)

        self.stats = {
            'total_records': 0,
            'events_created': 0,
            'skipped': 0,
            'by_category': Counter(),
            'by_rarity': Counter()
        }

        logger.info(f"Initialized TimelineEventTransformer")
        logger.info(f"  Source: {self.source_dir}")
        logger.info(f"  Output: {self.output_dir}")

    def generate_event_id(self, record: Dict[str, Any]) -> str:
        """
        Generate event ID from record.

        Must be snake_case, alphanumeric + underscores only.

        Args:
            record: Alignment research record

        Returns:
            Event ID string
        """
        # Use source + first part of hash
        source = record.get('source', 'unknown')
        record_id = record.get('id', '')[:16]  # First 16 chars of hash

        event_id = f"{source}_{record_id}"

        # Ensure snake_case and valid characters
        event_id = event_id.lower()
        event_id = re.sub(r'[^a-z0-9_]', '_', event_id)
        event_id = re.sub(r'_+', '_', event_id)  # Collapse multiple underscores
        event_id = event_id.strip('_')

        return event_id[:100]  # Max 100 chars

    def determine_category(self, record: Dict[str, Any]) -> str:
        """
        Determine event category from research record.

        Args:
            record: Alignment research record

        Returns:
            Event category
        """
        # Map based on source, topics, and content
        source = record.get('source', '')
        topics = record.get('primary_topics', [])
        title = record.get('title', '').lower()
        text = record.get('text', '')[:500].lower()  # First 500 chars

        # Check for research breakthroughs
        if source == 'arxiv' or 'research' in record.get('technical_level', '').lower():
            return 'technical_research_breakthrough'

        # Check for policy/governance
        if 'governance' in topics or 'policy' in title or 'regulation' in text:
            return 'policy_development'

        # Check for public awareness (blog posts, newsletters)
        if source in ['lesswrong', 'alignmentforum', 'eaforum']:
            return 'public_awareness'

        # Check for capability advances
        if 'capabilities' in topics or 'gpt' in title or 'claude' in title:
            return 'capability_advance'

        # Default to research breakthrough
        return 'technical_research_breakthrough'

    def determine_rarity(self, record: Dict[str, Any]) -> str:
        """
        Determine event rarity.

        Args:
            record: Alignment research record

        Returns:
            Rarity: common, rare, or legendary
        """
        safety_relevance = record.get('safety_relevance', 'Low')
        word_count = record.get('word_count', 0)
        source = record.get('source', '')

        # Legendary: High safety relevance + major publication + long form
        if safety_relevance == 'High' and source == 'arxiv' and word_count > 3000:
            return 'legendary'

        # Rare: High safety relevance OR major publication
        if safety_relevance == 'High' or source == 'arxiv':
            return 'rare'

        # Common: everything else
        return 'common'

    def calculate_impacts(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate game variable impacts from research record.

        Args:
            record: Alignment research record

        Returns:
            List of impact objects
        """
        impacts = []

        safety_relevance = record.get('safety_relevance', 'Low')
        technical_level = record.get('technical_level', 'Overview')
        word_count = record.get('word_count', 0)

        # Base research progress (all publications increase research)
        base_research = 5
        if technical_level == 'Research':
            base_research = 15
        elif technical_level == 'Tutorial':
            base_research = 10

        impacts.append({
            'variable': 'research',
            'change': base_research,
            'condition': None
        })

        # Papers count (if it's a paper)
        if record.get('source') == 'arxiv':
            impacts.append({
                'variable': 'papers',
                'change': 10,
                'condition': None
            })

        # Vibey doom (based on safety relevance)
        vibey_doom_map = {
            'High': 5,
            'Medium': 2,
            'Low': 0
        }
        vibey_change = vibey_doom_map.get(safety_relevance, 0)
        if vibey_change > 0:
            impacts.append({
                'variable': 'vibey_doom',
                'change': vibey_change,
                'condition': None
            })

        # Ethics risk (for alignment/safety topics)
        topics = record.get('primary_topics', [])
        if 'alignment' in topics or 'interpretability' in topics:
            impacts.append({
                'variable': 'ethics_risk',
                'change': -5,  # Negative = reducing risk
                'condition': None
            })

        return impacts

    def generate_description(self, record: Dict[str, Any]) -> str:
        """
        Generate event description from research record.

        Args:
            record: Alignment research record

        Returns:
            Description string (20-1000 chars)
        """
        # Try to use abstract if available
        description = record.get('abstract', '')

        # Fall back to first paragraph of text
        if not description:
            text = record.get('text', '')
            paragraphs = text.split('\n\n')
            description = paragraphs[0] if paragraphs else text[:500]

        # Clean up
        description = description.strip()

        # Truncate if too long
        if len(description) > 1000:
            description = description[:997] + '...'

        # Ensure minimum length
        if len(description) < 20:
            description = f"Research publication: {record.get('title', 'Unknown title')}"

        return description

    def generate_safety_researcher_reaction(self, record: Dict[str, Any]) -> str:
        """
        Generate safety researcher reaction quote.

        Args:
            record: Alignment research record

        Returns:
            Reaction string
        """
        safety_relevance = record.get('safety_relevance', 'Low')
        source = record.get('source', '')

        reactions = {
            'High': [
                "This is a significant contribution to alignment research",
                "Important work advancing our understanding of AI safety",
                "Critical insights for the field"
            ],
            'Medium': [
                "Useful research for the community",
                "Interesting perspective on safety challenges",
                "Adds to our knowledge base"
            ],
            'Low': [
                "Tangentially related to core safety concerns",
                "Provides general AI context",
                "Background research"
            ]
        }

        # Simple approach: pick based on safety relevance
        import random
        random.seed(record.get('id', ''))  # Deterministic based on ID
        return random.choice(reactions.get(safety_relevance, reactions['Low']))

    def generate_media_reaction(self, record: Dict[str, Any]) -> str:
        """
        Generate media reaction summary.

        Args:
            record: Alignment research record

        Returns:
            Media reaction string
        """
        source = record.get('source', '')
        year = record.get('year', 2020)

        # Map source to media coverage
        source_coverage = {
            'arxiv': "Published in academic venue",
            'alignmentforum': "Discussed in AI safety community",
            'lesswrong': "Shared in rationalist community",
            'eaforum': "Featured in effective altruism discussions",
            'deepmind': "Released by major AI lab",
            'openai': "Released by major AI lab",
            'anthropic': "Released by major AI lab"
        }

        return source_coverage.get(source, "Shared in AI safety research community")

    def transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single alignment research record to timeline event.

        Args:
            record: Enriched alignment research record

        Returns:
            Timeline event dict
        """
        # Generate event ID
        event_id = self.generate_event_id(record)

        # Determine category and rarity
        category = self.determine_category(record)
        rarity = self.determine_rarity(record)

        # Calculate impacts
        impacts = self.calculate_impacts(record)

        # Generate narrative elements
        description = self.generate_description(record)
        safety_reaction = self.generate_safety_researcher_reaction(record)
        media_reaction = self.generate_media_reaction(record)

        # Build event
        event = {
            'id': event_id,
            'title': record.get('title', 'Unknown')[:200],  # Max 200 chars
            'year': record.get('year', 2020),
            'category': category,
            'description': description,
            'impacts': impacts,
            'sources': [record.get('url')] if record.get('url') else [],
            'tags': record.get('tags', [])[:10],  # Max 10 tags
            'rarity': rarity,
            'pdoom_impact': None,  # Most research doesn't directly affect p(doom)
            'safety_researcher_reaction': safety_reaction,
            'media_reaction': media_reaction
        }

        # Track stats
        self.stats['by_category'][category] += 1
        self.stats['by_rarity'][rarity] += 1

        return event

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

    def save_json(self, events: List[Dict[str, Any]], file_path: Path):
        """Save events to JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=True)

    def transform_directory(self):
        """Transform all enriched research files to timeline events."""
        logger.info("="*80)
        logger.info("STARTING TIMELINE EVENT TRANSFORMATION")
        logger.info("="*80)

        # Find enriched data files
        data_files = list(self.source_dir.glob('**/*.jsonl'))
        # Exclude sample files for production
        data_files = [f for f in data_files if 'sample' not in f.name]

        logger.info(f"\nFound {len(data_files)} files to transform")

        all_events = []

        for data_file in data_files:
            logger.info(f"\nProcessing: {data_file.relative_to(self.source_dir)}")

            # Load records
            records = self.load_jsonl(data_file)
            logger.info(f"  Loaded {len(records)} records")
            self.stats['total_records'] += len(records)

            # Transform each record
            for record in records:
                try:
                    event = self.transform_record(record)
                    all_events.append(event)
                    self.stats['events_created'] += 1
                except Exception as e:
                    logger.error(f"Error transforming record {record.get('id')}: {e}")
                    self.stats['skipped'] += 1

        # Save all events
        output_file = self.output_dir / 'alignment_research_events.json'
        self.save_json(all_events, output_file)
        logger.info(f"\nSaved {len(all_events)} events to {output_file}")

        # Save by year
        events_by_year = {}
        for event in all_events:
            year = event['year']
            if year not in events_by_year:
                events_by_year[year] = []
            events_by_year[year].append(event)

        by_year_dir = self.output_dir / 'by_year'
        for year, year_events in sorted(events_by_year.items()):
            year_file = by_year_dir / f'{year}.json'
            self.save_json(year_events, year_file)
            logger.info(f"  Saved {len(year_events)} events for {year}")

        # Print summary
        logger.info("\n" + "="*80)
        logger.info("TRANSFORMATION COMPLETE")
        logger.info("="*80)
        logger.info(f"\nStatistics:")
        logger.info(f"  Total records processed: {self.stats['total_records']}")
        logger.info(f"  Events created: {self.stats['events_created']}")
        logger.info(f"  Skipped: {self.stats['skipped']}")
        logger.info(f"\nBy category:")
        for category, count in self.stats['by_category'].most_common():
            logger.info(f"  {category:40s} {count:4d}")
        logger.info(f"\nBy rarity:")
        for rarity, count in self.stats['by_rarity'].most_common():
            logger.info(f"  {rarity:15s} {count:4d}")
        logger.info(f"\nOutput directory: {self.output_dir}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Transform alignment research to timeline events')
    parser.add_argument('--source', type=str, required=True, help='Source directory (enriched data)')
    parser.add_argument('--output', type=str, required=True, help='Output directory (timeline events)')

    args = parser.parse_args()

    transformer = TimelineEventTransformer(
        source_dir=Path(args.source),
        output_dir=Path(args.output)
    )

    transformer.transform_directory()


if __name__ == '__main__':
    main()
