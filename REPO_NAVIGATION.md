# P(DOOM) PROJECT NAVIGATION
# Copy this file to all related repositories for agent/LLM navigation

## PROJECT ECOSYSTEM

This is part of the P(Doom) project ecosystem consisting of three repositories:

### [DATA] [pdoom-data](https://github.com/PipFoweraker/pdoom-data)
**Historical Events Database**
- 28+ real AI safety events (2016-2025)
- Game mechanics data and impacts
- JSON exports for integration
- ASCII-only content for agent compatibility

**Key Files:**
- `event_data_structures.py` - Core data types
- `*_events.py` - Event categories (funding, technical, organizational, institutional)
- `game_integration_helpers.py` - Game logic utilities
- `data/events/*.json` - Exported data formats

### [WEB] [pdoom-website](https://github.com/PipFoweraker/pdoom-website) 
**Public Website**
- Event timeline displays
- Game information and downloads
- Documentation and guides
- Community engagement

**Integration Points:**
- Consumes JSON exports from pdoom-data
- Displays interactive event timelines
- Links to game scenarios
- Provides public API endpoints

### [GAME] [pdoom1](https://github.com/PipFoweraker/pdoom1)
**Strategy Game**
- Interactive P(Doom) simulation
- Historical event integration
- Player choice mechanics
- Save/load game states

**Integration Points:**
- Imports event modules from pdoom-data
- Processes historical events in gameplay
- Tracks player interactions with events
- Provides gameplay analytics

## INTEGRATION ARCHITECTURE

```
pdoom-data (Source of Truth)
    |
    |-- JSON Exports --> pdoom-website (Display)
    |                        |
    |                        v
    |                   Public API
    |
    |-- Python Modules --> pdoom1 (Gameplay)
                               |
                               v
                          Analytics
```

## DEVELOPMENT STANDARDS

### ASCII-ONLY PROTOCOL
- ALL content must be ASCII characters (0-127)
- NO Unicode quotes, em-dashes, special characters
- Use validation tools: `validate_ascii.py`
- Critical for agent/LLM compatibility

### FILE ENCODING
```python
# Always specify ASCII encoding
with open("file.txt", "w", encoding='ascii') as f:
    f.write(content)
```

### CROSS-REPO SYNCHRONIZATION
- Data schema versioning (semantic versioning)
- Automated sync workflows between repos
- Breaking change notifications
- Backward compatibility maintenance

## AGENT/LLM INSTRUCTIONS

When working on any P(Doom) repository:

1. **Check related repos** for existing implementations
2. **Maintain ASCII-only** content everywhere
3. **Follow data schemas** defined in pdoom-data
4. **Update integration docs** when making changes
5. **Test cross-repo** functionality

### Navigation Commands
```bash
# Clone all related repositories
git clone https://github.com/PipFoweraker/pdoom-data.git
git clone https://github.com/PipFoweraker/pdoom-website.git  
git clone https://github.com/PipFoweraker/pdoom1.git

# Validate ASCII compliance across all repos
find . -name "*.py" -o -name "*.md" | xargs python validate_ascii.py
```

## DATA FLOW PATTERNS

### From pdoom-data to Website:
1. Historical events updated in pdoom-data
2. JSON exports generated automatically
3. Website pulls new data via API/webhook
4. Event timeline updates displayed

### From pdoom-data to Game:
1. Event modules imported directly
2. Game logic uses helper functions
3. Player interactions tracked
4. Analytics fed back to website

### Cross-Repo Updates:
1. Schema changes in pdoom-data
2. Migration scripts provided
3. Dependent repos updated
4. Version compatibility verified

## COMMON TASKS

### Adding New Historical Event:
1. **In pdoom-data**: Add to appropriate `*_events.py` file
2. **Test locally**: Run `python setup_clean.py`
3. **Commit changes**: Triggers sync to other repos
4. **Update website**: Event appears in timeline
5. **Update game**: Event available in gameplay

### Updating Game Mechanics:
1. **In pdoom-data**: Modify `game_integration_helpers.py`
2. **Update schema**: Increment version if breaking
3. **In pdoom1**: Update integration code
4. **Test compatibility**: Ensure old saves work

### Website Content Updates:
1. **In pdoom-website**: Update display components
2. **Test with real data**: Use pdoom-data JSON exports
3. **Verify mobile**: Responsive design
4. **Update documentation**: Cross-repo impact

## TROUBLESHOOTING

### Integration Issues:
- Check schema versions match
- Validate ASCII compliance
- Test JSON export/import
- Review error logs

### Development Setup:
- Ensure all repos cloned
- Install dependencies in each
- Run validation scripts
- Test cross-repo imports

### Data Synchronization:
- Check webhook endpoints
- Verify API credentials  
- Test automated workflows
- Monitor sync status

## PROJECT CONTACTS

For questions about:
- **Data schemas**: See pdoom-data/docs/
- **Website integration**: See pdoom-website/docs/
- **Game mechanics**: See pdoom1/docs/
- **Cross-repo issues**: Check integration documentation

## VERSION COMPATIBILITY

Current stable versions:
- pdoom-data: v1.0.0
- pdoom-website: (check repo)
- pdoom1: (check repo)

Compatibility matrix and migration guides available in each repository's docs/ folder.

---

**Remember**: This ecosystem is designed for agent-based development. 
Always maintain ASCII-only content and clear documentation for AI assistants.
