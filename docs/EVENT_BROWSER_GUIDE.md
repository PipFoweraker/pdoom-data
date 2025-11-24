# Event Browser Tool - Comprehensive Guide

**Last Updated**: 2025-11-24
**Location**: `tools/event_browser.html`
**Purpose**: Interactive browser for reviewing, annotating, and managing timeline events

---

## Overview

The Event Browser is a standalone HTML tool that provides a visual interface for working with timeline events. It enables you to review large event datasets, add custom metadata for game integration, and manage event filtering - all without modifying the original event data.

### Key Features

- **100% Browser-Based**: No installation, servers, or dependencies
- **Nondestructive Metadata**: All annotations stored separately from source events
- **Visual Interface**: Paginated browsing with filters, dropdowns, and form controls
- **Real-Time Filtering**: Search, category, impact level, and year range filters
- **Bulk Export**: Download metadata JSON or filtered event sets
- **Color-Coded Display**: Visual indicators for impact levels and categories

---

## Quick Start

### 1. Open the Browser

Open `tools/event_browser.html` in any modern web browser (Chrome, Firefox, Edge, Safari).

### 2. Load Events

Click **"Choose File"** next to "Events JSON" and select one of:
- `data/serveable/api/timeline_events/all_events.json` (28 curated events)
- `data/serveable/api/timeline_events/alignment_research/alignment_research_events.json` (1000 research events)

### 3. Browse and Annotate

- Use filters in the sidebar to narrow down events
- Click on event cards to view details
- Fill out metadata form fields for each event
- Click "Save Metadata" to record your annotations

### 4. Export Your Work

When finished:
- Click **"Export Metadata JSON"** to download your annotations
- Save the file as `<dataset_name>_metadata.json`
- You can reload this metadata file later to continue work

---

## Interface Overview

### Sidebar (Left Panel)

**Load Data Section**
- **Events JSON**: Primary event dataset (required)
- **Metadata JSON**: Previously saved metadata (optional)

**Stats Panel**
- Total Events: Count in loaded dataset
- Filtered: Events matching current filters
- With Metadata: Events you've annotated

**Filters**
- Search: Text search in title/description
- Category: Filter by event category
- Impact Level: Filter by metadata impact level
- Year Range: Min/max year filters
- Apply/Clear buttons

**Actions**
- Export Metadata JSON: Download annotations
- Export Filtered Events: Download events with metadata merged

### Main Content (Right Panel)

**Pagination**
- Previous/Next buttons
- Page indicator
- 20 events per page

**Event Cards**
- Title with impact level badge (Critical/High/Medium/Low/Unset)
- Year and category metadata
- Description preview (2 lines)
- Click to select and view details

**Event Detail View** (appears when event selected)
- Full event information
- All impacts with visual indicators (+/- values)
- Tags and sources
- Metadata editing form

### Metadata Editor

**Standard Fields**
- **Impact Level**: Critical/High/Medium/Low (game importance)
- **Game Relevance**: Essential/High/Medium/Low (should it be in game)
- **Player Choice Event**: Yes/No (is this a player decision point)
- **Notes**: Free-form text for your thoughts

**Custom Field**
- JSON object for any additional metadata
- Flexible structure for future needs

**Actions**
- Save Metadata: Store annotations for this event
- Clear Metadata: Remove all annotations for this event

---

## Workflow Examples

### Example 1: Tag Events for Game Integration

**Goal**: Review 1000 alignment research events and identify the 50 most game-relevant ones.

```
1. Load alignment_research_events.json
2. Set filter: Impact Level = "unset" (events not yet reviewed)
3. For each event:
   - Read description and impacts
   - Set Impact Level: Critical/High/Medium/Low
   - Set Game Relevance: Essential/High/Medium/Low
   - Add Notes if relevant
   - Click Save Metadata
4. Filter: Game Relevance = "Essential" or "High"
5. Export Filtered Events -> save as game_ready_events.json
6. Export Metadata JSON -> save as alignment_research_events_metadata.json
```

### Example 2: Identify Player Choice Events

**Goal**: Mark events that should be player decisions in p(Doom)1.

