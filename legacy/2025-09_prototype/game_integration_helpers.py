# game_integration_helpers.py
# Helper functions for integrating historical events into the pdoom1 game

from typing import Dict, List, Optional, Tuple
import random
from event_data_structures import (
    HistoricalEvent, EventCategory, ImpactType, Rarity,
    DOOM_INCREASING_EVENT_IDS, FUNDING_CRISIS_EVENT_IDS, 
    INSTITUTIONAL_DECAY_EVENT_IDS, LEGENDARY_EVENTS
)

# Import all event dictionaries
from organizational_events import ORGANIZATIONAL_EVENTS
from technical_breakthrough_events import TECHNICAL_BREAKTHROUGH_EVENTS
from funding_events import FUNDING_EVENTS
from institutional_decay_events import INSTITUTIONAL_DECAY_EVENTS

# Combine all events into master database
ALL_HISTORICAL_EVENTS: Dict[str, HistoricalEvent] = {
    **ORGANIZATIONAL_EVENTS,
    **TECHNICAL_BREAKTHROUGH_EVENTS,
    **FUNDING_EVENTS,
    **INSTITUTIONAL_DECAY_EVENTS
}

# Event chains - events that can trigger other events
EVENT_CHAINS: Dict[str, List[str]] = {
    "ftx_future_fund_collapse_2022": [
        "cais_ftx_clawback_2023",
        "ea_funding_concentration_risk_2023",
        "crypto_funding_crash_2022"
    ],
    "ai_sandbagging_research_2024": [
        "anthropic_alignment_faking_2024",
        "apollo_scheming_evals_2024"
    ],
    "openai_board_crisis_2023": [
        "openai_safety_team_departures_2024"
    ],
    "google_project_maven_2018": [
        "anthropic_exodus_2021"
    ]
}

# Probability modifiers based on game state
PROBABILITY_MODIFIERS: Dict[str, Dict[str, float]] = {
    "late_game_high_capability": {
        "ai_sandbagging_research_2024": 2.0,
        "anthropic_alignment_faking_2024": 1.8,
        "claude_4_opus_blackmail_2025": 2.5,
        "apollo_scheming_evals_2024": 1.5
    },
    "low_funding": {
        "ftx_future_fund_collapse_2022": 0.3,  # Less likely if already low funded
        "crypto_funding_crash_2022": 1.8,
        "grant_application_backlog_2024": 2.0
    },
    "high_media_attention": {
        "grok_mechahitler_2025": 1.4,
        "replit_database_wipe_2025": 1.2,
        "tesla_autopilot_incidents_2016_2024": 1.3
    },
    "high_vibey_doom": {
        "uk_ai_safety_to_security_2025": 1.5,
        "us_aisi_to_caisi_2025": 1.3,
        "safety_researcher_brain_drain_2024": 1.4
    }
}

# Rarity weights for random selection
RARITY_WEIGHTS = {
    Rarity.COMMON: 1.0,
    Rarity.UNCOMMON: 0.6,
    Rarity.RARE: 0.3,
    Rarity.LEGENDARY: 0.1
}

def get_events_by_category(category: EventCategory) -> List[HistoricalEvent]:
    """Get all events in a specific category"""
    return [event for event in ALL_HISTORICAL_EVENTS.values() if event.category == category]

def get_events_by_year_range(start_year: int, end_year: int) -> List[HistoricalEvent]:
    """Get events within a year range for game progression"""
    return [event for event in ALL_HISTORICAL_EVENTS.values() 
            if start_year <= event.year <= end_year]

def get_events_by_rarity(rarity: Rarity) -> List[HistoricalEvent]:
    """Get all events of a specific rarity"""
    return [event for event in ALL_HISTORICAL_EVENTS.values() if event.rarity == rarity]

def calculate_total_impact(event: HistoricalEvent, game_state: Dict[str, int]) -> Dict[str, int]:
    """Calculate total impact of an event on game state"""
    impact_summary = {}
    for impact in event.impacts:
        # Apply conditional logic if specified
        if impact.condition:
            # Parse condition (e.g., "if cash > 50")
            # Simple implementation - could be more sophisticated
            if not evaluate_condition(impact.condition, game_state):
                continue
                
        impact_summary[impact.variable.value] = impact.change
    
    return impact_summary

def evaluate_condition(condition: str, game_state: Dict[str, int]) -> bool:
    """Evaluate a simple condition string against game state"""
    # Simple condition parser - could be expanded
    # Example: "if cash > 50" or "requires_funding>50"
    
    if ">" in condition:
        parts = condition.split(">")
        if len(parts) == 2:
            var_name = parts[0].strip().replace("if ", "").replace("requires_", "")
            threshold = int(parts[1].strip())
            return game_state.get(var_name, 0) > threshold
    
    return True  # Default to true if condition not understood

