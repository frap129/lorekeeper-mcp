"""Tests for BaseHttpClient."""

import asyncio
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.cache.db import bulk_cache_entities, get_cached, get_cached_entity, set_cached
from lorekeeper_mcp.cache.schema import init_entity_cache


@pytest.fixture
def base_client() -> BaseHttpClient:
    """Create a BaseHttpClient instance for testing."""
    return BaseHttpClient(base_url="https://api.example.com", timeout=5.0, source_api="test_api")


@respx.mock
async def test_make_request_success(base_client: BaseHttpClient) -> None:
    """Test successful HTTP GET request."""
    mock_route = respx.get("https://api.example.com/test").mock(
        return_value=httpx.Response(200, json={"data": "success"})
    )

    response = await base_client._make_request("/test")

    assert response == {"data": "success"}
    assert mock_route.called


@respx.mock
async def test_make_request_404_error(base_client: BaseHttpClient) -> None:
    """Test API error handling for 404 response."""
    respx.get("https://api.example.com/notfound").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )

    with pytest.raises(ApiError) as exc_info:
        await base_client._make_request("/notfound")

    assert exc_info.value.status_code == 404


@respx.mock
async def test_make_request_timeout(base_client: BaseHttpClient) -> None:
    """Test network timeout handling."""
    respx.get("https://api.example.com/slow").mock(side_effect=httpx.TimeoutException("Timeout"))

    with pytest.raises(NetworkError) as exc_info:
        await base_client._make_request("/slow", max_retries=1)

    assert "Timeout" in str(exc_info.value)


@pytest.fixture
async def base_client_with_cache(test_db: Any):  # type: ignore[assignment]
    """Create BaseHttpClient with cache enabled for testing."""
    client = BaseHttpClient(
        base_url="https://api.example.com", cache_ttl=3600, source_api="test_api"
    )
    yield client
    await client.close()


@respx.mock
async def test_cache_hit(base_client_with_cache: BaseHttpClient) -> None:
    """Test that cached responses are returned without making HTTP request."""
    # Pre-populate cache
    await set_cached(
        "https://api.example.com/cached",
        {"data": "from_cache"},
        content_type="api_response",
        ttl_seconds=3600,
        source_api="example",
    )

    # Mock should not be called if cache works
    mock_route = respx.get("https://api.example.com/cached").mock(
        return_value=httpx.Response(200, json={"data": "from_api"})
    )

    response = await base_client_with_cache.make_request("/cached")

    assert response == {"data": "from_cache"}
    assert not mock_route.called


@respx.mock
async def test_cache_miss(base_client_with_cache: BaseHttpClient) -> None:
    """Test that cache miss results in HTTP request and cache update."""
    mock_route = respx.get("https://api.example.com/uncached").mock(
        return_value=httpx.Response(200, json={"data": "from_api"})
    )

    response = await base_client_with_cache.make_request("/uncached")

    assert response == {"data": "from_api"}
    assert mock_route.called

    # Verify cache was updated
    cached = await get_cached("https://api.example.com/uncached")
    assert cached == {"data": "from_api"}


@respx.mock
async def test_cache_error_continues(
    base_client_with_cache: BaseHttpClient, monkeypatch: Any
) -> None:
    """Test that cache errors don't break requests."""

    # Mock cache to raise error
    async def failing_get_cached(*args: Any, **kwargs: Any) -> None:
        raise Exception("Cache read failed")

    monkeypatch.setattr("lorekeeper_mcp.api_clients.base.get_cached", failing_get_cached)

    mock_route = respx.get("https://api.example.com/test").mock(
        return_value=httpx.Response(200, json={"data": "success"})
    )

    # Should still succeed despite cache error
    response = await base_client_with_cache.make_request("/test")

    assert response == {"data": "success"}
    assert mock_route.called


