"""Pytest configuration and fixtures for lorekeeper-mcp testing."""

import asyncio
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest

from lorekeeper_mcp.cache.milvus import MilvusCache
from lorekeeper_mcp.server import mcp


@pytest.fixture
async def test_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncGenerator[MilvusCache, None]:
    """Provide a temporary Milvus cache for testing.

    This fixture:
    - Creates a temporary database file
    - Provides a MilvusCache instance
    - Cleans up after the test
    """
    # Create temporary database file
    db_file = tmp_path / "test_cache.db"
    cache = MilvusCache(str(db_file))

    yield cache

    cache.close()


@pytest.fixture
def mcp_server():
    """Provide a configured MCP server instance for testing.

    Returns the mcp instance from lorekeeper_mcp.server.
    """
    return mcp


@pytest.fixture
async def live_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncGenerator[MilvusCache, None]:
    """Provide isolated test Milvus cache for live tests.

    Creates temporary database, yields cache instance, cleans up after test.
    """
    db_file = tmp_path / "test_live_cache.db"
    cache = MilvusCache(str(db_file))

    yield cache

    cache.close()


@pytest.fixture
def rate_limiter():
    """Enforce rate limiting between API calls to prevent throttling.

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
async def clear_cache(live_db: MilvusCache) -> AsyncGenerator[None, None]:
    """Clear cache before test execution."""
    # MilvusCache doesn't have in-memory clear functions
    # The test database is already fresh due to tmp_path fixture
    yield
    # Cache will be cleared with temp database
