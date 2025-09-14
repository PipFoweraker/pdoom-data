# Game Integration Template  
# Copy to pdoom1 repository

## Historical Events Integration

### 1. Event System Core
```python
# src/events/historical_event_system.py
import random
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import from pdoom-data (add as dependency or copy files)
from pdoom_data.game_integration_helpers import (
    ALL_HISTORICAL_EVENTS,
    get_weighted_random_event,
    apply_event_to_game_state,
    format_event_for_display,
    EVENT_CHAINS
)

@dataclass
class EventOccurrence:
    event_id: str
    year_occurred: int
    player_choice: Optional[str] = None
    impact_applied: Dict[str, int] = None

class HistoricalEventManager:
    def __init__(self):
        self.occurred_events: List[EventOccurrence] = []
        self.triggered_events: List[str] = []
        self.event_probability = 0.3  # Base chance per turn
        
    def can_trigger_event(self, event_id: str, game_state: Dict) -> bool:
        """Check if event can be triggered"""
        # Don't repeat events (unless specifically allowed)
        if event_id in [occ.event_id for occ in self.occurred_events]:
            return False
            
        # Check event-specific conditions
        event = ALL_HISTORICAL_EVENTS.get(event_id)
        if not event:
            return False
            
        # Add custom game state conditions here
        return True
    
    def process_turn_events(self, game_state: Dict, current_year: int) -> Optional[EventOccurrence]:
        """Main event processing for each game turn"""
        
        # Check for triggered events first (higher priority)
        triggered_event = self._check_triggered_events(game_state, current_year)
        if triggered_event:
            return self._apply_event(triggered_event, game_state, current_year)
        
        # Random event chance
        if random.random() < self.event_probability:
            # Use pdoom-data's weighted selection
            event = get_weighted_random_event(
                game_state, 
                current_year,
                exclude_ids=[occ.event_id for occ in self.occurred_events]
            )
            
            if event and self.can_trigger_event(event.id, game_state):
                return self._apply_event(event, game_state, current_year)
        
        return None
    
    def _check_triggered_events(self, game_state: Dict, current_year: int):
        """Check for events triggered by previous events"""
        for event_occurrence in self.occurred_events:
            triggered_ids = EVENT_CHAINS.get(event_occurrence.event_id, [])
            
            for triggered_id in triggered_ids:
                if (triggered_id not in self.triggered_events and 
                    triggered_id not in [occ.event_id for occ in self.occurred_events]):
                    
                    event = ALL_HISTORICAL_EVENTS.get(triggered_id)
                    if event and self.can_trigger_event(triggered_id, game_state):
                        self.triggered_events.append(triggered_id)
                        return event
        
        return None
    
    def _apply_event(self, event, game_state: Dict, current_year: int) -> EventOccurrence:
        """Apply event effects and record occurrence"""
        
        # Apply game state changes using pdoom-data logic
        new_state = apply_event_to_game_state(event, game_state)
        impact_applied = {
            var: new_state.get(var, 0) - game_state.get(var, 0)
            for var in new_state.keys()
        }
        
        # Record the occurrence
        occurrence = EventOccurrence(
            event_id=event.id,
            year_occurred=current_year,
            impact_applied=impact_applied
        )
        self.occurred_events.append(occurrence)
        
        return occurrence
    
    def get_event_history(self) -> List[EventOccurrence]:
        """Get chronological list of events that have occurred"""
        return sorted(self.occurred_events, key=lambda x: x.year_occurred)
    
    def export_analytics(self) -> Dict:
        """Export event analytics for debugging/balancing"""
        return {
            'total_events': len(self.occurred_events),
            'events_by_category': self._count_by_category(),
            'legendary_events': self._count_legendary(),
            'average_doom_impact': self._average_doom_impact(),
            'event_timeline': [
                {
                    'id': occ.event_id,
                    'year': occ.year_occurred,
                    'impacts': occ.impact_applied
                }
                for occ in self.occurred_events
            ]
        }
    
    def _count_by_category(self) -> Dict[str, int]:
        counts = {}
        for occ in self.occurred_events:
            event = ALL_HISTORICAL_EVENTS.get(occ.event_id)
            if event:
                category = event.category.value
                counts[category] = counts.get(category, 0) + 1
        return counts
    
    def _count_legendary(self) -> int:
        return sum(1 for occ in self.occurred_events 
                  if ALL_HISTORICAL_EVENTS.get(occ.event_id, None) and
                     ALL_HISTORICAL_EVENTS[occ.event_id].rarity.value == 'legendary')
    
    def _average_doom_impact(self) -> float:
        doom_impacts = []
        for occ in self.occurred_events:
            if occ.impact_applied and 'vibey_doom' in occ.impact_applied:
                doom_impacts.append(occ.impact_applied['vibey_doom'])
        
        return sum(doom_impacts) / len(doom_impacts) if doom_impacts else 0.0
```

