"""Pytest configuration and fixtures for lorekeeper-mcp testing."""

import asyncio
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest

from lorekeeper_mcp.cache.db import init_db
from lorekeeper_mcp.config import settings
from lorekeeper_mcp.server import mcp


@pytest.fixture
async def test_db(tmp_path, monkeypatch):
    """Provide a temporary database for testing.

    This fixture:
    - Creates a temporary database file
    - Initializes the schema
    - Uses monkeypatch to modify settings.db_path
    - Cleans up after the test
    """
    # Create temporary database file
    db_file = tmp_path / "test_cache.db"

    # Patch settings to use temporary database
    monkeypatch.setattr(settings, "db_path", db_file)

    # Initialize database schema
    await init_db()

    yield db_file


@pytest.fixture
def mcp_server():
    """Provide a configured MCP server instance for testing.

    Returns the mcp instance from lorekeeper_mcp.server.
    """
    return mcp


@pytest.fixture
async def live_db(tmp_path: Path, monkeypatch) -> AsyncGenerator[str]:
    """
    Provide isolated test database for live tests.

    Creates temporary database, yields path, cleans up after test.
    """
    db_file = tmp_path / "test_live_cache.db"

    # Patch settings to use temporary database
    monkeypatch.setattr(settings, "db_path", str(db_file))

    # Initialize test database
    await init_db()

    yield str(db_file)

    # Cleanup handled by tmp_path fixture


@pytest.fixture
def rate_limiter():
    """
    Enforce rate limiting between API calls to prevent throttling.

    Tracks last call time per API and enforces minimum delay.
    """
    last_call: dict[str, float] = {}

    async def wait_if_needed(api_name: str = "default", min_delay: float = 0.1) -> None:
        """Wait if needed to respect rate limits."""
        if api_name in last_call:
            elapsed = time.time() - last_call[api_name]
            if elapsed < min_delay:
                await asyncio.sleep(min_delay - elapsed)
        last_call[api_name] = time.time()

    return wait_if_needed


class CacheStats:
    """Track cache hit/miss statistics for validation."""

    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0
        self.queries: list[dict[str, Any]] = []

    def record_hit(self, query: dict[str, Any]) -> None:
        """Record cache hit."""
        self.hits += 1
        self.queries.append({"type": "hit", "query": query})

    def record_miss(self, query: dict[str, Any]) -> None:
        """Record cache miss."""
        self.misses += 1
        self.queries.append({"type": "miss", "query": query})

    def reset(self) -> None:
        """Reset statistics."""
        self.hits = 0
        self.misses = 0
        self.queries = []


@pytest.fixture
def cache_stats() -> CacheStats:
    """Provide cache statistics tracker for tests."""
    return CacheStats()


@pytest.fixture
async def clear_cache(live_db: str) -> AsyncGenerator[None]:
    """Clear cache before test execution."""
    from lorekeeper_mcp.cache.db import cleanup_expired
    from lorekeeper_mcp.tools.creature_lookup import clear_creature_cache
    from lorekeeper_mcp.tools.spell_lookup import clear_spell_cache

    # Clear in-memory caches
    clear_spell_cache()
    clear_creature_cache()

    # Clean up any expired entries
    await cleanup_expired()
    yield
    # Cache will be cleared with temp database
