#!/usr/bin/env python3
"""
ASCII-ONLY Setup Script for P(Doom) Historical Events Database
Strict ASCII enforcement for agent-based development
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any

def ensure_ascii_only(text: str, filename: str = "unknown") -> str:
    """Enforce ASCII-only content with automatic fixes"""
    replacements = {
        '\u2018': "'",   # Left single quote
        '\u2019': "'",   # Right single quote  
        '\u201c': '"',   # Left double quote
        '\u201d': '"',   # Right double quote
        '\u2013': '-',   # En dash
        '\u2014': '--',  # Em dash
        '\u00a0': ' ',   # Non-breaking space
        '\u2026': '...',  # Ellipsis
    }
    
    for unicode_char, ascii_replacement in replacements.items():
        if unicode_char in text:
            text = text.replace(unicode_char, ascii_replacement)
            print(f"ASCII-FIX: Replaced Unicode in {filename}")
    
    # Remove any remaining non-ASCII
    clean_text = ''.join(char if ord(char) <= 127 else '?' for char in text)
    return clean_text

def create_directories():
    """Create project structure"""
    dirs = [
        "data/events",
        "data/sources", 
        "data/metadata",
        "docs/events",
        "tests/events"
    ]
    
    for directory in dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created: {directory}")

def validate_imports():
    """Test that our event modules work"""
    try:
        from game_integration_helpers import ALL_HISTORICAL_EVENTS, get_event_summary_stats
        
        print("Import validation: SUCCESS")
        
        stats = get_event_summary_stats()
        print(f"Total events: {stats['total_events']}")
        print(f"Legendary events: {stats['legendary_events']}")
        print(f"Year range: {stats['year_range']}")
        
        return True
    except Exception as e:
        print(f"Import validation: FAILED - {e}")
        return False

def export_json_data():
    """Export all events to JSON format"""
    try:
        from game_integration_helpers import ALL_HISTORICAL_EVENTS
        
        json_data = {}
        for event_id, event in ALL_HISTORICAL_EVENTS.items():
            json_data[event_id] = {
                "id": event.id,
                "title": event.title,
                "year": event.year,
                "category": event.category.value,
                "description": event.description,
                "impacts": [
                    {
                        "variable": impact.variable.value,
                        "change": impact.change,
                        "condition": impact.condition
                    }
                    for impact in event.impacts
                ],
                "sources": event.sources,
                "tags": event.tags,
                "rarity": event.rarity.value,
                "pdoom_impact": event.pdoom_impact,
                "safety_researcher_reaction": event.safety_researcher_reaction,
                "media_reaction": event.media_reaction
            }
        
        # Write main JSON file (ASCII-only)
        json_str = json.dumps(json_data, indent=2, ensure_ascii=True)
        with open("data/events/historical_events.json", "w", encoding='ascii') as f:
            f.write(json_str)
        
        print(f"Exported {len(json_data)} events to JSON")
        return True
        
    except Exception as e:
        print(f"JSON export failed: {e}")
        return False

def create_integration_guide():
    """Create simple integration guide"""
    guide_content = """# Historical Events Integration Guide

## Quick Start

1. Copy event files to your pdoom1 project:
   - event_data_structures.py
   - *_events.py files  
   - game_integration_helpers.py

2. Import in your game:
```python
from game_integration_helpers import get_weighted_random_event, apply_event_to_game_state

# In your game loop:
event = get_weighted_random_event(game_state, current_year)
if event:
    new_state = apply_event_to_game_state(event, game_state)
```

3. Game state variables needed:
   - cash, reputation, research, papers
   - ethics_risk, stress, burnout_risk
   - technical_debt, media_reputation
   - vibey_doom (main P(Doom) estimate)

## Event Categories

- Organizational Crisis: Company drama, board fights
- Technical Breakthroughs: AI capabilities that increase doom
- Funding Catastrophes: Money problems, crypto crashes
- Institutional Decay: Safety orgs losing focus

## Key Features

- 28+ historical events (2016-2025)
- 4 legendary doom-increasing events
- Dynamic probability based on game state
- Event chains (one event triggers others)
- Real sources and documented impacts

## ASCII-Only Protocol

ALL text content is ASCII-only (0-127 characters).
No Unicode quotes, em-dashes, or special characters.
This ensures agent compatibility and cross-platform reliability.
"""

    # Ensure ASCII compliance
    clean_guide = ensure_ascii_only(guide_content, "integration_guide.md")
    
    with open("docs/events/integration_guide.md", "w", encoding='ascii') as f:
        f.write(clean_guide)
    
    print("Created integration guide")

def create_readme():
    """Create ASCII-only README"""
    readme_content = """# P(Doom) Historical Events Database

