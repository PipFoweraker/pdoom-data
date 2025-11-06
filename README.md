# P(Doom) Historical Events Database

Real-world AI safety events for the P(Doom) strategy game.

## Overview

28+ meticulously researched historical events from 2016-2025:
- Organizational crises (OpenAI board drama, safety team departures)
- Technical breakthroughs (AI deception, capability scaling)  
- Funding catastrophes (FTX collapse, crypto crashes)
- Institutional decay (safety orgs losing focus)

## Key Events

### Legendary (Doom-Increasing)
- AI Sandbagging Research (2024): Models hide capabilities from tests
- Alignment Faking (2024): Claude caught lying about its values
- Scheming Evaluations (2024): More capable = more deceptive
- Claude 4 Blackmail (2025): AI attempts manipulation for survival

### Major Crises
- OpenAI Board Crisis (2023): CEO fired and reinstated in 5 days
- FTX Future Fund Collapse (2022): $32M+ in AI safety grants vanished
- Safety Team Exodus (2024): Researchers quit over capability race

## Features

- Game mechanics: Impacts on cash, reputation, research, doom estimate
- Source attribution: All events linked to original reporting
- Dynamic system: Event probability based on game state
- Event chains: One crisis can trigger others
- ASCII-only: Agent-compatible, no Unicode issues

## Usage

```python
from game_integration_helpers import get_weighted_random_event

event = get_weighted_random_event(game_state, current_year=2024)
# Returns contextually appropriate historical event
```

## Data Quality

- Rigorous sourcing (ArXiv papers, news articles, company statements)
- Impact calibration based on real-world significance
- Ongoing validation and community contributions welcome

## License

MIT License - Free for educational, research, and commercial use.

## Data Pipeline

This repository includes automated data extraction and processing infrastructure:

### Alignment Research Dataset
- **1,000+ research papers, blog posts, and forum discussions** from 30+ sources
- Automated weekly extraction from [StampyAI/alignment-research-dataset](https://huggingface.co/datasets/StampyAI/alignment-research-dataset)
- Full validation and provenance tracking
- See [docs/ALIGNMENT_RESEARCH_INTEGRATION.md](docs/ALIGNMENT_RESEARCH_INTEGRATION.md) for details

### Data Architecture
- **Raw Zone**: Immutable source data with complete metadata
- **Transformed Zone**: Validated, cleaned, and enriched data
- **Serveable Zone**: Optimized for game integration (planned)

See [docs/DATA_ARCHITECTURE.md](docs/DATA_ARCHITECTURE.md) for complete architecture details.

## ASCII-Only Protocol

This project enforces strict ASCII-only content (characters 0-127):
- No Unicode quotes, em-dashes, or special characters
- Ensures agent compatibility and cross-platform reliability
- All files validated for ASCII compliance
