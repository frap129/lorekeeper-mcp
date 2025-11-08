# Scaffold Project Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use skills_executing_plans to implement this plan task-by-task.

**Goal:** Bootstrap a production-ready LoreKeeper MCP server project with complete development infrastructure, testing framework, and caching layer.

**Architecture:** Three-layer async architecture: MCP Protocol Layer (FastMCP) → Business Logic Layer (Tools) → Data Layer (SQLite cache + External APIs). Cache-aside pattern with 7-day TTL for game content.

**Tech Stack:** Python 3.13+, FastMCP, aiosqlite, httpx, pytest, ruff, uv package manager

---

## Task 1: Update pyproject.toml with core dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add core production dependencies**

Edit `pyproject.toml` to add the dependencies section:

```toml
[project]
name = "lorekeeper-mcp"
version = "0.1.0"
description = "MCP server for D&D 5e information lookup with AI assistants"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.13"
authors = [
    { name = "LoreKeeper Contributors" }
]
dependencies = [
    "fastmcp>=0.2.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "aiosqlite>=0.19.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.4.0",
    "pre-commit>=3.5.0",
    "respx>=0.21.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "C4", "PIE", "RET", "SIM"]
ignore = []

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 2: Install dependencies**

Run: `uv sync --dev`

Expected: Successfully installs all dependencies and creates/updates `uv.lock`

**Step 3: Verify core imports**

Run: `uv run python -c "import fastmcp, httpx, pydantic, aiosqlite; print('✓ Core imports successful')"`

Expected: Prints "✓ Core imports successful"

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add core dependencies and project metadata"
```

---

## Task 2: Create project directory structure

**Files:**
- Create: `src/lorekeeper_mcp/__init__.py`
- Create: `src/lorekeeper_mcp/tools/__init__.py`
- Create: `src/lorekeeper_mcp/cache/__init__.py`
- Create: `src/lorekeeper_mcp/api_clients/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_cache/__init__.py`
- Create: `data/.gitkeep`
- Modify: `.gitignore`

**Step 1: Create source directory structure**

Run: `mkdir -p src/lorekeeper_mcp/{tools,cache,api_clients}`

Expected: Directories created

**Step 2: Create __init__.py files in source**

Run: `touch src/lorekeeper_mcp/__init__.py src/lorekeeper_mcp/tools/__init__.py src/lorekeeper_mcp/cache/__init__.py src/lorekeeper_mcp/api_clients/__init__.py`

Expected: Files created

**Step 3: Create test directory structure**

Run: `mkdir -p tests/test_cache && touch tests/__init__.py tests/test_cache/__init__.py`

Expected: Directories and files created

**Step 4: Create data directory with .gitkeep**

Run: `mkdir -p data && touch data/.gitkeep`

Expected: Directory created with placeholder file

**Step 5: Update .gitignore**

Append to `.gitignore`:

```
# Data directory (except .gitkeep)
data/*
!data/.gitkeep

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/

# Environment
.env
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

**Step 6: Verify structure**

Run: `ls -R src/lorekeeper_mcp/ tests/`

Expected: Shows all directories with __init__.py files

**Step 7: Commit**

```bash
git add src/ tests/ data/.gitkeep .gitignore
git commit -m "feat: create project directory structure"
```

---

## Task 3: Implement configuration management

**Files:**
- Create: `src/lorekeeper_mcp/config.py`
- Create: `.env.example`

**Step 1: Write test for configuration loading**

Create `tests/test_config.py`:

```python
"""Tests for configuration management."""
import os
from pathlib import Path
import pytest


def test_settings_loads_defaults():
    """Test that settings loads with default values."""
    from lorekeeper_mcp.config import Settings

    settings = Settings()

    assert settings.db_path == Path("./data/cache.db")
    assert settings.cache_ttl_days == 7
    assert settings.log_level == "INFO"
    assert settings.debug is False