```
1. Load all_events.json
2. For each high-impact event:
   - Review the event impacts
   - Consider: Does this feel like a decision point?
   - Set Player Choice Event: Yes/No
   - Add Notes explaining the choice
3. Filter: Player Choice Event = "Yes"
4. Export Filtered Events for game developer review
```

### Example 3: Categorize by Impact

**Goal**: Auto-review impact scores and adjust categorization.

```
1. Load events and existing metadata
2. Use search to find specific themes (e.g., "funding", "safety")
3. Review auto-tagged Impact Level
4. Adjust if needed based on domain knowledge
5. Add custom fields for special handling:
   {
     "doom_multiplier": 1.5,
     "triggers_scenario": "funding_crisis"
   }
6. Save metadata and export
```

### Example 4: Community Review Session

**Goal**: Work through events with a domain expert.

```
1. Share browser HTML with expert
2. Load events to review
3. Expert provides verbal feedback while you annotate:
   - Notes: Expert comments
   - Game Relevance: Expert assessment
   - Custom: {"expert": "Name", "review_date": "2025-11-24"}
4. Export metadata capturing expert input
```

---

## Metadata Schema

### Standard Fields (Recommended)

```json
{
  "event_id": {
    "impact_level": "Critical|High|Medium|Low",
    "game_relevance": "essential|high|medium|low",
    "player_choice_event": true|false,
    "notes": "Free-form text notes"
  }
}
```

### Custom Fields (Flexible)

You can add any custom metadata via the Custom Field JSON:

```json
{
  "event_id": {
    "impact_level": "Critical",
    "_custom": {
      "doom_multiplier": 1.5,
      "triggers_scenario": "funding_crisis",
      "narrative_arc": "Act2_CrisisPoint",
      "visual_style": "dramatic",
      "sound_cue": "tension_high",
      "player_agency_weight": 0.8,
      "reviewed_by": "Expert Name",
      "review_date": "2025-11-24"
    }
  }
}
```

### Export Formats

**Metadata Only** (Export Metadata JSON):
```json
{
  "event_id_1": { "impact_level": "Critical", ... },
  "event_id_2": { "game_relevance": "high", ... }
}
```

**Events with Metadata** (Export Filtered Events):
```json
{
  "event_id_1": {
    "id": "event_id_1",
    "title": "Event Title",
    "impacts": [...],
    "_custom_metadata": {
      "impact_level": "Critical",
      ...
    }
  }
}
```

---

## Integration with Data Pipeline

### Position in Pipeline

```
Raw Events
    ↓
Cleaned Events (clean.py)
    ↓
Enriched Events (enrich.py)
    ↓
Timeline Events (transform_to_timeline_events.py)
    ↓
Serveable Zone
    ↓
[EVENT BROWSER] ← You are here
    ↓
Game Integration / Website Display
```

### Nondestructive Design

The Event Browser **never modifies** the original event files. Instead:

1. **Source Events**: Remain untouched in `data/serveable/api/timeline_events/`
2. **Metadata File**: Stored separately (e.g., `all_events_metadata.json`)
3. **Merged Export**: Creates new files with metadata merged

This design allows:
- Safe experimentation without data corruption
- Multiple reviewers with separate metadata files
- Easy rollback by deleting metadata
- Version control of annotations separately from events

### Merging Metadata for Production

When ready to integrate into the game or website:

**Option 1: Runtime Merge**
```python
# Load events and metadata separately
with open('all_events.json') as f:
    events = json.load(f)

with open('all_events_metadata.json') as f:
    metadata = json.load(f)

# Merge at runtime
for event_id, event in events.items():
    if event_id in metadata:
        event['_metadata'] = metadata[event_id]
```

**Option 2: Pre-Merge Script**
```python
# Create merged dataset for deployment
merged = {}
for event_id, event in events.items():
    merged[event_id] = {
        **event,
        '_metadata': metadata.get(event_id, {})
    }

with open('events_with_metadata.json', 'w') as f:
    json.dump(merged, f, indent=2)
```

**Option 3: Use Export**
- Click "Export Filtered Events" in browser
- Metadata automatically merged into events
- Use exported file directly

