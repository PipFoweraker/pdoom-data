#!/usr/bin/env python3
"""
ASCII Fixer Script
Automatically converts Unicode characters to ASCII equivalents
"""

import sys
from pathlib import Path

def fix_unicode_to_ascii(text):
    """Convert common Unicode characters to ASCII equivalents"""
    replacements = {
        # Unicode quotes to ASCII
        '\u2018': "'",   # Left single quote
        '\u2019': "'",   # Right single quote  
        '\u201c': '"',   # Left double quote
        '\u201d': '"',   # Right double quote
        
        # Dashes to ASCII
        '\u2013': '-',   # En dash
        '\u2014': '--',  # Em dash
        
        # Spaces and punctuation
        '\u00a0': ' ',   # Non-breaking space
        '\u2026': '...',  # Ellipsis
        '\u2022': '*',   # Bullet point
        '\u00b7': '*',   # Middle dot
        
        # Other common Unicode
        '\u00e9': 'e',   # e with acute
        '\u00e8': 'e',   # e with grave
        '\u00e1': 'a',   # a with acute
        '\u00f1': 'n',   # n with tilde
        '\u00fc': 'u',   # u with umlaut
        '\u00c2': 'A',   # A with circumflex
    }
    
    fixed_text = text
    changes_made = []
    
    for unicode_char, ascii_replacement in replacements.items():
        if unicode_char in fixed_text:
            count = fixed_text.count(unicode_char)
            fixed_text = fixed_text.replace(unicode_char, ascii_replacement)
            changes_made.append(f"'{unicode_char}' -> '{ascii_replacement}' ({count}x)")
    
    # Handle any remaining non-ASCII characters
    remaining_non_ascii = []
    for i, char in enumerate(fixed_text):
        if ord(char) > 127:
            remaining_non_ascii.append((i, char, ord(char)))
    
    if remaining_non_ascii:
        print(f"  Removing {len(remaining_non_ascii)} other non-ASCII characters")
        fixed_text = ''.join(char if ord(char) <= 127 else '?' for char in fixed_text)
    
    return fixed_text, changes_made

def fix_file(filepath):
    """Fix Unicode characters in a single file"""
    try:
        # Try to read with UTF-8 first
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # If that fails, try with latin-1
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    fixed_content, changes = fix_unicode_to_ascii(content)
    
    if changes:
        print(f"FIXING: {filepath}")
        for change in changes:
            print(f"  {change}")
        
        # Write back as ASCII
        with open(filepath, 'w', encoding='ascii') as f:
            f.write(fixed_content)
        
        return True
    else:
        print(f"OK: {filepath} (no changes needed)")
        return False

def main():
    """Fix all files with Unicode issues"""
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("DRY RUN MODE - No files will be modified")
        return
    
    print("ASCII Fixer - Converting Unicode to ASCII")
    print("=" * 40)
    
    files_to_check = [
        "game_integration_helpers.py",
        "institutional_decay_events.py", 
        "setup_script.py",
        "ASCII_CODING_STANDARDS.md",
        "pdoom_historical_events.md"
    ]
    
    fixed_count = 0
    
    for filename in files_to_check:
        filepath = Path(filename)
        if filepath.exists():
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"SKIP: {filename} (not found)")
    
    print("\n" + "=" * 40)
    print(f"Fixed {fixed_count} files")
    print("\nRun 'python validate_ascii.py' to verify all files are now ASCII-compliant")

if __name__ == "__main__":
    main()