def test_settings_respects_env_vars(monkeypatch):
    """Test that environment variables override defaults."""
    from lorekeeper_mcp.config import Settings

    monkeypatch.setenv("DB_PATH", "/tmp/test.db")
    monkeypatch.setenv("CACHE_TTL_DAYS", "3")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DEBUG", "true")

    settings = Settings()

    assert settings.db_path == Path("/tmp/test.db")
    assert settings.cache_ttl_days == 3
    assert settings.log_level == "DEBUG"
    assert settings.debug is True
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.config'"

**Step 3: Implement configuration module**

Create `src/lorekeeper_mcp/config.py`:

```python
"""Configuration management using Pydantic settings."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    db_path: Path = Path("./data/cache.db")

    # Cache configuration
    cache_ttl_days: int = 7
    error_cache_ttl_seconds: int = 300

    # Logging configuration
    log_level: str = "INFO"
    debug: bool = False

    # API configuration
    open5e_base_url: str = "https://api.open5e.com"
    dnd5e_base_url: str = "https://www.dnd5eapi.co/api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py -v`

Expected: PASS (2 tests passed)

**Step 5: Create .env.example**

Create `.env.example`:

```bash
# Database Configuration
# Path to SQLite database file for caching API responses
DB_PATH=./data/cache.db

# Cache Configuration
# Number of days to cache successful API responses
CACHE_TTL_DAYS=7
# Number of seconds to cache error responses (prevents hammering failed endpoints)
ERROR_CACHE_TTL_SECONDS=300

# Logging Configuration
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
# Enable debug mode (more verbose logging)
DEBUG=false

# API Configuration
# Base URLs for external APIs (rarely need to change)
OPEN5E_BASE_URL=https://api.open5e.com
DND5E_BASE_URL=https://www.dnd5eapi.co/api
```

**Step 6: Verify configuration loads**

Run: `uv run python -c "from lorekeeper_mcp.config import settings; print(f'DB Path: {settings.db_path}')"`

Expected: Prints "DB Path: data/cache.db"

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/config.py tests/test_config.py .env.example
git commit -m "feat: implement configuration management with Pydantic settings"
```

---

## Task 4: Implement database cache layer - Part A (Schema)

**Files:**
- Create: `src/lorekeeper_mcp/cache/db.py`

**Step 1: Write test for database initialization**

Create `tests/test_cache/test_db.py`:

```python
"""Tests for database cache layer."""
import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_init_db_creates_schema(tmp_path):
    """Test that init_db creates the database schema."""
    from lorekeeper_mcp.cache.db import init_db
    from lorekeeper_mcp.config import settings
    import aiosqlite

    # Use temporary database
    db_file = tmp_path / "test.db"
    settings.db_path = db_file

    await init_db()

    # Verify database file exists
    assert db_file.exists()

    # Verify schema was created
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='api_cache'"
        )
        result = await cursor.fetchone()
        assert result is not None
        assert result[0] == "api_cache"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_init_db_creates_schema -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.cache.db'"

**Step 3: Implement database initialization**

Create `src/lorekeeper_mcp/cache/db.py`:

```python
"""Database cache layer for API responses using SQLite."""
import json
import time
from pathlib import Path
from typing import Any

import aiosqlite

from lorekeeper_mcp.config import settings


async def init_db() -> None:
    """Initialize the database schema.

    Creates the api_cache table with indexes if it doesn't exist.
    Also ensures the parent directory exists and enables WAL mode.
    """
    # Ensure parent directory exists
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode for better concurrent access
        await db.execute("PRAGMA journal_mode=WAL")

        # Create schema
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                response_data TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                content_type TEXT NOT NULL,
                source_api TEXT NOT NULL
            )
        """)

        # Create indexes
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_expires_at ON api_cache(expires_at)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_content_type ON api_cache(content_type)"
        )

        await db.commit()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_db.py::test_init_db_creates_schema -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_db.py
git commit -m "feat: implement database schema initialization"
```

---