### 2. UI Event Display System
```python
# src/ui/event_popup.py
import pygame
from typing import Dict, Optional
from pdoom_data.game_integration_helpers import format_event_for_display, ALL_HISTORICAL_EVENTS

class EventPopup:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 14)
        
        # Colors (ASCII-safe color names)
        self.colors = {
            'background': (30, 30, 30),
            'popup_bg': (50, 50, 50),
            'border': (100, 100, 100),
            'text': (255, 255, 255),
            'legendary': (255, 100, 100),
            'rare': (100, 255, 100),
            'button': (70, 130, 180),
            'button_hover': (100, 160, 210)
        }
    
    def display_event(self, screen, event_id: str, game_state: Dict) -> str:
        """Display event popup and return player choice"""
        
        event = ALL_HISTORICAL_EVENTS.get(event_id)
        if not event:
            return "continue"
        
        # Format event for display
        display_data = format_event_for_display(event)
        
        # Create popup rectangle
        popup_width = min(600, self.screen_width - 100)
        popup_height = min(500, self.screen_height - 100)
        popup_x = (self.screen_width - popup_width) // 2
        popup_y = (self.screen_height - popup_height) // 2
        
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        
        # Event loop for popup
        clock = pygame.time.Clock()
        choice = None
        
        while choice is None:
            for event_input in pygame.event.get():
                if event_input.type == pygame.QUIT:
                    return "quit"
                elif event_input.type == pygame.KEYDOWN:
                    if event_input.key == pygame.K_RETURN or event_input.key == pygame.K_SPACE:
                        choice = "continue"
                elif event_input.type == pygame.MOUSEBUTTONDOWN:
                    # Check if clicked on continue button
                    button_rect = pygame.Rect(popup_x + popup_width - 120, 
                                            popup_y + popup_height - 40, 
                                            100, 30)
                    if button_rect.collidepoint(event_input.pos):
                        choice = "continue"
            
            # Draw popup
            self._draw_event_popup(screen, popup_rect, display_data, event)
            pygame.display.flip()
            clock.tick(60)
        
        return choice
    
    def _draw_event_popup(self, screen, popup_rect, display_data, event):
        """Draw the event popup"""
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill(self.colors['background'])
        screen.blit(overlay, (0, 0))
        
        # Popup background
        pygame.draw.rect(screen, self.colors['popup_bg'], popup_rect)
        pygame.draw.rect(screen, self.colors['border'], popup_rect, 2)
        
        # Rarity indicator
        rarity_color = self.colors['legendary'] if event.rarity.value == 'legendary' else \
                      self.colors['rare'] if event.rarity.value == 'rare' else \
                      self.colors['text']
        
        # Title and year
        title_text = self.font_large.render(f"{display_data['title']} ({display_data['year']})", 
                                          True, rarity_color)
        screen.blit(title_text, (popup_rect.x + 20, popup_rect.y + 20))
        
        # Category and rarity
        category_text = self.font_small.render(f"{display_data['category']} - {display_data['rarity']}", 
                                             True, self.colors['text'])
        screen.blit(category_text, (popup_rect.x + 20, popup_rect.y + 50))
        
        # Description (word wrapped)
        self._draw_wrapped_text(screen, display_data['description'], 
                               popup_rect.x + 20, popup_rect.y + 80, 
                               popup_rect.width - 40, self.font_medium, self.colors['text'])
        
        # Researcher reaction
        if display_data['safety_reaction']:
            reaction_y = popup_rect.y + 200
            reaction_label = self.font_small.render("Safety Researcher:", True, self.colors['text'])
            screen.blit(reaction_label, (popup_rect.x + 20, reaction_y))
            
            self._draw_wrapped_text(screen, f'"{display_data["safety_reaction"]}"',
                                   popup_rect.x + 20, reaction_y + 20,
                                   popup_rect.width - 40, self.font_small, self.colors['text'])
        
        # Media reaction
        if display_data['media_reaction']:
            media_y = popup_rect.y + 280
            media_label = self.font_small.render("Media Coverage:", True, self.colors['text'])
            screen.blit(media_label, (popup_rect.x + 20, media_y))
            
            self._draw_wrapped_text(screen, f'"{display_data["media_reaction"]}"',
                                   popup_rect.x + 20, media_y + 20,
                                   popup_rect.width - 40, self.font_small, self.colors['text'])
        
        # Continue button
        button_rect = pygame.Rect(popup_rect.x + popup_rect.width - 120, 
                                 popup_rect.y + popup_rect.height - 40, 
                                 100, 30)
        
        mouse_pos = pygame.mouse.get_pos()
        button_color = self.colors['button_hover'] if button_rect.collidepoint(mouse_pos) else self.colors['button']
        
        pygame.draw.rect(screen, button_color, button_rect)
        pygame.draw.rect(screen, self.colors['border'], button_rect, 1)
        
        button_text = self.font_medium.render("Continue", True, self.colors['text'])
        text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, text_rect)
    
    def _draw_wrapped_text(self, screen, text, x, y, max_width, font, color):
        """Draw text with word wrapping"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        for i, line in enumerate(lines):
            line_surface = font.render(line, True, color)
            screen.blit(line_surface, (x, y + i * font.get_height()))
```

