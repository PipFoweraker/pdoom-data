# funding_events.py
# Funding catastrophes and financial crises in AI safety

from event_data_structures import HistoricalEvent, EventCategory, GameImpact, ImpactType, Rarity

FUNDING_EVENTS = {
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
        rarity=Rarity.RARE
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
        tags=["bankruptcy", "clawback", "legal_issues", "cais"],
        triggers=["ftx_future_fund_collapse_2022"],
        safety_researcher_reaction="Legal system now pursuing our research funding",
        media_reaction="Bankruptcy trustees target AI safety organization for clawback"
    ),

    "crypto_funding_crash_2022": HistoricalEvent(
        id="crypto_funding_crash_2022",
        title="Crypto Market AI Funding Crash",
        year=2022,
        category=EventCategory.FUNDING_CATASTROPHE,
        description="Multiple AI safety orgs lost funding when crypto-wealthy donors' portfolios crashed during bear market",
        impacts=[
            GameImpact(ImpactType.CASH, -40),
            GameImpact(ImpactType.RESEARCH, -20),
            GameImpact(ImpactType.STRESS, 35),
            GameImpact(ImpactType.BURNOUT_RISK, 25),
            GameImpact(ImpactType.VIBEY_DOOM, 20)
        ],
        sources=[
            "https://forum.effectivealtruism.org/posts/RueHqBuBKQBtSYkzp/observations-on-the-funding-landscape-of-ea-and-ai-safety",
            "https://www.lesswrong.com/posts/WGpFFJo2uFe5ssgEb/an-overview-of-the-ai-safety-funding-situation"
        ],
        tags=["cryptocurrency", "bear_market", "funding_diversification"],
        safety_researcher_reaction="Too much dependence on volatile crypto wealth",
        media_reaction="AI safety funding vulnerable to crypto market swings"
    ),

    "ltff_funding_gap_2023": HistoricalEvent(
        id="ltff_funding_gap_2023",
        title="Long-Term Future Fund Funding Gap",
        year=2023,
        category=EventCategory.FUNDING_CATASTROPHE,
        description="Long-Term Future Fund reports $450k/month funding gap after relationship changes with Open Philanthropy",
        impacts=[
            GameImpact(ImpactType.CASH, -45),
            GameImpact(ImpactType.RESEARCH, -15),
            GameImpact(ImpactType.PAPERS, -10),
            GameImpact(ImpactType.STRESS, 25),
            GameImpact(ImpactType.VIBEY_DOOM, 10)
        ],
        sources=[
            "https://forum.effectivealtruism.org/posts/RueHqBuBKQBtSYkzp/observations-on-the-funding-landscape-of-ea-and-ai-safety",
            "https://funds.effectivealtruism.org/funds/far-future"
        ],
        tags=["ltff", "open_philanthropy", "institutional_funding"],
        safety_researcher_reaction="Core funding infrastructure is breaking down",
        media_reaction="AI safety funding faces institutional challenges"
    ),

    "ea_funding_concentration_risk_2023": HistoricalEvent(
        id="ea_funding_concentration_risk_2023",
        title="EA Funding Concentration Crisis",
        year=2023,
        category=EventCategory.FUNDING_CATASTROPHE,
        description="Major EA funders projected to spend less on AI safety in 2023 compared to 2022, revealing dangerous funding concentration",
        impacts=[
            GameImpact(ImpactType.CASH, -30),
            GameImpact(ImpactType.RESEARCH, -20),
            GameImpact(ImpactType.STRESS, 25),
            GameImpact(ImpactType.VIBEY_DOOM, 20)
        ],
        sources=[
            "https://forum.effectivealtruism.org/posts/RueHqBuBKQBtSYkzp/observations-on-the-funding-landscape-of-ea-and-ai-safety"
        ],
        tags=["effective_altruism", "funding_concentration", "diversification"],
        safety_researcher_reaction="We put all our eggs in too few baskets",
        media_reaction="AI safety funding reveals dangerous over-reliance on few donors"
    ),

    "grant_application_backlog_2024": HistoricalEvent(
        id="grant_application_backlog_2024",
        title="Grant Application Backlog Crisis",
        year=2024,
        category=EventCategory.FUNDING_CATASTROPHE,
        description="Nonlinear Network and Lightspeed Grants received 500-600 applications for relatively small funding pools, showing demand-supply mismatch",
        impacts=[
            GameImpact(ImpactType.CASH, -20),
            GameImpact(ImpactType.STRESS, 30),
            GameImpact(ImpactType.BURNOUT_RISK, 25),
            GameImpact(ImpactType.RESEARCH, -10)
        ],
        sources=[
            "https://forum.effectivealtruism.org/posts/RueHqBuBKQBtSYkzp/observations-on-the-funding-landscape-of-ea-and-ai-safety"
        ],
        tags=["grant_applications", "funding_bottleneck", "competition"],
        safety_researcher_reaction="Too many qualified researchers, too little funding",
        media_reaction="AI safety researchers face fierce competition for limited grants"
    ),

    "venture_capital_ai_safety_drought_2024": HistoricalEvent(
        id="venture_capital_ai_safety_drought_2024",
        title="Venture Capital AI Safety Drought",
        year=2024,
        category=EventCategory.FUNDING_CATASTROPHE,
        description="VC funding flows heavily to AI capabilities companies while AI safety startups struggle to raise funds",
        impacts=[
            GameImpact(ImpactType.CASH, -35),
            GameImpact(ImpactType.RESEARCH, -15),
            GameImpact(ImpactType.REPUTATION, -10),
            GameImpact(ImpactType.VIBEY_DOOM, 15)
        ],
        sources=[
            "https://www.anthropic.com/news/anthropic-funding",
            "https://techcrunch.com/2024/03/25/ai-safety-funding-challenges/"
        ],
        tags=["venture_capital", "market_incentives", "capabilities_bias"],
        safety_researcher_reaction="The market only rewards capability advancement",
        media_reaction="VCs pour billions into AI capabilities while safety gets scraps"
    )
}