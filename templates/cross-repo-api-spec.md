# Cross-Repo API Specification

# Standardized interfaces for pdoom-data, pdoom-website, and pdoom1

## API Overview

This document defines the standardized APIs and data contracts between the three P(Doom) repositories to ensure seamless integration and agent/LLM navigation.

## Data Schema Versioning

### Current Version: 1.0.0
- Semantic versioning (MAJOR.MINOR.PATCH)
- Breaking changes increment MAJOR
- New features increment MINOR  
- Bug fixes increment PATCH

### Version Headers
All API responses include version information:
```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-09-14T12:00:00Z",
  "repository": "pdoom-data"
}
```

## Core Data Contracts

### 1. Historical Event Schema
```typescript
interface HistoricalEvent {
  id: string;                    // Unique identifier
  title: string;                 // Human-readable title
  year: number;                  // Year event occurred
  category: EventCategory;       // Event category enum
  description: string;           // ASCII-only description
  impacts: GameImpact[];         // Effects on game variables
  sources: string[];             // Source URLs
  tags: string[];               // Searchable tags
  rarity: Rarity;               // Common, uncommon, rare, legendary
  pdoom_impact?: number;         // Direct P(Doom) impact (0-10)
  safety_researcher_reaction?: string;  // Researcher quote
  media_reaction?: string;       // Media coverage quote
  triggers?: string[];           // Events this can trigger
  probability_modifier?: string; // Conditions affecting likelihood
}

enum EventCategory {
  ORGANIZATIONAL_CRISIS = "organizational_crisis",
  FUNDING_CATASTROPHE = "funding_catastrophe", 
  TECHNICAL_FAILURE = "technical_failure",
  REGULATORY_POLICY = "regulatory_policy",
  MEDIA_DISASTER = "media_disaster",
  SAFETY_RESEARCH = "safety_research",
  CORPORATE_ETHICS = "corporate_ethics",
  INTERNATIONAL_COMPETITION = "international_competition",
  ACADEMIC_COMMUNITY = "academic_community",
  INSTITUTIONAL_DECAY = "institutional_decay",
  TECHNICAL_RESEARCH_BREAKTHROUGH = "technical_research_breakthrough",
  WHISTLEBLOWING = "whistleblowing"
}

enum Rarity {
  COMMON = "common",
  UNCOMMON = "uncommon", 
  RARE = "rare",
  LEGENDARY = "legendary"
}
```

### 2. Game Impact Schema
```typescript
interface GameImpact {
  variable: ImpactType;          // Game variable affected
  change: number;                // Positive or negative change
  condition?: string;            // Optional condition for application
}

enum ImpactType {
  CASH = "cash",
  REPUTATION = "reputation",
  RESEARCH = "research", 
  PAPERS = "papers",
  ETHICS_RISK = "ethics_risk",
  STRESS = "stress",
  BURNOUT_RISK = "burnout_risk",
  TECHNICAL_DEBT = "technical_debt",
  MEDIA_REPUTATION = "media_reputation",
  VIBEY_DOOM = "vibey_doom"
}
```

### 3. Game State Schema
```typescript
interface GameState {
  cash: number;                  // 0-100
  reputation: number;            // 0-100
  research: number;              // 0-100+
  papers: number;                // 0-100+
  ethics_risk: number;           // 0-100
  stress: number;                // 0-100
  burnout_risk: number;          // 0-100
  technical_debt: number;        // 0-100
  media_reputation: number;      // -100 to 100
  vibey_doom: number;            // 0-100 (main P(Doom) estimate)
}
```

## pdoom-data API Endpoints

### Static JSON Exports (Primary Method)

#### GET /data/events/historical_events.json
Returns complete event database
```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-09-14T12:00:00Z",
  "event_count": 28,
  "events": {
    "ai_sandbagging_research_2024": { ...event_object },
    "anthropic_alignment_faking_2024": { ...event_object }
  }
}
```

#### GET /data/events/{category}_events.json
Returns events by category
- organizational_crisis_events.json
- technical_research_breakthrough_events.json
- funding_catastrophe_events.json
- institutional_decay_events.json

#### GET /data/metadata/schema.json
Returns current schema version and structure
```json
{
  "version": "1.0.0",
  "event_schema": { ...TypeScript_interfaces },
  "breaking_changes": [],
  "migration_guide": "docs/migrations/v1.0.0.md"
}
```

### Python Package Interface (For pdoom1)

#### Installation
```bash
# Option 1: Direct import (copy files)
cp -r pdoom-data/src/pdoom_data/ pdoom1/src/

# Option 2: Git submodule
git submodule add https://github.com/PipFoweraker/pdoom-data.git data
```

#### Usage
```python
from pdoom_data.game_integration_helpers import (
    ALL_HISTORICAL_EVENTS,
    get_weighted_random_event,
    apply_event_to_game_state,
    format_event_for_display
)

# Get contextual event
event = get_weighted_random_event(game_state, current_year=2024)

# Apply to game state
new_state = apply_event_to_game_state(event, game_state)
```

## pdoom-website API Integration

### Data Consumption Patterns

#### 1. Build-Time Data Fetching
```javascript
// gatsby-node.js or next.config.js
exports.onPreBuild = async () => {
  const response = await fetch('https://raw.githubusercontent.com/PipFoweraker/pdoom-data/main/data/events/historical_events.json');
  const events = await response.json();
  
  // Generate static pages for each event
  events.forEach(event => {
    createPage({
      path: `/events/${event.id}`,
      component: require.resolve('./src/templates/event-page.js'),
      context: { event }
    });
  });
};
```

