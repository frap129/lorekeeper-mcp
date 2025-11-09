"""Test that make_request works without cache parameters (Task 2.10)."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.base import BaseHttpClient


@pytest.fixture
def base_client() -> BaseHttpClient:
    """Create a BaseHttpClient instance for testing."""
    return BaseHttpClient(base_url="https://api.example.com", timeout=5.0)


@respx.mock
async def test_make_request_no_cache_parameters(base_client: BaseHttpClient) -> None:
    """Test that make_request doesn't accept cache parameters."""
    mock_route = respx.get("https://api.example.com/test").mock(
        return_value=httpx.Response(200, json={"data": "success"})
    )

    # This should work WITHOUT cache parameters
    response = await base_client.make_request("/test")

    assert response == {"data": "success"}
    assert mock_route.called


@respx.mock
async def test_make_request_simple_signature(base_client: BaseHttpClient) -> None:
    """Test that make_request has a simple signature."""
    mock_route = respx.post("https://api.example.com/create").mock(
        return_value=httpx.Response(201, json={"id": 123})
    )

    # make_request should accept: endpoint, method, **kwargs (for httpx params)
    response = await base_client.make_request("/create", method="POST", json={"name": "test"})

    assert response == {"id": 123}
    assert mock_route.called


async def test_no_cache_methods_in_client(base_client: BaseHttpClient) -> None:
    """Test that cache-related private methods don't exist."""
    # These methods should not exist on the client:
    assert not hasattr(base_client, "_query_cache_parallel")
    assert not hasattr(base_client, "_cache_api_entities")
    assert not hasattr(base_client, "_extract_entities")
    assert not hasattr(base_client, "_get_cached_response")
    assert not hasattr(base_client, "_cache_response")
