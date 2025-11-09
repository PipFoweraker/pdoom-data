# Quick Start: Integrating pdoom-data with Your Repo

**5-Minute Setup Guide**

---

## For pdoom1-website (PostgreSQL + API)

### 1. Add pdoom-data as Git Submodule

```bash
cd pdoom1-website
git submodule add https://github.com/PipFoweraker/pdoom-data.git data/pdoom-data
git submodule update --init --recursive
```

### 2. Create Database Schema

```sql
-- In your PostgreSQL database
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

### 3. Import Data (One-Time)

```python
# scripts/import_events.py
import json
import psycopg2
from pathlib import Path

# Load all events
data_dir = Path("data/pdoom-data/data/serveable/api/timeline_events")

# Manual events
with open(data_dir / "all_events.json") as f:
    manual_events = list(json.load(f).values())

# Alignment research events
research_file = data_dir / "alignment_research/alignment_research_events.json"
if research_file.exists():
    with open(research_file) as f:
        research_events = json.load(f)
else:
    research_events = []

all_events = manual_events + research_events

# Connect and import
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

for event in all_events:
    cur.execute("""
        INSERT INTO events (
            id, title, year, category, description,
            impacts, sources, tags, rarity, pdoom_impact,
            safety_researcher_reaction, media_reaction
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            impacts = EXCLUDED.impacts,
            updated_at = NOW()
    """, (
        event['id'], event['title'], event['year'],
        event['category'], event['description'],
        json.dumps(event['impacts']),
        json.dumps(event['sources']),
        json.dumps(event['tags']),
        event['rarity'], event['pdoom_impact'],
        event['safety_researcher_reaction'],
        event['media_reaction']
    ))

conn.commit()
print(f"Imported {len(all_events)} events")
```

Run: `python scripts/import_events.py`

### 4. Create API Endpoint (FastAPI)

```python
# app/api/events.py
from fastapi import APIRouter, Query
from typing import List, Optional
import asyncpg

router = APIRouter()

