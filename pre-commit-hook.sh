#!/bin/bash
# Pre-commit hook to enforce ASCII-only content
# Copy this to .git/hooks/pre-commit and make executable
#
# This hook deliberately does NOT call validate_ascii.py. Two readers of one
# rule is the property that caught the redaction verifier reporting clean while
# ten records still carried addresses, and CLAUDE.md's second clause -- do not
# derive what to look for from the system you are checking -- says a shared
# helper would make a defect in that helper invisible to both gates at once.
# What must stay in step is the extension list below and FILE_PATTERNS in
# validate_ascii.py, because a commit gate and a CI gate that disagree about
# scope let a file through one and stall it at the other.
#
# The hook itself was outside the gate it enforces until 2026-08-24. It printed
# two emoji, and validate_ascii.py's sweep globbed only *.py *.md *.txt *.json,
# so a `.sh` was never looked at and the ASCII enforcement tool shipped six
# non-ASCII bytes under a green "SUCCESS: All files are ASCII-compliant".

echo "Validating ASCII-only compliance..."

# Function to check if file contains only ASCII characters.
#
# stderr is NOT redirected to /dev/null. It was, and that is the same mistake
# blog_manager.sh made at line 184: an interpreter that is absent, or a file
# that cannot be read, comes back through the same nonzero exit as a genuine
# non-ASCII byte, and hiding the message leaves the committer with a true
# verdict and no way to tell which of the three happened. The filename is
# passed as argv rather than interpolated into the source, so a path
# containing a quote cannot rewrite the program checking it.
check_ascii() {
    python3 -c "
import sys
path = sys.argv[1]
try:
    with open(path, 'r', encoding='ascii') as f:
        f.read()
except UnicodeDecodeError as e:
    print('NON-ASCII in ' + path + ': ' + str(e))
    sys.exit(1)
except OSError as e:
    print('COULD NOT READ ' + path + ': ' + str(e))
    sys.exit(1)
" "$1"
}

# Check all staged files
failed_files=()

for file in $(git diff --cached --name-only); do
    if [[ -f "$file" ]]; then
        case "$file" in
            *.py|*.md|*.txt|*.json|*.yaml|*.yml|*.sh)
                if ! check_ascii "$file"; then
                    failed_files+=("$file")
                fi
                ;;
        esac
    fi
done

# Report results
if [[ ${#failed_files[@]} -gt 0 ]]; then
    echo "[FAIL] ASCII VALIDATION FAILED"
    echo "The following files could not be read as ASCII:"
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
    echo "There is no auto-fixer, and that is on purpose. This message used to"
    echo "say 'Run: python legacy/2025-09_prototype/setup_script.py to auto-fix"
    echo "some issues'. That script has never parsed -- SyntaxError at line 250"
    echo "since b810351 on 2025-09-14, from a nested triple-quote inside its"
    echo "integration-guide string -- so for eleven months the advice given to"
    echo "every failing commit was to run a file that cannot start. Its sibling"
    echo "legacy/2025-09_prototype/fix_ascii.py DOES run, and substitutes '?'"
    echo "for anything it does not recognise, which would shred every tree"
    echo "diagram in docs/ into rows of question marks. Do not run it either."
    echo ""
    echo "Substitute by hand, or with an explicit map that ERRORS on a"
    echo "character nobody has decided about. See legacy/2025-09_prototype/"
    echo "README.md and the 2026-08-10 clearance in CLAUDE.md."
    exit 1
else
    echo "[PASS] All files are ASCII-compliant"
fi
