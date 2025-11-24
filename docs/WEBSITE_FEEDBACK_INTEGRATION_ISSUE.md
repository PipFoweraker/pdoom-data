# GitHub Issue: Player Feedback System for Event Browser

**For**: pdoom1-website repository
**Priority**: Medium
**Epic**: Community Engagement

---

## Summary

Integrate the Event Browser tool into the website to allow players to view event details interactively and submit feedback on events. Feedback is quarantined for moderation before being incorporated into a community metadata layer.

---

## Background

pdoom-data now includes an interactive Event Browser (`tools/event_browser.html`) that allows visual exploration of 1,028 timeline events with filtering, searching, and metadata annotation capabilities. This tool should be embedded into the website to:

1. **Enhance player engagement**: Let players explore the events that power p(Doom)1
2. **Gather community input**: Collect suggestions for event impacts, categorization, and game relevance
3. **Improve data quality**: Leverage community knowledge to refine event metadata
4. **Build community**: Create a feedback loop between players and game development

---

## User Story

**As a** player visiting the pdoom1-website

**I want to** view detailed information about AI safety events and suggest improvements

**So that** I can better understand the game's historical basis and contribute to data quality

---

## Requirements

### Phase 1: Read-Only Event Browser (MVP)

**Acceptance Criteria**:
- [ ] Embed event browser HTML/JS into website event page
- [ ] Load events from PostgreSQL via API endpoint
- [ ] Display events with filtering (category, year, search)
- [ ] Show event details (title, description, impacts, sources)
- [ ] Responsive design for mobile/tablet
- [ ] No editing capabilities (read-only mode)

**Technical Requirements**:
- Copy/adapt `tools/event_browser.html` from pdoom-data
- Create API endpoint: `GET /api/events?category=X&year=Y&search=Z`
- Return events in compatible JSON format
- Add pagination support (20 events per page)
- Cache event data for performance

### Phase 2: Feedback Collection System

**Acceptance Criteria**:
- [ ] Add "Suggest Edit" button on event detail view
- [ ] Feedback form with fields:
  - Event ID (auto-populated)
  - Feedback type (correction/suggestion/rating)
  - Field being corrected
  - Suggested value
  - Rationale (required, min 50 chars)
  - Contact email (optional)
- [ ] Submit feedback to quarantined API endpoint
- [ ] Confirmation message after submission
- [ ] Rate limiting (5 submissions per hour per IP)
- [ ] CAPTCHA or similar spam prevention

**Technical Requirements**:
- Create API endpoint: `POST /api/events/feedback`
- Store submissions in separate `feedback` table (not event table)
- Log all submissions with timestamp, IP, user agent
- Email notification to admin on new feedback
- No automatic publication of feedback

**Feedback Table Schema**:
```sql
CREATE TABLE event_feedback (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,  -- 'correction', 'suggestion', 'rating'
    field_name VARCHAR(100),
    current_value TEXT,
    suggested_value TEXT,
    rationale TEXT NOT NULL,
    contact_email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    submitted_at TIMESTAMP DEFAULT NOW(),
    submitted_ip VARCHAR(45),
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id)
);
```

### Phase 3: Moderation Interface

**Acceptance Criteria**:
- [ ] Admin panel to view pending feedback
- [ ] Display original event data alongside suggestion
- [ ] Approve/Reject buttons for each submission
- [ ] Bulk actions (approve all, reject all)
- [ ] Filter by feedback type, event category, date
- [ ] Search feedback by event ID or keywords
- [ ] Moderator notes field
- [ ] Audit log of moderation decisions

**Technical Requirements**:
- Protected route: `/admin/feedback` (requires auth)
- API endpoints:
  - `GET /api/admin/feedback?status=pending`
  - `POST /api/admin/feedback/:id/approve`
  - `POST /api/admin/feedback/:id/reject`
- Email notification to submitter on approval/rejection (if email provided)
- Track moderator identity and timestamp

### Phase 4: Community Metadata Layer

**Acceptance Criteria**:
- [ ] Approved feedback creates community metadata entries
- [ ] Community metadata displayed on event pages
- [ ] "Community Notes" section showing:
  - Number of contributions
  - Consensus suggestions
  - Upvote/downvote counts (future)
- [ ] Export community metadata as JSON
- [ ] Sync community metadata back to pdoom-data repo

**Technical Requirements**:
- Create `event_community_metadata` table
- API endpoint: `GET /api/events/:id/community-metadata`
- Merge approved feedback into community metadata
- Track contributor statistics
- Weekly export to pdoom-data format:
  ```json
  {
    "event_id": {
      "_community_feedback": {
        "suggested_impact_level": "Critical",
        "contributor_count": 5,
        "consensus_confidence": 0.8,
        "approved_by": "admin",
        "approved_date": "2025-11-25"
      }
    }
  }
  ```

---

## Implementation Notes

### Event Browser Adaptation

The Event Browser HTML from pdoom-data can be adapted:

**Original** (standalone HTML):
- Loads events from local file picker
- All processing client-side
- Exports metadata to download

**Website Version** (embedded):
- Loads events from API endpoint
- Hybrid client/server processing
- Submits metadata to server
- Add feedback button and form

