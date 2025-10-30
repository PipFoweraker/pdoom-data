#!/usr/bin/env python3
"""
Safe File Operations Utilities
Provides atomic file operations with checksums and platform awareness
"""

import hashlib
import shutil
import tempfile
import os
from pathlib import Path
from typing import Optional, Tuple


def calculate_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate checksum of a file
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (default: sha256)
        
    Returns:
        Hex digest of file hash
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def get_file_metadata(file_path: Path) -> dict:
    """
    Get file metadata including size and modification time
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with metadata
    """
    stat = file_path.stat()
    return {
        'size_bytes': stat.st_size,
        'modified_timestamp': stat.st_mtime,
        'checksum': calculate_checksum(file_path)
    }


def has_sufficient_disk_space(dest_dir: Path, required_bytes: int) -> bool:
    """
    Check if destination has sufficient disk space
    
    Args:
        dest_dir: Destination directory
        required_bytes: Required space in bytes
        
    Returns:
        True if sufficient space available
    """
    try:
        stat = shutil.disk_usage(dest_dir)
        # Add 10% buffer
        return stat.free > (required_bytes * 1.1)
    except Exception:
        # If we can't check, assume sufficient space
        return True


def atomic_copy(source: Path, dest: Path, verify: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Copy file atomically using temp file and move
    
    Args:
        source: Source file path
        dest: Destination file path
        verify: Verify checksums after copy (default: True)
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Ensure source exists
        if not source.exists():
            return False, f"Source file does not exist: {source}"
        
        # Check disk space
        source_size = source.stat().st_size
        if not has_sufficient_disk_space(dest.parent, source_size):
            return False, "Insufficient disk space"
        
        # Create destination directory if needed
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate source checksum if verification requested
        source_checksum = None
        if verify:
            source_checksum = calculate_checksum(source)
        
        # Copy to temporary file in destination directory
        temp_fd, temp_path = tempfile.mkstemp(dir=dest.parent, prefix='.tmp_')
        try:
            os.close(temp_fd)
            temp_path = Path(temp_path)
            
            # Perform copy
            shutil.copy2(source, temp_path)
            
            # Verify checksum if requested
            if verify and source_checksum:
                temp_checksum = calculate_checksum(temp_path)
                if source_checksum != temp_checksum:
                    temp_path.unlink()
                    return False, "Checksum mismatch after copy"
            
            # Atomic move to final destination
            # On Windows, need to remove dest first if it exists
            if os.name == 'nt' and dest.exists():
                dest.unlink()
            
            temp_path.rename(dest)
            return True, None
            
        except Exception as e:
            # Cleanup temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise e
            
    except Exception as e:
        return False, str(e)


def atomic_move(source: Path, dest: Path, verify: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Move file atomically with verification
    
    Args:
        source: Source file path
        dest: Destination file path
        verify: Verify checksums before move (default: True)
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Ensure source exists
        if not source.exists():
            return False, f"Source file does not exist: {source}"
        
        # Calculate source checksum if verification requested
        source_checksum = None
        if verify:
            source_checksum = calculate_checksum(source)
        
        # Create destination directory if needed
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if on same filesystem (can use atomic rename)
        try:
            # On Windows, need to remove dest first if it exists
            if os.name == 'nt' and dest.exists():
                dest.unlink()
            
            source.rename(dest)
            
            # Verify if requested
            if verify and source_checksum:
                dest_checksum = calculate_checksum(dest)
                if source_checksum != dest_checksum:
                    return False, "Checksum mismatch after move"
            
            return True, None
            
        except OSError:
            # Different filesystem, use copy + delete
            success, error = atomic_copy(source, dest, verify)
            if success:
                source.unlink()
                return True, None
            return False, error
            
    except Exception as e:
        return False, str(e)


def safe_backup(file_path: Path, backup_dir: Optional[Path] = None) -> Tuple[bool, Optional[Path], Optional[str]]:
    """
    Create backup of file before operations
    
    Args:
        file_path: File to backup
        backup_dir: Directory for backups (default: same dir with .bak extension)
        
    Returns:
        Tuple of (success, backup_path, error_message)
    """
    try:
        if not file_path.exists():
            return False, None, f"File does not exist: {file_path}"
        
        # Determine backup location
        if backup_dir:
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / file_path.name
        else:
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        
        # Copy to backup location
        success, error = atomic_copy(file_path, backup_path, verify=True)
        if success:
            return True, backup_path, None
        else:
            return False, None, error
            
    except Exception as e:
        return False, None, str(e)


def restore_backup(backup_path: Path, original_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Restore file from backup
    
    Args:
        backup_path: Path to backup file
        original_path: Path to restore to
        
    Returns:
        Tuple of (success, error_message)
    """
    if not backup_path.exists():
        return False, f"Backup file does not exist: {backup_path}"
    
    return atomic_copy(backup_path, original_path, verify=True)


if __name__ == "__main__":
    # Test file operations
    test_dir = Path("logs/test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test file
    test_file = test_dir / "test.txt"
    test_file.write_text("Test content")
    
    # Test checksum
    checksum = calculate_checksum(test_file)
    print(f"Checksum: {checksum}")
    
    # Test metadata
    metadata = get_file_metadata(test_file)
    print(f"Metadata: {metadata}")
    
    # Test atomic copy
    copy_dest = test_dir / "test_copy.txt"
    success, error = atomic_copy(test_file, copy_dest)
    print(f"Atomic copy: success={success}, error={error}")
    
    # Test backup
    success, backup_path, error = safe_backup(test_file)
    print(f"Backup: success={success}, path={backup_path}, error={error}")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
    if copy_dest.exists():
        copy_dest.unlink()
    if backup_path and backup_path.exists():
        backup_path.unlink()
    
    print("\nFile operations test complete.")
