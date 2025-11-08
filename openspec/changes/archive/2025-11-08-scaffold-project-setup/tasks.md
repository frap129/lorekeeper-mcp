# Tasks: Scaffold Project Setup

## Overview
This document breaks down the scaffold-project-setup change into ordered, verifiable tasks that deliver incremental progress.

## Task List

### 1. Update pyproject.toml with dependencies and metadata
**Priority**: Critical
**Estimated Effort**: 30 minutes
**Dependencies**: None

**Description**: Configure the Python package with all required dependencies, metadata, and tool configurations.

**Acceptance Criteria**:
- [ ] Core dependencies added (fastmcp, httpx, pydantic, aiosqlite, python-dotenv)
- [ ] Dev dependencies added (pytest, pytest-asyncio, ruff, pre-commit, respx)
- [ ] Package metadata complete (name, version, description, license, authors)
- [ ] Tool configurations added (ruff, pytest)
- [ ] `uv sync` successfully installs all dependencies

**Validation**:
```bash
uv sync
uv run python -c "import fastmcp, httpx, pydantic, aiosqlite; print('✓ Core imports successful')"
```

---

### 2. Create project directory structure
**Priority**: Critical
**Estimated Effort**: 15 minutes
**Dependencies**: Task 1

**Description**: Set up the complete source code directory hierarchy with proper __init__.py files.

**Acceptance Criteria**:
- [ ] src/lorekeeper_mcp/ package created with __init__.py
- [ ] Subdirectories created: tools/, cache/, api_clients/
- [ ] Each subdirectory has __init__.py
- [ ] tests/ directory created with subdirectories mirroring src/
- [ ] data/ directory added to .gitignore

**Validation**:
```bash
# Verify structure exists
ls -R src/lorekeeper_mcp/
ls -R tests/
grep "data/" .gitignore
```

---

### 3. Implement configuration management (config.py)
**Priority**: Critical
**Estimated Effort**: 45 minutes
**Dependencies**: Task 2

**Description**: Create centralized configuration using pydantic-settings with environment variable support.

**Acceptance Criteria**:
- [ ] config.py created with Settings class using pydantic BaseSettings
- [ ] Configuration fields defined (DB_PATH, CACHE_TTL_DAYS, LOG_LEVEL, DEBUG)
- [ ] Default values provide working development configuration
- [ ] .env.example created documenting all configuration options
- [ ] Can load from environment variables or .env file

**Validation**:
```bash
uv run python -c "from lorekeeper_mcp.config import settings; print(f'DB Path: {settings.db_path}')"
```

---

### 4. Implement database cache layer (cache/db.py)
**Priority**: Critical
**Estimated Effort**: 90 minutes
**Dependencies**: Task 3

**Description**: Create async SQLite database operations for API response caching.

**Acceptance Criteria**:
- [ ] cache/db.py implements async database operations
- [ ] Schema initialization function creates api_cache table with indexes
- [ ] Functions: init_db(), get_cached(), set_cached(), cleanup_expired()
- [ ] All operations use async/await with aiosqlite
- [ ] Database file path uses configuration
- [ ] Parent directories created automatically if missing

**Validation**:
```bash
uv run python -c "
import asyncio
from lorekeeper_mcp.cache.db import init_db, set_cached, get_cached

async def test():
    await init_db()
    await set_cached('test_key', {'data': 'value'}, 'spell', 3600)
    result = await get_cached('test_key')
    print(f'✓ Cache works: {result}')

asyncio.run(test())
"
```

---

### 5. Initialize FastMCP server (server.py, __main__.py)
**Priority**: Critical
**Estimated Effort**: 45 minutes
**Dependencies**: Task 4

**Description**: Create the FastMCP server instance and CLI entry point.

**Acceptance Criteria**:
- [ ] server.py creates FastMCP instance with name and version
- [ ] Server configured with appropriate settings
- [ ] __main__.py provides entry point that starts server
- [ ] __init__.py exports server instance for import
- [ ] Server starts successfully and responds to MCP protocol

