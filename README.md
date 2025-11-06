# P(Doom) Data Repository

Curated data lake for AI safety, alignment research, and funding information.

## Overview

This repository provides production-grade data infrastructure for tracking AI safety developments, research publications, and funding patterns. Data flows through a three-zone architecture (raw → transformed → serveable) with comprehensive validation and provenance tracking.

## Data Collections

### Alignment Research
- 1,000+ research papers, blog posts, and forum discussions
- 30+ sources (ArXiv, Alignment Forum, LessWrong, EA Forum, etc.)
- Automated weekly extraction with delta detection
- Date range: 2020-present

### Funding Sources
- Survival and Flourishing Fund (SFF) grants
- Grant amounts, recipients, and project descriptions
- Historical funding patterns for AI safety organizations

### Historical Timeline
- 28+ curated AI safety events (2016-2025)
- Organizational crises, technical breakthroughs, funding events
- Full source attribution and metadata

## Architecture

**Raw Zone** → **Transformed Zone** → **Serveable Zone**

- Immutable source data with checksums
- Schema validation and quality checks
- Optimized formats for downstream consumption

See [docs/ALIGNMENT_RESEARCH_INTEGRATION.md](docs/ALIGNMENT_RESEARCH_INTEGRATION.md) for technical details.

## Data Quality Standards

- Rigorous sourcing with complete attribution
- JSON Schema validation on all datasets
- ASCII-only encoding for universal compatibility
- Comprehensive extraction and transformation logs

## License

MIT License - Free for educational, research, and commercial use.

## Data Sources

- **Historical Events**: 28+ curated game events (2016-2025)
- **Alignment Research**: 1,000+ research papers and discussions (automated weekly updates)
- **Funding Data**: SFF grants and funding patterns

Infrastructure documentation: [docs/ALIGNMENT_RESEARCH_INTEGRATION.md](docs/ALIGNMENT_RESEARCH_INTEGRATION.md)

## Repository Visibility

This repository is currently **private** during active development. A publishing workflow is configured to sync the serveable zone to a future public repository once data transformation pipelines are complete.

See [docs/DATA_PUBLISHING_STRATEGY.md](docs/DATA_PUBLISHING_STRATEGY.md) for details on the planned public data release strategy.

## Contributing

This repository maintains strict ASCII-only content for agent compatibility. See [CHANGELOG.md](CHANGELOG.md) for recent updates.
