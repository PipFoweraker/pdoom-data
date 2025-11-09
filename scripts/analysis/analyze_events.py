#!/usr/bin/env python3
"""
Analyze event log files to understand schema, identify issues, and prepare for cleaning.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def analyze_event_files():
    """Analyze all event JSON files."""
    events_dir = Path('data/events')

    all_events = []
    files_analyzed = []
    schema_fields = defaultdict(set)
    issues = []

    # Load all event files
    for event_file in events_dir.glob('*.json'):
        print(f"\nAnalyzing: {event_file.name}")
        files_analyzed.append(event_file.name)

        with open(event_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for event_id, event in data.items():
            event['_source_file'] = event_file.name
            all_events.append(event)

            # Track all fields used
            for field in event.keys():
                schema_fields[field].add(type(event[field]).__name__)

    print(f"\n{'='*80}")
    print(f"ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"\nFiles analyzed: {len(files_analyzed)}")
    print(f"Total events: {len(all_events)}")

    # Schema analysis
    print(f"\n{'='*80}")
    print(f"SCHEMA FIELDS")
    print(f"{'='*80}")
    for field, types in sorted(schema_fields.items()):
        print(f"  {field:30s} {', '.join(types)}")

    # Field consistency analysis
    print(f"\n{'='*80}")
    print(f"FIELD CONSISTENCY")
    print(f"{'='*80}")

    required_fields = ['id', 'title', 'year', 'category', 'description', 'impacts', 'sources', 'tags']
    for field in required_fields:
        count = sum(1 for e in all_events if field in e)
        pct = (count / len(all_events)) * 100
        status = "[OK]" if pct == 100 else "[MISSING]"
        print(f"  {status} {field:20s} {count:3d}/{len(all_events)} ({pct:5.1f}%)")

    # Optional fields
    optional_fields = ['rarity', 'pdoom_impact', 'safety_researcher_reaction', 'media_reaction']
    print(f"\nOptional fields:")
    for field in optional_fields:
        count = sum(1 for e in all_events if field in e)
        pct = (count / len(all_events)) * 100
        print(f"    {field:30s} {count:3d}/{len(all_events)} ({pct:5.1f}%)")

    # Category distribution
    print(f"\n{'='*80}")
    print(f"CATEGORY DISTRIBUTION")
    print(f"{'='*80}")
    categories = Counter(e.get('category') for e in all_events)
    for cat, count in categories.most_common():
        print(f"  {cat:40s} {count:3d}")

    # Year distribution
    print(f"\n{'='*80}")
    print(f"YEAR DISTRIBUTION")
    print(f"{'='*80}")
    years = Counter(e.get('year') for e in all_events)
    for year, count in sorted(years.items()):
        print(f"  {year:4d} {'*' * count} {count}")

    # Rarity distribution
    print(f"\n{'='*80}")
    print(f"RARITY DISTRIBUTION")
    print(f"{'='*80}")
    rarities = Counter(e.get('rarity') for e in all_events)
    for rarity, count in rarities.most_common():
        print(f"  {str(rarity):15s} {count:3d}")

    # Data quality checks
    print(f"\n{'='*80}")
    print(f"DATA QUALITY CHECKS")
    print(f"{'='*80}")

    # Check for missing required fields
    for event in all_events:
        for field in required_fields:
            if field not in event:
                issues.append(f"Missing {field} in {event.get('id', 'UNKNOWN')}")

    # Check for null pdoom_impact vs rarity
    null_pdoom = [e for e in all_events if e.get('pdoom_impact') is None]
    print(f"  Events with null pdoom_impact: {len(null_pdoom)}/{len(all_events)}")

    # Check for empty sources
    empty_sources = [e for e in all_events if not e.get('sources')]
    print(f"  Events with empty sources: {len(empty_sources)}/{len(all_events)}")
    if empty_sources:
        for e in empty_sources:
            issues.append(f"Empty sources in {e.get('id')}")

    # Check for empty tags
    empty_tags = [e for e in all_events if not e.get('tags')]
    print(f"  Events with empty tags: {len(empty_tags)}/{len(all_events)}")
    if empty_tags:
        for e in empty_tags:
            issues.append(f"Empty tags in {e.get('id')}")

    # Check impact structure
    print(f"\n{'='*80}")
    print(f"IMPACT VARIABLE ANALYSIS")
    print(f"{'='*80}")

    all_variables = Counter()
    for event in all_events:
        for impact in event.get('impacts', []):
            all_variables[impact.get('variable')] += 1

    for var, count in all_variables.most_common():
        print(f"  {var:25s} {count:3d}")

    # ASCII compliance check
    print(f"\n{'='*80}")
    print(f"ASCII COMPLIANCE")
    print(f"{'='*80}")

    non_ascii_events = []
    for event in all_events:
        event_str = json.dumps(event)
        if not event_str.isascii():
            non_ascii_chars = [c for c in event_str if ord(c) > 127]
            non_ascii_events.append({
                'id': event.get('id'),
                'chars': set(non_ascii_chars)
            })

    if non_ascii_events:
        print(f"  [FAIL] {len(non_ascii_events)} events contain non-ASCII characters")
        for e in non_ascii_events[:5]:  # Show first 5
            chars = ''.join(sorted(e['chars']))
            print(f"    {e['id']}: {repr(chars)}")
    else:
        print(f"  [OK] All events are ASCII-compliant")

    # Issues summary
    print(f"\n{'='*80}")
    print(f"ISSUES FOUND: {len(issues)}")
    print(f"{'='*80}")
    if issues:
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
    else:
        print("  [OK] No critical issues found")

    return all_events, issues

if __name__ == '__main__':
    events, issues = analyze_event_files()
    print(f"\n\nAnalysis complete. Found {len(events)} events with {len(issues)} issues.")
