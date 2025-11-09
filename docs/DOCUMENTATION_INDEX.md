# Documentation Index

**Last Updated**: 2025-11-09
**Purpose**: Complete navigation guide for all pdoom-data documentation

---

## Quick Navigation

### Start Here
- **[README.md](../README.md)** - Repository overview and quick start
- **[QUICK_START_INTEGRATION.md](QUICK_START_INTEGRATION.md)** - 5-minute integration guide for all platforms

### For Developers
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Complete integration documentation
- **[EVENT_SCHEMA.md](EVENT_SCHEMA.md)** - Timeline event schema reference
- **[DATA_ZONES.md](DATA_ZONES.md)** - Three-zone architecture explained

### For Data Engineers
- **[RUNBOOK.md](RUNBOOK.md)** - Operational procedures
- **[LINEAGE.md](LINEAGE.md)** - Data provenance and lineage tracking
- **[ALIGNMENT_RESEARCH_INTEGRATION.md](ALIGNMENT_RESEARCH_INTEGRATION.md)** - Alignment research pipeline

### For Project Managers
- **[ECOSYSTEM_OVERVIEW.md](ECOSYSTEM_OVERVIEW.md)** - How all repos fit together
- **[DATA_PUBLISHING_STRATEGY.md](DATA_PUBLISHING_STRATEGY.md)** - Public data publishing plan
- **[CROSS_REPO_INTEGRATION_ISSUES.md](CROSS_REPO_INTEGRATION_ISSUES.md)** - Issues for consuming repos

---

## Documentation by Category

### Architecture & Design

| Document | Purpose | Audience |
|----------|---------|----------|
| [DATA_ZONES.md](DATA_ZONES.md) | Three-zone data lake architecture | Engineers |
| [DATA_ARCHITECTURE.md](../DATA_ARCHITECTURE.md) | Overall data architecture | Architects |
| [ECOSYSTEM_OVERVIEW.md](ECOSYSTEM_OVERVIEW.md) | Cross-repo ecosystem | All |
| [CROSS_REPOSITORY_DOCUMENTATION_STRATEGY.md](CROSS_REPOSITORY_DOCUMENTATION_STRATEGY.md) | Documentation strategy | Maintainers |

### Integration & Setup

| Document | Purpose | Audience |
|----------|---------|----------|
| [QUICK_START_INTEGRATION.md](QUICK_START_INTEGRATION.md) | 5-minute integration | Developers |
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | Complete integration docs | Developers |
| [CROSS_REPO_INTEGRATION_ISSUES.md](CROSS_REPO_INTEGRATION_ISSUES.md) | GitHub issue templates | Maintainers |
| [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) | Historical integration planning | Reference |
| [CROSS_REPO_INTEGRATION.md](../CROSS_REPO_INTEGRATION.md) | Legacy cross-repo docs | Reference |

### Data & Schema

| Document | Purpose | Audience |
|----------|---------|----------|
| [EVENT_SCHEMA.md](EVENT_SCHEMA.md) | Timeline event schema | Developers |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Data field definitions | Analysts |
| [ALIGNMENT_RESEARCH_INTEGRATION.md](ALIGNMENT_RESEARCH_INTEGRATION.md) | Research data pipeline | Engineers |
| [HISTORICAL_DATA_INTEGRATION.md](HISTORICAL_DATA_INTEGRATION.md) | Historical events integration | Curators |

### Operations & Maintenance

| Document | Purpose | Audience |
|----------|---------|----------|
| [RUNBOOK.md](RUNBOOK.md) | Operational procedures | Operators |
| [LINEAGE.md](LINEAGE.md) | Data lineage tracking | Engineers |
| [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) | Development practices | Contributors |
| [ASCII_CODING_STANDARDS.md](../ASCII_CODING_STANDARDS.md) | Code standards | Contributors |

### Publishing & Communication

| Document | Purpose | Audience |
|----------|---------|----------|
| [DATA_PUBLISHING_STRATEGY.md](DATA_PUBLISHING_STRATEGY.md) | Public data publishing | Stakeholders |
| [DEVBLOG.md](../DEVBLOG.md) | Development blog | Community |
| [CHANGELOG.md](../CHANGELOG.md) | Change history | All |
| [WORKFLOW_SUMMARY.md](../WORKFLOW_SUMMARY.md) | Workflow documentation | Reference |

### Reference & Legacy

| Document | Purpose | Audience |
|----------|---------|----------|
| [FUNDING_DUMP_SPACES.md](FUNDING_DUMP_SPACES.md) | Funding data sources | Analysts |
| [SESSION_2025-11-06_ALIGNMENT_RESEARCH_INTEGRATION.md](SESSION_2025-11-06_ALIGNMENT_RESEARCH_INTEGRATION.md) | Session notes | Reference |
| [REPO_NAVIGATION.md](../REPO_NAVIGATION.md) | Repository navigation | New users |
| [INTEGRATION_SUMMARY.md](../INTEGRATION_SUMMARY.md) | Integration summary | Reference |
| [AGENT_CHARACTER_RESTRICTIONS.md](../AGENT_CHARACTER_RESTRICTIONS.md) | AI agent guidelines | Maintainers |

---

## Documentation by Use Case

### "I want to integrate pdoom-data into my app"

1. Start: [QUICK_START_INTEGRATION.md](QUICK_START_INTEGRATION.md)
2. Reference: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
3. Schema: [EVENT_SCHEMA.md](EVENT_SCHEMA.md)

### "I want to understand the data pipeline"

