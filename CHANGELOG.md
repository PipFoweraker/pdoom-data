# Changelog

All notable changes to pdoom-data will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2025-11-06

#### Alignment Research Dataset Integration

**Complete end-to-end data pipeline for StampyAI alignment research dataset**

- **Extraction Infrastructure**
  - `data/raw/alignment_research/extraction_script.py` - Full-featured extraction with streaming, filtering, delta detection
  - `data/raw/alignment_research/README.md` - Comprehensive source documentation
  - `data/raw/alignment_research/QUICK_START.md` - Quick reference guide
  - Weekly automated extraction via GitHub Actions (every Monday 2am UTC)
  - Support for both full and delta (incremental) extraction modes
  - Configurable filtering by date, source, keywords, and record limit

- **Validation Pipeline**
  - `scripts/validation/validate_alignment_research.py` - Schema validation with comprehensive checks
  - `config/schemas/alignment_research_v1.json` - JSON Schema for alignment research records
  - Validation for schema compliance, required fields, duplicates, ASCII compliance
  - 100% validation pass rate on initial 1,000 record dataset

- **Automation & Monitoring**
  - `.github/workflows/weekly-data-refresh.yml` - Automated weekly data refresh workflow
  - Structured logging (console + file + JSON formats)
  - Progress reporting every 100 records
  - Comprehensive error handling and recovery
  - GitHub Actions artifact retention (30 days)

- **Documentation Suite** (~60 pages)
  - `docs/ALIGNMENT_RESEARCH_INTEGRATION.md` - Complete technical integration guide (22KB)
  - `docs/SESSION_2025-11-06_ALIGNMENT_RESEARCH_INTEGRATION.md` - Session summary with decisions and lessons learned (25KB)
  - Architecture diagrams, operational procedures, troubleshooting guides
  - Performance metrics and benchmarks

- **Templates for Future Integrations**
  - `data/raw/_templates/INTEGRATION_TEMPLATE.md` - Step-by-step integration checklist (15KB)
  - `data/raw/_templates/extraction_script_template.py` - Fully commented script skeleton (10KB)
  - `data/raw/_templates/SOURCE_README.md` - Documentation template (4KB)

- **Configuration & Dependencies**
  - `requirements.txt` - Python dependencies for data pipeline
  - Updated `scripts/extraction/new_dump.py` - Added alignment_research as valid source
  - Updated `.gitignore` - Added .claude/ directory exclusion

#### Initial Data

- **1,000 alignment research records extracted** (27MB)
  - Date range: 2020-01-01 to present
  - Sources: alignmentforum, arxiv, lesswrong, eaforum, distill
  - 100% validation pass rate
  - Complete provenance and attribution metadata

#### GitHub Issues Created

- #13: Transform alignment research data to timeline events for pdoom1 game integration
- #14: Implement data cleaning and enrichment pipeline for transformed zone
- #15: Implement serveable zone and pdoom1 data sync mechanism
- #16: Optimize static historical data for game integration

### Changed - 2025-11-06

- Updated `scripts/extraction/new_dump.py` to support non-funding-source data sources
- Enhanced `.gitignore` to exclude Claude Code settings directory

### Performance - 2025-11-06

- Extraction throughput: 265 records/second
- Validation speed: ~800 records/second
- Memory usage: <100MB (streaming architecture)
- File size: 27KB average per record

## [0.1.0] - 2025-10-30

### Added

- Initial project structure
- Three-zone data lake architecture (raw/transformed/serveable)
- SFF funding data source investigation
- Data architecture documentation
- Migration scripts and utilities
- Structured logging infrastructure
- File operations utilities with checksum verification

---

**Legend**:
- 🎯 Major feature
- ✨ Enhancement
- 🐛 Bug fix
- 📚 Documentation
- 🔧 Configuration
- ⚡ Performance
- 🔒 Security