## Task 4: Implement database cache layer - Part B (Read operations)

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py`
- Modify: `tests/test_cache/test_db.py`

**Step 1: Write test for cache retrieval**

Append to `tests/test_cache/test_db.py`:

```python
@pytest.mark.asyncio
async def test_get_cached_returns_none_for_missing_key(tmp_path):
    """Test that get_cached returns None for missing keys."""
    from lorekeeper_mcp.cache.db import init_db, get_cached
    from lorekeeper_mcp.config import settings

    settings.db_path = tmp_path / "test.db"
    await init_db()

    result = await get_cached("nonexistent_key")

    assert result is None


@pytest.mark.asyncio
async def test_get_cached_returns_none_for_expired_entry(tmp_path):
    """Test that get_cached returns None for expired entries."""
    from lorekeeper_mcp.cache.db import init_db, get_cached
    from lorekeeper_mcp.config import settings
    import aiosqlite
    import json
    import time

    settings.db_path = tmp_path / "test.db"
    await init_db()

    # Insert expired entry directly
    async with aiosqlite.connect(settings.db_path) as db:
        now = time.time()
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("test_key", json.dumps({"data": "value"}), now - 100, now - 1, "spell", "test")
        )
        await db.commit()

    result = await get_cached("test_key")

    assert result is None


@pytest.mark.asyncio
async def test_get_cached_returns_valid_entry(tmp_path):
    """Test that get_cached returns valid non-expired entries."""
    from lorekeeper_mcp.cache.db import init_db, get_cached
    from lorekeeper_mcp.config import settings
    import aiosqlite
    import json
    import time

    settings.db_path = tmp_path / "test.db"
    await init_db()

    # Insert valid entry
    test_data = {"spell": "Fireball", "level": 3}
    async with aiosqlite.connect(settings.db_path) as db:
        now = time.time()
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("test_key", json.dumps(test_data), now, now + 3600, "spell", "test")
        )
        await db.commit()

    result = await get_cached("test_key")

    assert result == test_data
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cache/test_db.py -k "get_cached" -v`

Expected: FAIL with "AttributeError: module 'lorekeeper_mcp.cache.db' has no attribute 'get_cached'"

**Step 3: Implement get_cached function**

Append to `src/lorekeeper_mcp/cache/db.py`:

```python
async def get_cached(key: str) -> dict[str, Any] | None:
    """Retrieve cached data if not expired.

    Args:
        key: Cache key to look up

    Returns:
        Cached data as dict if found and not expired, None otherwise
    """
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """SELECT response_data, expires_at
               FROM api_cache
               WHERE cache_key = ?""",
            (key,)
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        # Check if expired
        if row["expires_at"] < time.time():
            return None

        return json.loads(row["response_data"])
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cache/test_db.py -k "get_cached" -v`

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_db.py
git commit -m "feat: implement cache read operations with TTL"
```

---

## Task 4: Implement database cache layer - Part C (Write operations)

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py`
- Modify: `tests/test_cache/test_db.py`

**Step 1: Write test for cache storage**

Append to `tests/test_cache/test_db.py`:

```python
@pytest.mark.asyncio
async def test_set_cached_stores_data(tmp_path):
    """Test that set_cached stores data correctly."""
    from lorekeeper_mcp.cache.db import init_db, set_cached, get_cached
    from lorekeeper_mcp.config import settings

    settings.db_path = tmp_path / "test.db"
    await init_db()

    test_data = {"spell": "Magic Missile", "level": 1}
    await set_cached("spell_123", test_data, "spell", 3600)

    result = await get_cached("spell_123")

    assert result == test_data


