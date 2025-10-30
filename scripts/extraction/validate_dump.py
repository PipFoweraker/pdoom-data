#!/usr/bin/env python3
"""
Validate funding event dump directory

This script validates the structure and content of a funding event
data dump directory.
"""

import argparse
import json
import sys
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

# Required metadata fields
REQUIRED_METADATA_FIELDS = [
    'extraction_date',
    'source_name',
    'source_url',
    'extraction_method',
    'data_format',
    'extraction_status'
]

# Valid extraction methods
VALID_METHODS = ['web_scrape', 'manual', 'api']

# Valid extraction statuses
VALID_STATUSES = ['complete', 'partial', 'failed', 'pending']


class ValidationResult:
    """Holds validation results"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def add_error(self, message):
        self.errors.append(message)
    
    def add_warning(self, message):
        self.warnings.append(message)
    
    def add_info(self, message):
        self.info.append(message)
    
    def is_valid(self):
        return len(self.errors) == 0
    
    def print_results(self):
        """Print validation results"""
        if self.info:
            print("\nInformation:")
            for msg in self.info:
                print(f"  [INFO] {msg}")
        
        if self.warnings:
            print("\nWarnings:")
            for msg in self.warnings:
                print(f"  [WARN] {msg}")
        
        if self.errors:
            print("\nErrors:")
            for msg in self.errors:
                print(f"  [ERROR] {msg}")
        
        print()
        if self.is_valid():
            print("Validation: PASSED")
        else:
            print("Validation: FAILED")


def validate_dump(source, dump_name, base_dir=None):
    """
    Validate a dump directory
    
    Args:
        source: Source identifier (e.g., 'sff')
        dump_name: Name of dump directory (timestamp)
        base_dir: Base directory path (defaults to project root)
    
    Returns:
        ValidationResult: Validation results
    """
    result = ValidationResult()
    
    if base_dir is None:
        # Get project root (3 levels up from scripts/extraction/)
        base_dir = Path(__file__).parent.parent.parent
    else:
        base_dir = Path(base_dir)
    
    # Validate source
    if source not in VALID_SOURCES:
        result.add_error(f"Invalid source: {source}")
        return result
    
    # Construct dump directory path
    dump_dir = base_dir / 'data' / 'raw' / 'funding_sources' / source / 'dumps' / dump_name
    
    # Check if directory exists
    if not dump_dir.exists():
        result.add_error(f"Dump directory does not exist: {dump_dir}")
        return result
    
    if not dump_dir.is_dir():
        result.add_error(f"Path is not a directory: {dump_dir}")
        return result
    
    result.add_info(f"Validating: {dump_dir}")
    
    # Initialize metadata variable
    metadata = None
    
    # Check for metadata file
    metadata_file = dump_dir / '_metadata.json'
    if not metadata_file.exists():
        result.add_error("Missing _metadata.json file")
    else:
        # Validate metadata
        try:
            with open(metadata_file, 'r', encoding='ascii') as f:
                metadata = json.load(f)
            
            # Check required fields
            for field in REQUIRED_METADATA_FIELDS:
                if field not in metadata:
                    result.add_error(f"Missing required metadata field: {field}")
                elif not metadata[field]:
                    result.add_warning(f"Empty metadata field: {field}")
            
            # Validate source_name matches
            if 'source_name' in metadata and metadata['source_name'] != source:
                result.add_error(f"Metadata source_name '{metadata['source_name']}' does not match directory source '{source}'")
            
            # Validate extraction_method
            if 'extraction_method' in metadata and metadata['extraction_method'] not in VALID_METHODS:
                result.add_error(f"Invalid extraction_method: {metadata['extraction_method']}")
            
            # Validate extraction_status
            if 'extraction_status' in metadata and metadata['extraction_status'] not in VALID_STATUSES:
                result.add_error(f"Invalid extraction_status: {metadata['extraction_status']}")
            
            # Check record count
            if 'record_count' in metadata:
                result.add_info(f"Record count: {metadata['record_count']}")
                if metadata['record_count'] == 0:
                    result.add_warning("Record count is 0")
            
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON in metadata file: {e}")
        except UnicodeDecodeError:
            result.add_error("Metadata file contains non-ASCII characters")
    
    # Check for data file
    data_file = dump_dir / 'data.json'
    if not data_file.exists():
        result.add_warning("No data.json file found")
    else:
        # Validate data file
        try:
            with open(data_file, 'r', encoding='ascii') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                result.add_info(f"Data file contains {len(data)} records")
                
                # Validate record count matches metadata (if metadata was loaded successfully)
                if metadata and 'record_count' in metadata and metadata['record_count'] != len(data):
                    result.add_warning(f"Record count mismatch: metadata says {metadata['record_count']}, data has {len(data)}")
            else:
                result.add_warning("Data file is not a JSON array")
                
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON in data file: {e}")
        except UnicodeDecodeError:
            result.add_error("Data file contains non-ASCII characters")
    
    return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Validate funding event dump directory'
    )
    parser.add_argument(
        '--source',
        required=True,
        choices=VALID_SOURCES,
        help='Funding source identifier'
    )
    parser.add_argument(
        '--dump',
        required=True,
        help='Dump directory name (timestamp)'
    )
    parser.add_argument(
        '--base-dir',
        help='Base directory (defaults to project root)'
    )
    
    args = parser.parse_args()
    
    print("Validating dump directory")
    print("=" * 60)
    
    result = validate_dump(args.source, args.dump, args.base_dir)
    result.print_results()
    
    print("=" * 60)
    
    return 0 if result.is_valid() else 1


if __name__ == '__main__':
    sys.exit(main())