### 3. Save/Load Integration
```python
# src/save_system/event_persistence.py
import json
from typing import Dict, List
from src.events.historical_event_system import EventOccurrence, HistoricalEventManager

class EventSaveData:
    @staticmethod
    def save_event_state(event_manager: HistoricalEventManager, save_data: Dict):
        """Add event data to save file"""
        save_data['events'] = {
            'occurred_events': [
                {
                    'event_id': occ.event_id,
                    'year_occurred': occ.year_occurred,
                    'player_choice': occ.player_choice,
                    'impact_applied': occ.impact_applied
                }
                for occ in event_manager.occurred_events
            ],
            'triggered_events': event_manager.triggered_events,
            'event_probability': event_manager.event_probability
        }
    
    @staticmethod
    def load_event_state(save_data: Dict) -> HistoricalEventManager:
        """Recreate event manager from save data"""
        event_manager = HistoricalEventManager()
        
        if 'events' in save_data:
            event_data = save_data['events']
            
            # Restore occurred events
            for occ_data in event_data.get('occurred_events', []):
                occurrence = EventOccurrence(
                    event_id=occ_data['event_id'],
                    year_occurred=occ_data['year_occurred'],
                    player_choice=occ_data.get('player_choice'),
                    impact_applied=occ_data.get('impact_applied', {})
                )
                event_manager.occurred_events.append(occurrence)
            
            # Restore triggered events
            event_manager.triggered_events = event_data.get('triggered_events', [])
            event_manager.event_probability = event_data.get('event_probability', 0.3)
        
        return event_manager
```

### 4. Game Loop Integration
```python
# src/core/game_loop.py
from src.events.historical_event_system import HistoricalEventManager
from src.ui.event_popup import EventPopup

class GameLoop:
    def __init__(self):
        self.event_manager = HistoricalEventManager()
        self.event_popup = EventPopup(800, 600)  # screen dimensions
        
    def process_turn(self, game_state: Dict, current_year: int):
        """Main turn processing"""
        
        # ... existing turn logic ...
        
        # Process historical events
        event_occurrence = self.event_manager.process_turn_events(game_state, current_year)
        
        if event_occurrence:
            # Display event to player
            choice = self.event_popup.display_event(
                self.screen, 
                event_occurrence.event_id, 
                game_state
            )
            
            if choice == "quit":
                return "quit"
            
            # Apply impacts to game state (already done in event_manager)
            # Update UI to reflect changes
            self.update_ui_after_event(event_occurrence)
            
            # Log for analytics
            self.log_event_occurrence(event_occurrence, game_state)
        
        # ... continue turn processing ...
```

### 5. Configuration
```python
# config/events_config.py
EVENT_CONFIG = {
    'enabled': True,
    'base_probability': 0.3,
    'allow_repeated_events': False,
    'year_flexibility': 2,  # Events can occur +/- 2 years from historical date
    'legendary_boost': 1.5,  # Multiplier for legendary event chances in late game
    'difficulty_scaling': {
        'easy': 0.8,     # 80% of normal event frequency
        'normal': 1.0,   # Normal frequency
        'hard': 1.3      # 130% frequency
    },
    'categories_enabled': {
        'organizational_crisis': True,
        'technical_research_breakthrough': True,
        'funding_catastrophe': True,
        'institutional_decay': True
    }
}
```

This template provides:
- Complete historical event integration
- Save/load compatibility  
- UI display system
- Game loop integration
- Configuration options
- Analytics and debugging tools

Copy to your pdoom1 repository and customize for your specific game engine.
