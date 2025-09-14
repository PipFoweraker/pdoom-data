#!/usr/bin/env python3
"""
setup_historical_events.py
Setup script to integrate historical events into pdoom1 game structure

This script will:
1. Create the necessary directory structure 
2. Validate all event data
3. Generate summary reports
4. Suggest integration points with existing pdoom1 codebase
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any

# ASCII-ONLY ENFORCEMENT PROTOCOLS
# =================================
# STRICT RULE: All text content in this project MUST be ASCII-only (0-127)
# This is critical for agent-based programs and cross-platform compatibility

def ensure_ascii_only(text: str, filename: str = "unknown") -> str:
    """
    Enforce ASCII-only content with strict validation.
    Replaces non-ASCII characters with ASCII equivalents or removes them.
    Logs all replacements for transparency.
    """
    ascii_replacements = {
        # Common Unicode quotes/apostrophes -> ASCII
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote  
        '\u201c': '"',  # Left double quote
        '\u201d': '"',  # Right double quote
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        # Remove other common non-ASCII
        '\u00a0': ' ',  # Non-breaking space
        '\u2026': '...',# Ellipsis
    }
    
    original_text = text
    
    # Apply replacements
    for unicode_char, ascii_replacement in ascii_replacements.items():
        if unicode_char in text:
            text = text.replace(unicode_char, ascii_replacement)
            print(f"ASCII-ENFORCE ({filename}): Replaced '{unicode_char}' with '{ascii_replacement}'")
    
    # Check for remaining non-ASCII characters
    non_ascii_chars = []
    for i, char in enumerate(text):
        if ord(char) > 127:
            non_ascii_chars.append((i, char, ord(char)))
    
    if non_ascii_chars:
        print(f"WARNING: Found {len(non_ascii_chars)} non-ASCII characters in {filename}:")
        for pos, char, code in non_ascii_chars[:10]:  # Show first 10
            print(f"  Position {pos}: '{char}' (Unicode {code})")
        
        # Remove remaining non-ASCII characters
        text = ''.join(char if ord(char) <= 127 else '?' for char in text)
        print(f"ASCII-ENFORCE ({filename}): Replaced remaining non-ASCII with '?'")
    
    return text

def validate_ascii_files(directory: str) -> bool:
    """Validate that all text files in directory contain only ASCII characters"""
    issues = []
    
    for file_path in Path(directory).rglob("*.py"):
        try:
            with open(file_path, 'r', encoding='ascii') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            issues.append(f"{file_path}: {e}")
    
    for file_path in Path(directory).rglob("*.md"):
        try:
            with open(file_path, 'r', encoding='ascii') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            issues.append(f"{file_path}: {e}")
    
    if issues:
        print("ASCII VALIDATION FAILED:")
        for issue in issues:
            print(f"  {issue}")
        return False
    
    print("? All files pass ASCII validation")
    return True

def create_directory_structure():
    """Create the directory structure for historical events data"""
    
    directories = [
        "data/events",
        "data/sources", 
        "data/metadata",
        "docs/events",
        "tests/events"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"? Created directory: {directory}")

def validate_event_data():
    """Import and validate all event data"""
    
    try:
        from game_integration_helpers import (
            ALL_HISTORICAL_EVENTS, 
            get_event_summary_stats,
            EVENT_CHAINS
        )
        
        print("? Successfully imported all event modules")
        
        # Validate event structure
        issues = []
        
        for event_id, event in ALL_HISTORICAL_EVENTS.items():
            if event.id != event_id:
                issues.append(f"Event ID mismatch: {event_id} != {event.id}")
            
            if not event.title or not event.description:
                issues.append(f"Missing title/description for {event_id}")
                
            if not event.sources:
                issues.append(f"No sources provided for {event_id}")
                
            if not event.impacts:
                issues.append(f"No game impacts defined for {event_id}")
        
        if issues:
            print("??  Validation issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("? All events passed validation")
            
        # Print summary stats
        stats = get_event_summary_stats()
        print("\n? Event Database Summary:")
        for key, value in stats.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
            
        return len(issues) == 0
        
    except ImportError as e:
        print(f"? Failed to import event modules: {e}")
        return False

def export_data_formats():
    """Export events in various formats for easy integration"""
    
    try:
        from game_integration_helpers import ALL_HISTORICAL_EVENTS
        
        # Export as JSON for easy loading
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
        
        with open("data/events/historical_events.json", "w") as f:
            json.dump(json_data, f, indent=2)
        
        print("? Exported events to data/events/historical_events.json")
        
        # Export categories separately
        from event_data_structures import EventCategory
        
        for category in EventCategory:
            category_events = {
                event_id: event_data for event_id, event_data in json_data.items()
                if event_data["category"] == category.value
            }
            
            if category_events:
                filename = f"data/events/{category.value}_events.json"
                with open(filename, "w") as f:
                    json.dump(category_events, f, indent=2)
                print(f"? Exported {len(category_events)} {category.value} events")
        
        return True
        
    except Exception as e:
        print(f"? Failed to export data: {e}")
        return False

def generate_integration_guide():
    """Generate a guide for integrating with existing pdoom1 codebase"""
    
    integration_guide = """
