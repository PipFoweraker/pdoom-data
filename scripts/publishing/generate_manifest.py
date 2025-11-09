#!/usr/bin/env python3
"""
Generate unified manifest for serveable zone.

This script creates a comprehensive manifest that describes all data
available in the serveable zone for consumption by applications.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.logger import get_logger

logger = get_logger('manifest_generation')


class ManifestGenerator:
    """Generate serveable zone manifest."""

    def __init__(self, serveable_dir: Path):
        """
        Initialize manifest generator.

        Args:
            serveable_dir: Root serveable directory
        """
        self.serveable_dir = Path(serveable_dir)
        self.api_dir = self.serveable_dir / 'api'
        self.analytics_dir = self.serveable_dir / 'analytics'

        logger.info(f"Initialized ManifestGenerator")
        logger.info(f"  Serveable dir: {self.serveable_dir}")

    def scan_timeline_events(self) -> Dict[str, Any]:
        """Scan timeline events directory."""
        timeline_dir = self.api_dir / 'timeline_events'

        if not timeline_dir.exists():
            return {}

        # Scan for datasets
        datasets = {}

        # Manual curated events
        if (timeline_dir / 'all_events.json').exists():
            with open(timeline_dir / 'all_events.json', 'r') as f:
                manual_events = json.load(f)

            datasets['manual_events'] = {
                'name': 'Manual Curated Events',
                'description': 'Hand-curated game timeline events',
                'source': 'data/raw/events/',
                'schema': 'config/schemas/event_v1.json',
                'count': len(manual_events),
                'files': {
                    'all': 'all_events.json',
                    'by_year': 'by_year/{year}.json',
                    'by_category': 'by_category/{category}.json',
                    'index': 'event_index.json',
                    'manifest': 'manifest.json',
                    'stats': 'stats.json'
                },
                'years': self._get_years_from_dir(timeline_dir / 'by_year'),
                'format': 'json'
            }

        # Alignment research events
        alignment_dir = timeline_dir / 'alignment_research'
        if alignment_dir.exists() and (alignment_dir / 'alignment_research_events.json').exists():
            with open(alignment_dir / 'alignment_research_events.json', 'r') as f:
                research_events = json.load(f)

            datasets['alignment_research_events'] = {
                'name': 'Alignment Research Events',
                'description': 'Timeline events generated from alignment research dataset',
                'source': 'data/transformed/enriched/alignment_research/',
                'schema': 'config/schemas/event_v1.json',
                'count': len(research_events),
                'files': {
                    'all': 'alignment_research/alignment_research_events.json',
                    'by_year': 'alignment_research/by_year/{year}.json'
                },
                'years': self._get_years_from_dir(alignment_dir / 'by_year'),
                'format': 'json'
            }

        return datasets

    def _get_years_from_dir(self, year_dir: Path) -> List[int]:
        """Get list of years from by_year directory."""
        if not year_dir.exists():
            return []

        years = []
        for file in year_dir.glob('*.json'):
            try:
                year = int(file.stem)
                years.append(year)
            except ValueError:
                continue

        return sorted(years)

    def generate_manifest(self) -> Dict[str, Any]:
        """Generate complete serveable zone manifest."""
        logger.info("Generating manifest...")

        # Scan timeline events
        timeline_datasets = self.scan_timeline_events()

        # Calculate totals
        total_events = sum(ds['count'] for ds in timeline_datasets.values())

        # Build manifest
        manifest = {
            'version': '1.0.0',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'description': 'PDoom Data Lake - Serveable Zone Manifest',
            'repository': 'https://github.com/PipFoweraker/pdoom-data',
            'license': 'MIT',

            'summary': {
                'total_datasets': len(timeline_datasets),
                'total_events': total_events,
                'data_types': ['timeline_events'],
                'formats': ['json']
            },

            'api': {
                'timeline_events': {
                    'path': 'api/timeline_events/',
                    'description': 'Game timeline events for pdoom1',
                    'datasets': timeline_datasets,
                    'schema': 'config/schemas/event_v1.json',
                    'documentation': 'docs/EVENT_SCHEMA.md'
                }
            },

            'analytics': {
                'description': 'Analytics-ready data (future)',
                'datasets': {}
            },

            'integration': {
                'pdoom1_website': {
                    'description': 'PostgreSQL database import',
                    'method': 'Import timeline events to events table',
                    'api_endpoint': 'GET /api/events',
                    'status': 'planned'
                },
                'pdoom_game': {
                    'description': 'Godot game integration',
                    'method': 'Fetch from pdoom1-website API',
                    'status': 'planned'
                },
                'pdoom_dashboard': {
                    'description': 'Analytics dashboard',
                    'method': 'Direct JSON load or API fetch',
                    'status': 'planned'
                }
            },

            'data_pipeline': {
                'stages': [
                    'Raw Zone (data/raw/) - Immutable source data',
                    'Validated Zone (data/transformed/validated/) - Schema-validated',
                    'Cleaned Zone (data/transformed/cleaned/) - Normalized, ASCII-converted',
                    'Enriched Zone (data/transformed/enriched/) - With derived fields',
                    'Serveable Zone (data/serveable/) - Production-ready, optimized'
                ],
                'automation': {
                    'validation': 'scripts/validation/validate_*.py',
                    'cleaning': 'scripts/transformation/clean.py',
                    'enrichment': 'scripts/transformation/enrich.py',
                    'event_transformation': 'scripts/transformation/transform_to_timeline_events.py',
                    'event_cleaning': 'scripts/transformation/clean_events.py'
                }
            },

            'quality_guarantees': [
                'Schema validated',
                'ASCII compliant',
                'Complete attribution',
                'Versioned',
                'Idempotent (safe to regenerate)'
            ],

            'related_documentation': [
                'docs/DATA_ZONES.md - Data lake architecture',
                'docs/EVENT_SCHEMA.md - Event schema details',
                'docs/DATA_PUBLISHING_STRATEGY.md - Public data strategy',
                'docs/LINEAGE.md - Data lineage tracking',
                'data/serveable/README.md - Serveable zone guide'
            ]
        }

        return manifest

    def save_manifest(self, manifest: Dict[str, Any]):
        """Save manifest to serveable directory."""
        manifest_path = self.serveable_dir / 'MANIFEST.json'

        logger.info(f"Saving manifest to {manifest_path}")

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=True)

        logger.info(f"Manifest saved successfully")

        # Print summary
        logger.info("\nManifest Summary:")
        logger.info(f"  Total datasets: {manifest['summary']['total_datasets']}")
        logger.info(f"  Total events: {manifest['summary']['total_events']}")
        logger.info(f"  Data types: {', '.join(manifest['summary']['data_types'])}")

        for dataset_name, dataset_info in manifest['api']['timeline_events']['datasets'].items():
            logger.info(f"\n  {dataset_name}:")
            logger.info(f"    Count: {dataset_info['count']}")
            logger.info(f"    Years: {dataset_info['years']}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate serveable zone manifest')
    parser.add_argument('--serveable-dir', type=str, default='data/serveable',
                        help='Serveable directory')

    args = parser.parse_args()

    generator = ManifestGenerator(serveable_dir=Path(args.serveable_dir))
    manifest = generator.generate_manifest()
    generator.save_manifest(manifest)


if __name__ == '__main__':
    main()
