# Integration Guide: pdoom-data → pdoom1 Game

**Version**: 1.0.0
**Last Updated**: 2025-11-09

---

## Overview

This guide explains how to integrate data from pdoom-data into the pdoom1 game, website, and dashboard ecosystem.

## Data Flow Architecture

```
pdoom-data (this repo)
    ├── data/raw/                    # Source of truth (never modified)
    ├── data/transformed/            # Processed data (cleaned, enriched)
    └── data/serveable/              # Production-ready, optimized
            ↓
    [Database Import or Direct Sync]
            ↓
pdoom1-website
    └── PostgreSQL events table
            ↓
    [REST API: GET /api/events]
            ↓
        ┌───────┴───────┐
        ↓               ↓
    pdoom (game)    pdoom-dashboard
```

## Available Data

### Timeline Events

**Location**: `data/serveable/api/timeline_events/`

**Datasets**:
1. **Manual Events** (28 events, 2016-2025)
   - Hand-curated game events
   - File: `all_events.json`
   - Organized by year and category

2. **Alignment Research Events** (1,000 events, 2020-2022)
   - Generated from StampyAI alignment research dataset
   - File: `alignment_research/alignment_research_events.json`
   - Organized by year

**Schema**: [config/schemas/event_v1.json](../config/schemas/event_v1.json)

**Documentation**: [EVENT_SCHEMA.md](EVENT_SCHEMA.md)

## Integration Methods

### Method 1: Database Import (Recommended)

Import timeline events into pdoom1-website PostgreSQL database.

#### Step 1: Create Events Table

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

#### Step 2: Import Data

**Python import script** (example):

```python
import json
import psycopg2

# Load events
with open('data/serveable/api/timeline_events/all_events.json') as f:
    manual_events = json.load(f)

with open('data/serveable/api/timeline_events/alignment_research/alignment_research_events.json') as f:
    research_events = json.load(f)

all_events = list(manual_events.values()) + research_events

# Connect to database
conn = psycopg2.connect("dbname=pdoom1 user=pdoom password=...")
cur = conn.cursor()

# Insert events
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
cur.close()
conn.close()

print(f"Imported {len(all_events)} events")
```

#### Step 3: Create API Endpoint

**FastAPI endpoint** (example):

```python
from fastapi import FastAPI
from typing import List, Optional
import asyncpg

app = FastAPI()

@app.get("/api/events")
async def get_events(
    year: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 100
):
    """Get timeline events."""
    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if year:
        query += f" AND year = ${len(params)+1}"
        params.append(year)

    if category:
        query += f" AND category = ${len(params)+1}"
        params.append(category)

    query += f" ORDER BY year DESC LIMIT ${len(params)+1}"
    params.append(limit)

    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(query, *params)
    await conn.close()

    return [dict(row) for row in rows]
```

### Method 2: Direct File Sync

For simpler setups, sync JSON files directly to pdoom1 repository.

#### Option A: Git Submodule

Add pdoom-data as a submodule in pdoom1:

```bash
cd pdoom1
git submodule add https://github.com/PipFoweraker/pdoom-data data/pdoom-data
git submodule update --init --recursive
```

Then reference files:
```python
events_path = Path("data/pdoom-data/data/serveable/api/timeline_events/all_events.json")
```

#### Option B: Copy Script

Create a sync script in pdoom1:

```bash
#!/bin/bash
# sync_events.sh

PDOOM_DATA="../pdoom-data"
TARGET="./data/events"

# Copy serveable events
cp -r "$PDOOM_DATA/data/serveable/api/timeline_events" "$TARGET/"

echo "Synced events from pdoom-data"
```

#### Option C: GitHub Actions Workflow

Automate syncing with GitHub Actions:

```yaml
name: Sync Events from pdoom-data

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2am
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Clone pdoom-data
        run: git clone https://github.com/PipFoweraker/pdoom-data.git

      - name: Copy serveable data
        run: |
          mkdir -p data/events
          cp -r pdoom-data/data/serveable/api/timeline_events/* data/events/

      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/events
          git commit -m "chore: sync events from pdoom-data" || echo "No changes"
          git push
```

### Method 3: S3/CDN Hosting

For production deployments, host serveable data on S3/CDN:

```bash
# Upload to S3
aws s3 sync data/serveable/api/timeline_events/ \
    s3://pdoom-data/timeline_events/ \
    --acl public-read

# Access from game
fetch('https://pdoom-data.s3.amazonaws.com/timeline_events/all_events.json')
```

## Game Integration

### Loading Events in Godot (GDScript)

```gdscript
# EventLoader.gd
extends Node

var events = []

func _ready():
    load_events()

func load_events():
    var file = File.new()

    # Load manual events
    if file.file_exists("res://data/events/all_events.json"):
        file.open("res://data/events/all_events.json", File.READ)
        var json = file.get_as_text()
        file.close()

        var result = JSON.parse(json)
        if result.error == OK:
            for event_id in result.result:
                events.append(result.result[event_id])

    # Load alignment research events
    if file.file_exists("res://data/events/alignment_research/alignment_research_events.json"):
        file.open("res://data/events/alignment_research/alignment_research_events.json", File.READ)
        var json = file.get_as_text()
        file.close()

        var result = JSON.parse(json)
        if result.error == OK:
            events.append_array(result.result)

    print("Loaded ", events.size(), " events")

func get_events_for_year(year: int) -> Array:
    var year_events = []
    for event in events:
        if event.year == year:
            year_events.append(event)
    return year_events

func get_random_event(rarity: String = "") -> Dictionary:
    var filtered = events
    if rarity != "":
        filtered = []
        for event in events:
            if event.rarity == rarity:
                filtered.append(event)

    if filtered.size() > 0:
        return filtered[randi() % filtered.size()]
    else:
        return {}
```

