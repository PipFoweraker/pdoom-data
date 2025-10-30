#!/usr/bin/env python3
"""
Test funding event dump space functionality

Tests for new_dump.py and validate_dump.py scripts
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from extraction.new_dump import create_dump_directory
from extraction.validate_dump import validate_dump


def test_create_dump_basic():
    """Test basic dump directory creation"""
    print("Testing dump directory creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create base structure
        base_dir = tmpdir / "test_repo"
        source_dir = base_dir / "data" / "raw" / "funding_sources" / "sff"
        source_dir.mkdir(parents=True)
        
        # Create dump
        dump_dir = create_dump_directory('sff', 'manual', base_dir)
        
        # Verify directory exists
        assert dump_dir.exists(), "Dump directory should exist"
        assert dump_dir.is_dir(), "Dump path should be a directory"
        
        # Verify metadata file exists and is valid
        metadata_file = dump_dir / '_metadata.json'
        assert metadata_file.exists(), "Metadata file should exist"
        
        with open(metadata_file, 'r', encoding='ascii') as f:
            metadata = json.load(f)
        
        assert metadata['source_name'] == 'sff', "Source name should match"
        assert metadata['extraction_method'] == 'manual', "Method should match"
        assert metadata['extraction_status'] == 'pending', "Initial status should be pending"
        
        # Verify data file exists
        data_file = dump_dir / 'data.json'
        assert data_file.exists(), "Data file should exist"
        
        with open(data_file, 'r', encoding='ascii') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Data should be an array"
        assert len(data) == 0, "Initial data should be empty"
        
        print("  PASSED: Dump directory creation works")
        return True


def test_create_dump_invalid_source():
    """Test dump creation with invalid source"""
    print("Testing invalid source handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        base_dir = tmpdir / "test_repo"
        base_dir.mkdir(parents=True)
        
        try:
            create_dump_directory('invalid_source', 'manual', base_dir)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'Invalid source' in str(e), "Error message should mention invalid source"
        
        print("  PASSED: Invalid source rejected correctly")
        return True


def test_create_dump_invalid_method():
    """Test dump creation with invalid method"""
    print("Testing invalid method handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        base_dir = tmpdir / "test_repo"
        base_dir.mkdir(parents=True)
        
        try:
            create_dump_directory('sff', 'invalid_method', base_dir)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'Invalid method' in str(e), "Error message should mention invalid method"
        
        print("  PASSED: Invalid method rejected correctly")
        return True


def test_validate_dump_valid():
    """Test validation of valid dump"""
    print("Testing validation of valid dump...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create base structure
        base_dir = tmpdir / "test_repo"
        source_dir = base_dir / "data" / "raw" / "funding_sources" / "sff"
        source_dir.mkdir(parents=True)
        
        # Create dump
        dump_dir = create_dump_directory('sff', 'manual', base_dir)
        
        # Update metadata to be complete
        metadata_file = dump_dir / '_metadata.json'
        with open(metadata_file, 'r', encoding='ascii') as f:
            metadata = json.load(f)
        
        metadata['source_url'] = 'https://example.com'
        metadata['record_count'] = 0
        metadata['extraction_status'] = 'complete'
        
        with open(metadata_file, 'w', encoding='ascii') as f:
            json.dump(metadata, f, indent=2)
        
        # Validate
        result = validate_dump('sff', dump_dir.name, base_dir)
        
        assert result.is_valid(), f"Validation should pass, errors: {result.errors}"
        assert len(result.errors) == 0, "Should have no errors"
        
        print("  PASSED: Valid dump validated successfully")
        return True


def test_validate_dump_missing_metadata():
    """Test validation with missing metadata file"""
    print("Testing validation with missing metadata...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create base structure
        base_dir = tmpdir / "test_repo"
        dump_dir = base_dir / "data" / "raw" / "funding_sources" / "sff" / "dumps" / "2024-01-01_000000"
        dump_dir.mkdir(parents=True)
        
        # Create only data file, no metadata
        data_file = dump_dir / 'data.json'
        with open(data_file, 'w', encoding='ascii') as f:
            json.dump([], f)
        
        # Validate
        result = validate_dump('sff', '2024-01-01_000000', base_dir)
        
        assert not result.is_valid(), "Validation should fail"
        assert any('metadata' in err.lower() for err in result.errors), "Should report missing metadata"
        
        print("  PASSED: Missing metadata detected correctly")
        return True


def test_validate_dump_record_count_mismatch():
    """Test validation with mismatched record count"""
    print("Testing record count mismatch detection...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create base structure
        base_dir = tmpdir / "test_repo"
        source_dir = base_dir / "data" / "raw" / "funding_sources" / "sff"
        source_dir.mkdir(parents=True)
        
        # Create dump
        dump_dir = create_dump_directory('sff', 'manual', base_dir)
        
        # Add data but don't update metadata record count
        data = [
            {"grant_id": "TEST-001", "amount": 1000},
            {"grant_id": "TEST-002", "amount": 2000}
        ]
        data_file = dump_dir / 'data.json'
        with open(data_file, 'w', encoding='ascii') as f:
            json.dump(data, f)
        
        # Update metadata with wrong count
        metadata_file = dump_dir / '_metadata.json'
        with open(metadata_file, 'r', encoding='ascii') as f:
            metadata = json.load(f)
        
        metadata['source_url'] = 'https://example.com'
        metadata['record_count'] = 5  # Wrong count
        metadata['extraction_status'] = 'complete'
        
        with open(metadata_file, 'w', encoding='ascii') as f:
            json.dump(metadata, f)
        
        # Validate
        result = validate_dump('sff', dump_dir.name, base_dir)
        
        # Should pass validation but have warning
        assert result.is_valid(), "Should pass validation with warnings"
        assert len(result.warnings) > 0, "Should have warnings"
        assert any('mismatch' in warn.lower() for warn in result.warnings), "Should warn about count mismatch"
        
        print("  PASSED: Record count mismatch detected")
        return True


def test_validate_dump_invalid_source():
    """Test validation with invalid source"""
    print("Testing validation with invalid source...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        base_dir = tmpdir / "test_repo"
        base_dir.mkdir()
        
        # Validate with invalid source
        result = validate_dump('invalid_source', '2024-01-01_000000', base_dir)
        
        assert not result.is_valid(), "Validation should fail"
        assert any('Invalid source' in err for err in result.errors), "Should report invalid source"
        
        print("  PASSED: Invalid source detected")
        return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Funding Dump Space Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_create_dump_basic,
        test_create_dump_invalid_source,
        test_create_dump_invalid_method,
        test_validate_dump_valid,
        test_validate_dump_missing_metadata,
        test_validate_dump_record_count_mismatch,
        test_validate_dump_invalid_source
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
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
