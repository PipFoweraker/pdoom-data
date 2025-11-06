#!/usr/bin/env python3
"""
Validate Alignment Research Dataset dumps against schema

This script validates extracted alignment research data files for:
- Schema compliance
- Required field presence
- Data type validation
- ASCII compliance (for pdoom-data standards)
- Duplicate detection
"""

import argparse
import json
import jsonschema
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.utils.logger import get_logger
except ImportError:
    def get_logger(name, log_dir=None):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger


class AlignmentResearchValidator:
    """Validator for alignment research dataset dumps"""

    def __init__(self, schema_path: Path, check_ascii: bool = True):
        """
        Initialize validator

        Args:
            schema_path: Path to JSON schema file
            check_ascii: If True, check ASCII compliance
        """
        self.schema_path = schema_path
        self.check_ascii = check_ascii
        self.logger = get_logger('alignment_validation', log_dir='logs/alignment_validation')

        # Load schema
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)

        self.logger.info("Loaded schema", path=str(schema_path))

        # Statistics
        self.stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'schema_errors': 0,
            'ascii_errors': 0,
            'duplicate_ids': 0,
            'missing_required_fields': 0
        }

        # Track seen IDs for duplicate detection
        self.seen_ids: Set[str] = set()

        # Track errors by type
        self.errors_by_type: Dict[str, List[Dict]] = defaultdict(list)

    def _check_ascii_compliance(self, record: Dict, record_num: int) -> List[str]:
        """
        Check if record contains only ASCII characters

        Returns:
            List of error messages (empty if compliant)
        """
        errors = []

        def check_string(value: str, field_name: str) -> None:
            """Check if string is ASCII"""
            try:
                value.encode('ascii')
            except UnicodeEncodeError as e:
                errors.append(
                    f"Non-ASCII character in field '{field_name}': {str(e)}"
                )

        def check_value(value, field_name: str, path: str = '') -> None:
            """Recursively check value for ASCII compliance"""
            current_path = f"{path}.{field_name}" if path else field_name

            if isinstance(value, str):
                check_string(value, current_path)
            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, k, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    check_value(item, f"{current_path}[{i}]", '')

        # Check all fields
        for field, value in record.items():
            if value is not None:
                check_value(value, field)

        return errors

    def _validate_record(self, record: Dict, record_num: int) -> Tuple[bool, List[str]]:
        """
        Validate a single record

        Args:
            record: Record to validate
            record_num: Record number (for error reporting)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Schema validation
        try:
            jsonschema.validate(instance=record, schema=self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            self.stats['schema_errors'] += 1

        # Check required fields
        required_fields = self.schema.get('required', [])
        for field in required_fields:
            if field not in record or record[field] is None or record[field] == '':
                errors.append(f"Missing required field: {field}")
                self.stats['missing_required_fields'] += 1

        # Check for duplicate IDs
        record_id = record.get('id')
        if record_id:
            if record_id in self.seen_ids:
                errors.append(f"Duplicate ID: {record_id}")
                self.stats['duplicate_ids'] += 1
            else:
                self.seen_ids.add(record_id)

        # ASCII compliance check
        if self.check_ascii:
            ascii_errors = self._check_ascii_compliance(record, record_num)
            if ascii_errors:
                errors.extend(ascii_errors)
                self.stats['ascii_errors'] += 1

        # Additional validation rules
        # Check date format
        date_published = record.get('date_published', '')
        if date_published:
            # Should be ISO 8601 format
            if not (len(date_published) >= 10 and date_published[4] == '-' and date_published[7] == '-'):
                errors.append(f"Invalid date format: {date_published}")

        # Check URL format
        url = record.get('url', '')
        if url and not (url.startswith('http://') or url.startswith('https://')):
            errors.append(f"Invalid URL format: {url}")

        # Check source is valid
        source = record.get('source', '')
        valid_sources = self.schema.get('properties', {}).get('source', {}).get('enum', [])
        if source and valid_sources and source not in valid_sources:
            errors.append(f"Invalid source: {source}")

        return len(errors) == 0, errors

    def validate_file(self, data_file: Path) -> bool:
        """
        Validate a JSONL data file

        Args:
            data_file: Path to data.jsonl file

        Returns:
            True if all records are valid, False otherwise
        """
        self.logger.info("Validating file", path=str(data_file))

        if not data_file.exists():
            self.logger.error("File not found", path=str(data_file))
            return False

        # Reset statistics
        self.stats = {k: 0 for k in self.stats}
        self.seen_ids = set()
        self.errors_by_type = defaultdict(list)

        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    self.stats['total_records'] += 1

                    # Parse JSON
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as e:
                        self.logger.error(
                            "JSON parse error",
                            line_num=line_num,
                            error=str(e)
                        )
                        self.stats['invalid_records'] += 1
                        self.errors_by_type['json_parse'].append({
                            'line_num': line_num,
                            'error': str(e)
                        })
                        continue

                    # Validate record
                    is_valid, errors = self._validate_record(record, line_num)

                    if is_valid:
                        self.stats['valid_records'] += 1
                    else:
                        self.stats['invalid_records'] += 1

                        # Log errors
                        for error in errors:
                            self.logger.warning(
                                "Validation error",
                                line_num=line_num,
                                record_id=record.get('id', 'unknown'),
                                error=error
                            )

                        # Store errors
                        self.errors_by_type['validation'].append({
                            'line_num': line_num,
                            'record_id': record.get('id', 'unknown'),
                            'errors': errors
                        })

                    # Progress reporting
                    if self.stats['total_records'] % 1000 == 0:
                        self.logger.info(
                            "Validation progress",
                            total=self.stats['total_records'],
                            valid=self.stats['valid_records'],
                            invalid=self.stats['invalid_records']
                        )

            # Log summary
            self.logger.info("Validation complete", **self.stats)

            # All records must be valid
            return self.stats['invalid_records'] == 0

        except Exception as e:
            self.logger.error("Validation failed", error=str(e))
            return False

    def validate_dump(self, dump_dir: Path) -> bool:
        """
        Validate a complete dump directory

        Args:
            dump_dir: Path to dump directory

        Returns:
            True if dump is valid, False otherwise
        """
        self.logger.info("Validating dump", path=str(dump_dir))

        if not dump_dir.exists():
            self.logger.error("Dump directory not found", path=str(dump_dir))
            return False

        # Check required files
        data_file = dump_dir / 'data.jsonl'
        metadata_file = dump_dir / '_metadata.json'

        if not data_file.exists():
            self.logger.error("data.jsonl not found", path=str(data_file))
            return False

        if not metadata_file.exists():
            self.logger.error("_metadata.json not found", path=str(metadata_file))
            return False

        # Validate metadata
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Check required metadata fields
            required_metadata_fields = [
                'extraction_date', 'source_name', 'source_url',
                'extraction_method', 'data_format', 'record_count'
            ]

            for field in required_metadata_fields:
                if field not in metadata:
                    self.logger.error("Missing metadata field", field=field)
                    return False

            self.logger.info("Metadata valid", record_count=metadata.get('record_count'))

        except Exception as e:
            self.logger.error("Failed to validate metadata", error=str(e))
            return False

        # Validate data file
        data_valid = self.validate_file(data_file)

        # Check record count matches
        if metadata.get('record_count') != self.stats['total_records']:
            self.logger.warning(
                "Record count mismatch",
                metadata_count=metadata.get('record_count'),
                actual_count=self.stats['total_records']
            )

        return data_valid

    def get_report(self) -> str:
        """Generate validation report"""
        report = [
            "="*60,
            "VALIDATION REPORT",
            "="*60,
            f"Total records: {self.stats['total_records']}",
            f"Valid records: {self.stats['valid_records']}",
            f"Invalid records: {self.stats['invalid_records']}",
            "",
            "Errors by type:",
            f"  Schema errors: {self.stats['schema_errors']}",
            f"  ASCII errors: {self.stats['ascii_errors']}",
            f"  Duplicate IDs: {self.stats['duplicate_ids']}",
            f"  Missing required fields: {self.stats['missing_required_fields']}",
            "",
            f"Validation {'PASSED' if self.stats['invalid_records'] == 0 else 'FAILED'}",
            "="*60
        ]

        return '\n'.join(report)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Validate alignment research dataset dumps',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'dump_dir',
        type=Path,
        help='Path to dump directory to validate'
    )
    parser.add_argument(
        '--schema',
        type=Path,
        help='Path to schema file (default: config/schemas/alignment_research_v1.json)'
    )
    parser.add_argument(
        '--no-ascii-check',
        action='store_true',
        help='Skip ASCII compliance check'
    )
    parser.add_argument(
        '--data-file-only',
        action='store_true',
        help='Validate only data.jsonl file (skip metadata checks)'
    )

    args = parser.parse_args()

    # Determine schema path
    if args.schema:
        schema_path = args.schema
    else:
        project_root = Path(__file__).parent.parent.parent
        schema_path = project_root / 'config' / 'schemas' / 'alignment_research_v1.json'

    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}", file=sys.stderr)
        return 1

    # Create validator
    validator = AlignmentResearchValidator(
        schema_path=schema_path,
        check_ascii=not args.no_ascii_check
    )

    # Run validation
    if args.data_file_only:
        data_file = args.dump_dir / 'data.jsonl' if args.dump_dir.is_dir() else args.dump_dir
        success = validator.validate_file(data_file)
    else:
        success = validator.validate_dump(args.dump_dir)

    # Print report
    print("\n" + validator.get_report())

    # Return exit code
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
