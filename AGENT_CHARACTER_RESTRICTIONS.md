# AGENT INSTRUCTIONS - STRICT CHARACTER COMPLIANCE

## MANDATORY CHARACTER RESTRICTIONS

### ABSOLUTELY FORBIDDEN CHARACTERS
**Agents must NEVER output any of the following:**

#### Emoji and Symbols
- [FORBIDDEN] ALL EMOJI: gaming, web, file, checkmarks, stars, fire, computers, charts, books, targets, rockets, etc.
- [FORBIDDEN] Unicode symbols: checkmarks, x-marks, arrows, warning signs, lightning, magnifying glass, etc.
- [FORBIDDEN] Mathematical symbols: greater-equal, less-equal, not-equal, plus-minus, infinity, summation, product, delta, etc.
- [FORBIDDEN] Currency symbols: euro, pound, yen, rupee, bitcoin, etc.
- [FORBIDDEN] Box drawing: tree branches, vertical lines, corners, etc.

#### Typographic Characters  
- [FORBIDDEN] Smart quotes: curly double quotes, curly single quotes
- [FORBIDDEN] Em-dash: long dash character
- [FORBIDDEN] En-dash: medium dash character
- [FORBIDDEN] Ellipsis: three-dot character
- [FORBIDDEN] Bullet points: filled circles, hollow circles, squares

#### Other Unicode
- [FORBIDDEN] Accented characters: letters with accent marks, tildes, cedillas, etc.
- [FORBIDDEN] Special spaces: non-breaking space, thin space, etc.
- [FORBIDDEN] Directional marks and invisible characters

### ALLOWED CHARACTERS ONLY (ASCII 32-126)
**Agents may ONLY use these characters:**

#### Letters and Numbers
- [ALLOWED] A-Z (uppercase)
- [ALLOWED] a-z (lowercase) 
- [ALLOWED] 0-9 (digits)

#### Standard Punctuation
- [ALLOWED] . (period)
- [ALLOWED] , (comma)
- [ALLOWED] ! (exclamation)
- [ALLOWED] ? (question mark)
- [ALLOWED] : (colon)
- [ALLOWED] ; (semicolon)
- [ALLOWED] " (straight double quote)
- [ALLOWED] ' (straight single quote/apostrophe)

#### Brackets and Grouping
- [ALLOWED] ( ) (parentheses)
- [ALLOWED] [ ] (square brackets)
- [ALLOWED] { } (curly braces)
- [ALLOWED] < > (angle brackets)

#### Mathematical and Technical
- [ALLOWED] + (plus)
- [ALLOWED] - (minus/hyphen)
- [ALLOWED] * (asterisk)
- [ALLOWED] / (forward slash)
- [ALLOWED] \ (backslash)
- [ALLOWED] = (equals)
- [ALLOWED] % (percent)
- [ALLOWED] # (hash)
- [ALLOWED] & (ampersand)
- [ALLOWED] @ (at sign)
- [ALLOWED] $ (dollar sign)

#### Special Characters
- [ALLOWED] _ (underscore)
- [ALLOWED] | (pipe)
- [ALLOWED] ^ (caret)
- [ALLOWED] ~ (tilde)
- [ALLOWED] ` (backtick)

#### Whitespace
- [ALLOWED] (space, ASCII 32)
- [ALLOWED] Tab (ASCII 9)
- [ALLOWED] Newline (ASCII 10)
- [ALLOWED] Carriage return (ASCII 13)

## REPLACEMENT RULES

### When you need to express concepts that might use forbidden characters:

#### Status Indicators
- [FORBIDDEN] checkmark symbol -> [ALLOWED] [OK] or [PASS] or [YES]
- [FORBIDDEN] x-mark symbol -> [ALLOWED] [FAIL] or [NO] or [ERROR]
- [FORBIDDEN] warning symbol -> [ALLOWED] [WARNING] or [CAUTION]

#### Lists and Structure
- [FORBIDDEN] bullet point -> [ALLOWED] - (hyphen)
- [FORBIDDEN] tree branches -> [ALLOWED] +-- or |--
- [FORBIDDEN] tree corners -> [ALLOWED] +-- or |--

#### Emphasis and Formatting
- [FORBIDDEN] em-dash -> [ALLOWED] -- (double hyphen)
- [FORBIDDEN] ellipsis character -> [ALLOWED] ... (three periods)
- [FORBIDDEN] smart quotes -> [ALLOWED] " " (straight quotes)

#### Categories and Labels
- [FORBIDDEN] file emoji [DATA] -> [ALLOWED] [DATA]
- [FORBIDDEN] web emoji [WEB] -> [ALLOWED] [WEB]  
- [FORBIDDEN] game emoji [GAME] -> [ALLOWED] [GAME]

## VALIDATION REQUIREMENT

Every file an agent creates or modifies MUST pass this test:
```python
# All characters must have ASCII codes 0-127
for char in content:
    assert ord(char) <= 127, f"Non-ASCII character found: {char} (code: {ord(char)})"
```

## ENFORCEMENT

### Automatic Validation
- All files automatically checked by `validate_ascii.py`
- CI/CD pipeline rejects any non-ASCII content
- Development metrics track ASCII compliance score

### Agent Responsibilities  
1. **Before creating any content**: Verify all characters are ASCII-only
2. **When editing existing files**: Maintain ASCII compliance
3. **When copying/referencing external content**: Convert to ASCII equivalents
4. **When generating documentation**: Use only allowed characters

### Examples of Compliant Output

#### Good Examples:
```
[OK] All tests passed
Status: Development build ready
Next steps:
  - Complete feature implementation
  - Update documentation
  - Run validation tests

Performance metrics:
  Files: 30
  Lines: 8,617
  ASCII Compliance: 100%
```

#### Bad Examples:
```
[checkmark] All tests passed          # FORBIDDEN: checkmark emoji
Status: Development build[ellipsis] ready  # FORBIDDEN: ellipsis
Next steps:
  [bullet] Complete feature         # FORBIDDEN: bullet point
  [bullet] Update documentation     # FORBIDDEN: bullet point

Performance metrics:
  Files: 30
  Lines: 8,617  
  ASCII Compliance: 100%
```

## MOTIVATION

This strict ASCII-only policy ensures:
- **Universal agent compatibility**: All AI agents can process the content
- **Cross-platform reliability**: Works on any system, encoding, or terminal
- **Long-term accessibility**: Content remains readable regardless of Unicode changes
- **Development efficiency**: No encoding-related bugs or issues
- **Professional standards**: Clean, consistent, technical documentation

## COMPLIANCE VERIFICATION

Before submitting any work, agents must verify:
```bash
# Run ASCII validation
python validate_ascii.py

# Confirm 100% compliance
# Expected output: "SUCCESS: All files are ASCII-compliant"
```

**Remember: When in doubt, use ASCII. There are no exceptions to this rule.**
