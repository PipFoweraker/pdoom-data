#!/usr/bin/env python3
"""
[SOURCE_NAME] Data Extraction Script

This script extracts data from [DATA_SOURCE_URL] and stores it in the
pdoom-data raw zone with comprehensive metadata and logging.

Features:
- [Streaming/Batch] data fetching
- Configurable filtering (date, [other criteria])
- Delta detection (incremental updates)
- Verbose structured logging
- Atomic file operations with checksum verification
- Dry-run mode for testing
- Progress reporting

Usage:
    # Test with dry run
    python extraction_script.py --mode full --limit 10 --dry-run

    # Extract full dataset
    python extraction_script.py --mode full

    # Extract delta (new records since last run)
    python extraction_script.py --mode delta

Author: [YOUR_NAME]
Date: [DATE]
License: MIT
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.utils.logger import get_logger
    from scripts.utils.file_ops import atomic_write, calculate_checksum
except ImportError:
    # Fallback if utils not available
    class FallbackLogger:
        """Minimal logger compatible with StructuredLogger API"""
        def __init__(self, name):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(handler)

        def info(self, message, **metadata):
            meta_str = ', '.join(f"{k}={v}" for k, v in metadata.items()) if metadata else ''
            self.logger.info(f"{message} {meta_str}" if meta_str else message)

        def error(self, message, **metadata):
            meta_str = ', '.join(f"{k}={v}" for k, v in metadata.items()) if metadata else ''
            self.logger.error(f"{message} {meta_str}" if meta_str else message)

        def warning(self, message, **metadata):
            meta_str = ', '.join(f"{k}={v}" for k, v in metadata.items()) if metadata else ''
            self.logger.warning(f"{message} {meta_str}" if meta_str else message)

    def get_logger(name, log_dir=None):
        return FallbackLogger(name)

    def atomic_write(content, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def calculate_checksum(file_path):
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"


class [SourceName]Extractor:
    """Extractor for [Source Name] data"""

    # TODO: Configure these for your data source
    DATA_SOURCE_NAME = '[source_name]'
    DATA_SOURCE_URL = '[https://data.source.url]'

    # Default filters
    DEFAULT_MIN_DATE = '2020-01-01'
    # TODO: Add other default filters as needed

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        mode: str = 'full',
        limit: Optional[int] = None,
        dry_run: bool = False,
        min_date: Optional[str] = None,
        # TODO: Add other filter parameters
    ):
        """
        Initialize extractor

        Args:
            output_dir: Output directory (auto-created if None)
            mode: 'full' or 'delta'
            limit: Maximum records to extract (None = unlimited)
            dry_run: If True, don't write files
            min_date: Minimum date filter (YYYY-MM-DD)
        """
        self.mode = mode
        self.limit = limit
        self.dry_run = dry_run
        self.min_date = min_date or self.DEFAULT_MIN_DATE

        # Setup logger
        self.logger = get_logger(
            f'{self.DATA_SOURCE_NAME}_extraction',
            log_dir=f'logs/{self.DATA_SOURCE_NAME}_extraction'
        )

        # Setup output directory
        if output_dir is None:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
            base_dir = Path(__file__).parent
            self.output_dir = base_dir / 'dumps' / timestamp
        else:
            self.output_dir = Path(output_dir)

        # Statistics tracking
        self.stats = {
            'records_fetched': 0,
            'records_filtered': 0,
            'records_written': 0,
            'errors_encountered': 0,
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0
        }

        # TODO: Add authentication if needed
        # self.api_token = os.environ.get('API_TOKEN')

    def _get_last_extraction_date(self) -> Optional[str]:
        """Get date of last successful extraction for delta mode"""
        dumps_dir = Path(__file__).parent / 'dumps'
        if not dumps_dir.exists():
            return None

        # Find most recent successful extraction
        for dump_dir in sorted(dumps_dir.iterdir(), reverse=True):
            if not dump_dir.is_dir():
                continue

            metadata_file = dump_dir / '_metadata.json'
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    if metadata.get('extraction_status') == 'complete':
                        last_date = metadata.get('extraction_date')
                        self.logger.info(
                            "Found last extraction",
                            date=last_date,
                            dump=dump_dir.name
                        )
                        return last_date
                except Exception as e:
                    self.logger.warning(
                        "Failed to read metadata",
                        file=str(metadata_file),
                        error=str(e)
                    )

        return None

    def _filter_record(self, record: Dict[str, Any]) -> bool:
        """
        Apply filtering criteria to a record

        Returns:
            True if record should be kept, False otherwise
        """
        try:
            # TODO: Implement your filtering logic

            # Example: Check date
            record_date = record.get('date', '')
            if not record_date:
                return False

            # For delta mode, only include records after last extraction
            if self.mode == 'delta':
                last_date = self._get_last_extraction_date()
                if last_date and record_date <= last_date:
                    return False

            # Check min date
            if record_date < self.min_date:
                return False

            # TODO: Add other filters as needed

            return True

        except Exception as e:
            self.logger.warning("Filter error", record_id=record.get('id'), error=str(e))
            return False

    def _transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform source record to pdoom-data schema

        Args:
            record: Raw record from data source

        Returns:
            Transformed record with provenance
        """
        # TODO: Map source fields to your schema
        transformed = {
            'id': record.get('id', ''),
            'title': record.get('title', ''),
            'url': record.get('url', ''),
            'date': record.get('date', ''),
            # Add other required fields
        }

        # Add optional fields if present
        optional_fields = []  # TODO: List your optional fields
        for field in optional_fields:
            if field in record and record[field] is not None:
                transformed[field] = record[field]

        # Add provenance
        transformed['_provenance'] = {
            'source_system': self.DATA_SOURCE_URL,
            'ingestion_date': datetime.now(timezone.utc).isoformat(),
            'license': '[LICENSE]',  # TODO: Set correct license
            'attribution': '[ATTRIBUTION]',  # TODO: Set attribution
            'extraction_method': '[api|web_scrape|manual]',  # TODO: Set method
            'transformations': ['schema_standardization', 'provenance_addition']
        }

        return transformed

    def _create_metadata(self) -> Dict[str, Any]:
        """Create metadata for extraction"""
        metadata = {
            'extraction_date': datetime.now(timezone.utc).isoformat(),
            'source_name': self.DATA_SOURCE_NAME,
            'source_url': self.DATA_SOURCE_URL,
            'extraction_method': '[api|web_scrape|manual]',  # TODO: Set method
            'extractor_version': '1.0.0',
            'data_format': 'jsonl',
            'record_count': self.stats['records_written'],
            'extraction_type': self.mode,
            'last_extraction_date': self._get_last_extraction_date() if self.mode == 'delta' else None,
            'filters_applied': {
                'date_range': f"{self.min_date} to present",
                # TODO: Add other filters
            },
            'extraction_status': 'complete',
            'attribution': '[ATTRIBUTION]',  # TODO: Set attribution
            'license': '[LICENSE]',  # TODO: Set license
            'extraction_statistics': self.stats,
            'data_quality': {
                'missing_required_fields': 0,
                'ascii_compliance_checked': False,
                'schema_validation_passed': False
            }
        }

        return metadata

    def _fetch_data(self):
        """
        Fetch data from source

        This method should yield records one at a time for streaming processing.

        TODO: Implement your data fetching logic here.

        Examples:
        - API: Paginate through API endpoints
        - Web scraping: Crawl pages and extract data
        - File download: Download and parse file
        """
        # Example API pagination:
        # page = 1
        # while True:
        #     response = requests.get(f"{API_URL}/data?page={page}")
        #     data = response.json()
        #     if not data['results']:
        #         break
        #     for record in data['results']:
        #         yield record
        #     page += 1

        # Example web scraping:
        # for url in page_urls:
        #     soup = BeautifulSoup(requests.get(url).content, 'html.parser')
        #     for item in soup.find_all('div', class_='item'):
        #         record = extract_record(item)
        #         yield record

        # Placeholder - replace with actual implementation
        raise NotImplementedError("Implement _fetch_data() method")

    def extract(self) -> bool:
        """
        Run extraction process

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(
            "Starting extraction",
            mode=self.mode,
            limit=self.limit,
            dry_run=self.dry_run,
            output_dir=str(self.output_dir)
        )

        self.stats['start_time'] = datetime.now(timezone.utc).isoformat()

        try:
            # Create output directory
            if not self.dry_run:
                self.output_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info("Created output directory", path=str(self.output_dir))

            # Open output file
            if not self.dry_run:
                output_file = self.output_dir / 'data.jsonl'
                f = open(output_file, 'w', encoding='utf-8')
                self.logger.info("Opened output file", path=str(output_file))
            else:
                f = None

            try:
                # Process records
                self.logger.info("Processing records")

                for record in self._fetch_data():
                    self.stats['records_fetched'] += 1

                    # Apply filters
                    if not self._filter_record(record):
                        self.stats['records_filtered'] += 1
                        continue

                    # Transform record
                    try:
                        transformed = self._transform_record(record)

                        # Write to file
                        if not self.dry_run:
                            f.write(json.dumps(transformed, ensure_ascii=False) + '\n')

                        self.stats['records_written'] += 1

                        # Progress reporting
                        if self.stats['records_written'] % 100 == 0:
                            self.logger.info(
                                "Progress update",
                                fetched=self.stats['records_fetched'],
                                written=self.stats['records_written'],
                                filtered=self.stats['records_filtered']
                            )

                        # Check limit
                        if self.limit and self.stats['records_written'] >= self.limit:
                            self.logger.info("Reached limit", limit=self.limit)
                            break

                    except Exception as e:
                        self.stats['errors_encountered'] += 1
                        self.logger.error(
                            "Failed to transform record",
                            record_id=record.get('id'),
                            error=str(e)
                        )

            finally:
                if f:
                    f.close()

            # Calculate duration
            self.stats['end_time'] = datetime.now(timezone.utc).isoformat()
            start_time = datetime.fromisoformat(self.stats['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(self.stats['end_time'].replace('Z', '+00:00'))
            self.stats['duration_seconds'] = (end_time - start_time).total_seconds()

            # Create metadata
            if not self.dry_run:
                metadata = self._create_metadata()
                metadata_file = self.output_dir / '_metadata.json'

                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)

                self.logger.info("Wrote metadata", path=str(metadata_file))

                # Calculate checksums
                data_checksum = calculate_checksum(output_file)
                metadata_checksum = calculate_checksum(metadata_file)

                self.logger.info(
                    "Checksums calculated",
                    data=data_checksum,
                    metadata=metadata_checksum
                )

            # Log summary
            self.logger.info(
                "Extraction complete",
                **self.stats
            )

            return True

        except Exception as e:
            self.logger.error("Extraction failed", error=str(e), error_type=type(e).__name__)
            self.stats['end_time'] = datetime.now(timezone.utc).isoformat()
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Extract data from [Source Name]',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with small sample (dry run)
  python extraction_script.py --mode full --limit 100 --dry-run

  # Extract first 1000 records
  python extraction_script.py --mode full --limit 1000

  # Full extraction
  python extraction_script.py --mode full

  # Delta update (only new records)
  python extraction_script.py --mode delta
        """
    )

    parser.add_argument(
        '--mode',
        choices=['full', 'delta'],
        default='full',
        help='Extraction mode: full (all records) or delta (only new records)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of records to extract (for testing)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without writing files (for testing)'
    )
    parser.add_argument(
        '--min-date',
        help='Minimum date (YYYY-MM-DD, default: 2020-01-01)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory (default: auto-generated timestamp)'
    )

    # TODO: Add other command-line arguments as needed

    args = parser.parse_args()

    # Create extractor
    extractor = [SourceName]Extractor(
        output_dir=args.output_dir,
        mode=args.mode,
        limit=args.limit,
        dry_run=args.dry_run,
        min_date=args.min_date,
    )

    # Run extraction
    success = extractor.extract()

    if success:
        print("\n" + "="*60)
        print("EXTRACTION SUCCESSFUL")
        print("="*60)
        print(f"Records written: {extractor.stats['records_written']}")
        print(f"Records filtered: {extractor.stats['records_filtered']}")
        print(f"Errors: {extractor.stats['errors_encountered']}")
        print(f"Duration: {extractor.stats['duration_seconds']:.1f} seconds")
        if not args.dry_run:
            print(f"Output: {extractor.output_dir}")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("EXTRACTION FAILED")
        print("="*60)
        print("Check logs for details")
        print("="*60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
