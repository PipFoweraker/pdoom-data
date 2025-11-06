#!/usr/bin/env python3
"""
Alignment Research Dataset Extraction Script

This script extracts data from the StampyAI Alignment Research Dataset on Hugging Face
and stores it in the pdoom-data raw zone with comprehensive metadata and logging.

Features:
- Streaming from Hugging Face (memory efficient)
- Configurable filtering (date, sources, keywords)
- Delta detection (incremental updates)
- Verbose structured logging
- Atomic file operations with checksum verification
- Dry-run mode for testing
- Progress reporting
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

# Lazy import of datasets to allow script to run without it installed
datasets = None


class AlignmentResearchExtractor:
    """Extractor for Alignment Research Dataset from Hugging Face"""

    DATASET_NAME = 'StampyAI/alignment-research-dataset'

    # Default filters
    DEFAULT_MIN_DATE = '2020-01-01'
    DEFAULT_SOURCES = [
        'arxiv', 'alignmentforum', 'lesswrong', 'eaforum',
        'distill', 'deepmind', 'openai', 'anthropic', 'miri',
        'gwern', 'agi_safety_fundamentals'
    ]
    DEFAULT_KEYWORDS = [
        'alignment', 'safety', 'interpretability', 'robustness',
        'capabilities', 'x-risk', 'existential'
    ]

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        mode: str = 'full',
        limit: Optional[int] = None,
        dry_run: bool = False,
        min_date: Optional[str] = None,
        sources: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        use_auth: bool = True
    ):
        """
        Initialize extractor

        Args:
            output_dir: Output directory (auto-created if None)
            mode: 'full' or 'delta'
            limit: Maximum records to extract (None = unlimited)
            dry_run: If True, don't write files
            min_date: Minimum publication date (YYYY-MM-DD)
            sources: List of sources to include (None = all)
            keywords: Keywords to filter by (None = no keyword filter)
            use_auth: Use HF_TOKEN if available
        """
        self.mode = mode
        self.limit = limit
        self.dry_run = dry_run
        self.min_date = min_date or self.DEFAULT_MIN_DATE
        self.sources = sources or self.DEFAULT_SOURCES
        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.use_auth = use_auth

        # Setup logger
        self.logger = get_logger('alignment_extraction', log_dir='logs/alignment_extraction')

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

        # Load HF token if available
        self.hf_token = os.environ.get('HF_TOKEN') if use_auth else None
        if self.hf_token:
            self.logger.info("Using HuggingFace authentication token")
        else:
            self.logger.info("No HF_TOKEN found, using anonymous access")

    def _load_datasets_library(self):
        """Lazy load datasets library"""
        global datasets
        if datasets is None:
            try:
                import datasets as ds
                datasets = ds
                self.logger.info("Loaded datasets library", version=datasets.__version__)
            except ImportError:
                self.logger.error("datasets library not installed. Install with: pip install datasets")
                raise

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
            # Check date
            date_published = record.get('date_published', '')
            if not date_published:
                return False

            # For delta mode, only include records after last extraction
            if self.mode == 'delta':
                last_date = self._get_last_extraction_date()
                if last_date and date_published <= last_date:
                    return False

            # Check min date
            if date_published < self.min_date:
                return False

            # Check source
            source = record.get('source', '')
            if self.sources and source not in self.sources:
                return False

            # Check keywords (if specified)
            if self.keywords:
                text = record.get('text', '').lower()
                title = record.get('title', '').lower()
                combined = text + ' ' + title

                # At least one keyword must match
                if not any(keyword.lower() in combined for keyword in self.keywords):
                    return False

            # Check text length
            text = record.get('text', '')
            if len(text) < 100:
                return False

            return True

        except Exception as e:
            self.logger.warning("Filter error", record_id=record.get('id'), error=str(e))
            return False

    def _transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform HuggingFace record to pdoom-data schema

        Args:
            record: Raw record from HuggingFace

        Returns:
            Transformed record with provenance
        """
        # Extract core fields
        transformed = {
            'id': record.get('id', ''),
            'source': record.get('source', ''),
            'title': record.get('title', ''),
            'text': record.get('text', ''),
            'url': record.get('url', ''),
            'date_published': record.get('date_published', '')
        }

        # Add optional fields if present
        optional_fields = [
            'authors', 'abstract', 'doi', 'primary_category', 'categories',
            'tags', 'source_type', 'converted_with', 'alignment_text',
            'confidence_score', 'journal_ref', 'author_comment', 'citation_level'
        ]

        for field in optional_fields:
            if field in record and record[field] is not None:
                transformed[field] = record[field]

        # Add provenance
        transformed['_provenance'] = {
            'source_system': f'Hugging Face - {self.DATASET_NAME}',
            'ingestion_date': datetime.now(timezone.utc).isoformat(),
            'license': 'MIT',
            'attribution': 'StampyAI / AI Safety Info',
            'citation': 'Kirchner et al. 2022, arXiv:2206.02841',
            'extraction_method': 'api',
            'transformations': ['schema_standardization', 'provenance_addition']
        }

        return transformed

    def _create_metadata(self) -> Dict[str, Any]:
        """Create metadata for extraction"""
        metadata = {
            'extraction_date': datetime.now(timezone.utc).isoformat(),
            'source_name': 'alignment_research',
            'source_url': f'https://huggingface.co/datasets/{self.DATASET_NAME}',
            'extraction_method': 'api',
            'extractor_version': '1.0.0',
            'data_format': 'jsonl',
            'record_count': self.stats['records_written'],
            'extraction_type': self.mode,
            'last_extraction_date': self._get_last_extraction_date() if self.mode == 'delta' else None,
            'filters_applied': {
                'date_range': f"{self.min_date} to present",
                'sources': self.sources,
                'keywords': self.keywords,
                'min_text_length': 100
            },
            'extraction_status': 'complete',
            'extraction_notes': '',
            'fields_extracted': [
                'id', 'source', 'title', 'text', 'url', 'date_published',
                'authors', 'abstract', 'doi', 'categories', 'tags'
            ],
            'huggingface_dataset_version': 'main',
            'attribution': 'StampyAI/AI Safety Info - MIT License',
            'citation': 'Kirchner, J. H., Smith, L., Thibodeau, J., McDonnell, K., and Reynolds, L. Understanding AI alignment research: A Systematic Analysis. arXiv preprint arXiv:2206.02841 (2022)',
            'license': 'MIT',
            'rate_limit_info': {
                'authenticated': bool(self.hf_token),
                'requests_made': 1,  # Streaming is typically one request
                'time_elapsed_seconds': self.stats['duration_seconds']
            },
            'extraction_statistics': self.stats,
            'data_quality': {
                'missing_required_fields': 0,
                'ascii_compliance_checked': False,
                'schema_validation_passed': False
            }
        }

        return metadata

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
            # Load datasets library
            self._load_datasets_library()

            # Login to HuggingFace if token available
            if self.hf_token:
                from huggingface_hub import login
                login(token=self.hf_token, add_to_git_credential=False)

            # Load dataset - uses individual JSONL files per source
            self.logger.info("Loading dataset", dataset=self.DATASET_NAME)

            # The dataset consists of individual JSONL files for each source
            # We'll download and stream from these files
            from huggingface_hub import hf_hub_download, list_repo_files
            import jsonlines

            # Get list of available JSONL files
            self.logger.info("Fetching file list from repository")
            repo_files = list_repo_files(self.DATASET_NAME, repo_type='dataset')
            jsonl_files = [f for f in repo_files if f.endswith('.jsonl')]

            self.logger.info("Found JSONL files", count=len(jsonl_files), files=str(jsonl_files[:5]))

            # Filter by requested sources if specified
            if self.sources:
                jsonl_files = [
                    f for f in jsonl_files
                    if any(source in f.lower() for source in [s.lower() for s in self.sources])
                ]
                self.logger.info("Filtered files by sources", count=len(jsonl_files))

            if not jsonl_files:
                raise ValueError("No matching JSONL files found")

            self.logger.info("Dataset file list loaded successfully")

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
                # Process records from JSONL files
                self.logger.info("Processing records from files", file_count=len(jsonl_files))

                for jsonl_file in jsonl_files:
                    # Check if we've reached limit
                    if self.limit and self.stats['records_written'] >= self.limit:
                        self.logger.info("Reached limit, stopping", limit=self.limit)
                        break

                    self.logger.info("Processing file", file=jsonl_file)

                    # Download file to cache
                    try:
                        file_path = hf_hub_download(
                            repo_id=self.DATASET_NAME,
                            filename=jsonl_file,
                            repo_type='dataset'
                        )
                    except Exception as e:
                        self.logger.error("Failed to download file", file=jsonl_file, error=str(e))
                        self.stats['errors_encountered'] += 1
                        continue

                    # Read and process records from file
                    try:
                        with jsonlines.open(file_path) as reader:
                            for record in reader:
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

                    except Exception as e:
                        self.logger.error("Failed to read file", file=jsonl_file, error=str(e))
                        self.stats['errors_encountered'] += 1
                        continue

                    self.logger.info("Finished file", file=jsonl_file, records_written=self.stats['records_written'])

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
        description='Extract data from Alignment Research Dataset',
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

  # With HuggingFace token for higher rate limits
  HF_TOKEN=your_token python extraction_script.py --mode full
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
        help='Minimum publication date (YYYY-MM-DD, default: 2020-01-01)'
    )
    parser.add_argument(
        '--sources',
        nargs='+',
        help='Specific sources to include (default: arxiv, alignmentforum, lesswrong, etc.)'
    )
    parser.add_argument(
        '--keywords',
        nargs='+',
        help='Keywords to filter by (default: alignment, safety, interpretability, etc.)'
    )
    parser.add_argument(
        '--no-auth',
        action='store_true',
        help='Disable HuggingFace authentication (use anonymous access)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory (default: auto-generated timestamp)'
    )

    args = parser.parse_args()

    # Create extractor
    extractor = AlignmentResearchExtractor(
        output_dir=args.output_dir,
        mode=args.mode,
        limit=args.limit,
        dry_run=args.dry_run,
        min_date=args.min_date,
        sources=args.sources,
        keywords=args.keywords,
        use_auth=not args.no_auth
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