@pytest.mark.asyncio
async def test_set_cached_overwrites_existing(tmp_path):
    """Test that set_cached overwrites existing entries."""
    from lorekeeper_mcp.cache.db import init_db, set_cached, get_cached
    from lorekeeper_mcp.config import settings

    settings.db_path = tmp_path / "test.db"
    await init_db()

    # Store initial data
    await set_cached("key", {"version": 1}, "spell", 3600)

    # Overwrite with new data
    await set_cached("key", {"version": 2}, "spell", 3600)

    result = await get_cached("key")

    assert result == {"version": 2}
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cache/test_db.py -k "set_cached" -v`

Expected: FAIL with "AttributeError: module 'lorekeeper_mcp.cache.db' has no attribute 'set_cached'"

**Step 3: Implement set_cached function**

Append to `src/lorekeeper_mcp/cache/db.py`:

```python
async def set_cached(
    key: str,
    data: dict[str, Any],
    content_type: str,
    ttl_seconds: int,
    source_api: str = "unknown"
) -> None:
    """Store data in cache with TTL.

    Args:
        key: Cache key
        data: Data to cache (must be JSON-serializable)
        content_type: Type of content (spell, monster, etc.)
        ttl_seconds: Time to live in seconds
        source_api: Source API name (default: "unknown")
    """
    now = time.time()
    expires_at = now + ttl_seconds

    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            """INSERT OR REPLACE INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (key, json.dumps(data), now, expires_at, content_type, source_api)
        )
        await db.commit()
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cache/test_db.py -k "set_cached" -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_db.py
git commit -m "feat: implement cache write operations"
```

---

## Task 4: Implement database cache layer - Part D (Cleanup operations)

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py`
- Modify: `tests/test_cache/test_db.py`

**Step 1: Write test for cleanup operations**

Append to `tests/test_cache/test_db.py`:

```python
@pytest.mark.asyncio
async def test_cleanup_expired_removes_old_entries(tmp_path):
    """Test that cleanup_expired removes expired entries."""
    from lorekeeper_mcp.cache.db import init_db, cleanup_expired
    from lorekeeper_mcp.config import settings
    import aiosqlite
    import json
    import time

    settings.db_path = tmp_path / "test.db"
    await init_db()

    # Insert expired and valid entries
    async with aiosqlite.connect(settings.db_path) as db:
        now = time.time()
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("expired", json.dumps({"data": 1}), now - 100, now - 1, "spell", "test")
        )
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("valid", json.dumps({"data": 2}), now, now + 3600, "spell", "test")
        )
        await db.commit()

    count = await cleanup_expired()

    assert count == 1

    # Verify expired entry was removed
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM api_cache")
        result = await cursor.fetchone()
        assert result[0] == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py -k "cleanup" -v`

Expected: FAIL with "AttributeError: module 'lorekeeper_mcp.cache.db' has no attribute 'cleanup_expired'"

**Step 3: Implement cleanup_expired function**

Append to `src/lorekeeper_mcp/cache/db.py`:

```python
async def cleanup_expired() -> int:
    """Remove expired cache entries.

    Returns:
        Number of entries deleted
    """
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute(
            "DELETE FROM api_cache WHERE expires_at < ?",
            (time.time(),)
        )
        await db.commit()
        return cursor.rowcount
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_db.py -k "cleanup" -v`

Expected: PASS

**Step 5: Run all cache tests**

Run: `uv run pytest tests/test_cache/ -v`

Expected: All tests pass

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_db.py
git commit -m "feat: implement cache cleanup operations"
```

---

## Task 5: Initialize FastMCP server

**Files:**
- Create: `src/lorekeeper_mcp/server.py`
- Create: `src/lorekeeper_mcp/__main__.py`
- Modify: `src/lorekeeper_mcp/__init__.py`

**Step 1: Write test for server initialization**

Create `tests/test_server.py`:

```python
"""Tests for FastMCP server initialization."""
import pytest


def test_server_instance_exists():
    """Test that server instance is created."""
    from lorekeeper_mcp.server import mcp

    assert mcp is not None
    assert mcp.name == "lorekeeper-mcp"


def test_server_exports_from_package():
    """Test that server is exported from package."""
    from lorekeeper_mcp import mcp

    assert mcp is not None
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_server.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.server'"

**Step 3: Implement server module**

Create `src/lorekeeper_mcp/server.py`:

```python
"""FastMCP server instance and lifecycle management."""
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from lorekeeper_mcp.cache.db import init_db


@asynccontextmanager
async def lifespan(app):
    """Initialize resources on startup, cleanup on shutdown."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Cleanup if needed (currently none)