**Validation**:
```bash
# Start server (Ctrl+C to stop)
uv run python -m lorekeeper_mcp

# In another terminal, verify it's responding (if MCP client available)
# Or just check it starts without errors
```

---

### 6. Configure pytest with fixtures (tests/conftest.py)
**Priority**: High
**Estimated Effort**: 60 minutes
**Dependencies**: Task 5

**Description**: Set up pytest configuration and common test fixtures.

**Acceptance Criteria**:
- [ ] conftest.py created with test fixtures
- [ ] test_db fixture provides in-memory SQLite database
- [ ] mcp_server fixture provides configured server instance
- [ ] Fixtures properly handle async setup/teardown
- [ ] pytest configuration in pyproject.toml enables async tests

**Validation**:
```bash
# Run pytest (will pass even with no tests)
uv run pytest -v
```

---

### 7. Write basic smoke tests
**Priority**: High
**Estimated Effort**: 45 minutes
**Dependencies**: Task 6

**Description**: Create initial tests to verify core functionality works.

**Acceptance Criteria**:
- [ ] tests/test_config.py tests configuration loading
- [ ] tests/test_cache/test_db.py tests database operations
- [ ] tests/test_server.py tests server initialization
- [ ] All tests pass
- [ ] Tests verify async operations work correctly

**Validation**:
```bash
uv run pytest -v
# Should show passing tests for config, cache, and server
```

---

### 8. Configure code quality tools (ruff, pre-commit)
**Priority**: High
**Estimated Effort**: 30 minutes
**Dependencies**: Task 7

**Description**: Set up linting, formatting, and pre-commit hooks.

**Acceptance Criteria**:
- [ ] ruff configuration in pyproject.toml follows project conventions
- [ ] .pre-commit-config.yaml created with ruff and basic hooks
- [ ] pre-commit hooks can be installed
- [ ] Running ruff check passes on all code
- [ ] Running ruff format checks code is properly formatted

**Validation**:
```bash
uv run ruff check .
uv run ruff format --check .
pre-commit install
pre-commit run --all-files
```

---

### 9. Update README.md with setup instructions
**Priority**: Medium
**Estimated Effort**: 30 minutes
**Dependencies**: Task 8

**Description**: Document how to set up and run the project.

**Acceptance Criteria**:
- [ ] README describes project purpose
- [ ] Installation instructions using uv
- [ ] Environment configuration documented
- [ ] How to run server documented
- [ ] How to run tests documented
- [ ] Links to docs/ for detailed specifications

**Validation**:
```bash
# Follow README instructions from scratch to verify they work
```

---

### 10. Create .env.example with all configuration options
**Priority**: Medium
**Estimated Effort**: 15 minutes
**Dependencies**: Task 3

**Description**: Provide example environment configuration file.

**Acceptance Criteria**:
- [ ] .env.example created
- [ ] All configuration options documented
- [ ] Default values shown
- [ ] Comments explain each option

**Validation**:
```bash
cat .env.example
# Should show all config options with comments
```

---

## Task Sequence

### Critical Path (Must complete in order)
1. Update pyproject.toml (Task 1)
2. Create directory structure (Task 2)
3. Implement configuration (Task 3)
4. Implement database cache (Task 4)
5. Initialize FastMCP server (Task 5)

### Parallel Work (Can be done concurrently after Task 5)
- Configure pytest and fixtures (Task 6)
- Configure code quality tools (Task 8)
- Create .env.example (Task 10)

### Final Tasks (Complete last)
- Write smoke tests (Task 7) - After Task 6
- Update README (Task 9) - After everything else

## Estimated Total Effort
**6.5 hours** for complete scaffold setup

## Success Validation

After completing all tasks, the following commands should succeed:

```bash
# Install dependencies
uv sync

# Run linter
uv run ruff check .

# Check formatting
uv run ruff format --check .

# Run tests
uv run pytest -v

# Start server (Ctrl+C to stop)
uv run python -m lorekeeper_mcp
```

All commands should complete successfully with no errors.
