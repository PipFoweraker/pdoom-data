#!/usr/bin/env python3
"""
Test migration functionality
Simple integration test to verify the migration script works correctly
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from migration.migrate import DataMigrator
from utils.file_ops import calculate_checksum


def test_migration_basic():
    """Test basic migration functionality"""
    print("Testing basic migration...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Setup test directories
        source_dir = tmpdir / "raw"
        dest_dir = tmpdir / "validated"
        log_dir = tmpdir / "logs"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        log_dir.mkdir()
        
        # Create test data
        test_data = [
            {
                "grant_id": "TEST-001",
                "amount": 50000,
                "date": "2024-01-15",
                "source": "Other",
                "recipient": "Test Org"
            }
        ]
        
        test_file = source_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Create config
        config = {
            'source_dir': str(source_dir),
            'dest_dir': str(dest_dir),
            'backup_dir': str(tmpdir / "backups"),
            'log_dir': str(log_dir),
            'state_file': str(log_dir / '.migration_state.json'),
            'required_columns': ['grant_id', 'amount', 'date', 'source'],
            'validation_schema': None,
            'fail_on_warning': False,
            'create_backups': True,
            'operation': 'copy'
        }
        
        # Run migration
        migrator = DataMigrator()
        migrator.config = config
        
        stats = migrator.migrate()
        
        # Verify results
        assert stats['processed'] == 1, f"Expected 1 processed, got {stats['processed']}"
        assert stats['failed'] == 0, f"Expected 0 failed, got {stats['failed']}"
        
        # Verify file exists in destination
        dest_file = dest_dir / "test.json"
        assert dest_file.exists(), "Destination file does not exist"
        
        # Verify checksums match
        source_checksum = calculate_checksum(test_file)
        dest_checksum = calculate_checksum(dest_file)
        assert source_checksum == dest_checksum, "Checksums do not match"
        
        print("  PASSED: Basic migration works")
        return True


def test_migration_idempotent():
    """Test that migration is idempotent"""
    print("Testing idempotency...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Setup test directories
        source_dir = tmpdir / "raw"
        dest_dir = tmpdir / "validated"
        log_dir = tmpdir / "logs"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        log_dir.mkdir()
        
        # Create test data
        test_data = [{"grant_id": "TEST-001", "amount": 50000, "date": "2024-01-15", "source": "Other"}]
        test_file = source_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Create config
        config = {
            'source_dir': str(source_dir),
            'dest_dir': str(dest_dir),
            'backup_dir': str(tmpdir / "backups"),
            'log_dir': str(log_dir),
            'state_file': str(log_dir / '.migration_state.json'),
            'required_columns': ['grant_id', 'amount', 'date', 'source'],
            'validation_schema': None,
            'fail_on_warning': False,
            'create_backups': True,
            'operation': 'copy'
        }
        
        # Run migration first time
        migrator = DataMigrator()
        migrator.config = config
        stats1 = migrator.migrate()
        
        # Run migration second time (should skip)
        migrator2 = DataMigrator()
        migrator2.config = config
        stats2 = migrator2.migrate()
        
        # Verify results
        assert stats1['processed'] == 1, "First run should process 1 file"
        assert stats2['processed'] == 0, "Second run should process 0 files"
        assert stats2['skipped'] == 1, "Second run should skip 1 file"
        
        print("  PASSED: Idempotency works")
        return True


def test_validation_failure():
    """Test that validation failures are handled correctly"""
    print("Testing validation failure handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Setup test directories
        source_dir = tmpdir / "raw"
        dest_dir = tmpdir / "validated"
        log_dir = tmpdir / "logs"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        log_dir.mkdir()
        
        # Create test data with missing required field
        test_data = [
            {
                "grant_id": "TEST-001",
                # Missing 'amount' field
                "date": "2024-01-15",
                "source": "Other"
            }
        ]
        
        test_file = source_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Create config
        config = {
            'source_dir': str(source_dir),
            'dest_dir': str(dest_dir),
            'backup_dir': str(tmpdir / "backups"),
            'log_dir': str(log_dir),
            'state_file': str(log_dir / '.migration_state.json'),
            'required_columns': ['grant_id', 'amount', 'date', 'source'],
            'validation_schema': None,
            'fail_on_warning': False,
            'create_backups': True,
            'operation': 'copy'
        }
        
        # Run migration
        migrator = DataMigrator()
        migrator.config = config
        stats = migrator.migrate()
        
        # Verify results
        assert stats['failed'] == 1, f"Expected 1 failed, got {stats['failed']}"
        assert stats['processed'] == 0, f"Expected 0 processed, got {stats['processed']}"
        
        # Verify file does NOT exist in destination
        dest_file = dest_dir / "test.json"
        assert not dest_file.exists(), "Destination file should not exist after validation failure"
        
        print("  PASSED: Validation failures handled correctly")
        return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("Migration Script Tests")
    print("=" * 50)
    print()
    
    tests = [
        test_migration_basic,
        test_migration_idempotent,
        test_validation_failure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
    
    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
