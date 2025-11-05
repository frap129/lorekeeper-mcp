# Project Context

## Purpose
LoreKeeper is an MCP (Model Context Protocol) server designed to fetch information about the Dungeons and Dragons TTRPG. It enables AI assistants to access comprehensive D&D 5e game data for:
- Quick information lookup (spells, items, monsters, classes, etc.)
- Combat encounter building
- Item and spell recommendations
- Rules clarification
- Character building assistance

## Tech Stack
- **Language**: Python
- **Framework**: FastMCP (MCP server framework)
- **Database**: SQLite (local database for caching API responses)
- **Package Manager**: uv
- **Build Tool**: uv
- **Code Formatter**: uv format
- **Linter**: ruff (modern, fast Python linter)
- **Testing Framework**: pytest

## Project Conventions

### Code Style
- Use `uv format` for all code formatting
- Use `ruff` for linting
- Follow PEP 8 naming conventions:
  - `snake_case` for functions, variables, and module names
  - `PascalCase` for class names
  - `UPPER_SNAKE_CASE` for constants
- Use type hints for function signatures
- Docstrings required for all public functions and classes

### Architecture Patterns
- MCP server architecture using FastMCP framework
- SQLite for caching layer to reduce API calls and improve response times
- Dual-API strategy:
  - Primary: Open5e API (comprehensive community-maintained data)
  - Fallback: Official D&D 5e API (for data not available in Open5e, such as rules)
- Cache-aside pattern for database caching

### Testing Strategy
- Unit tests required for all core functionality
- Use pytest as the testing framework
- Test coverage for API integrations (consider mocking external APIs)
- Test database caching logic
- Test MCP tool definitions and handlers

### Git Workflow
- **Branching**: `main` branch with feature branches
- **Feature branches**: `feature/<descriptive-name>`
- **Commit messages**: Clear, descriptive messages following conventional commit style preferred
- No direct commits to `main` - use feature branches and merge

## Domain Context
This project deals with Dungeons & Dragons 5th Edition game data, including:
- **Spells**: Spell details, levels, components, effects
- **Monsters**: Stat blocks, abilities, challenge ratings
- **Items**: Magic items, equipment, weapons, armor
- **Classes**: Character classes, subclasses, features
- **Races**: Character races and racial traits
- **Rules**: Game mechanics, conditions, combat rules
- **Backgrounds**: Character backgrounds and features
- **Feats**: Optional character abilities

Users will primarily be AI assistants helping players and DMs with game information, combat planning, and character building.

## Important Constraints
- **License**: MIT License
- **API Rate Limits**: Open5e and D&D 5e official APIs likely have rate limits (specific limits TBD - implement caching to minimize impact)
- **Data Accuracy**: Must maintain accuracy of game rules and mechanics
- **Database**: Uses local SQLite database for caching (no external database required)

## External Dependencies
- **Open5e API** (https://open5e.com/api): Primary data source for D&D 5e content
- **D&D 5e Official API** (http://www.dnd5eapi.co): Fallback source for missing data (especially rules)
- **SQLite**: Embedded database for caching API responses (no separate installation required)
- **FastMCP**: Framework for building MCP servers
