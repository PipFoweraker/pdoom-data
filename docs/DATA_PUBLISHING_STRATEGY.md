# Data Publishing Strategy

**Status**: Planned (not yet implemented)
**Repository Visibility**: Private (with future public publishing capability)
**Last Updated**: 2025-11-06

---

## Overview

This document outlines the strategy for managing data visibility and public access to the pdoom-data repository. The core principle is to maintain a private development repository while enabling selective publication of curated data to public consumers.

## Current State

**Repository Status**: Private
- All zones (raw, transformed, serveable) currently private
- Active development of extraction and transformation pipelines
- Building toward public data sharing capability

## Publishing Architecture

### Zone-Based Visibility Model

```
pdoom-data (private)
├── data/raw/              [NEVER PUBLIC]
│   ├── Source credentials, API tokens
│   ├── Unvalidated data dumps
│   └── Potentially sensitive metadata
│
├── data/transformed/      [NEVER PUBLIC]
│   ├── Intermediate processing artifacts
│   ├── Data quality logs
│   └── Work-in-progress transformations
│
└── data/serveable/        [PUBLISHABLE]
    ├── Fully validated datasets
    ├── Complete attribution
    └── Production-ready formats
```

### Publishing Strategy: GitHub Actions Automation (Recommended)

**Approach**: Automated sync from private repo serveable zone to public repo

**Workflow**:
1. Developer commits to pdoom-data (private)
2. CI/CD validates all changes
3. GitHub Action detects changes in `data/serveable/`
4. Action pushes serveable zone to `pdoom-data-public` (public repo)
5. Public repo contains only curated, validated data

**Benefits**:
- Single source of truth (private repo)
- Automated publishing reduces manual errors
- Clear separation of development vs. consumption
- Maintains complete development history privately
- Public repo stays clean and focused

**Trade-offs**:
- Requires setup of public destination repo
- Additional CI/CD complexity
- Slight delay between commit and public availability

## Alternative Strategies Considered

### Option 1: Repository Splitting
Split into two repos from the start:
- `pdoom-data` (public) - serveable zone only
- `pdoom-data-internal` (private) - raw + transformed

**Rejected because**: Complicates current development phase; premature optimization

### Option 2: Git Submodules
Use serveable zone as a submodule pointing to public repo

**Rejected because**: Submodules notoriously difficult to manage; poor developer experience

### Option 3: Keep Fully Private
Never publish raw data repository

**Rejected because**: Conflicts with goal of building public AI safety data resource

## Implementation Phases

### Phase 1: Current (No Publishing)
- ✅ Establish three-zone architecture
- ✅ Build extraction pipelines
- ✅ Implement validation infrastructure
- 🔄 Develop transformation scripts (Issues #13-16)

### Phase 2: Serveable Zone Population (Future)
- Transform raw data to serveable formats
- Implement cleaning and enrichment pipelines
- Generate API-ready JSON structures
- Complete data quality audits

### Phase 3: Public Publishing Infrastructure (Future)
- Create `pdoom-data-public` repository
- Implement GitHub Actions sync workflow
- Add automated validation before publishing
- Document public API and data schemas

### Phase 4: Production Publishing (Future)
- Enable automated daily/weekly syncs
- Monitor public repo usage
- Iterate on published data formats
- Maintain backward compatibility

## Publishing Workflow Details

### Stub Workflow Location
`.github/workflows/publish-serveable.yml` (currently disabled)

### Activation Criteria
Enable publishing when:
- [ ] Serveable zone has production-ready data
- [ ] All data has proper attribution and licensing
- [ ] Data quality validation passes 100%
- [ ] Public repository created and configured
- [ ] Team approval for public data release

### Data Quality Gates
Before publishing, automated checks verify:
- Schema validation passes
- No credentials or sensitive data
- ASCII compliance
- Complete attribution metadata
- License compatibility
- Checksum verification

## Security Considerations

### Never Publish
- API keys, tokens, credentials
- Personal identifiable information (PII)
- Unvalidated or unattributed data
- Internal notes or comments
- Intermediate processing artifacts

### Always Include in Published Data
- Full attribution and citations
- License information (MIT)
- Data provenance metadata
- Schema documentation
- Usage examples

## Maintenance

### Monitoring Published Data
- Track downstream usage via GitHub insights
- Monitor issues/feedback on public repo
- Maintain changelog for published datasets
- Version serveable data releases

### Update Cadence
- **Alignment Research**: Weekly automated updates
- **Funding Data**: As new dumps created
- **Historical Timeline**: As events curated

## Related Documentation

- [ALIGNMENT_RESEARCH_INTEGRATION.md](ALIGNMENT_RESEARCH_INTEGRATION.md) - Extraction pipeline details
- [Session documentation](SESSION_2025-11-06_ALIGNMENT_RESEARCH_INTEGRATION.md) - Implementation timeline
- [GitHub Issues #13-16](https://github.com/PipFoweraker/pdoom-data/issues) - Transformation work

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-06 | Adopt GitHub Actions publishing strategy | Balances automation, security, and simplicity |
| 2025-11-06 | Keep repo private during development | Allows iteration without public commitment |
| 2025-11-06 | Delay publishing until serveable zone populated | Avoid premature public releases |

## Next Steps

1. Complete transformation pipeline (Issues #13-16)
2. Validate serveable zone data quality
3. Create `pdoom-data-public` repository
4. Activate publishing workflow
5. Announce public data availability

---

**Questions or concerns?** Open an issue or contact the maintainers.