#### 2. Runtime Data Loading
```javascript
// React component
export function EventTimeline() {
  const [events, setEvents] = useState([]);
  
  useEffect(() => {
    fetch('/data/events/historical_events.json')
      .then(response => response.json())
      .then(data => setEvents(Object.values(data.events)));
  }, []);
  
  return <div>{/* render timeline */}</div>;
}
```

#### 3. API Proxy Endpoints
```javascript
// pages/api/events/[category].js
export default async function handler(req, res) {
  const { category } = req.query;
  
  try {
    const response = await fetch(
      `https://raw.githubusercontent.com/PipFoweraker/pdoom-data/main/data/events/${category}_events.json`
    );
    const data = await response.json();
    
    res.setHeader('Cache-Control', 's-maxage=3600'); // 1 hour cache
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch events' });
  }
}
```

## pdoom1 Game Integration

### Event System Interface

#### 1. Event Manager Integration
```python
# src/systems/event_system.py
class EventSystem:
    def __init__(self, game_config):
        # Import pdoom-data helpers
        from pdoom_data.game_integration_helpers import (
            ALL_HISTORICAL_EVENTS,
            get_weighted_random_event
        )
        
        self.events_db = ALL_HISTORICAL_EVENTS
        self.get_random_event = get_weighted_random_event
        self.occurred_events = []
    
    def process_turn(self, game_state, current_year):
        event = self.get_random_event(
            game_state, 
            current_year,
            exclude_ids=self.occurred_events
        )
        
        if event:
            return self.apply_event(event, game_state)
        
        return None
```

#### 2. Save Data Integration
```python
# Save format includes event history
save_data = {
    'game_state': { ...game_variables },
    'current_year': 2024,
    'events': {
        'occurred': ['ftx_future_fund_collapse_2022', 'openai_board_crisis_2023'],
        'triggered': ['cais_ftx_clawback_2023'],
        'analytics': {
            'total_events': 15,
            'legendary_count': 2,
            'average_doom_impact': 12.5
        }
    },
    'schema_version': '1.0.0'
}
```

## Cross-Repo Synchronization

### 1. Webhook Integration
```yaml
# .github/workflows/sync-repos.yml
name: Cross-Repo Sync
on:
  push:
    paths: ['data/events/*.json']

jobs:
  notify-website:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger website rebuild
        run: |
          curl -X POST "${{ secrets.WEBSITE_DEPLOY_HOOK }}" \
            -H "Content-Type: application/json" \
            -d '{"ref": "main", "source": "pdoom-data-update"}'
  
  notify-game:
    runs-on: ubuntu-latest
    steps:
      - name: Create PR in game repo
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.PAT }}
          repository: PipFoweraker/pdoom1
          event-type: data-update
          client-payload: '{"schema_version": "1.0.0", "change_type": "events"}'
```

### 2. Version Compatibility Matrix
```json
{
  "compatibility_matrix": {
    "pdoom-data": {
      "1.0.0": {
        "pdoom-website": ["1.0.0", "1.1.0"],
        "pdoom1": ["1.0.0", "1.0.1", "1.1.0"]
      }
    }
  },
  "migration_paths": {
    "0.9.x": "docs/migrations/v0.9-to-v1.0.md",
    "1.0.x": "docs/migrations/v1.0-to-v1.1.md"
  }
}
```

## Error Handling and Fallbacks

### 1. Schema Validation
```python
def validate_event_schema(event_data):
    required_fields = ['id', 'title', 'year', 'category', 'description']
    
    for field in required_fields:
        if field not in event_data:
            raise ValueError(f"Missing required field: {field}")
    
    # ASCII validation
    for text_field in ['title', 'description']:
        if not all(ord(c) <= 127 for c in event_data[text_field]):
            raise ValueError(f"Non-ASCII characters in {text_field}")
    
    return True
```

### 2. Graceful Degradation
```javascript
// Website fallback behavior
async function loadEvents() {
  try {
    // Try primary data source
    return await fetch('/data/events/historical_events.json');
  } catch (primary_error) {
    try {
      // Fallback to GitHub raw
      return await fetch('https://raw.githubusercontent.com/PipFoweraker/pdoom-data/main/data/events/historical_events.json');
    } catch (fallback_error) {
      // Return cached/static data
      return await import('./fallback-events.json');
    }
  }
}
```

## Development and Testing

### 1. Integration Testing
```python
# tests/test_cross_repo_integration.py
def test_schema_compatibility():
    """Test that schemas are compatible across repos"""
    from pdoom_data.event_data_structures import HistoricalEvent
    
    # Load sample event
    sample_event = load_sample_event()
    
    # Test website serialization
    json_data = json.dumps(sample_event.__dict__)
    assert validate_json_schema(json_data)
    
    # Test game integration  
    game_event = HistoricalEvent(**json.loads(json_data))
    assert game_event.id == sample_event.id
```

### 2. API Contract Testing
```bash
#!/bin/bash
# scripts/test-api-contracts.sh

echo "Testing API contracts..."

# Test JSON exports exist and are valid
curl -s "https://raw.githubusercontent.com/PipFoweraker/pdoom-data/main/data/events/historical_events.json" | jq . > /dev/null
echo "[OK] Historical events JSON is valid"

# Test schema compatibility
python -c "import json; data=json.load(open('data/events/historical_events.json')); assert 'schema_version' in data"
echo "[OK] Schema version present"

# Test ASCII compliance
python validate_ascii.py data/events/*.json
echo "[OK] All JSON files are ASCII-compliant"
```

This API specification ensures:
- Consistent data contracts across all repos
- Version compatibility and migration paths
- Error handling and fallback strategies
- Automated testing and validation
- Agent/LLM-friendly documentation
