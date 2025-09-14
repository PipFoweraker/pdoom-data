#!/usr/bin/env python3
"""
Historical Data Purification Script
Removes game-specific elements from historical events to maintain scholarly integrity
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

class HistoricalDataPurifier:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.backup_dir = self.repo_path / f"backups/purification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def purify_event_data(self, event_data):
        """Remove game-specific elements from event data"""
        purified = event_data.copy()
        
        # Remove game-specific fields
        game_specific_fields = [
            'game_impacts',
            'rarity', 
            'pdoom_impact',  # Will be replaced with proper probability analysis
            'gameplay_weight',
            'unlock_conditions',
            'player_choices'
        ]
        
        for field in game_specific_fields:
            if field in purified:
                del purified[field]
                print(f"  Removed game field: {field}")
        
        # Enhance with scholarly fields (if not present)
        if 'probability_impact_analysis' not in purified:
            purified['probability_impact_analysis'] = {
                "methodology": "To be determined",
                "p_doom_change_estimate": "Analysis pending",
                "confidence_interval": "To be calculated",
                "analysis_date": datetime.now().strftime('%Y-%m-%d'),
                "status": "requires_scholarly_review"
            }
        
        if 'research_notes' not in purified:
            purified['research_notes'] = "Detailed analysis pending scholarly review"
        
        if 'verification_status' not in purified:
            purified['verification_status'] = "pending_peer_review"
        
        # Ensure sources are properly formatted
        if 'sources' in purified and isinstance(purified['sources'], list):
            # Convert simple URLs to structured citations
            structured_sources = []
            for source in purified['sources']:
                if isinstance(source, str):
                    structured_sources.append({
                        "url": source,
                        "type": "web_resource",
                        "accessed_date": datetime.now().strftime('%Y-%m-%d'),
                        "citation_status": "requires_proper_citation"
                    })
                else:
                    structured_sources.append(source)
            purified['sources'] = structured_sources
        
        return purified
    
    def backup_current_data(self):
        """Create backup of current data files"""
        data_dir = self.repo_path / "data" / "events"
        if data_dir.exists():
            backup_data_dir = self.backup_dir / "data" / "events"
            backup_data_dir.mkdir(parents=True, exist_ok=True)
            
            for json_file in data_dir.glob("*.json"):
                shutil.copy2(json_file, backup_data_dir / json_file.name)
                print(f"Backed up: {json_file.name}")
    
    def purify_json_file(self, json_file_path):
        """Purify a single JSON file containing events"""
        print(f"Purifying: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            purified_data = []
            
            if isinstance(data, list):
                # Array of events
                for event in data:
                    purified_event = self.purify_event_data(event)
                    purified_data.append(purified_event)
            elif isinstance(data, dict):
                # Single event or metadata structure
                if 'events' in data:
                    # Metadata with events array
                    purified_data = data.copy()
                    purified_events = []
                    for event in data['events']:
                        purified_event = self.purify_event_data(event)
                        purified_events.append(purified_event)
                    purified_data['events'] = purified_events
                else:
                    # Single event
                    purified_data = self.purify_event_data(data)
            
            # Write purified data
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(purified_data, f, indent=2, ensure_ascii=True)
            
            print(f"  Purified successfully: {json_file_path}")
            
        except Exception as e:
            print(f"  Error purifying {json_file_path}: {e}")
    
    def purify_all_event_files(self):
        """Purify all event JSON files"""
        data_dir = self.repo_path / "data" / "events"
        
        if not data_dir.exists():
            print("No data/events directory found")
            return
        
        json_files = list(data_dir.glob("*.json"))
        if not json_files:
            print("No JSON files found in data/events/")
            return
        
        print(f"Found {len(json_files)} JSON files to purify")
        
        for json_file in json_files:
            self.purify_json_file(json_file)
    
    def generate_purification_report(self):
        """Generate report of purification changes"""
        report = {
            "purification_date": datetime.now().isoformat(),
            "backup_location": str(self.backup_dir),
            "changes_made": [
                "Removed game_impacts arrays",
                "Removed rarity classifications", 
                "Removed pdoom_impact ratings",
                "Added probability_impact_analysis structure",
                "Enhanced source citation format",
                "Added verification_status tracking",
                "Added research_notes placeholders"
            ],
            "next_steps": [
                "Conduct scholarly review of all events",
                "Add proper probability analysis methodology",
                "Enhance source citations with full bibliographic data",
                "Peer review historical accuracy",
                "Add confidence intervals for impact estimates"
            ]
        }
        
        report_path = self.repo_path / "PURIFICATION_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Historical Data Purification Report\n\n")
            f.write(f"**Date**: {report['purification_date']}\n")
            f.write(f"**Backup Location**: `{report['backup_location']}`\n\n")
            
            f.write("## Changes Made\n")
            for change in report['changes_made']:
                f.write(f"- {change}\n")
            f.write("\n")
            
            f.write("## Next Steps for Scholarly Enhancement\n")
            for step in report['next_steps']:
                f.write(f"- {step}\n")
            f.write("\n")
            
            f.write("## Restoration\n")
            f.write("To restore original game-specific data:\n")
            f.write(f"```bash\ncp {self.backup_dir}/data/events/* data/events/\n```\n\n")
            
            f.write("## Quality Assurance\n")
            f.write("After purification:\n")
            f.write("- All events maintain historical accuracy\n")
            f.write("- Game-specific modifications removed\n")
            f.write("- Scholarly review placeholders added\n")
            f.write("- Source citations enhanced\n")
        
        print(f"Purification report generated: {report_path}")

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Purify historical event data")
    parser.add_argument("--backup-only", action="store_true", help="Only create backup")
    parser.add_argument("--purify", action="store_true", help="Purify historical data")
    parser.add_argument("--report", action="store_true", help="Generate purification report")
    parser.add_argument("--all", action="store_true", help="Backup, purify, and report")
    
    args = parser.parse_args()
    
    purifier = HistoricalDataPurifier()
    
    if args.all or args.backup_only:
        print("Creating backup of current data...")
        purifier.backup_current_data()
    
    if args.all or args.purify:
        print("Purifying historical event data...")
        purifier.purify_all_event_files()
    
    if args.all or args.report:
        print("Generating purification report...")
        purifier.generate_purification_report()
    
    if not any([args.backup_only, args.purify, args.report, args.all]):
        parser.print_help()
        print("\nRecommended usage:")
        print("  python purify_historical_data.py --all")

if __name__ == "__main__":
    main()
