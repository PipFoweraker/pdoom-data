#!/bin/bash
# Pre-commit hook to enforce ASCII-only content
# Copy this to .git/hooks/pre-commit and make executable

echo "Validating ASCII-only compliance..."

# Function to check if file contains only ASCII characters
check_ascii() {
    if python3 -c "
import sys
try:
    with open('$1', 'r', encoding='ascii') as f:
        f.read()
except UnicodeDecodeError as e:
    print('NON-ASCII ERROR in $1: ' + str(e))
    sys.exit(1)
" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check all staged files
failed_files=()

for file in $(git diff --cached --name-only); do
    if [[ -f "$file" ]]; then
        case "$file" in
            *.py|*.md|*.txt|*.json|*.yaml|*.yml)
                if ! check_ascii "$file"; then
                    failed_files+=("$file")
                fi
                ;;
        esac
    fi
done

# Report results
if [[ ${#failed_files[@]} -gt 0 ]]; then
    echo "❌ ASCII VALIDATION FAILED"
    echo "The following files contain non-ASCII characters:"
    for file in "${failed_files[@]}"; do
        echo "  - $file"
    done
    echo ""
    echo "Fix these files before committing:"
    echo "1. Replace smart quotes with straight quotes"
    echo "2. Replace em-dashes with double hyphens"
    echo "3. Replace ellipsis with three dots"
    echo "4. Remove or replace other Unicode characters"
    echo ""
    echo "Run: python setup_script.py to auto-fix some issues"
    exit 1
else
    echo "✅ All files are ASCII-compliant"
fi
