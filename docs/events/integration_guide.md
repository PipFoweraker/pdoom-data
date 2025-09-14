# Historical Events Integration Guide

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