### Applying Event Impacts

```gdscript
# GameState.gd
extends Node

var player_stats = {
    "cash": 100,
    "reputation": 50,
    "research": 0,
    "papers": 0,
    "vibey_doom": 0,
    "ethics_risk": 50
}

func apply_event(event: Dictionary):
    print("Event triggered: ", event.title)

    for impact in event.impacts:
        var variable = impact.variable
        var change = impact.change
        var condition = impact.condition

        # Check condition if present
        if condition != null:
            if not evaluate_condition(condition):
                continue

        # Apply change
        if player_stats.has(variable):
            player_stats[variable] += change
            print("  ", variable, ": ", change)

    # Update UI, trigger effects, etc.
    emit_signal("stats_changed", player_stats)

func evaluate_condition(condition: String) -> bool:
    # Implement condition logic
    # Example: "research > 50" or "year >= 2024"
    return true  # Placeholder
```

## Dashboard Integration

### Loading in React/TypeScript

```typescript
// useEvents.ts
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
  sources: string[];
  tags: string[];
  rarity: string;
  pdoom_impact: number | null;
  safety_researcher_reaction: string;
  media_reaction: string;
}

export function useEvents() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadEvents() {
      // Load from API
      const response = await fetch('/api/events');
      const data = await response.json();

      setEvents(data);
      setLoading(false);
    }

    loadEvents();
  }, []);

  return { events, loading };
}

// EventTimeline.tsx
import { useEvents } from './useEvents';

export function EventTimeline() {
  const { events, loading } = useEvents();

  if (loading) return <div>Loading...</div>;

  const eventsByYear = events.reduce((acc, event) => {
    if (!acc[event.year]) acc[event.year] = [];
    acc[event.year].push(event);
    return acc;
  }, {} as Record<number, Event[]>);

  return (
    <div className="timeline">
      {Object.entries(eventsByYear).map(([year, yearEvents]) => (
        <div key={year} className="year-section">
          <h2>{year}</h2>
          {yearEvents.map(event => (
            <div key={event.id} className={`event ${event.rarity}`}>
              <h3>{event.title}</h3>
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

## Data Updates

### Regenerating Serveable Data

When raw data changes, regenerate serveable zone:

```bash
# Full pipeline
python scripts/validation/validate_alignment_research.py data/raw/alignment_research/dumps/latest
python scripts/transformation/clean.py --source data/transformed/validated/alignment_research/latest --output data/transformed/cleaned/alignment_research/latest --format jsonl
python scripts/transformation/enrich.py --source data/transformed/cleaned/alignment_research/latest --output data/transformed/enriched/alignment_research/latest --format jsonl
python scripts/transformation/transform_to_timeline_events.py --source data/transformed/enriched/alignment_research/latest --output data/serveable/api/timeline_events/alignment_research

# Manual events
python scripts/transformation/clean_events.py

# Generate manifest
python scripts/publishing/generate_manifest.py
```

### Automated Updates

Set up GitHub Actions to regenerate on data changes:

```yaml
name: Regenerate Serveable Data

on:
  push:
    paths:
      - 'data/raw/**'
      - 'config/schemas/**'

jobs:
  regenerate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install jsonschema

      - name: Run pipeline
        run: |
          # Run cleaning and enrichment
          python scripts/transformation/clean.py ...
          python scripts/transformation/enrich.py ...
          python scripts/transformation/transform_to_timeline_events.py ...
          python scripts/transformation/clean_events.py
          python scripts/publishing/generate_manifest.py

      - name: Commit serveable data
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/serveable
          git commit -m "chore: regenerate serveable data"
          git push
```

## Troubleshooting

### Events Not Loading

1. Check manifest: `data/serveable/MANIFEST.json`
2. Verify file paths match manifest
3. Check JSON validity: `python -m json.tool < file.json`
4. Review logs in `logs/`

### Database Import Errors

1. Check PostgreSQL connection
2. Verify schema matches event_v1.json
3. Check for duplicate IDs
4. Review JSONB fields for valid JSON

### Sync Issues

1. Verify Git/S3 credentials
2. Check file permissions
3. Review workflow logs
4. Test sync script manually

## Related Documentation

- [DATA_ZONES.md](DATA_ZONES.md) - Data lake architecture
- [EVENT_SCHEMA.md](EVENT_SCHEMA.md) - Event schema details
- [DATA_PUBLISHING_STRATEGY.md](DATA_PUBLISHING_STRATEGY.md) - Public data strategy

---

**Questions?** Open an issue at https://github.com/PipFoweraker/pdoom-data/issues
