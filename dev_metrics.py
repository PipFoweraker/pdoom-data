#!/usr/bin/env python3
"""
Development Metrics and Analytics
Tracks development progress and generates insights
"""

import json
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class DevMetrics:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.db_path = self.repo_path / "dev_metrics.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for metrics"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                id INTEGER PRIMARY KEY,
                hash TEXT UNIQUE,
                date TEXT,
                author TEXT,
                message TEXT,
                files_changed INTEGER,
                insertions INTEGER,
                deletions INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS releases (
                id INTEGER PRIMARY KEY,
                version TEXT UNIQUE,
                date TEXT,
                commit_hash TEXT,
                type TEXT,
                description TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics_snapshots (
                id INTEGER PRIMARY KEY,
                date TEXT,
                total_files INTEGER,
                total_lines INTEGER,
                ascii_compliance_score REAL,
                test_coverage REAL,
                documentation_coverage REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def collect_git_metrics(self):
        """Collect metrics from git history"""
        try:
            # Get commit history
            result = subprocess.run([
                "git", "log", "--pretty=format:%H|%ai|%an|%s", "--shortstat"
            ], capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode != 0:
                return {}
            
            lines = result.stdout.split('\n')
            commits = []
            
            i = 0
            while i < len(lines):
                if '|' in lines[i]:  # Commit line
                    parts = lines[i].split('|')
                    commit_hash = parts[0]
                    date = parts[1]
                    author = parts[2]
                    message = parts[3]
                    
                    # Look for shortstat line
                    files_changed = insertions = deletions = 0
                    if i + 1 < len(lines) and 'file' in lines[i + 1]:
                        shortstat = lines[i + 1]
                        if 'changed' in shortstat:
                            parts = shortstat.split(', ')
                            for part in parts:
                                if 'file' in part:
                                    files_changed = int(part.split()[0])
                                elif 'insertion' in part:
                                    insertions = int(part.split()[0])
                                elif 'deletion' in part:
                                    deletions = int(part.split()[0])
                    
                    commits.append({
                        'hash': commit_hash,
                        'date': date,
                        'author': author,
                        'message': message,
                        'files_changed': files_changed,
                        'insertions': insertions,
                        'deletions': deletions
                    })
                
                i += 1
            
            return {'commits': commits}
        
        except Exception as e:
            print(f"Error collecting git metrics: {e}")
            return {}
    
    def calculate_code_metrics(self):
        """Calculate current code metrics"""
        metrics = {
            'total_files': 0,
            'total_lines': 0,
            'python_files': 0,
            'markdown_files': 0,
            'json_files': 0,
            'largest_file': '',
            'largest_file_lines': 0
        }
        
        # Count files and lines
        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file() and not str(file_path).startswith('.'):
                metrics['total_files'] += 1
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                        metrics['total_lines'] += lines
                        
                        if lines > metrics['largest_file_lines']:
                            metrics['largest_file'] = str(file_path.relative_to(self.repo_path))
                            metrics['largest_file_lines'] = lines
                
                except:
                    continue
                
                # Count by file type
                if file_path.suffix == '.py':
                    metrics['python_files'] += 1
                elif file_path.suffix == '.md':
                    metrics['markdown_files'] += 1
                elif file_path.suffix == '.json':
                    metrics['json_files'] += 1
        
        return metrics
    
    def check_ascii_compliance(self):
        """Check ASCII compliance across all files"""
        try:
            result = subprocess.run([
                "python", "validate_ascii.py"
            ], capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode == 0:
                # Parse output to get compliance score
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Checked' in line and 'files' in line:
                        total_files = int(line.split()[1])
                    if 'SUCCESS' in line:
                        return 1.0  # 100% compliant
                    if 'FAILED' in line:
                        failed_count = 0
                        for l in lines:
                            if 'FAIL:' in l:
                                failed_count += 1
                        return max(0, 1.0 - (failed_count / total_files))
            
            return 0.0
        
        except:
            return 0.0
    
    def generate_development_report(self):
        """Generate comprehensive development report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'version': self.get_current_version(),
            'git_metrics': self.collect_git_metrics(),
            'code_metrics': self.calculate_code_metrics(),
            'ascii_compliance': self.check_ascii_compliance(),
            'recent_activity': self.get_recent_activity()
        }
        
        return report
    
    def get_current_version(self):
        """Get current version from VERSION file"""
        version_file = self.repo_path / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "0.0.0"
    
    def get_recent_activity(self, days=7):
        """Get recent development activity"""
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            result = subprocess.run([
                "git", "log", f"--since={since_date}", "--oneline"
            ], capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                return {
                    'commit_count': len([c for c in commits if c.strip()]),
                    'recent_commits': commits[:10]
                }
            
            return {'commit_count': 0, 'recent_commits': []}
        
        except:
            return {'commit_count': 0, 'recent_commits': []}
    
    def save_metrics_snapshot(self):
        """Save current metrics to database"""
        conn = sqlite3.connect(self.db_path)
        
        code_metrics = self.calculate_code_metrics()
        ascii_compliance = self.check_ascii_compliance()
        
        conn.execute("""
            INSERT INTO metrics_snapshots 
            (date, total_files, total_lines, ascii_compliance_score, test_coverage, documentation_coverage)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            code_metrics['total_files'],
            code_metrics['total_lines'],
            ascii_compliance,
            0.0,  # TODO: Calculate test coverage
            0.0   # TODO: Calculate documentation coverage
        ))
        
        conn.commit()
        conn.close()
    
    def export_report_json(self, output_file="dev_metrics_report.json"):
        """Export development report as JSON"""
        report = self.generate_development_report()
        
        output_path = self.repo_path / output_file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Development report exported to: {output_path}")
        return output_path
    
    def print_summary_report(self):
        """Print a summary development report"""
        report = self.generate_development_report()
        
        print("DEVELOPMENT METRICS REPORT")
        print("=" * 50)
        print(f"Generated: {report['generated_at']}")
        print(f"Version: {report['version']}")
        print()
        
        # Code metrics
        code = report['code_metrics']
        print("CODE METRICS:")
        print(f"  Total Files: {code['total_files']}")
        print(f"  Total Lines: {code['total_lines']}")
        print(f"  Python Files: {code['python_files']}")
        print(f"  Markdown Files: {code['markdown_files']}")
        print(f"  JSON Files: {code['json_files']}")
        print(f"  Largest File: {code['largest_file']} ({code['largest_file_lines']} lines)")
        print()
        
        # ASCII compliance
        print("QUALITY METRICS:")
        print(f"  ASCII Compliance: {report['ascii_compliance']*100:.1f}%")
        print()
        
        # Recent activity
        activity = report['recent_activity']
        print("RECENT ACTIVITY (7 days):")
        print(f"  Recent Commits: {activity['commit_count']}")
        if activity['recent_commits']:
            print("  Latest Commits:")
            for commit in activity['recent_commits'][:5]:
                if commit.strip():
                    print(f"    - {commit}")
        print()

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Development Metrics for pdoom-data")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--summary", action="store_true", help="Print summary report")
    parser.add_argument("--export", type=str, help="Export JSON report to file")
    parser.add_argument("--snapshot", action="store_true", help="Save metrics snapshot")
    
    args = parser.parse_args()
    
    metrics = DevMetrics()
    
    if args.summary:
        metrics.print_summary_report()
    elif args.export:
        metrics.export_report_json(args.export)
    elif args.snapshot:
        metrics.save_metrics_snapshot()
        print("Metrics snapshot saved to database")
    elif args.report:
        report = metrics.generate_development_report()
        print(json.dumps(report, indent=2, default=str))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
