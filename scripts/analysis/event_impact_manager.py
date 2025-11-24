#!/usr/bin/env python3
"""
Event Impact Manager - Interactive tool for browsing, filtering, and customizing
event impacts for p(Doom)1 game integration.

Features:
- Browse events with filtering by category, year, impact variables
- View event impact profiles and metadata
- Add custom metadata (impact_level, game_relevance, etc.) nondestructively
- Export filtered event sets for game integration
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, Counter

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.logger import get_logger

logger = get_logger('event_impact_manager')


class EventImpactManager:
    """Manage and customize event impacts for game integration."""

    def __init__(self, events_path: Path, metadata_path: Optional[Path] = None):
        """
        Initialize Event Impact Manager.

        Args:
            events_path: Path to events JSON file
            metadata_path: Path to custom metadata JSON (created if doesn't exist)
        """
        self.events_path = Path(events_path)
        self.metadata_path = metadata_path or self.events_path.parent / f"{self.events_path.stem}_metadata.json"

        self.events = self._load_events()
        self.metadata = self._load_metadata()

        logger.info(f"Loaded {len(self.events)} events from {events_path}")
        logger.info(f"Metadata file: {self.metadata_path}")

    def _load_events(self) -> Dict[str, Any]:
        """Load events from JSON file."""
        with open(self.events_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both dict and array formats
        if isinstance(data, list):
            return {event['id']: event for event in data}
        return data

    def _load_metadata(self) -> Dict[str, Any]:
        """Load custom metadata (nondestructive overlay)."""
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_metadata(self):
        """Save custom metadata to file."""
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=True)
        logger.info(f"Saved metadata for {len(self.metadata)} events")

    def get_impact_variables(self) -> Counter:
        """Get all impact variables used across events."""
        variables = Counter()
        for event in self.events.values():
            for impact in event.get('impacts', []):
                var = impact.get('variable')
                if var:
                    variables[var] += 1
        return variables

    def get_categories(self) -> Counter:
        """Get all event categories."""
        return Counter(event.get('category') for event in self.events.values())

    def get_year_range(self) -> tuple:
        """Get min and max years."""
        years = [event.get('year') for event in self.events.values() if event.get('year')]
        return (min(years), max(years)) if years else (None, None)

    def filter_events(
        self,
        categories: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        impact_variables: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        has_metadata: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Filter events based on criteria.

        Args:
            categories: Filter by event categories
            year_min: Minimum year
            year_max: Maximum year
            impact_variables: Events that affect these variables
            tags: Events with any of these tags
            has_metadata: Filter by whether event has custom metadata

        Returns:
            Filtered events dict
        """
        filtered = {}

        for event_id, event in self.events.items():
            # Category filter
            if categories and event.get('category') not in categories:
                continue

            # Year filter
            year = event.get('year')
            if year_min and (not year or year < year_min):
                continue
            if year_max and (not year or year > year_max):
                continue

            # Impact variables filter
            if impact_variables:
                event_vars = {imp.get('variable') for imp in event.get('impacts', [])}
                if not any(var in event_vars for var in impact_variables):
                    continue

            # Tags filter
            if tags:
                event_tags = set(event.get('tags', []))
                if not any(tag in event_tags for tag in tags):
                    continue

            # Metadata filter
            if has_metadata is not None:
                has_meta = event_id in self.metadata
                if has_meta != has_metadata:
                    continue

            filtered[event_id] = event

        return filtered

    def print_event_summary(self, event_id: str, show_impacts: bool = True):
        """Print a summary of an event."""
        if event_id not in self.events:
            print(f"Event not found: {event_id}")
            return

        event = self.events[event_id]
        metadata = self.metadata.get(event_id, {})

        print(f"\n{'='*80}")
        print(f"ID: {event_id}")
        print(f"{'='*80}")
        print(f"Title: {event.get('title', 'N/A')}")
        print(f"Year: {event.get('year', 'N/A')}")
        print(f"Category: {event.get('category', 'N/A')}")
        print(f"\nDescription:")
        print(f"  {event.get('description', 'N/A')}")

        if show_impacts and event.get('impacts'):
            print(f"\nImpacts ({len(event['impacts'])}):")
            for imp in event['impacts']:
                var = imp.get('variable', 'unknown')
                change = imp.get('change', 0)
                sign = '+' if change > 0 else ''
                print(f"  {var:20s} {sign}{change:4d}")

        if event.get('tags'):
            print(f"\nTags: {', '.join(event['tags'])}")

        if event.get('sources'):
            print(f"\nSources ({len(event['sources'])}):")
            for src in event['sources'][:3]:
                print(f"  - {src}")

        # Show custom metadata
        if metadata:
            print(f"\nCustom Metadata:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")

    def set_event_metadata(self, event_id: str, key: str, value: Any):
        """Set custom metadata for an event (nondestructive)."""
        if event_id not in self.events:
            logger.error(f"Event not found: {event_id}")
            return False

        if event_id not in self.metadata:
            self.metadata[event_id] = {}

        self.metadata[event_id][key] = value
        logger.info(f"Set {key}={value} for {event_id}")
        return True

    def calculate_impact_score(self, event_id: str) -> float:
        """
        Calculate overall impact score for an event.
        Uses absolute values of all impact changes.
        """
        if event_id not in self.events:
            return 0.0

        event = self.events[event_id]
        total = sum(abs(imp.get('change', 0)) for imp in event.get('impacts', []))
        return total

    def categorize_impact_level(self, event_id: str) -> str:
        """
        Categorize event impact level (Critical/High/Medium/Low).
        Based on impact score thresholds.
        """
        score = self.calculate_impact_score(event_id)

        if score >= 150:
            return 'Critical'
        elif score >= 80:
            return 'High'
        elif score >= 30:
            return 'Medium'
        else:
            return 'Low'

    def auto_tag_impact_levels(self):
        """Automatically tag all events with impact_level metadata."""
        count = 0
        for event_id in self.events.keys():
            impact_level = self.categorize_impact_level(event_id)
            if self.set_event_metadata(event_id, 'impact_level', impact_level):
                count += 1

        logger.info(f"Auto-tagged {count} events with impact_level")
        return count

    def export_filtered_events(
        self,
        output_path: Path,
        filters: Dict[str, Any],
        include_metadata: bool = True
    ):
        """
        Export filtered events to JSON file.

        Args:
            output_path: Output file path
            filters: Filter criteria (same as filter_events)
            include_metadata: Whether to merge custom metadata into events
        """
        filtered = self.filter_events(**filters)

        if include_metadata:
            # Merge metadata into events
            export_data = {}
            for event_id, event in filtered.items():
                merged = event.copy()
                if event_id in self.metadata:
                    merged['_custom_metadata'] = self.metadata[event_id]
                export_data[event_id] = merged
        else:
            export_data = filtered

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=True)

        logger.info(f"Exported {len(export_data)} events to {output_path}")
        return len(export_data)

    def print_statistics(self, filtered_events: Optional[Dict[str, Any]] = None):
        """Print statistics about events."""
        events = filtered_events if filtered_events is not None else self.events

        print(f"\n{'='*80}")
        print(f"EVENT STATISTICS")
        print(f"{'='*80}")
        print(f"Total events: {len(events)}")

        # Categories
        categories = Counter(e.get('category') for e in events.values())
        print(f"\nCategories:")
        for cat, count in categories.most_common():
            print(f"  {cat:40s} {count:4d}")

        # Year distribution
        years = [e.get('year') for e in events.values() if e.get('year')]
        if years:
            print(f"\nYear range: {min(years)} - {max(years)}")

        # Impact variables
        variables = Counter()
        for event in events.values():
            for imp in event.get('impacts', []):
                variables[imp.get('variable')] += 1

        print(f"\nImpact variables (top 10):")
        for var, count in variables.most_common(10):
            print(f"  {var:25s} {count:4d}")

        # Metadata coverage
        with_metadata = sum(1 for eid in events.keys() if eid in self.metadata)
        pct = (with_metadata / len(events) * 100) if events else 0
        print(f"\nEvents with custom metadata: {with_metadata}/{len(events)} ({pct:.1f}%)")