def get_weighted_random_event(
    game_state: Dict[str, int], 
    current_year: int,
    exclude_ids: Optional[List[str]] = None
) -> Optional[HistoricalEvent]:
    """Get a weighted random event based on current game state and year"""
    
    exclude_ids = exclude_ids or []
    
    # Get events from current year ? 2 years for some flexibility
    available_events = [
        event for event in get_events_by_year_range(current_year - 2, current_year + 2)
        if event.id not in exclude_ids
    ]
    
    if not available_events:
        return None
    
    # Calculate weights based on rarity and game state modifiers
    weighted_events = []
    
    for event in available_events:
        base_weight = RARITY_WEIGHTS[event.rarity]
        
        # Apply game state modifiers
        modifier = 1.0
        
        # Check various game state conditions
        cash = game_state.get("cash", 0)
        vibey_doom = game_state.get("vibey_doom", 0)
        media_rep = game_state.get("media_reputation", 0)
        
        if cash < 20:
            modifier *= PROBABILITY_MODIFIERS.get("low_funding", {}).get(event.id, 1.0)
        
        if vibey_doom > 70:
            modifier *= PROBABILITY_MODIFIERS.get("high_vibey_doom", {}).get(event.id, 1.0)
            
        if current_year >= 2023:  # Late game
            modifier *= PROBABILITY_MODIFIERS.get("late_game_high_capability", {}).get(event.id, 1.0)
            
        if abs(media_rep) > 30:  # High media attention (positive or negative)
            modifier *= PROBABILITY_MODIFIERS.get("high_media_attention", {}).get(event.id, 1.0)
        
        final_weight = base_weight * modifier
        
        if final_weight > 0:
            weighted_events.append((event, final_weight))
    
    if not weighted_events:
        return None
    
    # Select random event based on weights
    total_weight = sum(weight for _, weight in weighted_events)
    random_value = random.uniform(0, total_weight)
    
    current_weight = 0
    for event, weight in weighted_events:
        current_weight += weight
        if random_value <= current_weight:
            return event
    
    return weighted_events[-1][0]  # Fallback

def get_triggered_events(event_id: str) -> List[str]:
    """Get events that can be triggered by the given event"""
    return EVENT_CHAINS.get(event_id, [])

def apply_event_to_game_state(event: HistoricalEvent, game_state: Dict[str, int]) -> Dict[str, int]:
    """Apply an event's impacts to the game state and return the new state"""
    new_state = game_state.copy()
    
    impacts = calculate_total_impact(event, game_state)
    
    for variable, change in impacts.items():
        current_value = new_state.get(variable, 0)
        new_state[variable] = max(0, min(100, current_value + change))  # Clamp to 0-100
    
    return new_state

def format_event_for_display(event: HistoricalEvent) -> Dict[str, str]:
    """Format an event for display in the game UI"""
    return {
        "title": event.title,
        "year": str(event.year),
        "description": event.description,
        "category": event.category.value.replace("_", " ").title(),
        "rarity": event.rarity.value.title(),
        "safety_reaction": event.safety_researcher_reaction or "",
        "media_reaction": event.media_reaction or "",
        "sources": ", ".join(event.sources[:2])  # Limit to first 2 sources for display
    }

def get_event_summary_stats() -> Dict[str, int]:
    """Get summary statistics about the event database"""
    return {
        "total_events": len(ALL_HISTORICAL_EVENTS),
        "organizational_crises": len(get_events_by_category(EventCategory.ORGANIZATIONAL_CRISIS)),
        "technical_breakthroughs": len(get_events_by_category(EventCategory.TECHNICAL_RESEARCH_BREAKTHROUGH)),
        "funding_catastrophes": len(get_events_by_category(EventCategory.FUNDING_CATASTROPHE)),
        "institutional_decay": len(get_events_by_category(EventCategory.INSTITUTIONAL_DECAY)),
        "legendary_events": len(get_events_by_rarity(Rarity.LEGENDARY)),
        "doom_increasing": len([e for e in ALL_HISTORICAL_EVENTS.values() 
                              if e.pdoom_impact and e.pdoom_impact > 0]),
        "year_range": f"{min(e.year for e in ALL_HISTORICAL_EVENTS.values())}-{max(e.year for e in ALL_HISTORICAL_EVENTS.values())}"
    }

# Export for easy importing in main game
__all__ = [
    'ALL_HISTORICAL_EVENTS',
    'EVENT_CHAINS', 
    'get_events_by_category',
    'get_events_by_year_range',
    'get_weighted_random_event',
    'apply_event_to_game_state',
    'format_event_for_display',
    'get_event_summary_stats',
    'DOOM_INCREASING_EVENT_IDS',
    'FUNDING_CRISIS_EVENT_IDS',
    'INSTITUTIONAL_DECAY_EVENT_IDS',
    'LEGENDARY_EVENTS'
]