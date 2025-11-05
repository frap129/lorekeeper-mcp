# Proposal: Scaffold Project Setup

## Overview
Initialize the LoreKeeper MCP server project with the complete development infrastructure, dependencies, and project structure required to build a production-ready D&D 5e information service.

## Problem Statement
The repository currently lacks the fundamental project setup needed to develop, test, and deploy an MCP server. Without proper scaffolding including:
- Python dependency management and packaging configuration
- Database connectivity and caching infrastructure
- MCP server framework integration
- Testing and code quality tooling

developers cannot efficiently build the five core tools (spell lookup, creature lookup, character options, equipment, and rules) specified in the tools documentation.

## Proposed Solution
Set up a complete Python project foundation using modern best practices:

1. **Development Environment**: Configure `uv` as package manager with FastMCP framework and async HTTP/database libraries
2. **Database Integration**: Set up SQLite connectivity using aiosqlite for async database operations in the caching layer
3. **Project Structure**: Organize code into logical modules (server, tools, cache, api_clients) with proper configuration management
4. **Testing Infrastructure**: Configure pytest with async support and database fixtures
5. **Code Quality**: Integrate ruff for linting and uv format for code formatting

## Benefits
- **Developer Velocity**: Immediate development start with all tooling in place
- **Best Practices**: Modern Python tooling (uv, ruff, pytest) following project conventions
- **Production Ready**: Async-first architecture with connection pooling and proper error handling
- **Maintainability**: Clear project structure and comprehensive testing foundation

## Scope
**In Scope:**
- Python package configuration (pyproject.toml with all dependencies)
- Core project structure (directories, __init__.py files)
- Database connection setup (SQLite with aiosqlite)
- FastMCP server initialization
- Testing framework configuration (pytest with async support)
- Code quality tooling (ruff, pre-commit hooks)
- Basic configuration management (environment variables, settings)

**Out of Scope:**
- Implementation of the 5 MCP tools (separate change)
- API client implementations for Open5e and D&D 5e APIs
- Database schema design and migrations
- Deployment configuration (Docker, CI/CD)
- Authentication/authorization

## Dependencies
- Python 3.13+ (specified in .python-version)
- uv package manager installed
- No external database required (SQLite is embedded)

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| FastMCP API changes | Pin to specific version, monitor for updates |
| SQLite concurrent access | Use connection pooling and proper locking, accept read-heavy workload |
| Async complexity | Provide clear examples and documentation for async patterns |

## Success Criteria
- [ ] `uv sync` successfully installs all dependencies
- [ ] `pytest` runs (even with no tests initially)
- [ ] `ruff check .` passes with no errors
- [ ] `uv run python -m lorekeeper_mcp` starts the MCP server
- [ ] Database connection can be established
- [ ] All project conventions from project.md are followed

## Related Changes
None (foundational change)

## Validation
```bash
# Verify dependencies install
uv sync

# Verify code quality
ruff check .
uv format --check .

# Verify tests run
pytest

# Verify server starts
uv run python -m lorekeeper_mcp
```
