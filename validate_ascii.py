#!/usr/bin/env python3
"""
ASCII Validation Script
Ensures all project files contain only ASCII characters (0-127)

Two modes, and the second one exists because its absence made a caller lie.
Given no arguments this globs the tree below the current working directory,
which is what `.github/workflows/documentation-ci.yml` and every "python
validate_ascii.py" line in the docs rely on. Given paths it validates exactly
those paths and nothing else.

Until 2026-08-19 the second mode did not exist while callers already assumed
it did. `main()` took no argv and dropped whatever it was handed on the floor,
so `scripts/blog_manager.sh` passing a blog file, with stderr sent to
/dev/null, got a sweep of the caller's working directory back and printed
"Blog post validation passed!" -- a true statement about a different thing,
the same shape as the redaction verifier that reported clean while ten records
still carried addresses. `templates/cross-repo-api-spec.md` line 406 has
documented `validate_ascii.py data/events/*.json` the whole time.

The rule that follows from that: when this is told to check a named path it
must either check that exact path or fail. A path that does not exist, or is a
directory, or cannot be read, is a FAILURE and not a skip, because a skip is
indistinguishable from a pass to the shell that called us.
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
    except OSError as e:
        # Missing, unreadable, or a directory. Returned as a failure rather
        # than raised so the caller reports it in the same shape as a
        # non-ASCII byte: either way we did not manage to check the thing we
        # were asked about, and either way the answer is not "pass".
        return False, "could not read: %s" % e

def glob_tree():
    """Every file the no-argument sweep considers, below the working directory."""
    file_patterns = ["*.py", "*.md", "*.txt", "*.json"]
    for pattern in file_patterns:
        for filepath in Path(".").rglob(pattern):
            # Skip hidden files and directories
            if any(part.startswith('.') for part in filepath.parts):
                continue
            yield filepath

def named_paths(names):
    """Exactly the paths asked for, with anything unusable already failed.

    Nothing here silently drops a name. A directory is refused rather than
    walked: the caller wrote a path it believed was a file, and quietly
    substituting a different question is precisely the defect this argument
    handling was added to close.
    """
    targets, refusals = [], []
    for name in names:
        path = Path(name)
        if path.is_dir():
            refusals.append((path, "is a directory, not a file -- pass a glob"))
        elif not path.exists():
            refusals.append((path, "does not exist"))
        else:
            targets.append(path)
    return targets, refusals

def main(argv=None):
    """Check ASCII compliance: the named paths if any were given, else the tree."""
    argv = list(sys.argv[1:] if argv is None else argv)
    issues = []
    checked = 0

    print("ASCII Compliance Validator")
    print("=" * 30)

    if argv:
        paths, refusals = named_paths(argv)
        for path, why in refusals:
            print(f"FAIL: {path} - {why}")
            issues.append((path, why))
    else:
        paths, refusals = glob_tree(), []

    for filepath in paths:
        checked += 1
        is_ascii, error = check_file_ascii(filepath)

        if is_ascii:
            print(f"OK: {filepath}")
        else:
            print(f"FAIL: {filepath} - {error}")
            issues.append((filepath, error))

    print("\n" + "=" * 30)
    print(f"Checked {checked} files")

    # Named paths that all failed to resolve leave checked at zero. Say so
    # loudly: "Checked 0 files" followed by SUCCESS is the exact reading that
    # let a broken call site look healthy for eleven months.
    if argv and not checked:
        print("FAILED: nothing could be checked out of "
              f"{len(argv)} path(s) named on the command line")
        return False

    if issues:
        # "contain non-ASCII characters" was accurate while the only possible
        # failure was a bad byte. A path that could not be read now fails too,
        # and calling that a non-ASCII character would be the same species of
        # true-about-something-else that this script was just fixed for.
        print(f"FAILED: {len(issues)} path(s) did not pass")
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