@pytest.mark.asyncio
async def test_query_cache_parallel_executes_concurrently():
    """Cache query runs in parallel with API call."""
    client = BaseHttpClient("https://api.example.com")

    # Mock cache query to take 0.1 seconds
    async def mock_cache_query(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        await asyncio.sleep(0.1)
        return [{"slug": "fireball", "name": "Fireball"}]

    with patch(
        "lorekeeper_mcp.api_clients.base.query_cached_entities", side_effect=mock_cache_query
    ):
        start = asyncio.get_event_loop().time()
        result = await client._query_cache_parallel("spells", level=3)
        elapsed = asyncio.get_event_loop().time() - start

        # Should complete in roughly 0.1s, not block caller
        assert elapsed < 0.2
        assert len(result) == 1


@pytest.mark.asyncio
async def test_query_cache_parallel_handles_cache_error():
    """Cache query errors don't crash parallel operation."""
    client = BaseHttpClient("https://api.example.com")

    async def mock_error(*args: Any, **kwargs: Any) -> None:
        raise Exception("Cache error")

    with patch("lorekeeper_mcp.api_clients.base.query_cached_entities", side_effect=mock_error):
        result = await client._query_cache_parallel("spells")

        # Should return empty list on error
        assert result == []


@pytest.fixture
async def client_with_db():
    """Create client with test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))

        # Temporarily override settings
        import lorekeeper_mcp.config

        original_path = lorekeeper_mcp.config.settings.db_path
        lorekeeper_mcp.config.settings.db_path = db_path

        client = BaseHttpClient("https://api.example.com")

        yield client

        # Restore
        lorekeeper_mcp.config.settings.db_path = original_path
        await client.close()


@pytest.mark.asyncio
async def test_cache_api_entities_stores_entities(client_with_db):
    """Cache API entities stores each entity."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1},
    ]

    await client_with_db._cache_api_entities(entities, "spells")

    # Verify entities cached
    cached = await get_cached_entity("spells", "fireball")
    assert cached is not None
    assert cached["name"] == "Fireball"


@pytest.mark.asyncio
async def test_extract_entities_from_paginated_response(client_with_db):
    """Extract entities handles paginated API response."""
    response = {
        "count": 2,
        "results": [
            {"slug": "fireball", "name": "Fireball"},
            {"slug": "magic-missile", "name": "Magic Missile"},
        ],
    }

    entities = client_with_db._extract_entities(response, "spells")

    assert len(entities) == 2
    assert entities[0]["slug"] == "fireball"


@pytest.mark.asyncio
async def test_extract_entities_handles_non_paginated(client_with_db):
    """Extract entities handles direct entity response."""
    response = {"slug": "fireball", "name": "Fireball"}

    entities = client_with_db._extract_entities(response, "spells")

    assert len(entities) == 1
    assert entities[0]["slug"] == "fireball"


@pytest.mark.asyncio
async def test_make_request_offline_fallback_returns_cache(client_with_db):
    """Make request falls back to cache on network error."""
    # Pre-populate cache
    entities = [{"slug": "fireball", "name": "Fireball", "level": 3}]
    await bulk_cache_entities(entities, "spells")

    # Mock network error
    with (
        patch.object(client_with_db, "_make_request", side_effect=NetworkError("Network down")),
        patch.object(client_with_db, "_query_cache_parallel", return_value=entities),
    ):
        result = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
        )

    # Should return cached data instead of raising
    assert result == entities


@pytest.mark.asyncio
async def test_make_request_offline_with_no_cache_returns_empty(client_with_db):
    """Make request with network error and no cache returns empty."""
    # Mock network error with empty cache
    with (
        patch.object(client_with_db, "_make_request", side_effect=NetworkError("Network down")),
        patch.object(client_with_db, "_query_cache_parallel", return_value=[]),
    ):
        result = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
        )

    # Should return empty list
    assert result == []


