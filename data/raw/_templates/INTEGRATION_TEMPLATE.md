# New Data Source Integration Template

**Purpose**: Step-by-step guide for adding new data sources to pdoom-data
**Based on**: Alignment Research Dataset integration (2025-11-06)
**Target Audience**: Data engineers, contributors

---

## Overview

This template guides you through integrating a new data source into the pdoom-data pipeline. Following this process ensures consistency with our three-zone data lake architecture and maintains world-class data engineering standards.

**Estimated Time**: 4-8 hours for a complete integration

---

## Prerequisites

- [ ] Identified data source with clear access method (API, web scraping, manual download)
- [ ] Confirmed data license is compatible (open source, MIT, CC-BY, etc.)
- [ ] Reviewed data structure and available fields
- [ ] Determined update frequency (one-time, weekly, daily, real-time)
- [ ] Python 3.11+ development environment set up

---

## Integration Checklist

### Phase 1: Planning & Design (1-2 hours)

- [ ] **1.1 Define Data Source**
  - Data source name (lowercase, underscores)
  - Data source URL/location
  - License and attribution requirements
  - Update frequency and method
  - Estimated data volume

- [ ] **1.2 Design Schema**
  - Required fields
  - Optional fields
  - Data types and formats
  - Validation rules
  - Provenance requirements

- [ ] **1.3 Plan Architecture**
  - Extraction method (API, scraping, file download)
  - Filtering strategy
  - Delta detection approach
  - Error handling needs

### Phase 2: Directory Structure (15 minutes)

- [ ] **2.1 Create Source Directory**
  ```bash
  mkdir -p "data/raw/[source_name]/{_templates,dumps}"
  ```

- [ ] **2.2 Copy Templates**
  - Copy `_templates/_metadata.json` to source directory
  - Copy `_templates/extraction_script_template.py` to source directory
  - Copy `_templates/SOURCE_README.md` to source directory

### Phase 3: Schema Definition (30 minutes)

- [ ] **3.1 Create JSON Schema**
  - File: `config/schemas/[source_name]_v1.json`
  - Based on: `alignment_research_v1.json`
  - Define required and optional fields
  - Add validation patterns and constraints

- [ ] **3.2 Test Schema**
  - Create sample record
  - Validate with jsonschema library
  - Iterate until schema is correct

### Phase 4: Extraction Script (2-3 hours)

- [ ] **4.1 Implement Extraction**
  - File: `data/raw/[source_name]/extraction_script.py`
  - Based on: `alignment_research/extraction_script.py`
  - Implement data fetching logic
  - Add filtering capabilities
  - Implement delta detection

- [ ] **4.2 Add Logging**
  - Use `scripts/utils/logger.py`
  - Log all major operations
  - Include progress reporting (every 100 records)
  - Log errors with full context

- [ ] **4.3 Add Metadata Generation**
  - Generate `_metadata.json` with all fields
  - Calculate checksums
  - Record statistics

- [ ] **4.4 Test Extraction**
  - Dry run with `--dry-run` flag
  - Small sample with `--limit 10`
  - Medium sample with `--limit 100`
  - Review output format and metadata

### Phase 5: Validation Script (1 hour)

- [ ] **5.1 Create Validator**
  - File: `scripts/validation/validate_[source_name].py`
  - Based on: `validate_alignment_research.py`
  - Implement schema validation
  - Add custom validation rules
  - Generate validation report

- [ ] **5.2 Test Validation**
  - Run on test data
  - Verify all checks work
  - Confirm error reporting

### Phase 6: Documentation (1-2 hours)

- [ ] **6.1 Source README**
  - File: `data/raw/[source_name]/README.md`
  - Document data source details
  - Explain extraction process
  - Provide usage examples
  - Include troubleshooting tips

- [ ] **6.2 Integration Guide**
  - File: `docs/[SOURCE_NAME]_INTEGRATION.md`
  - Based on: `ALIGNMENT_RESEARCH_INTEGRATION.md`
  - Comprehensive technical documentation
  - Architecture diagrams
  - Operational procedures

- [ ] **6.3 Update Main Documentation**
  - Add source to `DATA_ARCHITECTURE.md`
  - Update `README.md` if needed
  - Link from related docs

### Phase 7: Automation (Optional, 1 hour)

- [ ] **7.1 GitHub Actions Workflow**
  - Create `.github/workflows/[source_name]-refresh.yml`
  - Based on: `weekly-data-refresh.yml`
  - Configure schedule
  - Add secrets if needed