---

## Player Feedback Integration (Website)

### Vision

Integrate the Event Browser into the pdoom1-website to allow players to:
- View event details in a visual interface
- Suggest corrections or improvements
- Submit feedback on event impacts
- Vote on game relevance

### Architecture

```
Website Event Page
    ↓
[Event Browser Component] (embedded)
    ↓
Player Feedback Form
    ↓
Feedback API Endpoint (quarantined)
    ↓
Moderation Queue
    ↓
Approved Feedback → Metadata Updates
```

### Implementation Strategy

**Phase 1: Read-Only Display**
- Embed event browser HTML in website
- Load events from API endpoint
- Display-only mode (no editing)
- Players can view event details and impacts

**Phase 2: Feedback Collection**
- Add "Suggest Edit" button per event
- Feedback form captures:
  - Event ID
  - Field being corrected
  - Suggested value
  - Player rationale
  - Player contact (optional)
- Submit to quarantined feedback API

**Phase 3: Moderation System**
- Admin panel to review submissions
- Approve/Reject feedback
- Approved feedback creates metadata entries
- Track contributor statistics

**Phase 4: Community Integration**
- Upvote/downvote suggestions
- Contributor reputation system
- Public feedback visible on event pages
- Integration with game achievements

### Feedback API Spec

**Endpoint**: `POST /api/events/feedback`

**Request**:
```json
{
  "event_id": "apollo_scheming_evals_2024",
  "feedback_type": "correction|suggestion|rating",
  "field": "impact_level",
  "current_value": "High",
  "suggested_value": "Critical",
  "rationale": "This event fundamentally changed safety research",
  "player_id": "optional_uuid",
  "contact_email": "optional@email.com"
}
```

**Response**:
```json
{
  "status": "submitted",
  "feedback_id": "fb_12345",
  "message": "Thank you! Your feedback will be reviewed."
}
```

### Data Quarantine

All player feedback is quarantined until review:

```
data/
└── feedback/
    ├── pending/
    │   └── feedback_12345.json
    ├── approved/
    │   └── feedback_12346.json
    ├── rejected/
    │   └── feedback_12347.json
    └── metadata_updates/
        └── events_metadata_community.json
```

### Moderation Interface

Admin panel shows:
- Pending feedback count
- Recent submissions
- Approval queue with:
  - Original event data
  - Suggested change
  - Player rationale
  - Approve/Reject buttons
  - Add to metadata checkbox

### Community Metadata Layer

Approved feedback creates a **community metadata layer**:

```json
{
  "event_id": {
    "_community_feedback": {
      "suggested_impact_level": "Critical",
      "upvotes": 15,
      "contributor_count": 3,
      "consensus_confidence": 0.87,
      "approved_by": "admin_user",
      "approved_date": "2025-11-25"
    }
  }
}
```

This layer can be:
- Displayed alongside official metadata
- Used to inform future curation
- Tracked for quality metrics
- Shown as "Community Notes" on website

---

## Advanced Features

### Keyboard Shortcuts

- `Enter` in search box: Apply filters
- `←/→` arrow keys: Navigate pages (future enhancement)
- `Esc`: Clear selection (future enhancement)

### Bulk Operations

For bulk tagging, consider:

1. Filter to target set
2. Use custom script to batch-update metadata
3. Load updated metadata in browser to verify

Example script:
```python
import json

with open('metadata.json') as f:
    metadata = json.load(f)

# Bulk update all funding events
for event_id, meta in metadata.items():
    if 'funding' in event_id:
        meta['category_tag'] = 'financial_crisis'

with open('metadata_updated.json', 'w') as f:
    json.dump(metadata, f, indent=2)
```

### Multi-Reviewer Workflow

For team review:

1. **Distribute work**: Each reviewer gets subset of events
2. **Create individual metadata**: `metadata_reviewer1.json`, etc.
3. **Merge metadata**:

```python
merged = {}
for file in ['metadata_reviewer1.json', 'metadata_reviewer2.json']:
    with open(file) as f:
        data = json.load(f)
        merged.update(data)  # Last wins for conflicts

with open('metadata_merged.json', 'w') as f:
    json.dump(merged, f, indent=2)
```

