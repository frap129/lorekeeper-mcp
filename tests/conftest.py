"""Pytest configuration and fixtures for lorekeeper-mcp testing."""

import asyncio
import time
from collections.abc import AsyncGenerator, Generator
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


# Module-scoped cache container to avoid reloading embedding model for each test
_live_db_state: dict[str, Any] = {"cache": None, "path": None}


@pytest.fixture(scope="module")
def live_db(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[MilvusCache, None, None]:
    """Provide isolated test Milvus cache for live tests.

    Module-scoped to avoid reloading the embedding model for each test.
    Pre-warms the embedding model during fixture setup to avoid delays
    during test execution (HuggingFace model loading can take 30+ seconds).
    """
    if _live_db_state["cache"] is None:
        db_path = tmp_path_factory.mktemp("live_tests") / "test_live_cache.db"
        _live_db_state["path"] = db_path
        cache = MilvusCache(str(db_path))
        _live_db_state["cache"] = cache

        # Pre-warm the embedding model by generating a dummy embedding
        # This loads the model from HuggingFace once during fixture setup
        # instead of during the first test that tries to store data
        cache._embedding_service.encode("warmup")  # type: ignore[attr-defined]

    yield _live_db_state["cache"]

    # Cleanup happens at module end (handled by pytest)


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
    """Clear cache before test execution and inject test cache into tools.

    This fixture ensures that live tests use the fresh temporary database
    instead of the global cache, which may be corrupted or cause hangs.
    """
    from lorekeeper_mcp.repositories.factory import RepositoryFactory
    from lorekeeper_mcp.tools.search_character_option import (
        _repository_context as char_option_ctx,
    )
    from lorekeeper_mcp.tools.search_creature import _repository_context as creature_ctx
    from lorekeeper_mcp.tools.search_equipment import _repository_context as equipment_ctx
    from lorekeeper_mcp.tools.search_rule import _repository_context as rule_ctx

    # Import _repository_context from each tool module
    from lorekeeper_mcp.tools.search_spell import _repository_context as spell_ctx

    # Create repositories with the test cache
    spell_repo = RepositoryFactory.create_spell_repository(cache=live_db)
    creature_repo = RepositoryFactory.create_creature_repository(cache=live_db)
    equipment_repo = RepositoryFactory.create_equipment_repository(cache=live_db)
    rule_repo = RepositoryFactory.create_rule_repository(cache=live_db)
    char_option_repo = RepositoryFactory.create_character_option_repository(cache=live_db)

    # Inject repositories into tool modules for testing
    spell_ctx["repository"] = spell_repo
    creature_ctx["repository"] = creature_repo
    equipment_ctx["repository"] = equipment_repo
    rule_ctx["repository"] = rule_repo
    char_option_ctx["repository"] = char_option_repo

    yield

    # Cleanup - clear repository contexts
    spell_ctx.clear()
    creature_ctx.clear()
    equipment_ctx.clear()
    rule_ctx.clear()
    char_option_ctx.clear()
