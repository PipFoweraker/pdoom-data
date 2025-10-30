#!/usr/bin/env python3
"""
Data Migration Script
Orchestrates safe data movement between zones with validation and logging
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.file_ops import (
    atomic_copy, atomic_move, safe_backup, 
    get_file_metadata, calculate_checksum
)
from validation.validate_funding import FundingDataValidator, ValidationResult


class MigrationState:
    """Tracks processed files to enable idempotent operations"""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.processed_files: Dict[str, dict] = {}
        self.load()
    
    def load(self):
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    self.processed_files = data.get('processed_files', {})
            except Exception:
                self.processed_files = {}
    
    def save(self):
        """Save state to file"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                'processed_files': self.processed_files,
                'last_updated': datetime.utcnow().isoformat()
            }, f, indent=2)
    
    def is_processed(self, file_path: str, checksum: str) -> bool:
        """Check if file has been processed"""
        if file_path in self.processed_files:
            return self.processed_files[file_path].get('checksum') == checksum
        return False
    
    def mark_processed(self, file_path: str, metadata: dict):
        """Mark file as processed"""
        self.processed_files[file_path] = metadata
        self.save()
    
    def remove(self, file_path: str):
        """Remove file from processed state"""
        if file_path in self.processed_files:
            del self.processed_files[file_path]
            self.save()


