"""Test live testing fixtures."""

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_live_db_creates_temp_database(live_db, tmp_path):
    """Verify live_db fixture creates isolated test database."""
    # live_db should return a path to a temporary database
    assert live_db is not None
    db_path = Path(live_db)
    assert db_path.exists()
    assert "test" in str(db_path).lower() or str(db_path).startswith("/tmp")


@pytest.mark.asyncio
async def test_rate_limiter_tracks_calls(rate_limiter):
    """Verify rate_limiter fixture enforces delays between calls."""
    import time

    # First call should complete immediately
    start = time.time()
    await rate_limiter("test_api")
    first_duration = time.time() - start
    assert first_duration < 0.05  # Should be near instant

    # Second call should enforce minimum delay
    start = time.time()
    await rate_limiter("test_api", min_delay=0.1)
    second_duration = time.time() - start
    assert second_duration >= 0.1  # Should respect min_delay


@pytest.mark.asyncio
async def test_rate_limiter_separate_per_api(rate_limiter):
    """Verify rate_limiter tracks separate APIs independently."""
    import time

    # Call first API
    await rate_limiter("api1", min_delay=0.1)

    # Call second API - should not be delayed
    start = time.time()
    await rate_limiter("api2", min_delay=0.1)
    duration = time.time() - start
    assert duration < 0.05  # Should not enforce delay for different API


@pytest.mark.asyncio
async def test_cache_stats_fixture_provided(cache_stats):
    """Verify cache_stats fixture provides stats tracker."""
    assert cache_stats is not None
    assert hasattr(cache_stats, "hits")
    assert hasattr(cache_stats, "misses")
    assert hasattr(cache_stats, "queries")
    assert cache_stats.hits == 0
    assert cache_stats.misses == 0
    assert len(cache_stats.queries) == 0


@pytest.mark.asyncio
async def test_cache_stats_record_hit(cache_stats):
    """Verify cache_stats can record hits."""
    query = {"name": "test"}
    cache_stats.record_hit(query)

    assert cache_stats.hits == 1
    assert cache_stats.misses == 0
    assert len(cache_stats.queries) == 1
    assert cache_stats.queries[0]["type"] == "hit"
    assert cache_stats.queries[0]["query"] == query


@pytest.mark.asyncio
async def test_cache_stats_record_miss(cache_stats):
    """Verify cache_stats can record misses."""
    query = {"name": "test"}
    cache_stats.record_miss(query)

    assert cache_stats.hits == 0
    assert cache_stats.misses == 1
    assert len(cache_stats.queries) == 1
    assert cache_stats.queries[0]["type"] == "miss"


@pytest.mark.asyncio
async def test_cache_stats_reset(cache_stats):
    """Verify cache_stats can be reset."""
    cache_stats.record_hit({"test": "query"})
    cache_stats.record_miss({"test": "query"})

    assert cache_stats.hits == 1
    assert cache_stats.misses == 1

    cache_stats.reset()

    assert cache_stats.hits == 0
    assert cache_stats.misses == 0
    assert len(cache_stats.queries) == 0


@pytest.mark.asyncio
async def test_clear_cache_fixture_works(clear_cache, live_db):
    """Verify clear_cache fixture clears cache before tests."""
    # This test just verifies the fixture works without errors
    # The actual clearing is tested in integration tests
    assert clear_cache is None  # Fixture is a context manager
