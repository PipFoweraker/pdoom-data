# Data Lineage Documentation

## Overview

This document tracks the flow of data through the pipeline, documenting transformations, dependencies, and data provenance.

## Data Flow Architecture

```
External Source Systems
         |
         | [Manual/Automated Ingestion]
         v
+------------------+
| Raw Zone         |  Immutable source data
| data/raw/        |  - Never modified
+------------------+  - Organized by source
         |            - Complete audit trail
         |
         | [Migration Script]
         | - Checksum verification
         | - Schema validation
         v
+------------------+
| Validated Zone   |  Schema-compliant data
| data/transformed/|  - All required fields present
| validated/       |  - Data types correct
+------------------+  - Format validated
         |
         | [Cleaning Pipeline]
         | - Deduplication
         | - Normalization
         v
+------------------+
| Cleaned Zone     |  Normalized data
| data/transformed/|  - Duplicates removed
| cleaned/         |  - Consistent formats
+------------------+  - Null handling
         |
         | [Enrichment Pipeline]
         | - Derived fields
         | - Aggregations
         v
+------------------+
| Enriched Zone    |  Analysis-ready data
| data/transformed/|  - Calculated fields
| enriched/        |  - Categorizations
+------------------+  - Denormalized views
         |
         | [Publishing Pipeline]
         | - Format conversion
         | - Optimization
         v
+------------------+
| Serveable Zone   |  Production data
| data/serveable/  |  - API formats
+------------------+  - Analytics optimized
         |
         v
  Applications/APIs
```

## Stage Definitions

### Stage 1: Raw Ingestion

**Input**: External funding source data
**Output**: `data/raw/funding_sources/[source]/`
**Process**: Manual or automated data ingestion
**Responsibility**: Data ingestion team/scripts

**Transformations**: None (immutable landing)

**Quality Checks**:
- File format is readable (JSON, CSV)
- ASCII encoding verified
- File size reasonable

**Metadata Added**:
- Ingestion timestamp
- Source system identifier
- File checksum

**Frequency**: Ad-hoc or scheduled based on source

**Dependencies**: None (first stage)

### Stage 2: Validation

**Input**: `data/raw/funding_sources/[source]/`
**Output**: `data/transformed/validated/`
**Process**: `scripts/migration/migrate.py`
**Responsibility**: Automated migration pipeline

**Transformations**:
- Schema validation
- Required field verification
- Data type checking
- Format standardization

**Quality Checks**:
- All required fields present
- Data types match schema
- Dates in valid format
- Amounts are numeric
- Enum values match allowed list

**Metadata Added**:
- Validation timestamp
- Validation status
- Error/warning counts

**Frequency**: On-demand or scheduled

**Dependencies**:
- Raw zone data
- Schema file: `config/schemas/funding_data_v1.json`
- Validation script: `scripts/validation/validate_funding.py`

**Rollback**: Can reprocess from raw zone

### Stage 3: Cleaning

**Input**: `data/transformed/validated/`
**Output**: `data/transformed/cleaned/`
**Process**: Cleaning pipeline (to be implemented)
**Responsibility**: Data quality team

**Transformations**:
- Remove duplicate grants
- Normalize organization names
- Standardize amount formats
- Handle null values
- Correct known data issues

**Quality Checks**:
- No duplicate grant IDs
- Consistent organization names
- All amounts in USD
- Null fields documented

**Metadata Added**:
- Cleaning timestamp
- Records removed (duplicates)
- Corrections applied

**Frequency**: After validation

**Dependencies**:
- Validated zone data
- Deduplication rules
- Name normalization mappings

**Rollback**: Can reprocess from validated zone

### Stage 4: Enrichment

**Input**: `data/transformed/cleaned/`
**Output**: `data/transformed/enriched/`
**Process**: Enrichment pipeline (to be implemented)
**Responsibility**: Analytics team

**Transformations**:
- Add derived fields (year, quarter)
- Calculate aggregations
- Add categorizations
- Join with reference data

**Derived Fields**:
- `year`: Extracted from date
- `quarter`: Calculated from date
- `amount_category`: small/medium/large
- `source_type`: foundation/government/private

**Quality Checks**:
- Derived fields consistent with source
- Aggregations sum correctly
- No broken references

**Metadata Added**:
- Enrichment timestamp
- Fields added/modified
- Reference data versions

**Frequency**: After cleaning

**Dependencies**:
- Cleaned zone data
- Derivation logic scripts
- Reference data tables

**Rollback**: Can reprocess from cleaned zone

### Stage 5: Publishing

**Input**: `data/transformed/enriched/`
**Output**: `data/serveable/analytics/`, `data/serveable/api/`
**Process**: Publishing pipeline (to be implemented)
**Responsibility**: Platform team

**Transformations**:
- Convert to API formats (JSON)
- Create analytics views
- Apply indexing
- Generate aggregations

**Quality Checks**:
- Output format valid
- No data loss during conversion
- Performance acceptable