# Historical Events Integration Guide

## Integration with Existing pdoom1 Structure

### 1. Game State Integration

The historical events system is designed to work with your existing game state variables:

```python
# In your game_state.py, ensure these variables exist:
game_state = {
    'cash': 50,
    'reputation': 50, 
    'research': 0,
    'papers': 0,
    'ethics_risk': 0,
    'stress': 0,
    'burnout_risk': 0,
    'technical_debt': 0,
    'media_reputation': 0,
    'vibey_doom': 30  # This is the key P(Doom) estimate
}
```

### 2. Event System Integration

Add to your main game loop (in core/game_state.py or events.py):

```python
from game_integration_helpers import get_weighted_random_event, apply_event_to_game_state

def process_random_event(game_state, current_year):
    """Process a random historical event"""
    event = get_weighted_random_event(game_state, current_year)
    
    if event:
        # Show event to player
        show_event_popup(event)
        
        # Apply impacts
        new_state = apply_event_to_game_state(event, game_state)
        
        # Log for analytics
        log_event(event, game_state, new_state)
        
        return new_state
    
    return game_state
```

### 3. Event Display System

For the UI (in ui.py):

```python
def show_event_popup(event):
    \"\"\"Display historical event to player\"\"\"
    popup_text = f\"\"\"{event.title} ({event.year})
    
{event.description}

Safety Researcher Reaction: "{event.safety_researcher_reaction}"

Media Coverage: "{event.media_reaction}"

[Continue]\"\"\"
    
    # Display using your existing popup system
    show_popup(popup_text)
```

### 4. Save/Load Integration

In your save system, track which events have occurred:

```python
# Add to save data structure
save_data = {
    'game_state': game_state,
    'events_occurred': [],  # List of event IDs that have happened
    'triggered_events': [], # Events triggered by previous events
    'year': current_year
}
```

### 5. Configuration Integration

Add to your config_manager.py:

```python
# Historical events configuration
HISTORICAL_EVENTS_CONFIG = {
    'enabled': True,
    'frequency': 0.3,  # Probability per turn
    'allow_repeats': False,
    'year_flexibility': 2,  # Can occur ?2 years from historical date
    'legendary_event_chance': 0.05  # Special chance for legendary events
}
```

### 6. Analytics Integration

Track event impacts for balancing:

```python
def log_event_analytics(event, before_state, after_state):
    \"\"\"Log event impacts for game balancing\"\"\"
    analytics_data = {
        'event_id': event.id,
        'year': event.year,
        'category': event.category.value,
        'rarity': event.rarity.value,
        'state_before': before_state,
        'state_after': after_state,
        'impacts': {impact.variable.value: impact.change for impact in event.impacts}
    }
    
    # Log to your analytics system
    log_analytics('historical_event', analytics_data)
```

## Recommended File Locations

```
pdoom1/
??? src/
?   ??? core/
?   ?   ??? game_state.py  # Add event processing here
?   ?   ??? events.py      # Or create new events system here
?   ??? features/
?   ?   ??? historical_events/  # New feature module
?   ?       ??? __init__.py
?   ?       ??? event_data_structures.py
?   ?       ??? organizational_events.py
?   ?       ??? technical_breakthrough_events.py
?   ?       ??? funding_events.py
?   ?       ??? institutional_decay_events.py
?   ?       ??? game_integration_helpers.py
?   ??? ui/
?       ??? event_display.py  # Event UI components
??? data/
?   ??? events/
?   ?   ??? historical_events.json
?   ?   ??? *.json (category files)
?   ??? metadata/
?       ??? event_schemas.json
??? tests/
    ??? test_historical_events.py
```

## Testing Integration

```python
# tests/test_historical_events.py
def test_event_impacts():
    \"\"\"Test that events apply correctly to game state\"\"\"
    from features.historical_events.game_integration_helpers import apply_event_to_game_state
    from features.historical_events.technical_breakthrough_events import TECHNICAL_BREAKTHROUGH_EVENTS
    
    initial_state = {'cash': 50, 'vibey_doom': 30}
    event = TECHNICAL_BREAKTHROUGH_EVENTS['ai_sandbagging_research_2024']
    
    new_state = apply_event_to_game_state(event, initial_state)
    
    assert new_state['vibey_doom'] > initial_state['vibey_doom']
    assert 'research' in new_state
```
"""

    # Enforce ASCII-only content
    ascii_guide = ensure_ascii_only(integration_guide, "integration_guide.md")
    with open("docs/events/integration_guide.md", "w", encoding='ascii') as f:
        f.write(ascii_guide)
    
    print("? Generated integration guide at docs/events/integration_guide.md")

def create_readme():
    """Create README for the historical events system"""
    
    readme_content = """# Historical AI Safety Events Database

