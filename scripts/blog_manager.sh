#!/bin/bash
# Development Blog Post Generator
# Creates structured development blog posts with standardized format

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
DEVBLOG_FILE="$REPO_ROOT/DEVBLOG.md"
BLOG_POSTS_DIR="$REPO_ROOT/blog"

# Create blog posts directory if it doesn't exist
mkdir -p "$BLOG_POSTS_DIR"

# Get current date and version
CURRENT_DATE=$(date +"%Y-%m-%d")
CURRENT_TIME=$(date +"%H:%M:%S")
CURRENT_VERSION=$(cat "$REPO_ROOT/VERSION" 2>/dev/null || echo "0.0.0")

# Function to create a new blog post
create_blog_post() {
    local title="$1"
    local category="$2"
    
    if [ -z "$title" ]; then
        echo "Usage: create_blog_post <title> [category]"
        echo "Categories: feature, bugfix, documentation, architecture, release"
        exit 1
    fi
    
    if [ -z "$category" ]; then
        category="development"
    fi
    
    # Create filename from title
    filename=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')
    blog_file="$BLOG_POSTS_DIR/${CURRENT_DATE}-${filename}.md"
    
    # Create blog post template
    cat > "$blog_file" << EOF
# $title

**Date**: $CURRENT_DATE $CURRENT_TIME UTC
**Version**: $CURRENT_VERSION
**Category**: $category
**Author**: Development Team

## Summary
Brief summary of changes or developments.

## Technical Details
### Changes Made
- Change 1
- Change 2
- Change 3

### Files Modified
\`\`\`
# List modified files
git diff --name-only
\`\`\`

### Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] ASCII compliance verified
- [ ] Documentation updated

## Impact Assessment
### User Impact
- How this affects end users

### Developer Impact  
- How this affects other developers

### Integration Impact
- How this affects cross-repo integration

## Next Steps
- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3

## Links
- Related Issues: #
- Related PRs: #
- Documentation: [Link]()

---
*This post is permanently stored and accessible via:*
- GitHub: https://github.com/PipFoweraker/pdoom-data/blob/main/blog/${CURRENT_DATE}-${filename}.md
- Local: \`blog/${CURRENT_DATE}-${filename}.md\`
EOF

    echo "Created blog post: $blog_file"
    echo "Edit the file to add your content, then run:"
    echo "  $0 publish $blog_file"
}

# Function to publish a blog post (add to main DEVBLOG.md)
publish_blog_post() {
    local blog_file="$1"
    
    if [ ! -f "$blog_file" ]; then
        echo "Blog file not found: $blog_file"
        exit 1
    fi
    
    # Extract title and date from blog post
    title=$(head -1 "$blog_file" | sed 's/^# //')
    post_date=$(grep "^**Date**:" "$blog_file" | sed 's/^**Date**: //')
    category=$(grep "^**Category**:" "$blog_file" | sed 's/^**Category**: //')
    
    # Create summary entry for main DEVBLOG.md
    blog_entry="
### $title ($post_date)
**Category**: $category

$(head -20 "$blog_file" | grep -A 5 "## Summary" | tail -n +2 | head -3)

[Read full post](blog/$(basename "$blog_file"))

"
    
    # Add to DEVBLOG.md after "## Recent Changes"
    if grep -q "## Recent Changes" "$DEVBLOG_FILE"; then
        # Use temporary file for safe editing
        temp_file=$(mktemp)
        awk '
            /^## Recent Changes/ { 
                print $0; 
                print "'"$blog_entry"'"; 
                next 
            } 
            { print }
        ' "$DEVBLOG_FILE" > "$temp_file"
        mv "$temp_file" "$DEVBLOG_FILE"
        echo "Published blog post to DEVBLOG.md"
    else
        echo "Warning: Could not find '## Recent Changes' section in DEVBLOG.md"
    fi
}

# Function to list all blog posts
list_blog_posts() {
    echo "Development Blog Posts:"
    echo "======================="
    
    if [ -d "$BLOG_POSTS_DIR" ]; then
        for post in "$BLOG_POSTS_DIR"/*.md; do
            if [ -f "$post" ]; then
                title=$(head -1 "$post" | sed 's/^# //')
                date=$(grep "^**Date**:" "$post" | sed 's/^**Date**: //')
                echo "- $(basename "$post"): $title ($date)"
            fi
        done
    else
        echo "No blog posts found."
    fi
}

# Function to validate blog post format
validate_blog_post() {
    local blog_file="$1"
    
    if [ ! -f "$blog_file" ]; then
        echo "Blog file not found: $blog_file"
        exit 1
    fi
    
    echo "Validating blog post: $blog_file"
    
    # Check required sections
    required_sections=("# " "**Date**:" "**Version**:" "**Category**:" "## Summary" "## Technical Details")
    
    for section in "${required_sections[@]}"; do
        if ! grep -q "^$section" "$blog_file"; then
            echo "ERROR: Missing required section: $section"
            exit 1
        fi
    done
    
    # Check ASCII compliance
    if ! python "$REPO_ROOT/validate_ascii.py" "$blog_file" 2>/dev/null; then
        echo "ERROR: Blog post contains non-ASCII characters"
        exit 1
    fi
    
    echo "Blog post validation passed!"
}

# Function to generate release notes
generate_release_notes() {
    local version="$1"
    
    if [ -z "$version" ]; then
        version="$CURRENT_VERSION"
    fi
    
    release_file="$BLOG_POSTS_DIR/${CURRENT_DATE}-release-${version}.md"
    
    cat > "$release_file" << EOF
# Release Notes v$version

**Date**: $CURRENT_DATE $CURRENT_TIME UTC
**Version**: $version
**Category**: release
**Author**: Release Team

## Release Summary
Version $version of pdoom-data is now available.

## What's New
### Features
- Feature 1
- Feature 2

### Improvements
- Improvement 1
- Improvement 2

### Bug Fixes
- Fix 1
- Fix 2

## Technical Changes
### Files Changed
\`\`\`bash
# Generate with: git diff --name-only v$(previous_version)..v$version
\`\`\`

### Breaking Changes
- None in this release

### Deprecations
- None in this release

## Installation
\`\`\`bash
git clone https://github.com/PipFoweraker/pdoom-data.git
cd pdoom-data
git checkout v$version
python setup_clean.py
\`\`\`

## Verification
\`\`\`bash
# Verify ASCII compliance
python validate_ascii.py

# Check version
cat VERSION
\`\`\`

## Migration Guide
No migration required for this release.

## Known Issues
- None reported

## Next Release
Planned features for next release:
- Planned feature 1
- Planned feature 2

## Support
- GitHub Issues: https://github.com/PipFoweraker/pdoom-data/issues
- Documentation: https://github.com/PipFoweraker/pdoom-data/blob/main/README.md

---
*Release notes are permanently stored at:*
- GitHub: https://github.com/PipFoweraker/pdoom-data/blob/main/blog/${CURRENT_DATE}-release-${version}.md
EOF

    echo "Generated release notes: $release_file"
    echo "Edit the file to add specific release details."
}

# Main command handling
case "$1" in
    "new"|"create")
        create_blog_post "$2" "$3"
        ;;
    "publish")
        publish_blog_post "$2"
        ;;
    "list")
        list_blog_posts
        ;;
    "validate")
        validate_blog_post "$2"
        ;;
    "release")
        generate_release_notes "$2"
        ;;
    *)
        echo "Development Blog Manager"
        echo "======================="
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  new <title> [category]    Create new blog post"
        echo "  publish <file>            Publish blog post to DEVBLOG.md"
        echo "  list                      List all blog posts"
        echo "  validate <file>           Validate blog post format"
        echo "  release [version]         Generate release notes"
        echo ""
        echo "Categories: feature, bugfix, documentation, architecture, release"
        echo ""
        echo "Examples:"
        echo "  $0 new 'Added event validation' feature"
        echo "  $0 publish blog/2025-09-14-added-event-validation.md"
        echo "  $0 release 1.1.0"
        ;;
esac