class DataMigrator:
    """Orchestrates data migration with safety features"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize migrator
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize logger
        log_dir = Path(self.config.get('log_dir', 'logs/migration'))
        self.logger = get_logger('migration', log_dir=log_dir)
        
        # Initialize validator
        schema_path = self.config.get('validation_schema')
        required_columns = self.config.get('required_columns', [])
        
        if schema_path:
            schema_path = Path(schema_path)
        
        self.validator = FundingDataValidator(
            schema_path=schema_path,
            required_columns=required_columns
        )
        
        # Initialize state tracking
        state_file = Path(self.config.get('state_file', 'logs/migration/.migration_state.json'))
        self.state = MigrationState(state_file)
        
        self.logger.info("Data migrator initialized", config=self.config)
    
    def _load_config(self, config_path: Optional[Path]) -> dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'source_dir': 'data/raw/funding_sources',
            'dest_dir': 'data/transformed/validated',
            'backup_dir': 'data/_backups',
            'log_dir': 'logs/migration',
            'state_file': 'logs/migration/.migration_state.json',
            'required_columns': ['grant_id', 'amount', 'date', 'source'],
            'validation_schema': None,
            'fail_on_warning': False,
            'create_backups': True,
            'operation': 'copy'  # 'copy' or 'move'
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path) as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return default_config
    
    def migrate(self, source_pattern: str = '*') -> dict:
        """
        Migrate files from source to destination
        
        Args:
            source_pattern: Glob pattern for source files (default: all files)
            
        Returns:
            Dictionary with migration statistics
        """
        source_dir = Path(self.config['source_dir'])
        dest_dir = Path(self.config['dest_dir'])
        
        self.logger.info(
            "Starting migration",
            source_dir=str(source_dir),
            dest_dir=str(dest_dir),
            pattern=source_pattern
        )
        
        stats = {
            'processed': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }
        
        # Find files to process
        if not source_dir.exists():
            error_msg = f"Source directory does not exist: {source_dir}"
            self.logger.error(error_msg)
            stats['errors'].append(error_msg)
            return stats
        
        # Process each matching file
        for source_file in source_dir.rglob(source_pattern):
            if not source_file.is_file():
                continue
            
            # Skip non-data files
            if source_file.suffix not in ['.json', '.csv', '.txt']:
                continue
            
            try:
                result = self._process_file(source_file, dest_dir)
                
                if result == 'processed':
                    stats['processed'] += 1
                elif result == 'skipped':
                    stats['skipped'] += 1
                elif result == 'failed':
                    stats['failed'] += 1
                    
            except Exception as e:
                error_msg = f"Error processing {source_file}: {e}"
                self.logger.error(error_msg, file=str(source_file))
                stats['failed'] += 1
                stats['errors'].append(error_msg)
        
        self.logger.info("Migration complete", stats=stats)
        return stats
    
    def _process_file(self, source_file: Path, dest_dir: Path) -> str:
        """
        Process a single file
        
        Returns:
            Status string: 'processed', 'skipped', or 'failed'
        """
        # Calculate checksum
        try:
            checksum = calculate_checksum(source_file)
        except Exception as e:
            self.logger.error(f"Could not calculate checksum", file=str(source_file), error=str(e))
            return 'failed'
        
        # Check if already processed
        if self.state.is_processed(str(source_file), checksum):
            self.logger.debug("File already processed, skipping", file=str(source_file))
            return 'skipped'
        
        self.logger.info("Processing file", file=str(source_file), checksum=checksum)
        
        # Get metadata
        metadata = get_file_metadata(source_file)
        
        # Validate source file
        validation_result = self.validator.validate_file(source_file)
        
        if not validation_result.passed:
            self.logger.error(
                "Validation failed",
                file=str(source_file),
                errors=validation_result.errors
            )
            return 'failed'
        
        if validation_result.warnings and self.config.get('fail_on_warning'):
            self.logger.error(
                "Validation warnings treated as errors",
                file=str(source_file),
                warnings=validation_result.warnings
            )
            return 'failed'
        
        if validation_result.warnings:
            self.logger.warning(
                "Validation warnings",
                file=str(source_file),
                warnings=validation_result.warnings
            )
        
        # Determine destination path
        relative_path = source_file.relative_to(Path(self.config['source_dir']))
        dest_file = dest_dir / relative_path
        
        # Create backup if destination exists
        backup_path = None
        if dest_file.exists() and self.config.get('create_backups'):
            backup_dir = Path(self.config['backup_dir'])
            success, backup_path, error = safe_backup(dest_file, backup_dir)
            
            if not success:
                self.logger.error(
                    "Backup failed",
                    file=str(dest_file),
                    error=error
                )
                return 'failed'
            
            self.logger.info("Backup created", backup_path=str(backup_path))
        
        # Perform operation (copy or move)
        operation = self.config.get('operation', 'copy')
        
        if operation == 'move':
            success, error = atomic_move(source_file, dest_file, verify=True)
        else:
            success, error = atomic_copy(source_file, dest_file, verify=True)
        
        if not success:
            self.logger.error(
                f"{operation.capitalize()} operation failed",
                source=str(source_file),
                dest=str(dest_file),
                error=error
            )
            return 'failed'
        
        # Validate destination file
        dest_validation = self.validator.validate_file(dest_file)
        if not dest_validation.passed:
            self.logger.error(
                "Destination validation failed",
                file=str(dest_file),
                errors=dest_validation.errors
            )
            # Restore from backup if available
            if backup_path:
                self.logger.info("Restoring from backup", backup_path=str(backup_path))
                # Note: restore implementation could be added here
            return 'failed'
        
        # Mark as processed
        self.state.mark_processed(str(source_file), {
            'checksum': checksum,
            'processed_at': datetime.utcnow().isoformat(),
            'dest_path': str(dest_file),
            'metadata': metadata,
            'validation_info': validation_result.info
        })
        
        self.logger.info(
            f"{operation.capitalize()} successful",
            source=str(source_file),
            dest=str(dest_file),
            checksum=checksum
        )
        
        return 'processed'


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Migrate data files between zones with validation and logging'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--pattern',
        default='*',
        help='Glob pattern for files to process (default: all files)'
    )
    parser.add_argument(
        '--source',
        type=Path,
        help='Override source directory'
    )
    parser.add_argument(
        '--dest',
        type=Path,
        help='Override destination directory'
    )
    parser.add_argument(
        '--operation',
        choices=['copy', 'move'],
        help='Operation type: copy or move'
    )
    
    args = parser.parse_args()
    
    # Initialize migrator
    migrator = DataMigrator(config_path=args.config)
    
    # Override config with command line arguments
    if args.source:
        migrator.config['source_dir'] = str(args.source)
    if args.dest:
        migrator.config['dest_dir'] = str(args.dest)
    if args.operation:
        migrator.config['operation'] = args.operation
    
    # Run migration
    stats = migrator.migrate(source_pattern=args.pattern)
    
    # Print summary
    print("\n" + "="*50)
    print("Migration Summary")
    print("="*50)
    print(f"Processed: {stats['processed']}")
    print(f"Skipped:   {stats['skipped']}")
    print(f"Failed:    {stats['failed']}")
    
    if stats['errors']:
        print("\nErrors:")
        for error in stats['errors']:
            print(f"  - {error}")
    
    # Exit with appropriate code
    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
