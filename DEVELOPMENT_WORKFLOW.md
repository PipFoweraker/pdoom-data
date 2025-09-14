# Development Workflow and Standards

## Overview
This document establishes the complete development workflow for pdoom-data, including versioning, documentation, and quality assurance protocols.

## Core Principles
- **Sparse**: Minimal necessary components only
- **Technical**: Engineering-focused documentation
- **Modular**: Clear separation of concerns  
- **Lightweight**: Fast, efficient operations
- **Permanent**: All development notes permanently stored
- **Accessible**: Documentation available through GitHub
- **ASCII-Compliant**: Full compatibility with agent-based development

## Versioning System

### Semantic Versioning
- **MAJOR.MINOR.PATCH** format (e.g., 1.0.0)
- **Major**: Breaking changes, architectural overhauls
- **Minor**: New features, significant improvements
- **Patch**: Bug fixes, minor improvements

### Version Management Tools
```bash
# Check current version
python version_manager.py --current

# Auto-increment based on changes
python version_manager.py --auto

# Manual increment
python version_manager.py --increment patch|minor|major

# Create git tag
python version_manager.py --increment minor --tag
```

## Documentation Standards

### Required Documentation
1. **DEVBLOG.md** - Primary development log
2. **README.md** - Project overview and setup
3. **CROSS_REPO_INTEGRATION.md** - Integration architecture
4. **ASCII_CODING_STANDARDS.md** - Coding standards
5. **Individual blog posts** - Detailed development notes

### Blog Management
```bash
# Create new blog post
scripts/blog_manager.sh new "Feature description" feature

# Publish to main devblog
scripts/blog_manager.sh publish blog/2025-09-14-feature.md

# Generate release notes
scripts/blog_manager.sh release 1.1.0

# Validate blog post format
scripts/blog_manager.sh validate blog/post.md
```

## Quality Assurance

### Automated Testing (CI/CD)
- **ASCII Compliance**: All files must pass strict ASCII validation
- **Documentation Quality**: Required documentation must exist and be complete
- **Version Consistency**: Version references must be synchronized
- **JSON Validation**: All JSON exports must be valid
- **Behavioral Tests**: Documentation permanence and accessibility verified

### Manual Quality Checks
```bash
# ASCII compliance check
python validate_ascii.py

# Generate development metrics
python dev_metrics.py --summary

# Export detailed metrics
python dev_metrics.py --export metrics_$(date +%Y%m%d).json
```

## Development Workflow

### 1. Feature Development
```bash
# Start feature development
git checkout -b feature/new-feature

# Create development blog post
scripts/blog_manager.sh new "Implementing new feature" feature

# Develop feature...
# Edit files, maintain ASCII compliance

# Validate changes
python validate_ascii.py
python dev_metrics.py --summary
```

### 2. Documentation Updates
```bash
# Update relevant documentation
# Edit DEVBLOG.md, README.md, etc.

# Publish blog post
scripts/blog_manager.sh publish blog/2025-09-14-new-feature.md

# Validate documentation
scripts/blog_manager.sh validate blog/2025-09-14-new-feature.md
```

### 3. Version Management
```bash
# Auto-detect version increment
python version_manager.py --auto

# Or manual increment
python version_manager.py --increment minor --message "Added new feature"

# Create git tag for release
python version_manager.py --increment minor --tag
```

### 4. Release Process
```bash
# Generate release notes
scripts/blog_manager.sh release 1.1.0

# Create metrics snapshot
python dev_metrics.py --snapshot

# Commit and push
git add .
git commit -m "Release v1.1.0: Added new feature"
git push origin main --tags
```

## CI/CD Pipeline

### Triggers
- **Push to main**: Full documentation validation and publishing
- **Pull requests**: Quality assurance checks
- **Manual triggers**: Comprehensive testing

### Validation Steps
1. ASCII compliance across all files
2. Development blog completeness validation
3. Documentation permanence verification
4. Version consistency checks
5. JSON schema validation
6. Behavioral documentation requirements

### Automated Actions
- Update build timestamps in DEVBLOG.md
- Generate permanent documentation URLs
- Create development metrics snapshots
- Publish documentation updates

## Metrics and Analytics

### Tracked Metrics
- Code metrics (files, lines, complexity)
- ASCII compliance score
- Recent development activity
- Git commit statistics
- Documentation coverage

### Reporting
```bash
# Generate comprehensive development report
python dev_metrics.py --report > development_report.json

# Print summary to console
python dev_metrics.py --summary

# Save periodic snapshot
python dev_metrics.py --snapshot
```

## Integration with External Systems

### GitHub Integration
- All documentation permanently accessible via GitHub URLs
- CI/CD pipeline ensures quality standards
- Release tags create permanent version snapshots
- Issues and PRs linked to development blog posts

### Cross-Repository Coordination
- Version synchronization across pdoom-data, pdoom-website, pdoom1
- Shared documentation standards
- Coordinated release processes
- Common quality assurance protocols

## File Structure

```
pdoom-data/
+-- VERSION                        # Current version number
+-- DEVBLOG.md                     # Primary development log
+-- version_manager.py             # Version management tool
+-- dev_metrics.py                 # Development analytics
+-- validate_ascii.py              # ASCII compliance checker
+-- scripts/
|   +-- blog_manager.sh            # Blog post management
+-- blog/                          # Individual blog posts
|   +-- YYYY-MM-DD-post-title.md   # Timestamped blog posts
+-- .github/workflows/
|   +-- documentation-ci.yml       # CI/CD pipeline
+-- dev_metrics.db                 # Metrics database (auto-generated)
```

## Best Practices

### Development Notes
- Document all significant changes in blog posts
- Use structured templates for consistency
- Include technical details and impact assessments
- Link related issues, PRs, and documentation

### Version Control
- Use semantic versioning consistently
- Tag all releases in git
- Maintain comprehensive changelogs
- Document breaking changes clearly

### Quality Assurance
- Run ASCII validation before commits
- Validate all JSON exports
- Test documentation links and accessibility
- Verify cross-repository integration points

### Communication
- Keep development blog updated with recent changes
- Use standardized categories for blog posts
- Include permanent URLs for reference
- Maintain public accessibility through GitHub

This workflow ensures comprehensive documentation, quality assurance, and permanent accessibility of all development activities while maintaining the lightweight, modular architecture required for effective agent-based development.