# Create FastMCP server instance
mcp = FastMCP(
    name="lorekeeper-mcp",
    version="0.1.0",
    description="D&D 5e information server for AI assistants",
    lifespan=lifespan,
)


# Tools will be registered here in future tasks
```

**Step 4: Create __main__ entry point**

Create `src/lorekeeper_mcp/__main__.py`:

```python
"""Main entry point for running the MCP server."""
from lorekeeper_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
```

**Step 5: Export server from package**

Modify `src/lorekeeper_mcp/__init__.py`:

```python
"""LoreKeeper MCP Server - D&D 5e information for AI assistants."""
from lorekeeper_mcp.server import mcp

__all__ = ["mcp"]
```

**Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_server.py -v`

Expected: PASS (2 tests)

**Step 7: Verify server starts**

Run: `timeout 3 uv run python -m lorekeeper_mcp || true`

Expected: Server starts and outputs FastMCP initialization message (timeout kills it after 3 seconds)

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/server.py src/lorekeeper_mcp/__main__.py src/lorekeeper_mcp/__init__.py tests/test_server.py
git commit -m "feat: initialize FastMCP server with lifecycle management"
```

---

## Task 6: Configure pytest with fixtures

**Files:**
- Create: `tests/conftest.py`

**Step 1: Create pytest configuration with fixtures**

Create `tests/conftest.py`:

```python
"""Pytest configuration and fixtures."""
import pytest
from pathlib import Path


@pytest.fixture
async def test_db(tmp_path, monkeypatch):
    """Provide an in-memory database for testing.

    This fixture:
    - Creates a temporary database file
    - Initializes the schema
    - Cleans up settings after test
    """
    from lorekeeper_mcp.cache.db import init_db
    from lorekeeper_mcp.config import settings

    # Use temporary database
    db_file = tmp_path / "test.db"
    original_path = settings.db_path
    monkeypatch.setattr(settings, "db_path", db_file)

    # Initialize database
    await init_db()

    yield db_file

    # Cleanup is automatic (tmp_path is removed by pytest)


@pytest.fixture
def mcp_server():
    """Provide configured MCP server instance for testing."""
    from lorekeeper_mcp.server import mcp

    return mcp
```

**Step 2: Verify fixtures work**

Run: `uv run pytest tests/ -v --collect-only`

Expected: Shows all tests collected successfully with fixtures available

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "feat: configure pytest with database and server fixtures"
```

---

## Task 7: Refactor existing tests to use fixtures

**Files:**
- Modify: `tests/test_cache/test_db.py`
- Modify: `tests/test_server.py`

**Step 1: Refactor cache tests to use fixture**

Replace the beginning of each test in `tests/test_cache/test_db.py` that sets up the database. For example, change:

```python
@pytest.mark.asyncio
async def test_get_cached_returns_none_for_missing_key(tmp_path):
    """Test that get_cached returns None for missing keys."""
    from lorekeeper_mcp.cache.db import init_db, get_cached
    from lorekeeper_mcp.config import settings

    settings.db_path = tmp_path / "test.db"
    await init_db()
```

To:

```python
@pytest.mark.asyncio
async def test_get_cached_returns_none_for_missing_key(test_db):
    """Test that get_cached returns None for missing keys."""
    from lorekeeper_mcp.cache.db import get_cached
```

Apply this pattern to all tests in the file that use `tmp_path` and manually initialize the database.

**Step 2: Update server tests to use fixture**

Modify `tests/test_server.py`:

```python
"""Tests for FastMCP server initialization."""


def test_server_instance_exists(mcp_server):
    """Test that server instance is created."""
    assert mcp_server is not None
    assert mcp_server.name == "lorekeeper-mcp"


def test_server_exports_from_package():
    """Test that server is exported from package."""
    from lorekeeper_mcp import mcp

    assert mcp is not None
```

**Step 3: Run all tests to verify they pass**

Run: `uv run pytest -v`

Expected: All tests pass

**Step 4: Commit**

```bash
git add tests/test_cache/test_db.py tests/test_server.py
git commit -m "refactor: use pytest fixtures for cleaner tests"
```

---

## Task 8: Configure code quality tools

**Files:**
- Create: `.pre-commit-config.yaml`

**Step 1: Create pre-commit configuration**

Create `.pre-commit-config.yaml`:

```yaml
# Pre-commit hooks for code quality
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-toml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      # Run linter
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      # Run formatter
      - id: ruff-format

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true
```

**Step 2: Run ruff check**

Run: `uv run ruff check .`

Expected: No errors (or auto-fixable issues)

**Step 3: Run ruff format check**

Run: `uv run ruff format --check .`

Expected: All files properly formatted

**Step 4: Format code if needed**

Run: `uv run ruff format .`

Expected: Formats any unformatted files

**Step 5: Install pre-commit hooks**

Run: `pre-commit install`

Expected: Pre-commit hooks installed

**Step 6: Test pre-commit hooks**

Run: `pre-commit run --all-files`

Expected: All hooks pass

**Step 7: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "feat: configure pre-commit hooks for code quality"
```

---

## Task 9: Update README with setup instructions

**Files:**
- Modify: `README.md`

**Step 1: Write comprehensive README**

Replace `README.md` content with:

```markdown
# LoreKeeper MCP Server

> D&D 5e information server for AI assistants using the Model Context Protocol

LoreKeeper provides AI assistants with comprehensive access to Dungeons & Dragons 5th Edition game data including spells, monsters, items, classes, and rules. It uses intelligent caching to provide fast responses while respecting external API rate limits.

## Features

- **Comprehensive D&D 5e Data**: Access spells, monsters, items, classes, races, and rules
- **Intelligent Caching**: 7-day cache for game data with automatic cleanup
- **Dual-API Strategy**: Primary Open5e API with D&D 5e API fallback
- **Fast & Async**: Built on FastMCP with async SQLite for non-blocking operations
- **Zero Configuration**: Works out of the box with sensible defaults

## Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd lorekeeper-mcp

# Install dependencies
uv sync

# (Optional) Install pre-commit hooks
pre-commit install
```

## Configuration

LoreKeeper works with zero configuration. For customization, create a `.env` file:

```bash
# Copy example configuration
cp .env.example .env

# Edit as needed
nano .env
```

See `.env.example` for all available configuration options.

## Usage

### Running the Server

```bash
# Start the MCP server
uv run python -m lorekeeper_mcp
```

The server will start and listen for MCP protocol connections.

### Using with AI Assistants

Configure your AI assistant (Claude Desktop, etc.) to connect to this MCP server. Add to your MCP configuration:

```json
{
  "mcpServers": {
    "lorekeeper": {
      "command": "uv",
      "args": ["run", "python", "-m", "lorekeeper_mcp"],
      "cwd": "/path/to/lorekeeper-mcp"
    }
  }
}
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=lorekeeper_mcp

# Run specific test file
uv run pytest tests/test_cache/test_db.py -v
```

### Code Quality

```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Run all pre-commit hooks
pre-commit run --all-files
```

### Project Structure

```
lorekeeper-mcp/
├── src/lorekeeper_mcp/    # Main package
│   ├── server.py          # FastMCP server setup
│   ├── config.py          # Configuration management
│   ├── cache/             # Database caching layer
│   ├── api_clients/       # External API clients
│   └── tools/             # MCP tool implementations
├── tests/                 # Test suite
├── data/                  # SQLite database (gitignored)
└── docs/                  # Detailed specifications
```

## Architecture

LoreKeeper uses a three-layer architecture:

1. **MCP Protocol Layer** - FastMCP framework handles protocol communication
2. **Business Logic Layer** - Tool implementations orchestrate data retrieval
3. **Data Layer** - SQLite cache + external API clients

See [design documentation](openspec/changes/scaffold-project-setup/design.md) for detailed architecture decisions.

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please read our contributing guidelines and code of conduct.

## Support

For issues and questions, please use the GitHub issue tracker.
```

