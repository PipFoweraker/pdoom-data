#!/usr/bin/env python3
"""
ASCII Validation Script
Ensures all project files contain only ASCII characters (0-127)
"""

import sys
from pathlib import Path

def check_file_ascii(filepath):
    """Check if file contains only ASCII characters (0-127) and detect emoji/Unicode"""
    try:
        with open(filepath, 'r', encoding='ascii') as f:
            content = f.read()
        
        # Additional check for common emoji and Unicode ranges
        emoji_found = []
        for i, char in enumerate(content):
            char_code = ord(char)
            if char_code > 127:
                # Identify common problematic characters
                if 0x1F600 <= char_code <= 0x1F64F:  # Emoticons
                    emoji_found.append(f"Line {content[:i].count(chr(10))+1}: Emoticon '{char}'")
                elif 0x1F300 <= char_code <= 0x1F5FF:  # Misc Symbols
                    emoji_found.append(f"Line {content[:i].count(chr(10))+1}: Symbol '{char}'")
                elif 0x1F680 <= char_code <= 0x1F6FF:  # Transport Symbols
                    emoji_found.append(f"Line {content[:i].count(chr(10))+1}: Transport symbol '{char}'")
                elif 0x2600 <= char_code <= 0x26FF:   # Misc symbols
                    emoji_found.append(f"Line {content[:i].count(chr(10))+1}: Misc symbol '{char}'")
                elif char_code in [0x2014, 0x2018, 0x2019, 0x201C, 0x201D]:  # Smart quotes, em-dash
                    emoji_found.append(f"Line {content[:i].count(chr(10))+1}: Smart punctuation '{char}'")
        
        if emoji_found:
            return False, "Emoji/Unicode characters found: " + "; ".join(emoji_found[:3])
        
        return True, None
    except UnicodeDecodeError as e:
        return False, str(e)

def main():
    """Check all relevant files for ASCII compliance"""
    file_patterns = ["*.py", "*.md", "*.txt", "*.json"]
    issues = []
    checked = 0
    
    print("ASCII Compliance Validator")
    print("=" * 30)
    
    for pattern in file_patterns:
        for filepath in Path(".").rglob(pattern):
            # Skip hidden files and directories
            if any(part.startswith('.') for part in filepath.parts):
                continue
                
            checked += 1
            is_ascii, error = check_file_ascii(filepath)
            
            if is_ascii:
                print(f"OK: {filepath}")
            else:
                print(f"FAIL: {filepath} - {error}")
                issues.append((filepath, error))
    
    print("\n" + "=" * 30)
    print(f"Checked {checked} files")
    
    if issues:
        print(f"FAILED: {len(issues)} files contain non-ASCII characters")
        print("\nTo fix:")
        print("1. Replace smart quotes with straight quotes")
        print("2. Replace em-dashes with double hyphens")  
        print("3. Replace ellipsis with three dots")
        print("4. Remove other Unicode characters")
        return False
    else:
        print("SUCCESS: All files are ASCII-compliant")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