1. Overview: [DATA_ZONES.md](DATA_ZONES.md)
2. Details: [ALIGNMENT_RESEARCH_INTEGRATION.md](ALIGNMENT_RESEARCH_INTEGRATION.md)
3. Operations: [RUNBOOK.md](RUNBOOK.md)

### "I want to add new data sources"

1. Architecture: [DATA_ZONES.md](DATA_ZONES.md)
2. Procedures: [RUNBOOK.md](RUNBOOK.md)
3. Lineage: [LINEAGE.md](LINEAGE.md)

### "I want to understand the ecosystem"

1. Overview: [ECOSYSTEM_OVERVIEW.md](ECOSYSTEM_OVERVIEW.md)
2. Integration: [CROSS_REPO_INTEGRATION_ISSUES.md](CROSS_REPO_INTEGRATION_ISSUES.md)
3. Publishing: [DATA_PUBLISHING_STRATEGY.md](DATA_PUBLISHING_STRATEGY.md)

### "I want to contribute"

1. Standards: [ASCII_CODING_STANDARDS.md](../ASCII_CODING_STANDARDS.md)
2. Workflow: [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md)
3. Guidelines: [AGENT_CHARACTER_RESTRICTIONS.md](../AGENT_CHARACTER_RESTRICTIONS.md)

---

## Data Files Reference

### Serveable Zone
- **Location**: `data/serveable/`
- **README**: [data/serveable/README.md](../data/serveable/README.md)
- **Manifest**: [data/serveable/MANIFEST.json](../data/serveable/MANIFEST.json)

### Configuration
- **Schemas**: `config/schemas/`
  - [event_v1.json](../config/schemas/event_v1.json) - Timeline event schema

### Scripts
- **Transformation**: `scripts/transformation/`
  - [clean_events.py](../scripts/transformation/clean_events.py)
  - [clean.py](../scripts/transformation/clean.py)
  - [enrich.py](../scripts/transformation/enrich.py)
  - [transform_to_timeline_events.py](../scripts/transformation/transform_to_timeline_events.py)

- **Publishing**: `scripts/publishing/`
  - [generate_manifest.py](../scripts/publishing/generate_manifest.py)

- **Validation**: `scripts/validation/`
  - [validate_alignment_research.py](../scripts/validation/validate_alignment_research.py)

---

## Workflows & Automation

### GitHub Actions
- **Weekly Data Refresh**: [.github/workflows/weekly-data-refresh.yml](../.github/workflows/weekly-data-refresh.yml)
- **Automated Pipeline**: [.github/workflows/data-pipeline-automation.yml](../.github/workflows/data-pipeline-automation.yml)
- **Documentation CI**: [.github/workflows/documentation-ci.yml](../.github/workflows/documentation-ci.yml)
- **Public Publishing**: [.github/workflows/publish-serveable.yml](../.github/workflows/publish-serveable.yml) (disabled)

---

## Documentation Status

### Complete & Current
- ✅ Quick Start Integration
- ✅ Integration Guide
- ✅ Event Schema
- ✅ Data Zones Architecture
- ✅ Runbook
- ✅ Cross-Repo Integration Issues

### In Progress
- 🔄 Public Communication Strategy
- 🔄 Logs Consolidation Strategy
- 🔄 DEVBLOG updates

### Planned
- 📋 API Documentation (once pdoom1-website implements)
- 📋 Public Data Portal Documentation
- 📋 Community Contribution Guide

---

## Maintenance

### Keeping Documentation Current

**When to update**:
- New features added -> Update relevant guides
- Schema changes -> Update EVENT_SCHEMA.md and MANIFEST.json
- New data sources -> Update DATA_DICTIONARY.md
- Pipeline changes -> Update RUNBOOK.md and LINEAGE.md
- Integration changes -> Update INTEGRATION_GUIDE.md

**Who maintains**:
- Core docs: pdoom-data maintainers
- Integration docs: Respective repo maintainers
- Session notes: Archive only, no updates

### Documentation Review Checklist

- [ ] All links work (internal and external)
- [ ] Code examples are tested and work
- [ ] Schema versions match actual schemas
- [ ] Workflow examples match actual workflows
- [ ] Status badges reflect actual state

---

## Getting Help

**For documentation questions**:
- Check this index first
- Search repository: `gh search "your topic" --repo PipFoweraker/pdoom-data`
- Open issue: [New Documentation Issue](https://github.com/PipFoweraker/pdoom-data/issues/new)

**For implementation questions**:
- See [QUICK_START_INTEGRATION.md](QUICK_START_INTEGRATION.md)
- See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- Check [RUNBOOK.md](RUNBOOK.md) for operations

---

## Document Hierarchy

```
README.md (start here)
  |
  |-- QUICK_START_INTEGRATION.md (5-min setup)
  |     |
  |     |-- INTEGRATION_GUIDE.md (detailed integration)
  |           |
  |           |-- EVENT_SCHEMA.md (schema reference)
  |           |-- DATA_ZONES.md (architecture)
  |
  |-- ECOSYSTEM_OVERVIEW.md (understand ecosystem)
  |     |
  |     |-- CROSS_REPO_INTEGRATION_ISSUES.md (create issues)
  |     |-- DATA_PUBLISHING_STRATEGY.md (public data)
  |
  |-- RUNBOOK.md (operations)
        |
        |-- LINEAGE.md (data provenance)
        |-- ALIGNMENT_RESEARCH_INTEGRATION.md (pipelines)
```

---

**Maintained by**: pdoom-data team
**Last audit**: 2025-11-09
**Next review**: When new major features added
