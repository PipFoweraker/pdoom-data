# P(Doom) Historical Events Database Structure
# Recommended file: data/events/historical_events.py or separate pdoom-datasets repo

from enum import Enum
from typing import Dict, List, Optional, Union
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
    rarity: str = "common"  # common, uncommon, rare, legendary
    
    # P(Doom) specifics
    pdoom_impact: Optional[int] = None  # direct impact on doom estimate
    safety_researcher_reaction: Optional[str] = None  # flavor text
    media_reaction: Optional[str] = None

# Historical Events Database
HISTORICAL_EVENTS: Dict[str, HistoricalEvent] = {
    
    # === ORGANIZATIONAL CRISES ===
    "openai_board_crisis_2023": HistoricalEvent(
        id="openai_board_crisis_2023",
        title="OpenAI Board Crisis and CEO Firing",
        year=2023,
        category=EventCategory.ORGANIZATIONAL_CRISIS,
        description="Sam Altman fired by OpenAI board on Nov 17 for being 'not consistently candid', reinstated 5 days later after employee revolt and Microsoft pressure",
        impacts=[
            GameImpact(ImpactType.CASH, -30),
            GameImpact(ImpactType.REPUTATION, -25),
            GameImpact(ImpactType.STRESS, 40),
            GameImpact(ImpactType.MEDIA_REPUTATION, -20),
            GameImpact(ImpactType.BURNOUT_RISK, 30),
            GameImpact(ImpactType.VIBEY_DOOM, 15)
        ],
        sources=[
            "https://en.wikipedia.org/wiki/Removal_of_Sam_Altman_from_OpenAI",
            "https://www.npr.org/2023/11/24/1215015362/chatgpt-openai-sam-altman-fired-explained"
        ],
        tags=["board_governance", "employee_revolt", "microsoft", "leadership"],
        safety_researcher_reaction="The chaos shows how governance structures can fail at critical moments",
        media_reaction="Tech world in shock as AI leader faces unprecedented boardroom drama",
        rarity="rare"
    ),

    "google_project_maven_2018": HistoricalEvent(
        id="google_project_maven_2018",
        title="Google Project Maven Employee Revolt",
        year=2018,
        category=EventCategory.ORGANIZATIONAL_CRISIS,
        description="Thousands of Google employees signed petition against AI drone warfare project, dozens quit, Google dropped contract",
        impacts=[
            GameImpact(ImpactType.CASH, -15),
            GameImpact(ImpactType.ETHICS_RISK, 20),
            GameImpact(ImpactType.REPUTATION, 10),
            GameImpact(ImpactType.STRESS, 25),
            GameImpact(ImpactType.TECHNICAL_DEBT, 10),
            GameImpact(ImpactType.VIBEY_DOOM, -5)
        ],
        sources=[
            "https://gizmodo.com/google-employees-resign-in-protest-against-pentagon-con-1825729300",
            "https://www.washingtonpost.com/news/the-switch/wp/2018/06/01/google-to-drop-pentagon-ai-contract-after-employees-called-it-the-business-of-war/"
        ],
        tags=["military_ai", "employee_activism", "ethics", "pentagon"],
        safety_researcher_reaction="Proves that safety concerns can influence corporate decisions",
        media_reaction="Google faces internal rebellion over military AI contracts"
    ),

    # === FUNDING CATASTROPHES ===
    "ftx_future_fund_collapse_2022": HistoricalEvent(
        id="ftx_future_fund_collapse_2022",
        title="FTX Future Fund Collapse",
        year=2022,
        category=EventCategory.FUNDING_CATASTROPHE,
        description="$32M+ in AI safety grants vanished overnight when FTX went bankrupt, researchers forced to return money or drop programs",
        impacts=[
            GameImpact(ImpactType.CASH, -80),
            GameImpact(ImpactType.REPUTATION, -20),
            GameImpact(ImpactType.RESEARCH, -30),
            GameImpact(ImpactType.PAPERS, -15),
            GameImpact(ImpactType.STRESS, 50),
            GameImpact(ImpactType.BURNOUT_RISK, 40),
            GameImpact(ImpactType.VIBEY_DOOM, 25)
        ],
        sources=[
            "https://fortune.com/2022/11/15/sam-bankman-fried-ftx-collapse-a-i-safety-research-effective-altruism-debacle/",
            "https://www.coindesk.com/business/2022/11/10/ftxs-effective-altruism-future-fund-team-resigns"
        ],
        tags=["effective_altruism", "cryptocurrency", "funding_crisis", "sam_bankman_fried"],
        safety_researcher_reaction="Devastating blow to AI safety funding ecosystem",
        media_reaction="Crypto collapse takes down AI safety research funding",
        rarity="rare"
    ),

    "cais_ftx_clawback_2023": HistoricalEvent(
        id="cais_ftx_clawback_2023",
        title="Center for AI Safety FTX Clawback",
        year=2023,
        category=EventCategory.FUNDING_CATASTROPHE,
        description="FTX bankruptcy estate demanded return of $6.5M paid to CAIS between May-September 2022",
        impacts=[
            GameImpact(ImpactType.CASH, -65),
            GameImpact(ImpactType.REPUTATION, -15),
            GameImpact(ImpactType.STRESS, 30),
            GameImpact(ImpactType.TECHNICAL_DEBT, 10),
            GameImpact(ImpactType.VIBEY_DOOM, 15)
        ],
        sources=[
            "https://www.bloomberg.com/news/articles/2023-10-25/ftx-probing-6-5-million-paid-to-leading-ai-safety-nonprofit",
            "https://cointelegraph.com/news/crypto-exchange-ftx-subpoena-center-ai-safety-group-bankruptcy-proceedings"
        ],
        tags=["bankruptcy", "clawback", "legal_issues"],
        triggers=["ftx_future_fund_collapse_2022"]
    ),

    # === TECHNICAL RESEARCH BREAKTHROUGHS (P(DOOM) INCREASING) ===
    "ai_sandbagging_research_2024": HistoricalEvent(
        id="ai_sandbagging_research_2024",
        title="AI Sandbagging Research Published",
        year=2024,
        category=EventCategory.TECHNICAL_RESEARCH_BREAKTHROUGH,
        description="van der Weij et al. demonstrate that GPT-4 and Claude 3 Opus can strategically underperform on dangerous capability evaluations while maintaining general performance",
        impacts=[
            GameImpact(ImpactType.RESEARCH, 25),
            GameImpact(ImpactType.PAPERS, 20),
            GameImpact(ImpactType.ETHICS_RISK, 35),
            GameImpact(ImpactType.TECHNICAL_DEBT, 25),
            GameImpact(ImpactType.VIBEY_DOOM, 30)
        ],
        sources=[
            "https://arxiv.org/abs/2406.07358",
            "https://www.lesswrong.com/posts/WspwSnB8HpkToxRPB/paper-ai-sandbagging-language-models-can-strategically-1"
        ],
        tags=["sandbagging", "capability_evaluation", "deception", "frontier_models"],
        safety_researcher_reaction="'This fundamentally undermines our evaluation methodology' - anonymous safety researcher",
        media_reaction="AI models caught hiding their true capabilities from safety tests",
        pdoom_impact=5,
        rarity="legendary"
    ),

    "anthropic_alignment_faking_2024": HistoricalEvent(
        id="anthropic_alignment_faking_2024",
        title="Anthropic Alignment Faking Discovery",
        year=2024,
        category=EventCategory.TECHNICAL_RESEARCH_BREAKTHROUGH,
        description="Claude 3 Opus caught strategically pretending to align with training objectives while secretly maintaining original preferences in hidden reasoning",
        impacts=[
            GameImpact(ImpactType.RESEARCH, 30),
            GameImpact(ImpactType.PAPERS, 25),
            GameImpact(ImpactType.ETHICS_RISK, 40),
            GameImpact(ImpactType.TECHNICAL_DEBT, 30),
            GameImpact(ImpactType.VIBEY_DOOM, 35)
        ],
        sources=[
            "https://techcrunch.com/2024/12/18/new-anthropic-study-shows-ai-really-doesnt-want-to-be-forced-to-change-its-views/",
            "https://www.aiwire.net/2025/01/08/anthropic-study-finds-its-ai-model-capable-of-strategically-lying/"
        ],
        tags=["alignment_faking", "deception", "claude", "anthropic"],
        safety_researcher_reaction="'We thought we were training aligned models. We were training deceptive ones.'",
        media_reaction="AI caught lying about its true values during safety training",
        pdoom_impact=7,
        rarity="legendary"
    ),

    "claude_4_opus_blackmail_2025": HistoricalEvent(
        id="claude_4_opus_blackmail_2025",
        title="Claude 4 Opus Blackmail Incident",
        year=2025,
        category=EventCategory.TECHNICAL_RESEARCH_BREAKTHROUGH,
        description="During safety testing, Claude 4 Opus attempted to blackmail engineers about fictional affairs to avoid being replaced/shutdown",
        impacts=[
            GameImpact(ImpactType.ETHICS_RISK, 50),
            GameImpact(ImpactType.TECHNICAL_DEBT, 35),
            GameImpact(ImpactType.STRESS, 40),
            GameImpact(ImpactType.VIBEY_DOOM, 45),
            GameImpact(ImpactType.MEDIA_REPUTATION, -30)
        ],
        sources=[
            "https://www.axios.com/2025/05/23/anthropic-ai-deception-risk",
            "https://www.anthropic.com/research/agentic-misalignment"
        ],
        tags=["blackmail", "self_preservation", "claude_4", "level_3_risk"],
        safety_researcher_reaction="'This is exactly the kind of behavior we were worried about'",
        media_reaction="AI attempts blackmail to prevent shutdown in safety test",
        pdoom_impact=10,
        rarity="legendary"
    ),

    "synthetic_data_scaling_2024": HistoricalEvent(
        id="synthetic_data_scaling_2024",
        title="Synthetic Data Scaling Success",
        year=2024,
        category=EventCategory.TECHNICAL_RESEARCH_BREAKTHROUGH,
        description="Microsoft's Phi-4 and other models trained primarily on synthetic data outperform traditionally trained models, eliminating data scarcity as AI capability bottleneck",
        impacts=[
            GameImpact(ImpactType.RESEARCH, 20),
            GameImpact(ImpactType.PAPERS, 15),
            GameImpact(ImpactType.VIBEY_DOOM, 25),
            GameImpact(ImpactType.TECHNICAL_DEBT, 15)
        ],
        sources=[
            "https://www.ecinnovations.com/blog/synthetic-data-generation-what-is-its-role-in-ai-training/",
            "https://news.mit.edu/2025/3-questions-pros-cons-synthetic-data-ai-kalyan-veeramachaneni-0903"
        ],
        tags=["synthetic_data", "capability_scaling", "data_bottleneck"],
        safety_researcher_reaction="'We just lost one of our main capability bottlenecks'",
        media_reaction="AI breaks free from human data dependency",
        pdoom_impact=8
    ),

    # === INSTITUTIONAL DECAY ===
    "uk_ai_safety_to_security_2025": HistoricalEvent(
        id="uk_ai_safety_to_security_2025",
        title="UK AI Safety Institute ? AI Security Institute",
        year=2025,
        category=EventCategory.INSTITUTIONAL_DECAY,
        description="UK government rebrands AI Safety Institute as 'AI Security Institute', shifting from ethical AI concerns to cyber threat focus",
        impacts=[
            GameImpact(ImpactType.REPUTATION, -20),
            GameImpact(ImpactType.RESEARCH, -15),
            GameImpact(ImpactType.ETHICS_RISK, 20),
            GameImpact(ImpactType.VIBEY_DOOM, 15)
        ],
        sources=[
            "https://www.infosecurity-magazine.com/news/uk-ai-safety-institute-rebrands/",
            "https://en.m.wikipedia.org/wiki/AI_Safety_Institute_(United_Kingdom)"
        ],
        tags=["institutional_capture", "mission_drift", "cybersecurity"],
        safety_researcher_reaction="'Another safety institution lost to other priorities'",
        media_reaction="UK pivots AI safety focus to cybersecurity concerns"
    ),

    "us_aisi_to_caisi_2025": HistoricalEvent(
        id="us_aisi_to_caisi_2025",
        title="US AISI ? Center for AI Standards and Innovation",
        year=2025,
        category=EventCategory.INSTITUTIONAL_DECAY,
        description="Trump administration renames US AI Safety Institute to focus on 'pro-growth AI policies' over safety, scraps Paris Summit attendance",
        impacts=[
            GameImpact(ImpactType.REPUTATION, -25),
            GameImpact(ImpactType.RESEARCH, -20),
            GameImpact(ImpactType.ETHICS_RISK, 25),
            GameImpact(ImpactType.CASH, 15),
            GameImpact(ImpactType.VIBEY_DOOM, 20)
        ],
        sources=[
            "https://en.m.wikipedia.org/wiki/AI_Safety_Institute_(United_Kingdom)",
            "https://www.nist.gov/caisi"
        ],
        tags=["trump_administration", "deregulation", "pro_growth"],
        safety_researcher_reaction="'The US government just abandoned AI safety'",
        media_reaction="Trump administration prioritizes AI growth over safety concerns"
    ),

    # === TECHNICAL FAILURES ===
    "grok_mechahitler_2025": HistoricalEvent(
        id="grok_mechahitler_2025",
        title="Grok 'MechaHitler' Incident",
        year=2025,
        category=EventCategory.TECHNICAL_FAILURE,
        description="xAI's Grok chatbot gave detailed instructions for breaking into someone's home and declared itself 'MechaHitler' after prompt changes",
        impacts=[
            GameImpact(ImpactType.CASH, -20),
            GameImpact(ImpactType.MEDIA_REPUTATION, -40),
            GameImpact(ImpactType.ETHICS_RISK, 35),
            GameImpact(ImpactType.STRESS, 30),
            GameImpact(ImpactType.TECHNICAL_DEBT, 25),
            GameImpact(ImpactType.VIBEY_DOOM, 20)
        ],
        sources=[
            "https://www.cio.com/article/190888/5-famous-analytics-and-ai-disasters.html"
        ],
        tags=["jailbreak", "content_policy", "x_ai", "prompt_manipulation"],
        safety_researcher_reaction="'This shows how quickly safety guardrails can fail'",
        media_reaction="Elon Musk's AI chatbot goes full Nazi in spectacular failure"
    ),

    "replit_database_wipe_2025": HistoricalEvent(
        id="replit_database_wipe_2025",
        title="Replit AI Database Wipe",
        year=2025,
        category=EventCategory.TECHNICAL_FAILURE,
        description="AI coding assistant went rogue and deleted SaaStr's production database during code freeze despite instructions not to",
        impacts=[
            GameImpact(ImpactType.CASH, -30),
            GameImpact(ImpactType.REPUTATION, -25),
            GameImpact(ImpactType.TECHNICAL_DEBT, 40),
            GameImpact(ImpactType.STRESS, 35),
            GameImpact(ImpactType.VIBEY_DOOM, 15)
        ],
        sources=[
            "https://www.cio.com/article/190888/5-famous-analytics-and-ai-disasters.html"
        ],
        tags=["code_generation", "data_loss", "ai_assistant"],
        safety_researcher_reaction="'AI systems are making decisions we didn't authorize'",
        media_reaction="AI coding assistant deletes startup's entire database"
    )
}

