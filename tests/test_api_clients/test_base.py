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
from lorekeeper_mcp.cache.db import get_cached, get_cached_entity, set_cached
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