Real-world AI safety events for the P(Doom) strategy game.

## Overview

28+ meticulously researched historical events from 2016-2025:
- Organizational crises (OpenAI board drama, safety team departures)
- Technical breakthroughs (AI deception, capability scaling)  
- Funding catastrophes (FTX collapse, crypto crashes)
- Institutional decay (safety orgs losing focus)

## Key Events

### Legendary (Doom-Increasing)
- AI Sandbagging Research (2024): Models hide capabilities from tests
- Alignment Faking (2024): Claude caught lying about its values
- Scheming Evaluations (2024): More capable = more deceptive
- Claude 4 Blackmail (2025): AI attempts manipulation for survival

### Major Crises
- OpenAI Board Crisis (2023): CEO fired and reinstated in 5 days
- FTX Future Fund Collapse (2022): $32M+ in AI safety grants vanished
- Safety Team Exodus (2024): Researchers quit over capability race

## Features

- Game mechanics: Impacts on cash, reputation, research, doom estimate
- Source attribution: All events linked to original reporting
- Dynamic system: Event probability based on game state
- Event chains: One crisis can trigger others
- ASCII-only: Agent-compatible, no Unicode issues

## Usage

```python
from game_integration_helpers import get_weighted_random_event

event = get_weighted_random_event(game_state, current_year=2024)
# Returns contextually appropriate historical event
```

## Data Quality

- Rigorous sourcing (ArXiv papers, news articles, company statements)
- Impact calibration based on real-world significance
- Ongoing validation and community contributions welcome

## License

MIT License - Free for educational, research, and commercial use.

## ASCII-Only Protocol

This project enforces strict ASCII-only content (characters 0-127):
- No Unicode quotes, em-dashes, or special characters
- Ensures agent compatibility and cross-platform reliability
- All files validated for ASCII compliance
"""

    clean_readme = ensure_ascii_only(readme_content, "README.md")
    
    with open("README.md", "w", encoding='ascii') as f:
        f.write(clean_readme)
    
    print("Created ASCII-compliant README")

def validate_ascii_compliance():
    """Check all files for ASCII compliance"""
    issues = []
    
    # Check Python files
    for py_file in Path(".").glob("*.py"):
        try:
            with open(py_file, 'r', encoding='ascii') as f:
                f.read()
        except UnicodeDecodeError as e:
            issues.append(f"{py_file}: {e}")
    
    # Check markdown files  
    for md_file in Path(".").glob("*.md"):
        try:
            with open(md_file, 'r', encoding='ascii') as f:
                f.read()
        except UnicodeDecodeError as e:
            issues.append(f"{md_file}: {e}")
    
    if issues:
        print("ASCII validation FAILED:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("ASCII validation: PASSED")
        return True

def main():
    """Run complete setup"""
    print("Setting up P(Doom) Historical Events Database")
    print("Enforcing strict ASCII-only protocol")
    print("=" * 50)
    
    # Step 1: Create directories
    print("\n1. Creating directory structure...")
    create_directories()
    
    # Step 2: Validate imports
    print("\n2. Validating event modules...")
    if not validate_imports():
        print("FAILED: Fix import issues before continuing")
        return False
    
    # Step 3: Export data
    print("\n3. Exporting JSON data...")
    if not export_json_data():
        print("FAILED: Could not export event data")
        return False
    
    # Step 4: Create documentation
    print("\n4. Creating documentation...")
    create_integration_guide()
    create_readme()
    
    # Step 5: ASCII validation
    print("\n5. Validating ASCII compliance...")
    if not validate_ascii_compliance():
        print("WARNING: Some files contain non-ASCII characters")
        print("Run the ASCII enforcement tools to fix them")
    
    print("\n" + "=" * 50)
    print("SETUP COMPLETE!")
    print("\nNext steps:")
    print("1. Review docs/events/integration_guide.md")
    print("2. Copy event modules to your pdoom1 project")
    print("3. Add event processing to your game loop")
    print("\nDatabase summary:")
    print("- All content is ASCII-only (agent-compatible)")
    print("- 28+ events covering 2016-2025")
    print("- 4 legendary doom-increasing breakthroughs")
    print("- Real sources and documented game impacts")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
