#!/usr/bin/env python3
"""
Version Management System for pdoom-data
Handles semantic versioning and automated increment detection
"""

import re
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

class VersionManager:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.version_file = self.repo_path / "VERSION"
        self.devblog_file = self.repo_path / "DEVBLOG.md"
    
    def get_current_version(self):
        """Get current version from VERSION file"""
        if not self.version_file.exists():
            return "0.0.0"
        return self.version_file.read_text().strip()
    
    def parse_version(self, version_str):
        """Parse semantic version string"""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_str)
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")
        return tuple(map(int, match.groups()))
    
    def format_version(self, major, minor, patch):
        """Format version tuple as string"""
        return f"{major}.{minor}.{patch}"
    
    def increment_version(self, increment_type="patch"):
        """Increment version based on type: major, minor, or patch"""
        current = self.get_current_version()
        major, minor, patch = self.parse_version(current)
        
        if increment_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif increment_type == "minor":
            minor += 1
            patch = 0
        elif increment_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid increment type: {increment_type}")
        
        new_version = self.format_version(major, minor, patch)
        return new_version
    
    def detect_increment_type(self):
        """Analyze git changes to suggest version increment type"""
        try:
            # Get changed files since last tag/commit
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True, text=True, cwd=self.repo_path
            )
            
            if result.returncode != 0:
                return "patch"  # Default to patch if git fails
            
            changed_files = result.stdout.strip().split('\n')
            
            # Analyze change significance
            major_changes = any(
                f.endswith('.py') and 'event_data_structures' in f
                for f in changed_files
            )
            
            minor_changes = any(
                f.endswith('.py') or f.endswith('.md') and f != 'DEVBLOG.md'
                for f in changed_files
            )
            
            if major_changes:
                return "major"
            elif minor_changes:
                return "minor"
            else:
                return "patch"
        
        except Exception:
            return "patch"
    
    def update_version_file(self, new_version):
        """Update VERSION file with new version"""
        self.version_file.write_text(new_version)
        print(f"Updated VERSION file to {new_version}")
    
    def update_devblog(self, new_version, changes_description=""):
        """Update DEVBLOG.md with new version entry"""
        if not self.devblog_file.exists():
            return
        
        content = self.devblog_file.read_text()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Prepare new version entry
        version_entry = f"""
### v{new_version} ({current_date})
**Changes:**
{changes_description if changes_description else "- Bug fixes and improvements"}

**Status:** Development Build
**Commit:** {self.get_git_commit_hash()}

"""
        
        # Insert after "## Version History"
        updated_content = re.sub(
            r'(## Version History\n)',
            f'\\1{version_entry}',
            content
        )
        
        # Update current version at top
        updated_content = re.sub(
            r'## Current Version: [\d.]+',
            f'## Current Version: {new_version}',
            updated_content
        )
        
        self.devblog_file.write_text(updated_content)
        print(f"Updated DEVBLOG.md with version {new_version}")
    
    def get_git_commit_hash(self):
        """Get short git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, cwd=self.repo_path
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def create_git_tag(self, version):
        """Create git tag for version"""
        try:
            subprocess.run(
                ["git", "tag", f"v{version}"],
                cwd=self.repo_path, check=True
            )
            print(f"Created git tag v{version}")
        except subprocess.CalledProcessError:
            print(f"Failed to create git tag v{version}")
    
    def generate_changelog_entry(self):
        """Generate changelog entry from git commits"""
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--since='1 day ago'"],
                capture_output=True, text=True, cwd=self.repo_path
            )
            
            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split('\n')
                changelog = "- " + "\n- ".join(
                    commit.split(' ', 1)[1] for commit in commits[:5]
                )
                return changelog
            return "- Development updates and improvements"
        
        except Exception:
            return "- Development updates and improvements"

def main():
    """Main CLI interface for version management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Version Management for pdoom-data")
    parser.add_argument("--current", action="store_true", help="Show current version")
    parser.add_argument("--increment", choices=["major", "minor", "patch"], 
                       help="Increment version")
    parser.add_argument("--auto", action="store_true", 
                       help="Auto-detect increment type and update")
    parser.add_argument("--tag", action="store_true", help="Create git tag")
    parser.add_argument("--message", type=str, help="Custom change description")
    
    args = parser.parse_args()
    
    vm = VersionManager()
    
    if args.current:
        print(vm.get_current_version())
        return
    
    if args.increment:
        new_version = vm.increment_version(args.increment)
        vm.update_version_file(new_version)
        
        changes = args.message or vm.generate_changelog_entry()
        vm.update_devblog(new_version, changes)
        
        if args.tag:
            vm.create_git_tag(new_version)
        
        print(f"Version updated to {new_version}")
    
    elif args.auto:
        increment_type = vm.detect_increment_type()
        new_version = vm.increment_version(increment_type)
        
        print(f"Auto-detected increment type: {increment_type}")
        print(f"New version would be: {new_version}")
        
        confirm = input("Proceed with version update? (y/N): ")
        if confirm.lower() == 'y':
            vm.update_version_file(new_version)
            
            changes = args.message or vm.generate_changelog_entry()
            vm.update_devblog(new_version, changes)
            
            if args.tag:
                vm.create_git_tag(new_version)
            
            print(f"Version updated to {new_version}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
