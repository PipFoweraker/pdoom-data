#!/usr/bin/env python3
"""
Create dump spaces for funding event data from multiple sources

This script sets up the directory structure for collecting funding event
data from various sources through web crawling and manual extraction.
"""

import os
import sys
from pathlib import Path


# Funding sources configuration
FUNDING_SOURCES = [
    'sff',
    'open_philanthropy',
    'ai2050',
    'macroscopic',
    'givewiki',
    'cooperative_ai',
    'catalyze_impact'
]


def create_dump_spaces(base_dir=None):
    """
    Create directory structure for funding source dump spaces
    
    Args:
        base_dir: Base directory path (defaults to project root)
    
    Returns:
        dict: Statistics about created directories
    """
    if base_dir is None:
        # Get project root (3 levels up from scripts/setup/)
        base_dir = Path(__file__).parent.parent.parent
    else:
        base_dir = Path(base_dir)
    
    funding_sources_dir = base_dir / 'data' / 'raw' / 'funding_sources'
    
    stats = {
        'sources_created': 0,
        'directories_created': 0,
        'already_existed': 0
    }
    
    print(f"Creating dump spaces in: {funding_sources_dir}")
    print("=" * 60)
    
    # Create base directory if it doesn't exist
    funding_sources_dir.mkdir(parents=True, exist_ok=True)
    
    # Create each funding source directory structure
    for source in FUNDING_SOURCES:
        source_dir = funding_sources_dir / source
        dumps_dir = source_dir / 'dumps'
        manual_dir = source_dir / 'manual'
        
        print(f"\nSetting up: {source}")
        
        # Create directories
        for directory in [source_dir, dumps_dir, manual_dir]:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                stats['directories_created'] += 1
                print(f"  Created: {directory.relative_to(base_dir)}")
            else:
                stats['already_existed'] += 1
                print(f"  Exists:  {directory.relative_to(base_dir)}")
        
        # Create .gitkeep for empty directories
        for directory in [dumps_dir, manual_dir]:
            gitkeep = directory / '.gitkeep'
            if not gitkeep.exists():
                gitkeep.touch()
                print(f"  Created: {gitkeep.relative_to(base_dir)}")
        
        stats['sources_created'] += 1
    
    # Create _templates directory
    templates_dir = funding_sources_dir / '_templates'
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)
        stats['directories_created'] += 1
        print(f"\nCreated templates directory: {templates_dir.relative_to(base_dir)}")
    else:
        print(f"\nTemplates directory exists: {templates_dir.relative_to(base_dir)}")
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Sources configured: {stats['sources_created']}")
    print(f"  Directories created: {stats['directories_created']}")
    print(f"  Already existed: {stats['already_existed']}")
    print("=" * 60)
    
    return stats


def main():
    """Main entry point"""
    print("Funding Event Dump Space Setup")
    print("=" * 60)
    
    try:
        stats = create_dump_spaces()
        
        print("\nSetup complete!")
        print("\nNext steps:")
        print("  1. Review README.md files in each source directory")
        print("  2. Use scripts/extraction/new_dump.py to create new dumps")
        print("  3. Use scripts/extraction/validate_dump.py to validate dumps")
        
        return 0
        
    except Exception as e:
        print(f"\nError during setup: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
