# Cross-Repository Integration Issues

**Generated**: 2025-11-09
**Purpose**: GitHub issue templates for integrating pdoom-data with consuming repositories

---

## For pdoom1-website Repository

### Issue: Integrate pdoom-data Timeline Events via PostgreSQL

**Labels**: `enhancement`, `data`, `backend`

**Title**: Integrate 1,028 Timeline Events from pdoom-data Repository

**Description**:

Integrate the pdoom-data repository to import 1,028 timeline events (28 manual + 1,000 alignment research) into PostgreSQL database and expose via REST API.

#### Background

The [pdoom-data](https://github.com/PipFoweraker/pdoom-data) repository now has a complete serveable zone with:
- 28 manually curated timeline events (2016-2025)
- 1,000 alignment research events (2020-2022)
- Schema-validated, ASCII-compliant, production-ready data
- Automated weekly updates via GitHub Actions

#### Implementation Tasks

- [ ] **Add pdoom-data as Git Submodule**
  ```bash
  git submodule add https://github.com/PipFoweraker/pdoom-data.git data/pdoom-data
  git submodule update --init --recursive
  ```

- [ ] **Create Database Schema**
  ```sql
  CREATE TABLE events (
      id VARCHAR(100) PRIMARY KEY,
      title VARCHAR(200) NOT NULL,
      year INTEGER NOT NULL,
      category VARCHAR(50) NOT NULL,
      description TEXT NOT NULL,
      impacts JSONB NOT NULL,
      sources JSONB NOT NULL,
      tags JSONB NOT NULL,
      rarity VARCHAR(20) NOT NULL,
      pdoom_impact INTEGER,
      safety_researcher_reaction TEXT NOT NULL,
      media_reaction TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
  );

  CREATE INDEX idx_events_year ON events(year);
  CREATE INDEX idx_events_category ON events(category);
  CREATE INDEX idx_events_rarity ON events(rarity);
  ```

- [ ] **Create Import Script** (`scripts/import_events.py`)
  - Load all_events.json (manual events)
  - Load alignment_research_events.json (research events)
  - Upsert into PostgreSQL with conflict resolution
  - Log import statistics

- [ ] **Create FastAPI Endpoint** (`/api/events`)
  - Support filters: `?year=2024&category=technical_research_breakthrough&rarity=rare`
  - Pagination: `?limit=100&offset=0`
  - Return JSON array of events
  - Document with OpenAPI schema

- [ ] **Add Auto-Sync Workflow** (`.github/workflows/sync-pdoom-data.yml`)
  - Daily cron job to update submodule
  - Re-run import script
  - Commit submodule pointer if updated

- [ ] **Documentation**
  - Add API endpoint to website documentation
  - Document event schema
  - Add example queries

#### Quick Start Reference

See [pdoom-data QUICK_START_INTEGRATION.md](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/QUICK_START_INTEGRATION.md) for:
- Complete PostgreSQL schema
- Full import script implementation
- FastAPI endpoint code
- Auto-sync workflow

#### Success Criteria

- [ ] All 1,028 events imported to database
- [ ] API endpoint returns events with filters
- [ ] Daily sync updates events automatically
- [ ] API documented in OpenAPI spec

#### Related Documentation

- [pdoom-data Integration Guide](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/INTEGRATION_GUIDE.md)
- [Event Schema](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/EVENT_SCHEMA.md)
- [Data Manifest](https://github.com/PipFoweraker/pdoom-data/blob/main/data/serveable/MANIFEST.json)

---

## For pdoom (Godot Game) Repository

### Issue: Integrate Timeline Events from pdoom-data

**Labels**: `enhancement`, `data`, `game-mechanics`

**Title**: Load 1,028 Timeline Events for Game Event System

**Description**:

Integrate timeline events from pdoom-data repository to power the game's event system with real AI safety historical data.

#### Background

The pdoom-data repository provides 1,028 timeline events with:
- Event categories (technical_research_breakthrough, policy_development, etc.)
- Rarity levels (common, rare, legendary)
- Game variable impacts (research, cash, vibey_doom, ethics_risk, etc.)
- Full source attribution and descriptions

#### Implementation Tasks

- [ ] **Copy Event Data to Game Resources**
  ```bash
  mkdir -p res://data/events

  # From pdoom-data repository
  cp ../pdoom-data/data/serveable/api/timeline_events/all_events.json res://data/events/
  cp -r ../pdoom-data/data/serveable/api/timeline_events/alignment_research res://data/events/
  ```

- [ ] **Create EventLoader Singleton** (`scripts/EventLoader.gd`)
  - Load all_events.json on game start
  - Load alignment_research_events.json
  - Provide query methods:
    - `get_events_for_year(year: int) -> Array`
    - `get_events_by_category(category: String) -> Array`
    - `get_random_event_by_rarity(rarity: String) -> Dictionary`
  - Cache loaded events

- [ ] **Integrate with GameState** (`scripts/GameState.gd`)
  - Add `trigger_event(event: Dictionary)` method
  - Apply impacts to player stats
  - Emit signals for UI updates
  - Log event triggers

- [ ] **Create Event UI Display**
  - Event card scene showing title, description, impacts
  - Category/rarity visual indicators
  - Source attribution display
  - Animation on event trigger

- [ ] **Test Event System**
  - Verify all 1,028 events load correctly
  - Test impact application to game variables
  - Validate rarity-based selection works
  - Ensure year filtering works

- [ ] **Add Sync Script** (`scripts/sync_events.sh`)
  ```bash
  #!/bin/bash
  PDOOM_DATA="../pdoom-data"
  TARGET="res://data/events"

  cp "$PDOOM_DATA/data/serveable/api/timeline_events/all_events.json" "$TARGET/"
  cp -r "$PDOOM_DATA/data/serveable/api/timeline_events/alignment_research" "$TARGET/"
  echo "Events synced!"
  ```

#### Quick Start Reference

See [pdoom-data QUICK_START_INTEGRATION.md](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/QUICK_START_INTEGRATION.md) for:
- Complete GDScript EventLoader implementation
- GameState impact application code
- Event UI examples

#### Success Criteria

- [ ] All events load on game start without errors
- [ ] Events can be filtered by year/category/rarity
- [ ] Impacts correctly modify game variables
- [ ] UI displays events with proper formatting
- [ ] Sync script updates events easily

#### Game Design Integration

Events should trigger based on:
- Player year progression (historical events by year)
- Research milestones (unlock rare events)
- Random draws weighted by rarity
- Category-specific unlocks

#### Related Documentation

- [Event Schema](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/EVENT_SCHEMA.md)
- [Integration Guide](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/INTEGRATION_GUIDE.md)

---

## For pdoom-dashboard Repository

### Issue: Display Timeline Events from pdoom1-website API

**Labels**: `enhancement`, `frontend`, `data-viz`

**Title**: Create Interactive Timeline Visualization for 1,028 AI Safety Events

**Description**:

Build an interactive timeline visualization that fetches and displays all 1,028 timeline events from the pdoom1-website API.

#### Background

Once pdoom1-website implements the `/api/events` endpoint, the dashboard can display:
- 1,028 timeline events (28 manual + 1,000 alignment research)
- Filterable by year, category, rarity
- Sortable and searchable
- Visual timeline with event cards

#### Implementation Tasks

- [ ] **Create useEvents Hook** (`src/hooks/useEvents.ts`)
  - Fetch from `/api/events` endpoint
  - Support filters: year, category, rarity
  - Handle loading/error states
  - Cache results with React Query or SWR

- [ ] **Create Timeline Component** (`src/components/Timeline.tsx`)
  - Group events by year
  - Display event cards with title, description, impacts
  - Color-code by category
  - Visual indicators for rarity (common, rare, legendary)
  - Responsive layout

- [ ] **Add Filter Controls** (`src/components/TimelineFilters.tsx`)
  - Year range slider (2016-2025)
  - Category dropdown (multi-select)
  - Rarity checkboxes
  - Search box for title/description
  - Clear filters button

- [ ] **Create Event Detail Modal** (`src/components/EventDetail.tsx`)
  - Full event information
  - Impact breakdown visualization
  - Source links (clickable)
  - Tags display
  - Safety researcher reaction
  - Media reaction

- [ ] **Add Statistics Dashboard** (`src/components/EventStats.tsx`)
  - Total events count
  - Events by category (pie chart)
  - Events by year (bar chart)
  - Events by rarity (donut chart)
  - Impact distribution (histogram)

- [ ] **Implement Data Visualization**
  - Use Recharts or D3.js for charts
  - Timeline view with scroll/zoom
  - Network graph showing event relationships
  - Heatmap of events over time

#### Quick Start Reference

See [pdoom-data QUICK_START_INTEGRATION.md](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/QUICK_START_INTEGRATION.md) for:
- Complete TypeScript interfaces
- React hook implementation
- Timeline component code

#### Success Criteria

- [ ] Timeline displays all events fetched from API
- [ ] Filters work correctly (year, category, rarity)
- [ ] Event detail modal shows complete information
- [ ] Statistics accurately reflect dataset
- [ ] Responsive on mobile/tablet/desktop
- [ ] Performance optimized for 1,000+ events

#### UI/UX Design Notes

- Use card-based layout for events
- Color scheme:
  - Technical research: Blue
  - Policy development: Green
  - Public awareness: Yellow
  - Capability advance: Red
- Rarity indicators:
  - Common: Gray border
  - Rare: Gold border
  - Legendary: Purple border with glow

#### Related Documentation

- [Event Schema](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/EVENT_SCHEMA.md)
- [Integration Guide](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/INTEGRATION_GUIDE.md)

---

## Integration Dependencies

```
pdoom-data (this repo)
    |
    |-- (submodule) --> pdoom1-website
    |                       |
    |                       |-- PostgreSQL events table
    |                       |-- GET /api/events
    |                       |
    |                       v
    |                   pdoom-dashboard
    |                   (fetches from API)
    |
    |-- (file sync) --> pdoom (game)
                        (loads from res://data/events/)
```

### Integration Order

1. **First**: pdoom1-website (creates database + API)
2. **Second**: pdoom (game) (can load from files OR fetch from API)
3. **Third**: pdoom-dashboard (fetches from API)

### Update Flow

1. pdoom-data: Weekly automated data refresh
2. pdoom1-website: Daily submodule update + reimport
3. pdoom (game): Manual sync or pre-build hook
4. pdoom-dashboard: Real-time via API

---

## Testing Integration

### pdoom1-website Tests
- [ ] Import script handles all 1,028 events
- [ ] API returns correct data for filters
- [ ] Pagination works correctly
- [ ] Database indexes improve query performance

### pdoom (game) Tests
- [ ] All events load without JSON parse errors
- [ ] Event impacts apply correctly to game variables
- [ ] Rarity-based random selection works
- [ ] Year filtering returns correct events

### pdoom-dashboard Tests
- [ ] Timeline renders all events
- [ ] Filters update results correctly
- [ ] Charts accurately represent data
- [ ] Performance acceptable with 1,000+ events

---

## Support

For implementation questions:
- Reference: [pdoom-data QUICK_START_INTEGRATION.md](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/QUICK_START_INTEGRATION.md)
- Full guide: [pdoom-data INTEGRATION_GUIDE.md](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/INTEGRATION_GUIDE.md)
- Schema: [pdoom-data EVENT_SCHEMA.md](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/EVENT_SCHEMA.md)
- Issues: Open issue in respective repository

---

**Generated from**: pdoom-data automation session 2025-11-09
**Maintained by**: pdoom-data team