- [ ] **7.2 Test Workflow**
  - Manual dispatch test
  - Verify all steps work
  - Check commit messages

### Phase 8: Integration Testing (1 hour)

- [ ] **8.1 End-to-End Test**
  - Full extraction
  - Validation passes
  - Metadata correct
  - Logs generated
  - Checksums verified

- [ ] **8.2 Delta Test**
  - Run second extraction
  - Verify delta detection works
  - Confirm no duplicates

- [ ] **8.3 Error Handling Test**
  - Test with network issues
  - Test with invalid data
  - Verify graceful failures

### Phase 9: Code Review & Merge

- [ ] **9.1 Self Review**
  - Code follows existing patterns
  - All TODOs removed
  - Documentation complete
  - Tests passing

- [ ] **9.2 Create Pull Request**
  - Clear title and description
  - Link to issue/planning docs
  - Request review

- [ ] **9.3 Address Feedback**
  - Implement requested changes
  - Update documentation
  - Re-test

### Phase 10: Deployment & Monitoring

- [ ] **10.1 Initial Deployment**
  - Merge to main branch
  - Run initial extraction
  - Verify data in repository

- [ ] **10.2 Monitor First Automated Run**
  - Check workflow execution
  - Review logs
  - Verify data quality

- [ ] **10.3 Document Lessons Learned**
  - Update this template if needed
  - Note any gotchas
  - Share with team

---

## Detailed Instructions

### Creating JSON Schema

**Template** (`config/schemas/[source_name]_v1.json`):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "[Source Name] Data Schema",
  "description": "Schema for [source name] data records",
  "version": "1.0.0",
  "type": "object",
  "required": [
    "id",
    "title",
    "url",
    "date"
  ],
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique identifier",
      "pattern": "^[a-zA-Z0-9_-]+$"
    },
    "title": {
      "type": "string",
      "description": "Record title",
      "minLength": 1
    },
    "url": {
      "type": "string",
      "description": "Source URL",
      "format": "uri"
    },
    "date": {
      "type": "string",
      "description": "Date in ISO 8601",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}"
    },
    "_provenance": {
      "type": "object",
      "required": ["source_system", "ingestion_date", "license"],
      "properties": {
        "source_system": {"type": "string"},
        "ingestion_date": {"type": "string", "format": "date-time"},
        "license": {"type": "string"},
        "attribution": {"type": "string"}
      }
    }
  }
}
```

### Implementing Extraction Script

**Key Components**:

1. **Class-based architecture**:
```python
class [SourceName]Extractor:
    def __init__(self, output_dir, mode, limit, ...):
        # Initialize configuration
        pass

    def extract(self):
        # Main extraction logic
        pass

    def _filter_record(self, record):
        # Apply filters
        pass

    def _transform_record(self, record):
        # Transform to schema
        pass
```

2. **Logging integration**:
```python
from scripts.utils.logger import get_logger

self.logger = get_logger('[source_name]_extraction', log_dir='logs/[source_name]_extraction')
self.logger.info("Starting extraction", mode=mode, limit=limit)
```

3. **Progress reporting**:
```python
if self.stats['records_written'] % 100 == 0:
    self.logger.info("Progress", written=self.stats['records_written'])
```

4. **Error handling**:
```python
try:
    # Process record
    transformed = self._transform_record(record)
    f.write(json.dumps(transformed) + '\n')
except Exception as e:
    self.stats['errors_encountered'] += 1
    self.logger.error("Transform failed", record_id=record.get('id'), error=str(e))
```

### Updating Configuration

**Add to** `scripts/extraction/new_dump.py`:

```python
VALID_SOURCES = [
    'sff',
    'open_philanthropy',
    # ... existing sources ...
    '[source_name]'  # Add your source
]
```

**Handle special paths**:

```python
if source == '[source_name]':
    source_dir = base_dir / 'data' / 'raw' / source
else:
    source_dir = base_dir / 'data' / 'raw' / 'funding_sources' / source
```

---

## Example: API-based Source

If integrating an API-based source:

```python
import requests

class APIExtractor:
    API_BASE_URL = "https://api.example.com/v1"

    def fetch_records(self, page=1, per_page=100):
        """Fetch records from API with pagination"""
        response = requests.get(
            f"{self.API_BASE_URL}/records",
            params={"page": page, "per_page": per_page},
            headers={"Authorization": f"Bearer {self.api_token}"}
        )
        response.raise_for_status()
        return response.json()

    def extract(self):
        page = 1
        while True:
            try:
                data = self.fetch_records(page=page)
                records = data.get('records', [])

                if not records:
                    break  # No more records

                for record in records:
                    # Process record
                    ...

                page += 1

            except requests.HTTPError as e:
                self.logger.error("API request failed", page=page, error=str(e))
                break