**Step 2: Verify README renders correctly**

Run: `cat README.md`

Expected: Shows complete README content

**Step 3: Verify installation instructions work**

Run: `uv sync && uv run python -c "from lorekeeper_mcp import mcp; print('✓ Installation verified')"`

Expected: Prints "✓ Installation verified"

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive setup and usage instructions"
```

---

## Task 10: Final validation and cleanup

**Step 1: Run full test suite**

Run: `uv run pytest -v`

Expected: All tests pass

**Step 2: Run code quality checks**

Run: `uv run ruff check . && uv run ruff format --check .`

Expected: No errors, all code properly formatted

**Step 3: Verify server starts successfully**

Run: `timeout 3 uv run python -m lorekeeper_mcp || true`

Expected: Server starts without errors (timeout kills it)

**Step 4: Verify cache operations work end-to-end**

Run:
```bash
uv run python -c "
import asyncio
from lorekeeper_mcp.cache.db import init_db, set_cached, get_cached, cleanup_expired

async def test():
    await init_db()
    await set_cached('test', {'data': 'value'}, 'spell', 3600)
    result = await get_cached('test')
    print(f'✓ End-to-end cache test: {result}')
    count = await cleanup_expired()
    print(f'✓ Cleanup removed {count} expired entries')

asyncio.run(test())
"
```

Expected: Prints confirmation messages

**Step 5: Verify all project conventions are followed**

Run: `ls -la src/lorekeeper_mcp/ && cat pyproject.toml | grep -A5 "\\[tool.ruff\\]"`

Expected: Shows proper project structure and ruff configuration

**Step 6: Create final validation script**

Create `scripts/validate.sh`:

```bash
#!/bin/bash
set -e

echo "🔍 Running validation checks..."

echo "✓ Installing dependencies..."
uv sync --quiet

echo "✓ Running linter..."
uv run ruff check .

echo "✓ Checking code formatting..."
uv run ruff format --check .

echo "✓ Running test suite..."
uv run pytest -v

echo "✓ Verifying imports..."
uv run python -c "import fastmcp, httpx, pydantic, aiosqlite; from lorekeeper_mcp import mcp; from lorekeeper_mcp.config import settings; from lorekeeper_mcp.cache.db import init_db"

echo ""
echo "✅ All validation checks passed!"
echo "🚀 Project scaffold is complete and ready for development"
```

Run: `chmod +x scripts/validate.sh`

**Step 7: Run validation script**

Run: `mkdir -p scripts && bash scripts/validate.sh`

Expected: All checks pass

**Step 8: Final commit**

```bash
git add scripts/validate.sh
git commit -m "chore: add validation script for project setup"
```

---

## Success Validation

After completing all tasks, run these commands to verify the scaffold is complete:

```bash
# Full validation
bash scripts/validate.sh

# Or manually:
uv sync                           # Install dependencies
uv run ruff check .               # Lint code
uv run ruff format --check .      # Check formatting
uv run pytest -v                  # Run tests (should have ~10+ passing tests)
uv run python -m lorekeeper_mcp   # Start server (Ctrl+C to stop)
```

All commands should complete successfully with no errors.

## Next Steps

With the scaffold complete, you're ready to implement the core MCP tools:
1. Spell lookup tool
2. Monster/creature lookup tool
3. Character options tool
4. Equipment lookup tool
5. Rules reference tool

See `docs/tools.md` for tool specifications.
