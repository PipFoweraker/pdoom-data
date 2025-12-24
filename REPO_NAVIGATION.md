# P(DOOM) PROJECT NAVIGATION
# Copy this file to all related repositories for agent/LLM navigation

## PROJECT ECOSYSTEM

This is part of the P(Doom) project ecosystem consisting of three repositories:

### [DATA] [pdoom-data](https://github.com/PipFoweraker/pdoom-data)
**AI Safety Data Lake & Timeline Events**
- 1,028 timeline events (28 curated + 1,000 alignment research)
- Three-zone data architecture (raw → transformed → serveable)
- Automated data pipeline with validation
- Interactive event browser tool
- JSON exports for integration
- ASCII-only content for agent compatibility

**Key Files:**
- `data/serveable/api/timeline_events/` - Production-ready event data
- `tools/event_browser.html` - Interactive event browser (open in browser)
- `config/schemas/event_v1.json` - Timeline event schema
- `scripts/transformation/` - Data pipeline scripts
- `docs/QUICK_START_INTEGRATION.md` - Integration guide

### [WEB] [pdoom-website](https://github.com/PipFoweraker/pdoom-website)
**Public Website & API**
- Event timeline displays with interactive browser
- Game information and downloads
- Documentation and guides
- Community engagement and player feedback
- PostgreSQL + FastAPI backend

**Integration Points:**
- Imports timeline events from pdoom-data to PostgreSQL
- Displays interactive event timelines
- Player feedback system (quarantined submissions)
- RESTful API endpoints for events and metadata
- Embeds event browser for community review

### [GAME] [pdoom1](https://github.com/PipFoweraker/pdoom1)
**Strategy Game (Godot)**
- Interactive P(Doom) simulation
- Historical event integration (1,028 events)
- Player choice mechanics
- Dynamic timeline system
- Save/load game states

**Integration Points:**
- Loads timeline events from pdoom-data JSON files
- Processes event impacts on game variables
- Tracks player interactions with events
- Uses event metadata for game mechanics (rarity, player_choice, impact_level)
- Provides gameplay analytics back to website

## CRITICAL: GAME/DATA BOUNDARY (ADR-001)

**This is the most important architectural decision in the ecosystem.**
Full details: `docs/ARCHITECTURE_DECISION_RECORDS.md`

### Layered Architecture

```
LAYER 1-2: pdoom-data (Facts + Defaults)
----------------------------------------
| Historical facts (immutable)         |
| Default impacts, rarity, reactions   |
| Community feedback (quarantined)     |
----------------------------------------
              |
              v
LAYER 3-4: pdoom1 (Game Mechanics)
----------------------------------------
| Impact overrides (balance tuning)    |
| Event chains & triggers              |
| Scenario assignments                 |
| Dialogue trees, probability curves   |
----------------------------------------
```

### What Goes Where

| pdoom-data (this repo)               | pdoom1 (game repo)                   |
|--------------------------------------|--------------------------------------|
| id, title, year, description         | Impact overrides (cash: +10 -> +15)  |
| category, tags, sources              | Rarity overrides for gameplay        |
| Default impacts (sensible starting)  | "Appears after turn 50" triggers     |
| Default rarity (common/rare/legend)  | "Event A unlocks Event B" chains     |
| Reactions (safety_researcher, media) | Scenario assignments (Hard mode)     |
| pdoom_impact (editorial assessment)  | Dialogue choices, player responses   |
| Community feedback (quarantined)     | Probability curves, balancing        |

### Key Rules

1. **Events here are game-ready** - Usable out-of-box with defaults
2. **pdoom1 can override anything** - Game team owns balance
3. **NO trigger conditions here** - Game logic stays in game
4. **NO event chains here** - Narrative design stays in game
5. **Facts are immutable** - Title, year, sources never change
6. **Impacts are defaults** - pdoom1 tunes for gameplay

## INTEGRATION ARCHITECTURE

```
pdoom-data (Source of Truth)
    |
    |-- Data Pipeline --> Serveable Zone (1,028 events)
    |                         |
    |                         |-- JSON --> pdoom1 (Godot Game)
    |                         |              |
    |                         |              +-- Applies overrides
    |                         |              +-- Adds game mechanics
    |                         |              v
    |                         |         Gameplay & Analytics
    |                         |
    |                         |-- Import --> pdoom-website (PostgreSQL)
    |                                            |
    |                                            v
    |                                   Public API & Event Browser
    |                                            |
    |                                            v
    |                                   Player Feedback (Quarantined)
    |                                            |
    |                                            v
    |                                   Community Metadata Layer
```

## DEVELOPMENT STANDARDS

### ASCII-ONLY PROTOCOL
- ALL content must be ASCII characters (0-127)
- NO Unicode quotes, em-dashes, special characters
- Use validation tools: `validate_ascii.py`
- Critical for agent/LLM compatibility

### FILE ENCODING
```python
# Always specify ASCII encoding
with open("file.txt", "w", encoding='ascii') as f:
    f.write(content)
```

### CROSS-REPO SYNCHRONIZATION
- Data schema versioning (semantic versioning)
- Automated sync workflows between repos
- Breaking change notifications
- Backward compatibility maintenance

## AGENT/LLM INSTRUCTIONS

When working on any P(Doom) repository:

1. **Check related repos** for existing implementations
2. **Maintain ASCII-only** content everywhere
3. **Follow data schemas** defined in pdoom-data (`config/schemas/event_v1.json`)
4. **Update integration docs** when making changes
5. **Test cross-repo** functionality
6. **Use Event Browser** (`tools/event_browser.html`) to review events interactively

### Key Documentation Locations

**pdoom-data**:
- Integration: `docs/QUICK_START_INTEGRATION.md`
- Event Schema: `docs/EVENT_SCHEMA.md`
- Event Browser: `docs/EVENT_BROWSER_GUIDE.md`
- Architecture: `docs/DATA_ZONES.md`
- All Docs: `docs/DOCUMENTATION_INDEX.md`

**pdoom-website**:
- API Documentation (check repo)
- Feedback Integration Guide (check repo)

**pdoom1**:
- Event System Documentation (check repo)
- Game Integration Guide (check repo)

### Navigation Commands
```bash
# Clone all related repositories
git clone https://github.com/PipFoweraker/pdoom-data.git
git clone https://github.com/PipFoweraker/pdoom-website.git
git clone https://github.com/PipFoweraker/pdoom1.git

# Open Event Browser
cd pdoom-data
# Then open tools/event_browser.html in your browser

# Load event data
# In browser: load data/serveable/api/timeline_events/all_events.json
```

## DATA FLOW PATTERNS

### From pdoom-data to Website:
1. Historical events updated in pdoom-data
2. JSON exports generated automatically
3. Website pulls new data via API/webhook
4. Event timeline updates displayed

### From pdoom-data to Game:
1. Event modules imported directly
2. Game logic uses helper functions
3. Player interactions tracked
4. Analytics fed back to website

### Cross-Repo Updates:
1. Schema changes in pdoom-data
2. Migration scripts provided
3. Dependent repos updated
4. Version compatibility verified

## COMMON TASKS

### Adding New Timeline Event:
1. **In pdoom-data**: Add to `data/raw/events/*.json`
2. **Run pipeline**: `python scripts/transformation/clean.py && python scripts/transformation/transform_to_timeline_events.py`
3. **Review in browser**: Open `tools/event_browser.html` and load the event
4. **Add metadata**: Tag impact level, game relevance, etc.
5. **Commit changes**: Triggers automated pipeline (GitHub Actions)
6. **Update website**: Re-import events to PostgreSQL
7. **Update game**: Copy new JSON to game data folder

### Reviewing Large Event Datasets:
1. **Open browser**: `tools/event_browser.html`
2. **Load events**: Select JSON file from `data/serveable/api/timeline_events/`
3. **Use filters**: Category, year range, search text
4. **Annotate events**: Add impact level, game relevance, notes
5. **Export metadata**: Download `*_metadata.json` file
6. **Commit metadata**: Store in version control for team review

### Integrating Player Feedback (Website):
1. **Design feedback form**: Capture event ID, suggested changes, rationale
2. **Create API endpoint**: `POST /api/events/feedback`
3. **Quarantine submissions**: Store in `data/feedback/pending/`
4. **Review in browser**: Load feedback alongside events
5. **Approve feedback**: Move to `approved/` and update community metadata
6. **Display on website**: Show community notes on event pages

### Updating Event Schema:
1. **Modify schema**: `config/schemas/event_v1.json`
2. **Update documentation**: `docs/EVENT_SCHEMA.md`
3. **Test pipeline**: Ensure validation passes
4. **Update cross-repo code**: pdoom1, pdoom-website
5. **Version bump**: Increment schema version if breaking

## TROUBLESHOOTING

### Integration Issues:
- Check schema versions match
- Validate ASCII compliance
- Test JSON export/import
- Review error logs

### Development Setup:
- Ensure all repos cloned
- Install dependencies in each
- Run validation scripts
- Test cross-repo imports

### Data Synchronization:
- Check webhook endpoints
- Verify API credentials  
- Test automated workflows
- Monitor sync status

## PROJECT CONTACTS

For questions about:
- **Data schemas**: See pdoom-data/docs/
- **Website integration**: See pdoom-website/docs/
- **Game mechanics**: See pdoom1/docs/
- **Cross-repo issues**: Check integration documentation

## VERSION COMPATIBILITY

Current versions:
- pdoom-data: v0.2.0 (In Development)
- Event Schema: v1.0.0
- pdoom-website: (check repo)
- pdoom1: (check repo)

Compatibility matrix and migration guides available in each repository's docs/ folder.

## TOOLS & UTILITIES

### Event Browser (`tools/event_browser.html`)
**Purpose**: Interactive browser for reviewing and annotating events
**How to use**:
1. Open HTML file in browser
2. Load events JSON
3. Browse, filter, annotate
4. Export metadata

**Use cases**:
- Review large event datasets
- Tag events for game integration
- Community feedback review
- Quality assurance checks

See `docs/EVENT_BROWSER_GUIDE.md` for complete documentation.

### Data Pipeline Scripts (`scripts/`)
- `transformation/clean.py` - Clean and normalize data
- `transformation/enrich.py` - Add derived fields
- `transformation/transform_to_timeline_events.py` - Convert to timeline format
- `validation/validate_alignment_research.py` - Validate schema compliance
- `publishing/generate_manifest.py` - Create data catalog
- `analysis/event_impact_manager.py` - CLI tool for event management

---

**Remember**: This ecosystem is designed for agent-based development. 
Always maintain ASCII-only content and clear documentation for AI assistants.
