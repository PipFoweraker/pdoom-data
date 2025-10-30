#!/usr/bin/env python3
"""
Create new timestamped dump directory for funding event extraction

This script creates a new timestamped directory for storing extracted
funding event data from a specific source.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# Valid funding sources
VALID_SOURCES = [
    'sff',
    'open_philanthropy',
    'ai2050',
    'macroscopic',
    'givewiki',
    'cooperative_ai',
    'catalyze_impact'
]

# Valid extraction methods
VALID_METHODS = ['web_scrape', 'manual', 'api']


def create_dump_directory(source, method, base_dir=None):
    """
    Create a new timestamped dump directory
    
    Args:
        source: Source identifier (e.g., 'sff')
        method: Extraction method ('web_scrape', 'manual', 'api')
        base_dir: Base directory path (defaults to project root)
    
    Returns:
        Path: Path to created dump directory
    """
    if base_dir is None:
        # Get project root (3 levels up from scripts/extraction/)
        base_dir = Path(__file__).parent.parent.parent
    else:
        base_dir = Path(base_dir)
    
    # Validate source
    if source not in VALID_SOURCES:
        raise ValueError(f"Invalid source: {source}. Must be one of: {', '.join(VALID_SOURCES)}")
    
    # Validate method
    if method not in VALID_METHODS:
        raise ValueError(f"Invalid method: {method}. Must be one of: {', '.join(VALID_METHODS)}")
    
    # Create timestamp in format YYYY-MM-DD_HHMMSS
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    
    # Construct dump directory path
    source_dir = base_dir / 'data' / 'raw' / 'funding_sources' / source
    dump_dir = source_dir / 'dumps' / timestamp
    
    # Create directory
    dump_dir.mkdir(parents=True, exist_ok=False)
    
    # Create metadata template
    metadata = {
        'extraction_date': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source_name': source,
        'source_url': '',  # To be filled in
        'extraction_method': method,
        'extractor_version': '1.0.0',
        'data_format': 'json',
        'record_count': 0,
        'extraction_notes': '',
        'fields_extracted': [],
        'extraction_status': 'pending'
    }
    
    metadata_file = dump_dir / '_metadata.json'
    with open(metadata_file, 'w', encoding='ascii') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=True)
    
    # Create placeholder data file
    data_file = dump_dir / 'data.json'
    with open(data_file, 'w', encoding='ascii') as f:
        json.dump([], f, indent=2, ensure_ascii=True)
    
    return dump_dir


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Create new timestamped dump directory for funding event extraction'
    )
    parser.add_argument(
        '--source',
        required=True,
        choices=VALID_SOURCES,
        help='Funding source identifier'
    )
    parser.add_argument(
        '--method',
        required=True,
        choices=VALID_METHODS,
        help='Extraction method'
    )
    parser.add_argument(
        '--base-dir',
        help='Base directory (defaults to project root)'
    )
    
    args = parser.parse_args()
    
    try:
        dump_dir = create_dump_directory(args.source, args.method, args.base_dir)
        
        print(f"Created dump directory: {dump_dir}")
        print()
        print("Files created:")
        print(f"  - {dump_dir / '_metadata.json'}")
        print(f"  - {dump_dir / 'data.json'}")
        print()
        print("Next steps:")
        print("  1. Extract data from source and save to data.json")
        print("  2. Update _metadata.json with extraction details")
        print("  3. Run validation:")
        print(f"     python scripts/extraction/validate_dump.py --source {args.source} --dump {dump_dir.name}")
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileExistsError:
        print("Error: Dump directory already exists (duplicate timestamp)", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
