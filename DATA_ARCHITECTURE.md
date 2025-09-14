# DATA ARCHITECTURE: PURE HISTORY vs GAME ADAPTATIONS

## ARCHITECTURAL PRINCIPLE
**Separation of Concerns**: Pure historical facts vs. game-specific adaptations

## CURRENT ARCHITECTURE DECISION

### pdoom-data (This Repo) = PURE HISTORICAL FACTS
**Purpose**: Authoritative source of unmodified historical AI safety events
**Principles**:
- Scholarly accuracy and integrity
- Useful to other researchers
- Real probability estimates from actual analysis
- Unmodified source citations
- No game-specific simplifications or ratings

**Content Standards**:
- Historical accuracy is paramount
- All claims must be sourced
- Probability estimates based on real analysis
- Events described as they actually occurred
- Suitable for academic or research use

### pdoom1-data (Game Repo's Data) = GAME ADAPTATIONS
**Purpose**: Game-playable versions adapted from pure historical data
**Principles**:
- Gameplay balance and fun
- Simplified for player comprehension
- Game-specific ratings and mechanics
- Modified for narrative flow
- Optimized for player engagement

**Transformation Process**:
```
pdoom-data (Pure History) 
    |
    | [Fetch and Transform]
    |
    v
pdoom1-data (Game Version)
```

## IMPLEMENTATION STRATEGY

### 1. Keep pdoom-data PURE
**What stays in pdoom-data:**
- Original event descriptions
- Real dates and actual participants
- Authentic source citations
- Scholarly probability estimates
- Unmodified historical context
- Research-grade documentation

**What gets removed from pdoom-data:**
- `game_impacts` arrays (these are game-specific)
- `rarity` classifications (game mechanic)
- Simplified/dramatized descriptions
- Player-facing language
- Game balance considerations

### 2. Create Transformation Pipeline
**In pdoom1 game engine:**
```python
# pdoom1/src/data/historical_adapter.py
class HistoricalEventAdapter:
    def fetch_from_pdoom_data(self):
        """Fetch pure historical events from pdoom-data repo"""
        # Load from JSON exports or API
        
    def transform_for_gameplay(self, historical_event):
        """Transform pure history into game-playable format"""
        # Add game mechanics
        # Simplify language for players
        # Add rarity classifications
        # Balance for gameplay
        
    def generate_game_impacts(self, event):
        """Generate game-specific impact arrays"""
        # Convert historical significance to game variables
```

### 3. Proposed File Structure Changes

#### pdoom-data (Pure History):
```
data/events/
+-- historical_events.json           # PURE historical data
    {
      "event_id": "openai_gpt4_2023",
      "title": "OpenAI Releases GPT-4",
      "date": "2023-03-14",
      "description": "OpenAI announced GPT-4, a large multimodal model...",
      "historical_significance": "Major milestone in AI capability development",
      "probability_impact_analysis": {
        "methodology": "Expert survey of AI researchers",
        "p_doom_change_estimate": "+5% (median estimate)",
        "confidence_interval": "2% to 12%",
        "sample_size": 47,
        "survey_date": "2023-04-15"
      },
      "sources": [
        "https://openai.com/research/gpt-4",
        "https://arxiv.org/abs/2303.08774"
      ],
      "research_notes": "Represents significant capability jump...",
      "related_events": ["openai_chatgpt_2022"],
      "verification_status": "peer_reviewed"
    }
```

#### pdoom1-data (Game Adaptations):
```
data/game_events/
+-- gameplay_events.json             # GAME-ADAPTED versions
    {
      "event_id": "openai_gpt4_2023",
      "title": "GPT-4 Released!",
      "player_description": "A breakthrough AI model shocks the world...",
      "game_impacts": [
        {"variable": "ai_capability", "change": 45},
        {"variable": "public_awareness", "change": 30},
        {"variable": "research_funding", "change": 25}
      ],
      "rarity": "rare",
      "gameplay_weight": 0.8,
      "unlock_conditions": ["year >= 2023", "research_level >= 3"],
      "player_choices": [
        {"text": "Accelerate our research", "effects": {...}},
        {"text": "Focus on safety", "effects": {...}}
      ],
      "based_on_historical_event": "openai_gpt4_2023",
      "adaptation_notes": "Simplified for gameplay, added player agency"
    }
```

## BENEFITS OF THIS ARCHITECTURE

### For Researchers
- **Pure historical accuracy** in pdoom-data
- **Citable source** for academic work  
- **Unbiased probability estimates**
- **Complete source documentation**

### For Game Development
- **Gameplay-optimized** content in pdoom1
- **Player-friendly** language and concepts
- **Balanced mechanics** for fun gameplay
- **Flexible adaptation** without corrupting source data

### For Maintenance
- **Clear separation** of concerns
- **Source of truth** remains pure
- **Game updates** don't affect historical accuracy
- **Multiple games** could use same historical base

## MIGRATION PLAN

### Phase 1: Clean Current Data
```bash
# Remove game-specific elements from historical events
python scripts/purify_historical_data.py

# This removes:
# - game_impacts arrays  
# - rarity classifications
# - game-specific descriptions
```

### Phase 2: Enhanced Historical Documentation
```bash
# Add scholarly elements to historical events
python scripts/enhance_historical_accuracy.py

# This adds:
# - Detailed source citations
# - Probability analysis methodology
# - Research confidence levels
# - Peer review status
```

### Phase 3: Create Game Adapter
```python
# In pdoom1 repository
class PDoomDataAdapter:
    def sync_from_historical_repo(self):
        # Fetch latest historical events
        
    def generate_game_versions(self):
        # Transform for gameplay
        
    def maintain_traceability(self):
        # Link game events to historical sources
```

## VALIDATION STANDARDS

### pdoom-data Quality Standards:
- All events must have primary sources
- Probability estimates must include methodology
- Historical accuracy verified by multiple sources
- Suitable for citation in academic work

### pdoom1-data Quality Standards:
- Balanced for engaging gameplay
- Clear player-facing language
- Consistent game mechanics
- Maintains connection to historical truth

This architecture ensures pdoom-data becomes a valuable resource for AI safety researchers while still enabling rich game content through thoughtful adaptation.
