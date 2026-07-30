# event_data_structures.py
# Core data structures for P(Doom) historical events system

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class EventCategory(Enum):
    ORGANIZATIONAL_CRISIS = "organizational_crisis"
    FUNDING_CATASTROPHE = "funding_catastrophe"
    TECHNICAL_FAILURE = "technical_failure"
    REGULATORY_POLICY = "regulatory_policy"
    MEDIA_DISASTER = "media_disaster"
    SAFETY_RESEARCH = "safety_research"
    CORPORATE_ETHICS = "corporate_ethics"
    INTERNATIONAL_COMPETITION = "international_competition"
    ACADEMIC_COMMUNITY = "academic_community"
    INSTITUTIONAL_DECAY = "institutional_decay"
    TECHNICAL_RESEARCH_BREAKTHROUGH = "technical_research_breakthrough"
    WHISTLEBLOWING = "whistleblowing"

class ImpactType(Enum):
    CASH = "cash"
    REPUTATION = "reputation" 
    RESEARCH = "research"
    PAPERS = "papers"
    ETHICS_RISK = "ethics_risk"
    STRESS = "stress"
    BURNOUT_RISK = "burnout_risk"
    TECHNICAL_DEBT = "technical_debt"
    MEDIA_REPUTATION = "media_reputation"
    VIBEY_DOOM = "vibey_doom"

class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"

@dataclass
class GameImpact:
    """Impact on specific game variables"""
    variable: ImpactType
    change: int  # positive or negative change
    condition: Optional[str] = None  # optional condition for when this applies

@dataclass
class HistoricalEvent:
    """Core structure for historical AI safety events"""
    id: str
    title: str
    year: int
    category: EventCategory
    description: str
    impacts: List[GameImpact]
    
    # Metadata
    sources: List[str]
    tags: List[str]
    probability_modifier: Optional[str] = None  # e.g., "late_game_only", "requires_funding>50"
    triggers: Optional[List[str]] = None  # other events that can trigger this
    
    # Game mechanics
    is_random_event: bool = True
    is_choice_consequence: bool = False
    rarity: Rarity = Rarity.COMMON
    
    # P(Doom) specifics
    pdoom_impact: Optional[int] = None  # direct impact on doom estimate
    safety_researcher_reaction: Optional[str] = None  # flavor text
    media_reaction: Optional[str] = None

# Quick access lists for game logic
DOOM_INCREASING_EVENT_IDS = [
    "ai_sandbagging_research_2024",
    "anthropic_alignment_faking_2024", 
    "claude_4_opus_blackmail_2025",
    "synthetic_data_scaling_2024",
    "apollo_scheming_evals_2024"
]

FUNDING_CRISIS_EVENT_IDS = [
    "ftx_future_fund_collapse_2022",
    "cais_ftx_clawback_2023",
    "crypto_funding_crash_2022"
]

INSTITUTIONAL_DECAY_EVENT_IDS = [
    "uk_ai_safety_to_security_2025",
    "us_aisi_to_caisi_2025",
    "ai_summit_pivot_2023_2025"
]

LEGENDARY_EVENTS = [
    "ai_sandbagging_research_2024",
    "anthropic_alignment_faking_2024",
    "claude_4_opus_blackmail_2025",
    "openai_board_crisis_2023"
]