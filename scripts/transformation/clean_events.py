#!/usr/bin/env python3
"""
Clean and export event log data for database import.

This script:
1. Loads all event files from data/events/
2. Validates against the event_v1.json schema
3. Cleans and standardizes the data
4. Exports to serveable zone in multiple formats
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import jsonschema

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.logger import get_logger

logger = get_logger('event_cleaning')


class EventCleaner:
    """Clean and validate event data."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.events_dir = self.root_dir / 'data' / 'raw' / 'events'
        self.schema_path = self.root_dir / 'config' / 'schemas' / 'event_v1.json'
        self.output_dir = self.root_dir / 'data' / 'serveable' / 'api' / 'timeline_events'

        # Load schema
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)

        logger.info(f"Initialized EventCleaner")
        logger.info(f"  Events dir: {self.events_dir}")
        logger.info(f"  Schema: {self.schema_path}")
        logger.info(f"  Output dir: {self.output_dir}")

    def load_all_events(self) -> Dict[str, Dict[str, Any]]:
        """Load all event files into a single dictionary."""
        all_events = {}
        event_files = sorted(self.events_dir.glob('*.json'))

        logger.info(f"Loading {len(event_files)} event files...")

        for event_file in event_files:
            logger.info(f"  Loading: {event_file.name}")

            with open(event_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Track source file in metadata
            for event_id, event in data.items():
                if event_id in all_events:
                    logger.debug(f"  Duplicate event ID found (expected for categorized files): {event_id}")
                    # Keep the most recent version (last file wins)
                    # This is OK because events are duplicated across category files

                event['_metadata'] = {
                    'source_file': event_file.name,
                    'category_file': event_file.stem
                }
                all_events[event_id] = event

        logger.info(f"Loaded {len(all_events)} total events")
        return all_events

    def validate_event(self, event_id: str, event: Dict[str, Any]) -> bool:
        """Validate a single event against the schema."""
        try:
            # Create a copy without metadata for validation
            event_copy = {k: v for k, v in event.items() if not k.startswith('_')}
            jsonschema.validate(instance=event_copy, schema=self.schema)
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"Validation failed for {event_id}: {e.message}")
            logger.error(f"  Path: {'.'.join(str(p) for p in e.path)}")
            return False

    def clean_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize a single event."""
        cleaned = event.copy()

        # Ensure sources are unique and sorted
        if 'sources' in cleaned:
            cleaned['sources'] = sorted(list(set(cleaned['sources'])))

        # Ensure tags are unique, sorted, and lowercase
        if 'tags' in cleaned:
            cleaned['tags'] = sorted(list(set(t.lower() for t in cleaned['tags'])))

        # Trim whitespace from strings
        for key in ['title', 'description', 'safety_researcher_reaction', 'media_reaction']:
            if key in cleaned and isinstance(cleaned[key], str):
                cleaned[key] = cleaned[key].strip()

        return cleaned

    def export_all_events(self, events: Dict[str, Dict[str, Any]]):
        """Export events in multiple formats for different use cases."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Remove metadata before export
        export_events = {}
        for event_id, event in events.items():
            export_event = {k: v for k, v in event.items() if not k.startswith('_')}
            export_events[event_id] = export_event

        # 1. Single consolidated file (for complete dataset)
        all_events_path = self.output_dir / 'all_events.json'
        logger.info(f"Exporting all events to: {all_events_path}")
        with open(all_events_path, 'w', encoding='utf-8') as f:
            json.dump(export_events, f, indent=2, ensure_ascii=True)

        # 2. Events by year (for temporal queries)
        events_by_year = {}
        for event_id, event in export_events.items():
            year = event['year']
            if year not in events_by_year:
                events_by_year[year] = {}
            events_by_year[year][event_id] = event

        by_year_dir = self.output_dir / 'by_year'
        by_year_dir.mkdir(exist_ok=True)

        for year, year_events in sorted(events_by_year.items()):
            year_path = by_year_dir / f'{year}.json'
            logger.info(f"  Exporting {len(year_events)} events for {year}")
            with open(year_path, 'w', encoding='utf-8') as f:
                json.dump(year_events, f, indent=2, ensure_ascii=True)

        # 3. Events by category (for game mechanics)
        events_by_category = {}
        for event_id, event in export_events.items():
            category = event['category']
            if category not in events_by_category:
                events_by_category[category] = {}
            events_by_category[category][event_id] = event

        by_category_dir = self.output_dir / 'by_category'
        by_category_dir.mkdir(exist_ok=True)

        for category, cat_events in sorted(events_by_category.items()):
            cat_path = by_category_dir / f'{category}.json'
            logger.info(f"  Exporting {len(cat_events)} events for {category}")
            with open(cat_path, 'w', encoding='utf-8') as f:
                json.dump(cat_events, f, indent=2, ensure_ascii=True)

        # 4. Event index (lightweight lookup)
        index = {}
        for event_id, event in export_events.items():
            index[event_id] = {
                'title': event['title'],
                'year': event['year'],
                'category': event['category'],
                'rarity': event['rarity']
            }

        index_path = self.output_dir / 'event_index.json'
        logger.info(f"Exporting event index to: {index_path}")
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=True)

        # 5. Manifest with metadata
        manifest = {
            'version': '1.0.0',
            'schema_version': self.schema['version'],
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'total_events': len(export_events),
            'years': sorted(list(events_by_year.keys())),
            'categories': sorted(list(events_by_category.keys())),
            'files': {
                'all_events': 'all_events.json',
                'by_year': 'by_year/{year}.json',
                'by_category': 'by_category/{category}.json',
                'index': 'event_index.json'
            }
        }

        manifest_path = self.output_dir / 'manifest.json'
        logger.info(f"Exporting manifest to: {manifest_path}")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=True)

    def generate_summary_stats(self, events: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for reporting."""
        from collections import Counter

        stats = {
            'total_events': len(events),
            'by_year': dict(Counter(e['year'] for e in events.values())),
            'by_category': dict(Counter(e['category'] for e in events.values())),
            'by_rarity': dict(Counter(e['rarity'] for e in events.values())),
            'impact_variables': dict(Counter(
                imp['variable']
                for e in events.values()
                for imp in e.get('impacts', [])
            )),
            'pdoom_impact_distribution': {
                'null': sum(1 for e in events.values() if e.get('pdoom_impact') is None),
                'negative': sum(1 for e in events.values() if e.get('pdoom_impact') is not None and e.get('pdoom_impact') < 0),
                'zero': sum(1 for e in events.values() if e.get('pdoom_impact') == 0),
                'positive': sum(1 for e in events.values() if e.get('pdoom_impact') is not None and e.get('pdoom_impact') > 0)
            }
        }

        return stats

    def run(self):
        """Main cleaning and export workflow."""
        logger.info("="*80)
        logger.info("STARTING EVENT CLEANING AND EXPORT")
        logger.info("="*80)

        # Load all events
        all_events = self.load_all_events()

        # Validate and clean
        logger.info("\nValidating and cleaning events...")
        cleaned_events = {}
        failed_events = []

        for event_id, event in all_events.items():
            if self.validate_event(event_id, event):
                cleaned = self.clean_event(event)
                # Validate cleaned version
                if self.validate_event(event_id, cleaned):
                    cleaned_events[event_id] = cleaned
                else:
                    failed_events.append(event_id)
                    logger.error(f"Cleaned event failed validation: {event_id}")
            else:
                failed_events.append(event_id)

        logger.info(f"\nValidation results:")
        logger.info(f"  Passed: {len(cleaned_events)}/{len(all_events)}")
        logger.info(f"  Failed: {len(failed_events)}/{len(all_events)}")

        if failed_events:
            logger.error(f"\nFailed events:")
            for event_id in failed_events:
                logger.error(f"  - {event_id}")
            return False

        # Generate stats
        logger.info("\nGenerating statistics...")
        stats = self.generate_summary_stats(cleaned_events)

        logger.info(f"\nEvent Statistics:")
        logger.info(f"  Total events: {stats['total_events']}")
        logger.info(f"  Years: {min(stats['by_year'].keys())} - {max(stats['by_year'].keys())}")
        logger.info(f"  Categories: {len(stats['by_category'])}")
        logger.info(f"  Rarities: {stats['by_rarity']}")

        # Export
        logger.info("\nExporting cleaned events...")
        self.export_all_events(cleaned_events)

        # Save stats
        stats_path = self.output_dir / 'stats.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=True)
        logger.info(f"Saved statistics to: {stats_path}")

        logger.info("\n" + "="*80)
        logger.info("EVENT CLEANING COMPLETE")
        logger.info("="*80)
        logger.info(f"Output directory: {self.output_dir}")

        return True


if __name__ == '__main__':
    cleaner = EventCleaner()
    success = cleaner.run()
    sys.exit(0 if success else 1)
