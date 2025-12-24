#!/usr/bin/env python3
"""
Transform Enriched Alignment Research to Timeline Events

This script transforms A-tier (and optionally B-tier) enriched alignment
research records into game timeline events.

Pipeline:
    1. Load quality scores from enrichment pass
    2. Filter to selected tiers (default: A only)
    3. Load source records matching the tier filter
    4. Transform to timeline event format
    5. Output to serveable zone
"""

import json
import sys
import re
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import Counter

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.logger import get_logger

logger = get_logger('enriched_transform')


class EnrichedTransformer:
    """Transform enriched alignment research to timeline events."""

    def __init__(
        self,
        scores_file: Path,
        source_file: Path,
        output_dir: Path,
        tiers: List[str] = None
    ):
        """
        Initialize transformer.

        Args:
            scores_file: Path to quality scores JSON
            source_file: Path to source JSONL data
            output_dir: Output directory for timeline events
            tiers: List of tiers to include (default: ['A'])
        """
        self.scores_file = Path(scores_file)
        self.source_file = Path(source_file)
        self.output_dir = Path(output_dir)
        self.tiers = tiers or ['A']

        self.stats = {
            'total_filtered': 0,
            'events_created': 0,
            'by_category': Counter(),
            'by_rarity': Counter(),
            'by_year': Counter()
        }

    def load_tier_ids(self) -> Set[str]:
        """Load IDs for selected tiers from quality scores."""
        logger.info(f"Loading quality scores from {self.scores_file}")
        with open(self.scores_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ids = set()
        for tier in self.tiers:
            tier_ids = data['tier_summary'].get(tier, {}).get('ids', [])
            ids.update(tier_ids)
            logger.info(f"  Tier {tier}: {len(tier_ids)} records")

        logger.info(f"  Total selected: {len(ids)} records")
        return ids

    def load_source_records(self, selected_ids: Set[str]) -> List[Dict[str, Any]]:
        """Load source records that match selected IDs."""
        logger.info(f"Loading source records from {self.source_file}")
        records = []
        with open(self.source_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record.get('id') in selected_ids:
                        records.append(record)
        logger.info(f"  Loaded {len(records)} matching records")
        return records

    def generate_event_id(self, record: Dict[str, Any]) -> str:
        """Generate event ID from record."""
        source = record.get('source', 'unknown')
        record_id = record.get('id', '')[:16]
        event_id = f"{source}_{record_id}"
        event_id = event_id.lower()
        event_id = re.sub(r'[^a-z0-9_]', '_', event_id)
        event_id = re.sub(r'_+', '_', event_id)
        event_id = event_id.strip('_')
        return event_id[:100]

    def determine_category(self, record: Dict[str, Any]) -> str:
        """Determine event category."""
        source = record.get('source', '')
        title = record.get('title', '').lower()
        text = record.get('text', '')[:500].lower()

        # Academic papers are technical research
        if source in ['arxiv', 'distill']:
            return 'technical_research_breakthrough'

        # Check for policy/governance
        if 'governance' in text or 'policy' in title or 'regulation' in text:
            return 'policy_development'

        # Check for capability advances
        if 'gpt' in title or 'claude' in title or 'language model' in title:
            return 'capability_advance'

        # Forum posts are public awareness
        if source in ['lesswrong', 'alignmentforum', 'eaforum']:
            return 'public_awareness'

        return 'technical_research_breakthrough'

    def determine_rarity(self, record: Dict[str, Any]) -> str:
        """Determine event rarity."""
        source = record.get('source', '')
        text_length = len(record.get('text', ''))

        # Distill articles are legendary (rare, high-quality)
        if source == 'distill':
            return 'legendary'

        # Long arxiv papers are rare
        if source == 'arxiv' and text_length > 20000:
            return 'rare'

        # Other arxiv papers are common but valuable
        if source == 'arxiv':
            return 'common'

        # Forum content rarity based on length
        if text_length > 10000:
            return 'rare'

        return 'common'

    def calculate_impacts(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate game variable impacts."""
        impacts = []
        source = record.get('source', '')
        text_length = len(record.get('text', ''))

        # Base research progress
        base_research = 15 if source in ['arxiv', 'distill'] else 10
        impacts.append({
            'variable': 'research',
            'change': base_research,
            'condition': None
        })

        # Papers count for academic papers
        if source in ['arxiv', 'distill']:
            impacts.append({
                'variable': 'papers',
                'change': 10,
                'condition': None
            })

        # Vibey doom based on source prestige
        if source == 'arxiv':
            impacts.append({
                'variable': 'vibey_doom',
                'change': 3,
                'condition': None
            })
        elif source == 'distill':
            impacts.append({
                'variable': 'vibey_doom',
                'change': 5,
                'condition': None
            })

        return impacts

    def generate_description(self, record: Dict[str, Any]) -> str:
        """Generate event description."""
        description = record.get('abstract', '')
        if not description:
            text = record.get('text', '')
            paragraphs = text.split('\n\n')
            description = paragraphs[0] if paragraphs else text[:500]

        description = description.strip()
        # Clean any non-ASCII for game compatibility
        description = description.encode('ascii', 'replace').decode('ascii')

        if len(description) > 1000:
            description = description[:997] + '...'
        if len(description) < 20:
            description = f"Research publication: {record.get('title', 'Unknown')}"

        return description

    def generate_reactions(self, record: Dict[str, Any]) -> tuple:
        """Generate safety researcher and media reactions."""
        source = record.get('source', '')
        random.seed(record.get('id', ''))

        safety_reactions = [
            "Important contribution to the field",
            "Advances our understanding of AI safety",
            "Valuable research for alignment",
            "Significant technical contribution",
            "Notable work on AI safety"
        ]

        if source == 'arxiv':
            media_reactions = [
                "Published in academic venue",
                "Academic research release",
                "Peer-reviewed publication"
            ]
        elif source == 'distill':
            media_reactions = [
                "Featured in Distill",
                "Interactive research publication",
                "Visual machine learning research"
            ]
        else:
            media_reactions = [
                "Shared in AI safety community",
                "Published online",
                "Community discussion"
            ]

        return (random.choice(safety_reactions), random.choice(media_reactions))

    def transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single record to timeline event."""
        event_id = self.generate_event_id(record)
        category = self.determine_category(record)
        rarity = self.determine_rarity(record)
        impacts = self.calculate_impacts(record)
        description = self.generate_description(record)
        safety_reaction, media_reaction = self.generate_reactions(record)

        # Extract year from date
        date_published = record.get('date_published', '')
        year = 2020
        if date_published:
            try:
                year = int(date_published[:4])
            except (ValueError, IndexError):
                pass

        # Clean title
        title = record.get('title', 'Unknown')[:200]
        title = title.encode('ascii', 'replace').decode('ascii')

        event = {
            'id': event_id,
            'title': title,
            'year': year,
            'category': category,
            'description': description,
            'impacts': impacts,
            'sources': [record.get('url')] if record.get('url') else [],
            'tags': record.get('tags', [])[:10],
            'rarity': rarity,
            'pdoom_impact': None,
            'safety_researcher_reaction': safety_reaction,
            'media_reaction': media_reaction,
            'source_id': record.get('id')  # Link back to source
        }

        self.stats['by_category'][category] += 1
        self.stats['by_rarity'][rarity] += 1
        self.stats['by_year'][year] += 1

        return event

    def run(self):
        """Run the transformation pipeline."""
        logger.info("=" * 80)
        logger.info("ENRICHED TIMELINE EVENT TRANSFORMATION")
        logger.info("=" * 80)
        logger.info(f"Tiers: {', '.join(self.tiers)}")

        # Load tier IDs
        selected_ids = self.load_tier_ids()
        self.stats['total_filtered'] = len(selected_ids)

        # Load matching source records
        records = self.load_source_records(selected_ids)

        # Transform records
        logger.info("\nTransforming records to timeline events...")
        events = []
        for record in records:
            try:
                event = self.transform_record(record)
                events.append(event)
                self.stats['events_created'] += 1
            except Exception as e:
                logger.error(f"Error transforming {record.get('id')}: {e}")

        # Save all events
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / 'enriched_alignment_research_events.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=True)
        logger.info(f"\nSaved {len(events)} events to {output_file}")

        # Save by year
        events_by_year = {}
        for event in events:
            year = event['year']
            if year not in events_by_year:
                events_by_year[year] = []
            events_by_year[year].append(event)

        by_year_dir = self.output_dir / 'by_year'
        by_year_dir.mkdir(parents=True, exist_ok=True)
        for year, year_events in sorted(events_by_year.items()):
            year_file = by_year_dir / f'{year}.json'
            with open(year_file, 'w', encoding='utf-8') as f:
                json.dump(year_events, f, indent=2, ensure_ascii=True)
            logger.info(f"  Year {year}: {len(year_events)} events")

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("TRANSFORMATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"\nTotal filtered: {self.stats['total_filtered']}")
        logger.info(f"Events created: {self.stats['events_created']}")

        logger.info("\nBy category:")
        for cat, count in self.stats['by_category'].most_common():
            logger.info(f"  {cat}: {count}")

        logger.info("\nBy rarity:")
        for rarity, count in self.stats['by_rarity'].most_common():
            logger.info(f"  {rarity}: {count}")

        logger.info("\nBy year:")
        for year in sorted(self.stats['by_year'].keys()):
            count = self.stats['by_year'][year]
            logger.info(f"  {year}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description='Transform enriched alignment research to timeline events'
    )
    parser.add_argument(
        '--scores', '-s',
        type=str,
        required=True,
        help='Quality scores JSON file'
    )
    parser.add_argument(
        '--source', '-i',
        type=str,
        required=True,
        help='Source JSONL file'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output directory'
    )
    parser.add_argument(
        '--tiers', '-t',
        type=str,
        default='A',
        help='Tiers to include (comma-separated, e.g. "A,B")'
    )

    args = parser.parse_args()
    tiers = [t.strip().upper() for t in args.tiers.split(',')]

    transformer = EnrichedTransformer(
        scores_file=Path(args.scores),
        source_file=Path(args.source),
        output_dir=Path(args.output),
        tiers=tiers
    )
    transformer.run()


if __name__ == '__main__':
    main()