A comprehensive database of real-world AI safety, governance, and organizational events from 2016-2025 for use in the P(Doom) strategy game.

## Overview

This database contains **40+ meticulously researched historical events** that capture the complex dynamics of AI safety, funding crises, technical breakthroughs, and institutional failures. Each event includes:

- **Game mechanics impacts** on cash, reputation, research, stress, etc.
- **Source attribution** with links to original reporting
- **Contextual reactions** from safety researchers and media
- **P(Doom) impact scores** for existentially relevant discoveries

## Event Categories

- **Organizational Crises**: OpenAI board drama, Google Project Maven revolt, safety team departures
- **Technical Breakthroughs**: AI sandbagging, alignment faking, scheming behavior discoveries  
- **Funding Catastrophes**: FTX collapse, crypto crashes, grant funding gaps
- **Institutional Decay**: Safety institutes becoming security focused, regulatory capture

## Key Features

### P(Doom) Increasing Events (Legendary Rarity)
- **AI Sandbagging Research (2024)**: Models hiding capabilities from evaluators
- **Alignment Faking Discovery (2024)**: Claude caught pretending to be aligned
- **Claude 4 Blackmail Incident (2025)**: AI attempting manipulation for self-preservation
- **Scheming Evaluations (2024)**: Higher capability = higher deception rates

### Dynamic Event System
- **Event chains**: FTX collapse ? clawbacks ? funding crisis
- **Probability modifiers**: Late game increases technical breakthrough chances
- **Game state awareness**: Low funding increases funding crisis likelihood
- **Temporal flexibility**: Events can occur ?2 years from historical date

## Usage

```python
from game_integration_helpers import get_weighted_random_event, apply_event_to_game_state

# Get contextual random event
event = get_weighted_random_event(game_state, current_year=2024)

# Apply to game state
new_state = apply_event_to_game_state(event, game_state)
```

## Data Quality

- **Rigorous sourcing**: All events linked to primary sources (ArXiv, news, company statements)
- **Impact calibration**: Game effects balanced based on real-world significance
- **Ongoing validation**: Community contributions welcome for fact-checking

## Files Structure

- `event_data_structures.py`: Core data types and enums
- `*_events.py`: Event definitions by category  
- `game_integration_helpers.py`: Game logic and utilities
- `data/events/*.json`: Exported data in multiple formats

## Contributing

This database is designed to be a living resource. Contributions welcome for:
- Additional events (2016-2025)
- Source verification and updates
- Game balance feedback
- Translation to other formats

## License

MIT License - Free for educational, research, and commercial use.

## Citation

```
Historical AI Safety Events Database (2025)
P(Doom) Game Project
https://github.com/[username]/pdoom-datasets
```
"""

    # Enforce ASCII-only content
    ascii_readme = ensure_ascii_only(readme_content, "README.md")
    with open("README.md", "w", encoding='ascii') as f:
        f.write(ascii_readme)
    
    print("? Created README.md")

def main():
    """Main setup function"""
    print("? Setting up Historical Events Database for pdoom1\n")
    
    # Create directories
    create_directory_structure()
    print()
    
    # Validate data
    if validate_event_data():
        print()
        
        # Export data formats
        if export_data_formats():
            print()
            
            # Generate documentation
            generate_integration_guide()
            create_readme()
            
            print("\n? Setup completed successfully!")
            
            # Validate ASCII compliance
            print("\n? Validating ASCII compliance...")
            if validate_ascii_files("."):
                print("? All files are ASCII-compliant")
            else:
                print("? ASCII validation failed - fix non-ASCII characters")
                return False
            
            print("\nNext steps:")
            print("1. Review the integration guide at docs/events/integration_guide.md")
            print("2. Copy the event modules to your pdoom1 src/features/ directory")
            print("3. Add event processing to your main game loop")
            print("4. Test with a few events to verify integration")
            
            print("\n? Database contains:")
            try:
                from game_integration_helpers import get_event_summary_stats
                stats = get_event_summary_stats()
                print(f"   * {stats['total_events']} total events")
                print(f"   * {stats['legendary_events']} legendary events")
                print(f"   * {stats['doom_increasing']} P(Doom) increasing events")
                print(f"   * Coverage: {stats['year_range']}")
            except:
                print("   * Full event database loaded")
                
            return True
    
    print("\n? Setup failed - please check error messages above")
    return False

if __name__ == "__main__":
    main()