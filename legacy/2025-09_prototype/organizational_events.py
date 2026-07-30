# organizational_events.py
# Organizational crisis and leadership drama events

from event_data_structures import HistoricalEvent, EventCategory, GameImpact, ImpactType, Rarity

ORGANIZATIONAL_EVENTS = {
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
        rarity=Rarity.RARE
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

    "anthropic_exodus_2021": HistoricalEvent(
        id="anthropic_exodus_2021",
        title="Anthropic Executive Departures from OpenAI",
        year=2021,
        category=EventCategory.ORGANIZATIONAL_CRISIS,
        description="Mass departure from OpenAI to form safety-focused competitor after ideological conflicts over safety vs capability race",
        impacts=[
            GameImpact(ImpactType.CASH, -50),
            GameImpact(ImpactType.REPUTATION, 15),
            GameImpact(ImpactType.RESEARCH, 20),
            GameImpact(ImpactType.ETHICS_RISK, -10),
            GameImpact(ImpactType.TECHNICAL_DEBT, 15),
            GameImpact(ImpactType.VIBEY_DOOM, -10)
        ],
        sources=[
            "https://www.anthropic.com/news/introducing-claude",
            "https://techcrunch.com/2021/05/28/former-openai-research-vp-dario-amodei-starts-anthropic-ai-safety-startup/"
        ],
        tags=["safety_culture", "competition", "brain_drain", "anthropic"],
        safety_researcher_reaction="Safety researchers finally have a well-funded alternative",
        media_reaction="OpenAI brain drain as safety concerns drive executive exodus"
    ),

    "microsoft_tay_2016": HistoricalEvent(
        id="microsoft_tay_2016",
        title="Microsoft Tay Chatbot Scandal",
        year=2016,
        category=EventCategory.ORGANIZATIONAL_CRISIS,
        description="Microsoft's AI chatbot learned to post offensive content within 24 hours from Twitter interactions",
        impacts=[
            GameImpact(ImpactType.CASH, -10),
            GameImpact(ImpactType.MEDIA_REPUTATION, -30),
            GameImpact(ImpactType.ETHICS_RISK, 25),
            GameImpact(ImpactType.STRESS, 15),
            GameImpact(ImpactType.TECHNICAL_DEBT, 20),
            GameImpact(ImpactType.VIBEY_DOOM, 10)
        ],
        sources=[
            "https://digitaldefynd.com/IQ/top-ai-scandals/",
            "https://www.theverge.com/2016/3/24/11297050/tay-microsoft-chatbot-racist"
        ],
        tags=["content_moderation", "social_media", "microsoft", "early_warning"],
        safety_researcher_reaction="This shows how quickly AI systems can be corrupted",
        media_reaction="Microsoft's AI chatbot goes full Nazi in under 24 hours"
    ),

    "tesla_autopilot_incidents_2016_2024": HistoricalEvent(
        id="tesla_autopilot_incidents_2016_2024",
        title="Tesla Autopilot Fatal Accidents",
        year=2018,  # Representative year for ongoing incidents
        category=EventCategory.ORGANIZATIONAL_CRISIS,
        description="AIAAIC documented 20+ Tesla autonomous driving system failures leading to fatal accidents",
        impacts=[
            GameImpact(ImpactType.CASH, -25),
            GameImpact(ImpactType.REPUTATION, -35),
            GameImpact(ImpactType.ETHICS_RISK, 30),
            GameImpact(ImpactType.MEDIA_REPUTATION, -25),
            GameImpact(ImpactType.STRESS, 20),
            GameImpact(ImpactType.VIBEY_DOOM, 20)
        ],
        sources=[
            "https://nucleo.jor.br/english/2025-03-31-aiaaic-ai-incidents-have-skyrocketed-since-2016/",
            "https://aiaaic.org/"
        ],
        tags=["autonomous_vehicles", "tesla", "fatal_accidents", "safety_critical"],
        safety_researcher_reaction="Real-world deployment without adequate safety testing",
        media_reaction="Tesla's autopilot faces scrutiny after multiple fatal crashes"
    ),

    "openai_safety_team_departures_2024": HistoricalEvent(
        id="openai_safety_team_departures_2024",
        title="OpenAI Safety Team Mass Departures",
        year=2024,
        category=EventCategory.ORGANIZATIONAL_CRISIS,
        description="Mass resignations from OpenAI's safety team over concerns about rapid capability advancement without adequate safety measures",
        impacts=[
            GameImpact(ImpactType.RESEARCH, -25),
            GameImpact(ImpactType.REPUTATION, 15),
            GameImpact(ImpactType.ETHICS_RISK, 20),
            GameImpact(ImpactType.STRESS, 30),
            GameImpact(ImpactType.BURNOUT_RISK, 35),
            GameImpact(ImpactType.VIBEY_DOOM, 20)
        ],
        sources=[
            "https://techcrunch.com/2024/05/17/openai-safety-researchers-resign/",
            "https://www.vox.com/future-perfect/2024/5/17/24158478/openai-departures-sam-altman-employees-agi-superintelligence"
        ],
        tags=["safety_culture", "resignations", "openai", "capability_race"],
        safety_researcher_reaction="The safety team is abandoning ship",
        media_reaction="OpenAI's top safety researchers quit over AI development pace"
    )
}