def interactive_browser(manager: EventImpactManager):
    """Interactive command-line browser for events."""
    print("\n" + "="*80)
    print("EVENT IMPACT MANAGER - Interactive Browser")
    print("="*80)
    print("\nCommands:")
    print("  stats              - Show statistics")
    print("  filter             - Filter events")
    print("  list [N]           - List first N events (default 10)")
    print("  show <id>          - Show event details")
    print("  tag-impacts        - Auto-tag all events with impact_level")
    print("  set <id> <key> <value> - Set metadata for event")
    print("  export <path>      - Export current filter to file")
    print("  save               - Save metadata")
    print("  quit               - Exit")

    current_filter = {}

    while True:
        try:
            cmd = input("\n> ").strip()

            if not cmd:
                continue

            parts = cmd.split()
            command = parts[0].lower()

            if command == 'quit':
                break

            elif command == 'stats':
                filtered = manager.filter_events(**current_filter)
                manager.print_statistics(filtered)

            elif command == 'list':
                n = int(parts[1]) if len(parts) > 1 else 10
                filtered = manager.filter_events(**current_filter)
                print(f"\nShowing first {n} events:")
                for i, (event_id, event) in enumerate(list(filtered.items())[:n], 1):
                    impact_level = manager.metadata.get(event_id, {}).get('impact_level', '?')
                    print(f"  {i:3d}. [{impact_level:8s}] {event_id:40s} - {event.get('title', 'N/A')[:60]}")
                print(f"\nTotal filtered: {len(filtered)} events")

            elif command == 'show':
                if len(parts) < 2:
                    print("Usage: show <event_id>")
                else:
                    manager.print_event_summary(parts[1])

            elif command == 'tag-impacts':
                count = manager.auto_tag_impact_levels()
                print(f"Tagged {count} events with impact_level")

            elif command == 'set':
                if len(parts) < 4:
                    print("Usage: set <event_id> <key> <value>")
                else:
                    event_id = parts[1]
                    key = parts[2]
                    value = ' '.join(parts[3:])
                    # Try to parse as JSON
                    try:
                        value = json.loads(value)
                    except:
                        pass
                    manager.set_event_metadata(event_id, key, value)

            elif command == 'export':
                if len(parts) < 2:
                    print("Usage: export <output_path>")
                else:
                    output_path = Path(parts[1])
                    count = manager.export_filtered_events(output_path, current_filter)
                    print(f"Exported {count} events to {output_path}")

            elif command == 'save':
                manager.save_metadata()
                print("Metadata saved")

            elif command == 'filter':
                print("\nFilter options (leave blank to skip):")
                cat_input = input("  Categories (comma-separated): ").strip()
                year_min = input("  Year min: ").strip()
                year_max = input("  Year max: ").strip()

                current_filter = {}
                if cat_input:
                    current_filter['categories'] = [c.strip() for c in cat_input.split(',')]
                if year_min:
                    current_filter['year_min'] = int(year_min)
                if year_max:
                    current_filter['year_max'] = int(year_max)

                filtered = manager.filter_events(**current_filter)
                print(f"\nFilter applied: {len(filtered)} events match")

            else:
                print(f"Unknown command: {command}")

        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Event Impact Manager')
    parser.add_argument('events_file', type=str, help='Path to events JSON file')
    parser.add_argument('--metadata', type=str, help='Path to metadata JSON file (optional)')
    parser.add_argument('--interactive', '-i', action='store_true', help='Launch interactive browser')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--auto-tag', action='store_true', help='Auto-tag all events with impact_level')

    args = parser.parse_args()

    metadata_path = Path(args.metadata) if args.metadata else None
    manager = EventImpactManager(Path(args.events_file), metadata_path)

    if args.stats:
        manager.print_statistics()

    if args.auto_tag:
        manager.auto_tag_impact_levels()
        manager.save_metadata()

    if args.interactive:
        interactive_browser(manager)

    if not (args.interactive or args.stats or args.auto_tag):
        parser.print_help()


if __name__ == '__main__':
    main()