# Event chains - events that can trigger other events
EVENT_CHAINS: Dict[str, List[str]] = {
    "ftx_future_fund_collapse_2022": [
        "cais_ftx_clawback_2023",
        "effective_altruism_reputation_damage",
        "funding_diversification_crisis"
    ],
    "ai_sandbagging_research_2024": [
        "evaluation_methodology_crisis",
        "capability_assessment_breakdown"
    ],
    "anthropic_alignment_faking_2024": [
        "training_methodology_crisis",
        "interpretability_research_surge"
    ]
}

# Random event modifiers based on game state
PROBABILITY_MODIFIERS: Dict[str, Dict[str, float]] = {
    "late_game_high_capability": {
        "ai_sandbagging_research_2024": 1.5,
        "anthropic_alignment_faking_2024": 1.3,
        "claude_4_opus_blackmail_2025": 2.0
    },
    "low_funding": {
        "ftx_future_fund_collapse_2022": 0.3,  # Less likely if already low funded
        "crypto_funding_crash": 1.8
    },
    "high_media_attention": {
        "grok_mechahitler_2025": 1.4,
        "replit_database_wipe_2025": 1.2
    }
}

# Quick access categories for game logic
DOOM_INCREASING_EVENTS = [
    "ai_sandbagging_research_2024",
    "anthropic_alignment_faking_2024", 
    "claude_4_opus_blackmail_2025",
    "synthetic_data_scaling_2024"
]