```

---

## Example: Web Scraping Source

If integrating a web scraping source:

```python
from bs4 import BeautifulSoup
import requests
import time

class WebScraperExtractor:
    def scrape_page(self, url):
        """Scrape single page with rate limiting"""
        time.sleep(2)  # Respectful crawling
        response = requests.get(url, headers={'User-Agent': 'pdoom-data/1.0'})
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup

    def extract_records(self, soup):
        """Extract records from parsed HTML"""
        records = []
        for item in soup.find_all('div', class_='record'):
            record = {
                'id': item.get('data-id'),
                'title': item.find('h2').text.strip(),
                'url': item.find('a')['href'],
                'date': item.find('time')['datetime']
            }
            records.append(record)
        return records
```

---

## Best Practices

### Data Quality

1. **Always add provenance**: Every record must have `_provenance` object
2. **Validate early**: Catch data issues during extraction, not later
3. **Log everything**: Verbose logging helps debug production issues
4. **Use checksums**: Verify data integrity with SHA-256 hashes
5. **Handle duplicates**: Check IDs to prevent duplicate records

### Performance

1. **Stream when possible**: Don't load entire dataset into memory
2. **Batch writes**: Write multiple records per I/O operation
3. **Progress reporting**: Log every 100 records minimum
4. **Respect rate limits**: Add delays for API/web scraping
5. **Cache aggressively**: Reuse downloaded data when safe

### Maintainability

1. **Follow existing patterns**: Match alignment_research structure
2. **Document assumptions**: Explain non-obvious decisions
3. **Version schemas**: Use v1, v2, etc. for schema files
4. **Test edge cases**: Empty results, malformed data, network errors
5. **Keep it simple**: Prefer clarity over cleverness

---

## Common Gotchas

### 1. Character Encoding

Always specify UTF-8 encoding:
```python
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

### 2. Path Handling

Use `pathlib.Path` for cross-platform compatibility:
```python
from pathlib import Path
output_dir = Path('data/raw/source_name')
```

### 3. Date Formats

Convert all dates to ISO 8601:
```python
from datetime import datetime
date_obj = datetime.strptime(date_str, '%m/%d/%Y')
iso_date = date_obj.strftime('%Y-%m-%dT%H:%M:%SZ')
```

### 4. Error Recovery

Always close files in `finally` blocks:
```python
f = None
try:
    f = open(file_path, 'w')
    # Process data
finally:
    if f:
        f.close()
```

### 5. Large Files

Use streaming for large files:
```python
import jsonlines
with jsonlines.open(file_path) as reader:
    for record in reader:  # Stream, don't load all
        process(record)
```

---

## Testing Checklist

- [ ] Dry run completes without errors
- [ ] Small sample (10 records) validates
- [ ] Medium sample (100 records) validates
- [ ] Full extraction completes successfully
- [ ] Delta mode detects new records only
- [ ] Metadata is complete and accurate
- [ ] Checksums match before/after
- [ ] Logs are verbose and informative
- [ ] Error handling works (test with bad data)
- [ ] Schema validation catches invalid records
- [ ] Automated workflow runs successfully
- [ ] Documentation is complete and accurate

---

## Resources

- **Reference Implementation**: [data/raw/alignment_research/](../alignment_research/)
- **Schema Examples**: [config/schemas/](../../config/schemas/)
- **Validation Examples**: [scripts/validation/](../../scripts/validation/)
- **Logger Utility**: [scripts/utils/logger.py](../../scripts/utils/logger.py)
- **File Operations**: [scripts/utils/file_ops.py](../../scripts/utils/file_ops.py)

---

## Questions?

- Review [ALIGNMENT_RESEARCH_INTEGRATION.md](../../docs/ALIGNMENT_RESEARCH_INTEGRATION.md) for detailed example
- Check [DATA_ARCHITECTURE.md](../../docs/DATA_ARCHITECTURE.md) for overall design
- Open GitHub issue for specific questions
- Contact pdoom-data maintainers

---

**Template Version**: 1.0.0
**Last Updated**: 2025-11-06
**Based On**: Alignment Research Dataset integration
