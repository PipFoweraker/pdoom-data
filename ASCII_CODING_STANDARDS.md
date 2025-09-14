# ASCII-ONLY CODING STANDARDS
# Strict Protocol for Agent-Based Development

## MANDATORY RULES

### 1. CHARACTER SET RESTRICTION
- **ALL TEXT CONTENT MUST BE ASCII-ONLY (characters 0-127)**
- NO Unicode characters, emojis, or extended ASCII (128-255)
- NO smart quotes, em dashes, or fancy punctuation
- This applies to: source code, comments, documentation, data files

### 2. FILE ENCODING
```python
# ALWAYS specify ASCII encoding when writing files
with open("filename.txt", "w", encoding='ascii') as f:
    f.write(content)

# ALWAYS validate ASCII compliance when reading
try:
    with open("filename.txt", "r", encoding='ascii') as f:
        content = f.read()
except UnicodeDecodeError:
    raise ValueError("File contains non-ASCII characters")
```

### 3. STRING LITERALS
```python
# GOOD: ASCII quotes and apostrophes
text = "This is a 'good' example with ASCII quotes"
message = 'Another "good" example'

# BAD: Unicode quotes
text = "This is a 'bad' example"  # Contains Unicode quotes
```

### 4. COMMENTS AND DOCSTRINGS
```python
# GOOD: ASCII-only comments
def process_data():
    """Process data using ASCII-safe methods"""
    # This is a regular comment with ASCII characters
    pass

# BAD: Non-ASCII in comments
def process_data():
    """Process data using smart quotes"""  # Contains Unicode
```

## AGENT INSTRUCTIONS

### For GitHub Copilot / AI Assistants:
```
CRITICAL INSTRUCTION: Generate only ASCII characters (0-127).
- Use straight quotes: " '
- Use regular hyphens: -
- Use three dots instead of ellipsis: ...
- No smart quotes, em dashes, or Unicode symbols
- Validate all generated content is ASCII-compatible
```

### Pre-commit Validation:
```bash
# Add this to your git pre-commit hook
python -c "
import sys
for line in sys.stdin:
    for char in line:
        if ord(char) > 127:
            print(f'Non-ASCII character found: {repr(char)}')
            sys.exit(1)
"
```

## REPLACEMENT GUIDE

### Common Unicode -> ASCII Replacements:
- Left/right single quotes ('') -> straight apostrophe (')
- Left/right double quotes ("") -> straight quotes (")
- Em dash (--) -> double hyphen (--)
- En dash (-) -> single hyphen (-)
- Ellipsis (...) -> three dots (...)
- Non-breaking space -> regular space
- Bullet points (*) -> asterisk (*) or hyphen (-)

## VALIDATION TOOLS

### 1. File Validation Function:
```python
def validate_ascii_file(filepath):
    try:
        with open(filepath, 'r', encoding='ascii') as f:
            content = f.read()
        return True, "File is ASCII-compliant"
    except UnicodeDecodeError as e:
        return False, f"Non-ASCII characters found: {e}"
```

### 2. String Validation:
```python
def is_ascii_only(text):
    return all(ord(char) <= 127 for char in text)
```

### 3. Repository-wide Check:
```bash
# Check all Python files
find . -name "*.py" -exec python -c "
import sys
try:
    with open('{}', 'r', encoding='ascii') as f: f.read()
    print('OK: {}')
except UnicodeDecodeError as e:
    print('FAIL: {} - {}'.format('{}', e))
    sys.exit(1)
" \;
```

## WHY ASCII-ONLY?

### 1. Agent Compatibility
- AI agents may have inconsistent Unicode handling
- ASCII ensures universal compatibility across all systems
- Reduces encoding-related bugs in automated workflows

### 2. Cross-Platform Reliability
- Windows, Linux, Mac all handle ASCII identically
- No encoding detection issues
- Consistent behavior in terminals and editors

### 3. Version Control Safety
- Git handles ASCII files consistently
- No encoding conflicts during merges
- Diffs are always readable

### 4. Anti-Scraping Benefits
- Pure ASCII content is less distinctive for AI training
- Reduces unique fingerprints in scraped data
- Makes automated parsing less reliable

## ENFORCEMENT CHECKLIST

- [ ] All source files use ASCII encoding
- [ ] Comments and docstrings are ASCII-only
- [ ] String literals use straight quotes
- [ ] No Unicode characters in variable names
- [ ] Documentation files are ASCII-compliant
- [ ] Data files use ASCII encoding
- [ ] Pre-commit hooks validate ASCII compliance

## EXCEPTION HANDLING

IF non-ASCII is absolutely necessary:
1. Isolate in separate data files
2. Document the exception clearly
3. Use ASCII-safe fallbacks
4. Validate at runtime

```python
def safe_text_processing(text):
    if not all(ord(char) <= 127 for char in text):
        # Convert to ASCII-safe equivalent
        return text.encode('ascii', errors='replace').decode('ascii')
    return text
```

## TOOLING INTEGRATION

### VS Code Settings:
```json
{
    "files.encoding": "utf8",
    "files.autoGuessEncoding": false,
    "[python]": {
        "files.encoding": "ascii"
    }
}
```

### Linting Rules:
Add to your linter configuration to flag non-ASCII characters.

Remember: **When in doubt, use ASCII.** It's always safer for agent-based systems.