### API Endpoints

**GET /api/events**
- Query params: `category`, `year_min`, `year_max`, `search`, `page`, `limit`
- Returns: `{ events: [...], total: N, page: P }`

**GET /api/events/:id**
- Returns: Full event details with impacts, sources, tags

**POST /api/events/feedback**
- Body: Feedback submission
- Returns: `{ status: 'submitted', feedback_id: X }`

**GET /api/events/:id/community-metadata**
- Returns: Community-contributed metadata for event

**GET /api/admin/feedback** (protected)
- Query params: `status`, `event_id`, `type`, `page`
- Returns: Paginated feedback submissions

### Security Considerations

- **Rate Limiting**: 5 submissions per hour per IP
- **Input Validation**: Sanitize all text inputs
- **SQL Injection**: Use parameterized queries
- **XSS Prevention**: Escape user content in display
- **CSRF Protection**: Token-based form submission
- **Authentication**: Admin routes require login
- **Data Quarantine**: Never auto-merge feedback into events

### Data Flow

```
Player Browser
    |
    v
[Event Browser Component]
    |
    v
Player submits feedback
    |
    v
POST /api/events/feedback
    |
    v
Stored in feedback table (status: pending)
    |
    v
Email notification to admin
    |
    v
[Admin Moderation Panel]
    |
    v
Admin approves feedback
    |
    v
Create/update community_metadata entry
    |
    v
Display on event page
    |
    v
Weekly export to pdoom-data
```

---

## Testing Requirements

### Unit Tests
- [ ] API endpoint parameter validation
- [ ] Feedback submission processing
- [ ] Moderation actions (approve/reject)
- [ ] Community metadata aggregation
- [ ] Export format validation

### Integration Tests
- [ ] End-to-end feedback submission
- [ ] Admin moderation workflow
- [ ] Community metadata display
- [ ] Export to pdoom-data format

### Manual Tests
- [ ] UI/UX testing on desktop and mobile
- [ ] Spam prevention mechanisms
- [ ] Performance with 1,000+ events
- [ ] Edge cases (malformed input, concurrent submissions)

---

## Success Metrics

### Engagement Metrics
- Number of feedback submissions per week
- Number of unique contributors
- Feedback approval rate
- Time to moderation (pending to approved/rejected)

### Quality Metrics
- Percentage of events with community metadata
- Consensus confidence scores
- Feedback rationale quality (subjective review)

### Goals (6 months)
- 100+ feedback submissions
- 50+ unique contributors
- 70%+ approval rate
- <48 hours average moderation time
- Community metadata on 20%+ of events

---

## Rollout Plan

### Week 1-2: Phase 1 (Read-Only Browser)
- Adapt event browser HTML for website
- Create events API endpoint
- Test on staging with real data
- Deploy to production
- Announce to community

### Week 3-4: Phase 2 (Feedback Collection)
- Build feedback form and API
- Implement rate limiting and spam prevention
- Test submission workflow
- Deploy to production
- Email existing users about new feature

### Week 5-6: Phase 3 (Moderation)
- Build admin panel
- Create moderation API endpoints
- Train moderators
- Begin processing feedback

### Week 7-8: Phase 4 (Community Metadata)
- Build community metadata system
- Display on event pages
- Export to pdoom-data format
- Set up weekly sync

---

## Documentation Requirements

- [ ] API documentation for all endpoints
- [ ] User guide for submitting feedback
- [ ] Moderator guide for review process
- [ ] Integration guide for syncing with pdoom-data
- [ ] Privacy policy update (data collection notice)

---

## Dependencies

### From pdoom-data
- Event Browser HTML/JS (`tools/event_browser.html`)
- Event Browser Guide (`docs/EVENT_BROWSER_GUIDE.md`)
- Event schema definition
- Community metadata export format

### Website Infrastructure
- PostgreSQL database with events table
- FastAPI backend
- Authentication system (for admin panel)
- Email notification system
- Rate limiting middleware

---

## Related Issues

- #XX: PostgreSQL Event Import (prerequisite)
- #XX: Website API Development (prerequisite)
- #XX: Admin Authentication System (prerequisite)

---

## Reference Links

- [Event Browser Guide](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/EVENT_BROWSER_GUIDE.md)
- [Event Schema](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/EVENT_SCHEMA.md)
- [Quick Start Integration](https://github.com/PipFoweraker/pdoom-data/blob/main/docs/QUICK_START_INTEGRATION.md)
- [Event Browser Tool](https://github.com/PipFoweraker/pdoom-data/blob/main/tools/event_browser.html)

---

## Questions for Discussion

1. Should feedback be public (visible to all players) before moderation?
2. Should we implement upvote/downvote for feedback submissions?
3. Should contributors receive in-game rewards/achievements?
4. Should we allow anonymous feedback or require email?
5. How should we handle conflicting feedback from multiple users?
6. Should we display community metadata alongside official data, or separately?

---

**Created**: 2025-11-24
**Last Updated**: 2025-11-24
**Status**: Draft
**Assigned To**: TBD
**Estimated Effort**: 4-6 weeks (all phases)