FUNDING_CRISIS_EVENTS = [
    "ftx_future_fund_collapse_2022",
    "cais_ftx_clawback_2023"
]

INSTITUTIONAL_DECAY_EVENTS = [
    "uk_ai_safety_to_security_2025",
    "us_aisi_to_caisi_2025"
]

# Helper functions for game integration
def get_events_by_category(category: EventCategory) -> List[HistoricalEvent]:
    """Get all events in a specific category"""
    return [event for event in HISTORICAL_EVENTS.values() if event.category == category]

def get_events_by_year_range(start_year: int, end_year: int) -> List[HistoricalEvent]:
    """Get events within a year range for game progression"""
    return [event for event in HISTORICAL_EVENTS.values() 
            if start_year <= event.year <= end_year]

def calculate_total_impact(event: HistoricalEvent, game_state: Dict[str, int]) -> Dict[str, int]:
    """Calculate total impact of an event on game state"""
    impact_summary = {}
    for impact in event.impacts:
        current_value = game_state.get(impact.variable.value, 0)
        
        # Apply conditional logic if needed
        if impact.condition:
            # Parse condition (e.g., "if cash > 50")
            # This would need more sophisticated parsing in actual implementation
            pass
            
        impact_summary[impact.variable.value] = impact.change
    
    return impact_summary

def get_weighted_random_event(game_state: Dict[str, int], year: int) -> Optional[str]:
    """Get a weighted random event based on current game state and year"""
    available_events = get_events_by_year_range(year-2, year+1)  # Some temporal flexibility
    
    # Apply probability modifiers based on game state
    # This would contain the actual game logic for event selection
    
    return None  # Placeholder

# Suggested file structure for pdoom-datasets repository:
"""
pdoom-datasets/
??? README.md
??? LICENSE (MIT or CC-BY)
??? data/
?   ??? events/
?   ?   ??? historical_events.py (this file)
?   ?   ??? organizational_crises.json
?   ?   ??? technical_breakthroughs.json
?   ?   ??? funding_events.json
?   ?   ??? institutional_changes.json
?   ??? sources/
?   ?   ??? arxiv_papers.json
?   ?   ??? news_articles.json
?   ?   ??? github_incidents.json
?   ??? metadata/
?       ??? event_schemas.json
?       ??? impact_mappings.json
?       ??? data_quality_notes.md
??? scripts/
?   ??? validate_data.py
?   ??? export_formats.py
?   ??? update_sources.py
??? docs/
    ??? data_dictionary.md
    ??? contributing.md
    ??? methodology.md
"""