**Metadata Added**:
- Publication timestamp
- Format version
- Target platform

**Frequency**: After enrichment or on schedule

**Dependencies**:
- Enriched zone data
- Format specifications
- API schema definitions

**Rollback**: Can republish from enriched zone

## Source System Mappings

### Survival & Flourishing Fund (SFF)

**Source Format**: CSV export
**Update Frequency**: Quarterly
**Ingestion Method**: Manual download
**Raw Location**: `data/raw/funding_sources/sff/`

**Field Mappings**:
- `Grant ID` → `grant_id`
- `Amount` → `amount`
- `Date Awarded` → `date`
- `Grantee` → `recipient`
- `Focus Area` → `category`

**Known Issues**:
- Date format varies (US vs ISO)
- Some amounts include currency symbols
- Organization names not standardized

**Transformations Applied**:
- Parse multiple date formats
- Strip currency symbols from amounts
- Map focus areas to standard categories

### Open Philanthropy

**Source Format**: JSON API
**Update Frequency**: Weekly
**Ingestion Method**: API pull
**Raw Location**: `data/raw/funding_sources/open_philanthropy/`

**Field Mappings**:
- `grant_id` → `grant_id` (direct)
- `amount_awarded` → `amount`
- `award_date` → `date`
- `organization` → `recipient`
- `focus_area` → `category`

**Known Issues**:
- Multi-year grants shown as single amount
- Some grants missing URLs
- Recipient names may include legal suffixes

**Transformations Applied**:
- None needed (clean API data)
- Filter to AI-related grants only

### Other Sources

*To be documented as sources are added*

## Transformation Logic

### Deduplication

**Algorithm**: Compare grant_id and source
**Logic**: If same grant_id and source, keep most recent record
**Location**: Cleaning stage
**Logged**: Yes, in cleaning logs

### Amount Normalization

**Input Formats**: 
- `$50,000`
- `50000`
- `50K`
- `50000.00`

**Output Format**: `50000` (numeric)

**Logic**:
1. Remove currency symbols ($, EUR, etc.)
2. Remove thousands separators (,)
3. Expand K/M notation (50K → 50000)
4. Convert to float
5. Round to 2 decimal places

### Date Standardization

**Input Formats**:
- `2024-03-15` (ISO)
- `03/15/2024` (US)
- `15/03/2024` (EU)
- `March 15, 2024` (text)

**Output Format**: `2024-03-15` (ISO 8601)

**Logic**:
1. Try ISO format first
2. Try US format (month first)
3. Try EU format (day first)
4. Try text parsing
5. Error if no format matches

### Category Mapping

Maps source-specific categories to standard taxonomy:

| Source Category | Standard Category |
|-----------------|-------------------|
| AI Alignment | Technical Alignment |
| Policy | AI Governance |
| Outreach | Public Outreach |
| Research Infrastructure | Infrastructure |

## Data Provenance

Every record maintains lineage information:

```json
{
  "grant_id": "OP-AI-2024-123",
  "amount": 125000,
  "date": "2024-03-15",
  "_provenance": {
    "source_system": "Open Philanthropy API",
    "ingestion_date": "2025-10-30T14:23:45Z",
    "source_file": "data/raw/funding_sources/open_philanthropy/2025-10-30.json",
    "source_checksum": "a3b2c1d4e5f6...",
    "validation_date": "2025-10-30T14:25:12Z",
    "transformations": [
      "schema_validation",
      "deduplication",
      "enrichment"
    ]
  }
}
```

## Recovery and Reprocessing

### Full Reprocess

To completely reprocess all data:

1. Clear transformed zones:
   ```bash
   rm -rf data/transformed/validated/*
   rm -rf data/transformed/cleaned/*
   rm -rf data/transformed/enriched/*
   ```

2. Reset processing state:
   ```bash
   rm logs/migration/.migration_state.json
   ```

3. Run full pipeline:
   ```bash
   python scripts/migration/migrate.py
   # Then run cleaning, enrichment, publishing
   ```

### Partial Reprocess

To reprocess specific source:

1. Clear state for source:
   ```bash
   # Edit .migration_state.json
   # Remove entries for specific source
   ```

2. Run migration for source:
   ```bash
   python scripts/migration/migrate.py \
     --source data/raw/funding_sources/[source]
   ```

## Validation Points

Data validated at each stage:

1. **Raw → Validated**: Schema compliance, required fields
2. **Validated → Cleaned**: Duplicates, data quality
3. **Cleaned → Enriched**: Derived field consistency
4. **Enriched → Serveable**: Format correctness, completeness

## Monitoring Lineage

Track data flow with these metrics:

- Records per stage
- Transformation success rate
- Data loss percentage (should be 0%)
- Processing time per stage
- Error frequency by stage

## References

- Data Zones: `docs/DATA_ZONES.md`
- Validation Rules: `scripts/validation/validate_funding.py`
- Migration Script: `scripts/migration/migrate.py`
- Schema: `config/schemas/funding_data_v1.json`