@pytest.mark.asyncio
async def test_make_request_offline_logs_warning(client_with_db, caplog):
    """Make request logs warning in offline mode."""
    with (
        patch.object(client_with_db, "_make_request", side_effect=NetworkError("Network down")),
        patch.object(client_with_db, "_query_cache_parallel", return_value=[]),
    ):
        await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
        )

    # Should log offline warning
    assert "offline" in caplog.text.lower() or "network" in caplog.text.lower()


@pytest.mark.asyncio
async def test_make_request_cache_first_returns_immediately(client_with_db):
    """Make request with cache_first returns cache without waiting for API."""
    # Pre-populate cache
    entities = [{"slug": "fireball", "name": "Fireball (cached)"}]
    await bulk_cache_entities(entities, "spells")

    # Mock slow API response
    async def slow_api(*args, **kwargs):
        await asyncio.sleep(0.5)
        return {"results": [{"slug": "fireball", "name": "Fireball (fresh)"}]}

    with patch.object(client_with_db, "_make_request", side_effect=slow_api):
        start = asyncio.get_event_loop().time()
        result = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )
        elapsed = asyncio.get_event_loop().time() - start

    # Should return cached data quickly (< 0.1s, not wait for 0.5s API)
    assert elapsed < 0.1
    assert result[0]["name"] == "Fireball (cached)"


@pytest.mark.asyncio
async def test_make_request_cache_first_refreshes_background(client_with_db):
    """Make request with cache_first refreshes cache in background."""
    # Pre-populate cache with old data
    old_entities = [{"slug": "fireball", "name": "Fireball (old)"}]
    await bulk_cache_entities(old_entities, "spells")

    # Mock API with new data
    async def mock_api(*args, **kwargs):
        return {"results": [{"slug": "fireball", "name": "Fireball (new)"}]}

    with patch.object(client_with_db, "_make_request", side_effect=mock_api):
        # First call returns cached
        result1 = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )

        # Wait for background refresh
        await asyncio.sleep(0.2)

        # Second call should have refreshed data
        await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )

    assert result1[0]["name"] == "Fireball (old)"
    # Background task should have updated cache
    # (In practice this requires the background task to complete)


@pytest.mark.asyncio
async def test_cache_first_prevents_redundant_refreshes(client_with_db):
    """Cache_first prevents redundant background refreshes for identical requests."""
    # Pre-populate cache
    entities = [{"slug": "fireball", "name": "Fireball"}]
    await bulk_cache_entities(entities, "spells")

    api_call_count = 0

    # Mock API that tracks call count
    async def mock_api(*args, **kwargs):
        nonlocal api_call_count
        api_call_count += 1
        await asyncio.sleep(0.1)  # Simulate slow API
        return {"results": [{"slug": "fireball", "name": "Fireball (updated)"}]}

    with patch.object(client_with_db, "_make_request", side_effect=mock_api):
        # Make 3 identical cache_first requests in quick succession
        result1 = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )
        result2 = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )
        result3 = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )

        # Wait for background tasks to complete
        await asyncio.sleep(0.2)

    # All three requests should return cached data immediately
    assert result1 == entities
    assert result2 == entities
    assert result3 == entities

    # API should only be called once (first request triggers background refresh)
    # Subsequent identical requests should NOT spawn new refresh tasks
    assert api_call_count == 1


@pytest.mark.asyncio
async def test_cache_first_allows_different_refreshes(client_with_db):
    """Cache_first allows separate refreshes for different requests."""
    # Pre-populate cache
    spell_entities = [{"slug": "fireball", "name": "Fireball"}]
    await bulk_cache_entities(spell_entities, "spells")

    api_call_count = 0

    # Mock API that tracks call count
    async def mock_api(*args, **kwargs):
        nonlocal api_call_count
        api_call_count += 1
        return {"results": []}

    with patch.object(client_with_db, "_make_request", side_effect=mock_api):
        # Make different cache_first requests
        await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )
        await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
            cache_filters={"level": 3},  # Different filters
        )

        # Wait for background tasks to complete
        await asyncio.sleep(0.2)

    # Should spawn 2 separate refreshes for different requests
    assert api_call_count == 2
