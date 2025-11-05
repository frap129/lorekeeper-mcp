"""Tests for BaseHttpClient."""

from typing import Any

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.cache.db import get_cached, set_cached


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
async def base_client_with_cache(test_db: Any) -> BaseHttpClient:
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
