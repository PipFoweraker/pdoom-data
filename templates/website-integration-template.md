# Website Integration Template
# Copy to pdoom-website repository

## Data Consumption from pdoom-data

### 1. Fetch Historical Events Data
```javascript
// src/services/eventDataService.js
export class EventDataService {
  constructor() {
    this.baseUrl = process.env.REACT_APP_DATA_URL || '/data';
    this.eventsCache = null;
  }

  async getHistoricalEvents() {
    if (this.eventsCache) return this.eventsCache;
    
    try {
      const response = await fetch(`${this.baseUrl}/events/historical_events.json`);
      const data = await response.json();
      this.eventsCache = data;
      return data;
    } catch (error) {
      console.error('Failed to load historical events:', error);
      return {};
    }
  }

  async getEventsByCategory(category) {
    const events = await this.getHistoricalEvents();
    return Object.values(events).filter(event => event.category === category);
  }

  async getEventsByYear(year) {
    const events = await this.getHistoricalEvents();
    return Object.values(events).filter(event => event.year === year);
  }

  async getLegendaryEvents() {
    const events = await this.getHistoricalEvents();
    return Object.values(events).filter(event => event.rarity === 'legendary');
  }
}
```

### 2. Event Timeline Component
```javascript
// src/components/EventTimeline.js
import React, { useState, useEffect } from 'react';
import { EventDataService } from '../services/eventDataService';

export function EventTimeline() {
  const [events, setEvents] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const eventService = new EventDataService();
    
    const loadEvents = async () => {
      try {
        const eventData = await eventService.getHistoricalEvents();
        const eventArray = Object.values(eventData).sort((a, b) => a.year - b.year);
        setEvents(eventArray);
      } catch (error) {
        console.error('Error loading events:', error);
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
  }, []);

  const filteredEvents = selectedCategory === 'all' 
    ? events 
    : events.filter(event => event.category === selectedCategory);

  if (loading) return <div>Loading historical events...</div>;

  return (
    <div className="event-timeline">
      <div className="filter-controls">
        <select 
          value={selectedCategory} 
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="all">All Categories</option>
          <option value="organizational_crisis">Organizational Crises</option>
          <option value="technical_research_breakthrough">Technical Breakthroughs</option>
          <option value="funding_catastrophe">Funding Catastrophes</option>
          <option value="institutional_decay">Institutional Decay</option>
        </select>
      </div>

      <div className="timeline">
        {filteredEvents.map(event => (
          <EventCard key={event.id} event={event} />
        ))}
      </div>
    </div>
  );
}

function EventCard({ event }) {
  return (
    <div className={`event-card rarity-${event.rarity}`}>
      <div className="event-header">
        <h3>{event.title}</h3>
        <span className="event-year">{event.year}</span>
        <span className="event-category">{event.category.replace('_', ' ')}</span>
      </div>
      
      <div className="event-content">
        <p>{event.description}</p>
        
        {event.safety_researcher_reaction && (
          <blockquote className="researcher-reaction">
            {event.safety_researcher_reaction}
          </blockquote>
        )}
        
        {event.media_reaction && (
          <div className="media-reaction">
            <strong>Media:</strong> {event.media_reaction}
          </div>
        )}
      </div>
      
      <div className="event-footer">
        <div className="game-impacts">
          {event.impacts.map((impact, index) => (
            <span key={index} className={`impact ${impact.change > 0 ? 'positive' : 'negative'}`}>
              {impact.variable}: {impact.change > 0 ? '+' : ''}{impact.change}
            </span>
          ))}
        </div>
        
        <div className="event-sources">
          {event.sources.map((source, index) => (
            <a key={index} href={source} target="_blank" rel="noopener noreferrer">
              Source {index + 1}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 3. CSS Styling for Events
```css
/* src/styles/eventTimeline.css */
.event-timeline {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.filter-controls {
  margin-bottom: 30px;
  text-align: center;
}

.filter-controls select {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.event-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.event-card.rarity-legendary {
  border-color: #ff6b6b;
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
}

.event-card.rarity-rare {
  border-color: #4ecdc4;
  background: linear-gradient(135deg, #f0fdfc 0%, #ffffff 100%);
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.event-header h3 {
  margin: 0;
  color: #333;
  flex: 1;
}

.event-year {
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  margin-left: 10px;
}

.event-category {
  background: #6c757d;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 5px;
  text-transform: capitalize;
}

.researcher-reaction {
  font-style: italic;
  border-left: 3px solid #007bff;
  padding-left: 15px;
  margin: 15px 0;
  color: #555;
}

.media-reaction {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  margin: 15px 0;
}

.event-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.game-impacts {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.impact {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.impact.positive {
  background: #d4edda;
  color: #155724;
}

.impact.negative {
  background: #f8d7da;
  color: #721c24;
}

.event-sources {
  display: flex;
  gap: 10px;
}

.event-sources a {
  color: #007bff;
  text-decoration: none;
  font-size: 12px;
}

.event-sources a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .event-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .event-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
```

### 4. Data Sync Automation
```javascript
// scripts/syncEventData.js
const fs = require('fs');
const path = require('path');
const https = require('https');

class EventDataSyncer {
  constructor(config) {
    this.sourceRepo = config.sourceRepo || 'https://raw.githubusercontent.com/PipFoweraker/pdoom-data/main';
    this.targetDir = config.targetDir || './public/data/events';
  }

  async syncHistoricalEvents() {
    try {
      console.log('Syncing historical events data...');
      
      const dataUrl = `${this.sourceRepo}/data/events/historical_events.json`;
      const localPath = path.join(this.targetDir, 'historical_events.json');
      
      await this.downloadFile(dataUrl, localPath);
      
      console.log('Successfully synced historical events data');
      return true;
    } catch (error) {
      console.error('Failed to sync event data:', error);
      return false;
    }
  }

  async downloadFile(url, localPath) {
    return new Promise((resolve, reject) => {
      // Ensure directory exists
      const dir = path.dirname(localPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      const file = fs.createWriteStream(localPath);
      
      https.get(url, (response) => {
        response.pipe(file);
        
        file.on('finish', () => {
          file.close();
          resolve();
        });
        
        file.on('error', (error) => {
          fs.unlink(localPath, () => {}); // Delete partial file
          reject(error);
        });
      }).on('error', reject);
    });
  }
}

// Usage
const syncer = new EventDataSyncer({
  targetDir: './public/data/events'
});

syncer.syncHistoricalEvents()
  .then(success => {
    process.exit(success ? 0 : 1);
  });
```

### 5. Package.json Scripts
```json
{
  "scripts": {
    "sync-events": "node scripts/syncEventData.js",
    "build": "npm run sync-events && react-scripts build",
    "prebuild": "npm run sync-events"
  }
}
```

### 6. Environment Configuration
```env
# .env
REACT_APP_DATA_URL=/data
REACT_APP_PDOOM_DATA_REPO=https://github.com/PipFoweraker/pdoom-data
REACT_APP_PDOOM_GAME_URL=https://github.com/PipFoweraker/pdoom1
```

This template provides:
- Complete data consumption from pdoom-data
- Interactive event timeline component
- Responsive CSS styling
- Automated data synchronization
- Build-time data fetching

Copy these files to your pdoom-website repository and customize as needed.
