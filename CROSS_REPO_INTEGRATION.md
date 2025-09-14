# CROSS-REPO INTEGRATION ARCHITECTURE
# pdoom-data <-> pdoom-website <-> pdoom1

## REPOSITORY ECOSYSTEM OVERVIEW

### pdoom-data (Current Repo)
**Purpose**: Historical events database and game content
**Role**: Data source and content management
**Key Assets**:
- 28+ historical AI safety events (2016-2025)
- Game mechanics data (impacts, probabilities)
- JSON exports for easy consumption
- ASCII-only content for agent compatibility

### pdoom-website (Website Repo)
**Purpose**: Public-facing website and documentation
**Likely Role**: Information display and community engagement
**Probable Assets**:
- Event showcases and timelines
- Game information and downloads
- Documentation and guides
- Blog/news updates

### pdoom1 (Game Repo)  
**Purpose**: The actual P(Doom) strategy game
**Likely Role**: Interactive gameplay experience
**Probable Assets**:
- Game engine and mechanics
- UI/UX components
- Save/load systems
- Event processing logic

## INTEGRATION PATTERNS TO IMPLEMENT

### 1. DATA FLOW ARCHITECTURE
```
pdoom-data (Source of Truth)
    |
    |-- JSON Exports --> pdoom-website (Display)
    |
    |-- Event Modules --> pdoom1 (Gameplay)
```

### 2. SHARED DATA FORMATS

#### Event Data Schema (JSON)
```json
{
  "event_id": "ai_sandbagging_research_2024",
  "title": "AI Sandbagging Research Published",
  "year": 2024,
  "category": "technical_research_breakthrough",
  "description": "Models hide capabilities from evaluators",
  "game_impacts": [
    {"variable": "vibey_doom", "change": 30},
    {"variable": "research", "change": 25}
  ],
  "sources": ["https://arxiv.org/abs/2406.07358"],
  "rarity": "legendary",
  "pdoom_impact": 5
}
```

#### Cross-Repo Metadata
```json
{
  "repo_version": "1.0.0",
  "last_updated": "2025-09-14",
  "event_count": 28,
  "schema_version": "1.0",
  "ascii_compliant": true
}
```

### 3. WEBSITE INTEGRATION OPPORTUNITIES

#### A. Event Timeline Display
- Interactive timeline of historical events
- Filter by category, year, impact level
- Source links and documentation
- "Play this scenario" buttons linking to game

#### B. Game Statistics Dashboard
- Real-time stats from game database
- Most impactful events in gameplay
- Player choice analytics (if available)
- Community event discussions

#### C. Content Management
- Admin interface for adding new events
- Community contribution system
- Event verification workflow
- Source validation tools

### 4. GAME INTEGRATION OPPORTUNITIES

#### A. Dynamic Event System
```python
# In pdoom1/src/events/historical_events.py
from pdoom_data.game_integration_helpers import get_weighted_random_event

def trigger_historical_event(game_state, current_year):
    event = get_weighted_random_event(game_state, current_year)
    if event:
        return process_event_impacts(event, game_state)
```

#### B. Save/Load Integration
- Track which historical events have occurred
- Store event outcomes and player reactions
- Analytics on event impact effectiveness
- Replay historical scenarios

#### C. Scenario Builder
- Custom scenarios using historical events
- "What if" alternative history gameplay
- Educational mode with real sources
- Challenge scenarios (legendary events only)

### 5. CROSS-REPO SYNCHRONIZATION

#### A. Automated Data Pipeline
```yaml
# .github/workflows/sync-data.yml
name: Sync Historical Events
on:
  push:
    paths: ['data/events/*.json']
jobs:
  sync-to-website:
    runs-on: ubuntu-latest
    steps:
      - name: Update website data
        run: |
          curl -X POST "$WEBSITE_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d @data/events/historical_events.json
```

#### B. Version Control Strategy
- Semantic versioning for data schemas
- Breaking change notifications
- Backward compatibility guarantees
- Migration scripts for schema updates

### 6. AGENT NAVIGATION SYSTEM

#### A. Cross-Repo README Links
Each repo should have:
```markdown
## Related Repositories
- [pdoom-data](https://github.com/PipFoweraker/pdoom-data) - Historical events database
- [pdoom-website](https://github.com/PipFoweraker/pdoom-website) - Public website
- [pdoom1](https://github.com/PipFoweraker/pdoom1) - Strategy game

## Integration Points
- Data consumption: See /docs/integration/
- API endpoints: See /docs/api/
- Development setup: See /docs/development/
```

#### B. Standardized Documentation Structure
```
docs/
+-- integration/
|   +-- data-sources.md      # How this repo consumes data
|   +-- data-exports.md      # How this repo provides data  
|   +-- cross-repo-apis.md   # API contracts
+-- development/
|   +-- setup.md            # Local development
|   +-- ascii-standards.md  # ASCII compliance rules
|   +-- testing.md          # Testing procedures
+-- architecture/
    +-- overview.md         # High-level architecture
    +-- data-flow.md        # Data flow diagrams
    +-- dependencies.md     # Inter-repo dependencies
```

### 7. SPECIFIC INTEGRATION IMPLEMENTATIONS

#### A. Website Event Browser
```javascript
// pdoom-website/src/components/EventBrowser.js
export function EventBrowser() {
  const [events, setEvents] = useState([]);
  
  useEffect(() => {
    // Load events from pdoom-data JSON export
    fetch('/data/historical_events.json')
      .then(response => response.json())
      .then(data => setEvents(data));
  }, []);
  
  return (
    <div className="event-timeline">
      {events.map(event => (
        <EventCard 
          key={event.id} 
          event={event}
          onPlayScenario={() => launchGame(event.id)}
        />
      ))}
    </div>
  );
}
```

#### B. Game Event Processor
```python
# pdoom1/src/core/event_processor.py
class HistoricalEventProcessor:
    def __init__(self):
        # Load events from pdoom-data
        self.events = self.load_historical_events()
    
    def load_historical_events(self):
        # Import from pdoom-data package
        from pdoom_data.game_integration_helpers import ALL_HISTORICAL_EVENTS
        return ALL_HISTORICAL_EVENTS
    
    def process_turn_events(self, game_state, current_year):
        # Use pdoom-data event selection logic
        return get_weighted_random_event(game_state, current_year)
```

### 8. DEVELOPMENT WORKFLOW COORDINATION

#### A. Shared Standards
- ASCII-only content across all repos
- Common linting and validation tools  
- Consistent commit message formats
- Synchronized testing procedures

#### B. Release Coordination
- Data updates trigger website rebuilds
- Game updates pull latest event data
- Coordinated version bumps
- Cross-repo changelog maintenance

### 9. MONITORING AND ANALYTICS

#### A. Cross-Repo Metrics
- Event usage statistics from game
- Website engagement with event content
- Data quality metrics
- Integration health monitoring

#### B. Error Tracking
- Failed data syncs between repos
- Schema compatibility issues
- API endpoint failures
- User experience problems

## NEXT STEPS FOR IMPLEMENTATION

1. **Examine actual repo structures** to refine this plan
2. **Create shared documentation standards** across repos
3. **Implement basic data export/import** between repos
4. **Set up automated synchronization** workflows
5. **Establish cross-repo testing** procedures
6. **Create agent navigation** documentation

This architecture ensures all three repos work together seamlessly while maintaining clear separation of concerns and ASCII-only agent compatibility.