@router.get("/api/events")
async def get_events(
    year: Optional[int] = None,
    category: Optional[str] = None,
    rarity: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get timeline events with optional filters."""
    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if year:
        query += f" AND year = ${len(params)+1}"
        params.append(year)

    if category:
        query += f" AND category = ${len(params)+1}"
        params.append(category)

    if rarity:
        query += f" AND rarity = ${len(params)+1}"
        params.append(rarity)

    query += f" ORDER BY year DESC, id LIMIT ${len(params)+1}"
    params.append(limit)

    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(query, *params)
    await conn.close()

    return [dict(row) for row in rows]
```

### 5. Auto-Sync Updates (Optional)

```yaml
# .github/workflows/sync-pdoom-data.yml
name: Sync pdoom-data

on:
  schedule:
    - cron: '0 3 * * *'  # Daily at 3am
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - name: Update submodule
        run: |
          git submodule update --remote data/pdoom-data

      - name: Reimport events
        run: |
          python scripts/import_events.py

      - name: Commit changes
        run: |
          git add data/pdoom-data
          git commit -m "chore: sync pdoom-data" || echo "No changes"
          git push
```

---

## For pdoom (Godot Game)

### 1. Copy Events to Game Resources

```bash
# In pdoom game directory
mkdir -p res://data/events

# Copy from pdoom-data repo
cp ../pdoom-data/data/serveable/api/timeline_events/all_events.json res://data/events/
cp -r ../pdoom-data/data/serveable/api/timeline_events/alignment_research res://data/events/
```

### 2. Create Event Loader (GDScript)

```gdscript
# scripts/EventLoader.gd
extends Node

var all_events = []

func _ready():
    load_all_events()

func load_all_events():
    # Load manual events
    var manual_file = File.new()
    if manual_file.file_exists("res://data/events/all_events.json"):
        manual_file.open("res://data/events/all_events.json", File.READ)
        var json = manual_file.get_as_text()
        manual_file.close()

        var result = JSON.parse(json)
        if result.error == OK:
            for event_id in result.result:
                all_events.append(result.result[event_id])

    # Load alignment research events
    var research_file = File.new()
    if research_file.file_exists("res://data/events/alignment_research/alignment_research_events.json"):
        research_file.open("res://data/events/alignment_research/alignment_research_events.json", File.READ)
        var json = research_file.get_as_text()
        research_file.close()

        var result = JSON.parse(json)
        if result.error == OK:
            all_events.append_array(result.result)

    print("Loaded ", all_events.size(), " events")

func get_events_for_year(year: int) -> Array:
    var year_events = []
    for event in all_events:
        if event.year == year:
            year_events.append(event)
    return year_events

func get_random_event_by_rarity(rarity: String) -> Dictionary:
    var filtered = []
    for event in all_events:
        if event.rarity == rarity:
            filtered.append(event)

    if filtered.size() > 0:
        return filtered[randi() % filtered.size()]
    return {}
```

### 3. Apply Event Impacts

```gdscript
# scripts/GameState.gd
extends Node

signal stats_changed(stats)

var player_stats = {
    "cash": 100,
    "reputation": 50,
    "stress": 0,
    "research": 0,
    "papers": 0,
    "vibey_doom": 0,
    "ethics_risk": 50
}

func trigger_event(event: Dictionary):
    print("Event: ", event.title)

    for impact in event.impacts:
        var variable = impact.variable
        var change = impact.change

        if player_stats.has(variable):
            player_stats[variable] += change
            print("  ", variable, ": ", change)

    emit_signal("stats_changed", player_stats)
```

### 4. Auto-Update Script (Optional)

```bash
#!/bin/bash
# sync_events.sh

PDOOM_DATA="../pdoom-data"
TARGET="res://data/events"

echo "Syncing events from pdoom-data..."
cp "$PDOOM_DATA/data/serveable/api/timeline_events/all_events.json" "$TARGET/"
cp -r "$PDOOM_DATA/data/serveable/api/timeline_events/alignment_research" "$TARGET/"

echo "Events synced!"
```

---

## For pdoom-dashboard (React/TypeScript)

### 1. Fetch from API

```typescript
// src/hooks/useEvents.ts
import { useState, useEffect } from 'react';

interface Event {
  id: string;
  title: string;
  year: number;
  category: string;
  description: string;
  impacts: Array<{
    variable: string;
    change: number;
    condition: string | null;
  }>;
  rarity: string;
  pdoom_impact: number | null;
}

export function useEvents(filters?: {
  year?: number;
  category?: string;
  rarity?: string;
}) {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchEvents() {
      try {
        // Build query params
        const params = new URLSearchParams();
        if (filters?.year) params.append('year', filters.year.toString());
        if (filters?.category) params.append('category', filters.category);
        if (filters?.rarity) params.append('rarity', filters.rarity);

        // Fetch from API (pdoom1-website)
        const response = await fetch(`/api/events?${params}`);
        const data = await response.json();

        setEvents(data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch events'));
        setLoading(false);
      }
    }

    fetchEvents();
  }, [filters]);

  return { events, loading, error };
}
```

### 2. Display Timeline

```typescript
// src/components/Timeline.tsx
import { useEvents } from '../hooks/useEvents';

export function Timeline() {
  const { events, loading } = useEvents();

  if (loading) return <div>Loading events...</div>;

  const eventsByYear = events.reduce((acc, event) => {
    if (!acc[event.year]) acc[event.year] = [];
    acc[event.year].push(event);
    return acc;
  }, {} as Record<number, typeof events>);

  return (
    <div className="timeline">
      {Object.entries(eventsByYear)
        .sort(([a], [b]) => Number(b) - Number(a))
        .map(([year, yearEvents]) => (
          <div key={year} className="year-section">
            <h2>{year}</h2>
            {yearEvents.map(event => (
              <div key={event.id} className={`event ${event.rarity}`}>
                <h3>{event.title}</h3>
                <span className="category">{event.category}</span>
                <p>{event.description}</p>
                <div className="impacts">
                  {event.impacts.map((impact, i) => (
                    <span key={i} className="impact">
                      {impact.variable}: {impact.change > 0 ? '+' : ''}{impact.change}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}
    </div>
  );
}
```

---

## Automation: Keep Data in Sync

All repositories automatically stay in sync with pdoom-data:

1. **pdoom-data updates** (weekly via GitHub Actions)
   - Extracts new alignment research
   - Runs cleaning/enrichment pipeline
   - Updates serveable zone
   - Commits to `main`

2. **Your repo syncs** (via Git submodule or scheduled workflow)
   - Pulls latest from pdoom-data
   - Reimports to database (pdoom1-website)
   - OR copies to game resources (pdoom)
   - Commits changes

3. **Users get latest data** automatically!

---

## Data Locations

### In pdoom-data Repository

- **Manual Events**: `data/serveable/api/timeline_events/all_events.json` (28 events)
- **Research Events**: `data/serveable/api/timeline_events/alignment_research/alignment_research_events.json` (1,000 events)
- **Manifest**: `data/serveable/MANIFEST.json` (complete catalog)

### After Integration

- **pdoom1-website**: PostgreSQL `events` table → API at `GET /api/events`
- **pdoom game**: `res://data/events/` → Loaded via `EventLoader.gd`
- **pdoom-dashboard**: Fetches from API → Displays in React components

---

## Need Help?

- **Full Integration Guide**: [docs/INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Event Schema**: [docs/EVENT_SCHEMA.md](EVENT_SCHEMA.md)
- **Data Architecture**: [docs/DATA_ZONES.md](DATA_ZONES.md)
- **Issues**: https://github.com/PipFoweraker/pdoom-data/issues

---

**Total Events Available**: 1,028 (28 manual + 1,000 alignment research)

**Last Updated**: 2025-11-09