---

## Troubleshooting

### Events Won't Load

**Problem**: File picker doesn't work or events don't appear.

**Solutions**:
- Ensure using modern browser (Chrome 90+, Firefox 88+, Safari 14+)
- Check browser console for errors (F12)
- Verify JSON file is valid (use `python -m json.tool file.json`)
- Try drag-and-drop instead of file picker

### Metadata Not Saving

**Problem**: Click "Save Metadata" but nothing happens.

**Solutions**:
- Check that you filled in at least one field
- Look for error alert messages
- Verify custom JSON field is valid JSON
- Empty metadata entries are auto-removed

### Export Doesn't Download

**Problem**: Click export but no file downloads.

**Solutions**:
- Check browser download settings
- Disable popup blocker
- Try different browser
- Check browser console for errors

### Filters Not Working

**Problem**: Filter applied but events unchanged.

**Solutions**:
- Click "Apply Filters" after changing filter values
- Clear filters and reapply
- Reload page and try again
- Ensure at least some events match filters

---

## Best Practices

### Reviewing Large Datasets

- **Start Small**: Review 10-20 events to calibrate
- **Use Filters**: Don't paginate through 1000 events
- **Take Breaks**: Annotation fatigue is real
- **Save Often**: Export metadata frequently
- **Consistent Criteria**: Define impact levels upfront

### Metadata Consistency

- **Document Criteria**: Write down what makes an event "Critical" vs "High"
- **Use Notes**: Explain non-obvious decisions
- **Review Examples**: Check previous annotations for consistency
- **Spot Check**: Periodically review old annotations

### Collaboration

- **Divide Work**: Split by category, year, or alphabetically
- **Shared Criteria**: All reviewers use same definitions
- **Regular Sync**: Merge metadata files frequently
- **Conflict Resolution**: Decide on merge strategy upfront

---

## Technical Details

### Browser Compatibility

**Tested On**:
- Chrome 96+
- Firefox 95+
- Safari 15+
- Edge 96+

**Required Features**:
- ES6 JavaScript
- File API
- JSON parsing
- CSS Grid
- LocalStorage (future feature)

### File Format Support

**Input Formats**:
- JSON object: `{ "event_id": {...}, ... }`
- JSON array: `[{...}, {...}]`

**Output Formats**:
- Metadata: JSON object
- Filtered events: JSON object with metadata merged

### Performance

**Large Datasets**:
- 1000 events: Instant loading
- 10,000 events: <1 second
- 100,000 events: May be slow, consider pagination

**Pagination**:
- 20 events per page (configurable in code)
- Instant page switching
- No lag with filters

### Security

- **No Server**: All processing client-side
- **No Network**: No data sent anywhere
- **No Cookies**: No tracking
- **No Storage**: Nothing persisted unless you export

Safe to use with confidential data.

---

## Future Enhancements

### Planned Features

- **Keyboard Shortcuts**: Navigate and annotate via keyboard
- **Undo/Redo**: Revert metadata changes
- **Bulk Edit**: Update multiple events at once
- **LocalStorage**: Auto-save work-in-progress
- **Dark Mode**: Visual theme toggle
- **Export Formats**: CSV, Excel, SQL
- **Import Sources**: Merge multiple metadata files
- **Comments Thread**: Per-event discussion
- **Version History**: Track metadata changes over time

### Integration Ideas

- **Game Editor**: Launch from Godot editor
- **Website Component**: Embed in React/Vue
- **CLI Companion**: Command-line metadata management
- **API Mode**: RESTful API for metadata CRUD
- **Electron App**: Desktop application wrapper

---

## See Also

- [QUICK_START_INTEGRATION.md](QUICK_START_INTEGRATION.md) - Integrating events into apps
- [EVENT_SCHEMA.md](EVENT_SCHEMA.md) - Event data structure
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Complete integration docs
- [DATA_ZONES.md](DATA_ZONES.md) - Data pipeline architecture

---

**Maintained by**: pdoom-data team
**Created**: 2025-11-24
**Version**: 1.0.0
