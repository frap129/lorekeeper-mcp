"""Tests for BaseHttpClient.

Note: Entity cache tests have been removed. Caching is now handled by the
repository layer using the cache-aside pattern. BaseHttpClient is responsible
for HTTP communication only.
"""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError


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

    response = await base_client.make_request("/test")

    assert response == {"data": "success"}
    assert mock_route.called


@respx.mock
async def test_make_request_404_error(base_client: BaseHttpClient) -> None:
    """Test API error handling for 404 response."""
    respx.get("https://api.example.com/notfound").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )

    with pytest.raises(ApiError) as exc_info:
        await base_client.make_request("/notfound")

    assert exc_info.value.status_code == 404


@respx.mock
async def test_make_request_timeout(base_client: BaseHttpClient) -> None:
    """Test network timeout handling."""
    respx.get("https://api.example.com/slow").mock(side_effect=httpx.TimeoutException("Timeout"))

    with pytest.raises(NetworkError) as exc_info:
        await base_client.make_request("/slow")

    assert "Timeout" in str(exc_info.value)


@respx.mock
async def test_make_request_with_params(base_client: BaseHttpClient) -> None:
    """Test make_request with query parameters."""
    mock_route = respx.get("https://api.example.com/search").mock(
        return_value=httpx.Response(200, json={"results": [{"id": 1}]})
    )

    response = await base_client.make_request("/search", params={"q": "test"})

    assert response == {"results": [{"id": 1}]}
    assert mock_route.called
    # Verify the parameters were sent
    assert "q=test" in str(mock_route.calls[0].request.url)


@respx.mock
async def test_make_request_post(base_client: BaseHttpClient) -> None:
    """Test make_request with POST method."""
    mock_route = respx.post("https://api.example.com/create").mock(
        return_value=httpx.Response(201, json={"id": 123, "name": "test"})
    )

    response = await base_client.make_request("/create", method="POST", json={"name": "test"})

    assert response == {"id": 123, "name": "test"}
    assert mock_route.called


@respx.mock
async def test_make_request_retries_on_timeout(base_client: BaseHttpClient) -> None:
    """Test that make_request retries on timeout."""
    # First attempt fails, second succeeds
    respx.get("https://api.example.com/flaky").mock(
        side_effect=[
            httpx.TimeoutException("Timeout"),
            httpx.Response(200, json={"data": "success"}),
        ]
    )

    response = await base_client.make_request("/flaky")

    assert response == {"data": "success"}


@respx.mock
async def test_make_request_max_retries_exceeded(base_client: BaseHttpClient) -> None:
    """Test that make_request fails after max retries."""
    respx.get("https://api.example.com/broken").mock(side_effect=httpx.TimeoutException("Timeout"))

    client = BaseHttpClient(base_url="https://api.example.com", timeout=1.0, max_retries=1)

    with pytest.raises(NetworkError) as exc_info:
        await client.make_request("/broken")

    assert "Timeout" in str(exc_info.value) or "Max retries" in str(exc_info.value)


@respx.mock
async def test_make_request_returns_list(base_client: BaseHttpClient) -> None:
    """Test make_request can return a list response."""
    mock_route = respx.get("https://api.example.com/items").mock(
        return_value=httpx.Response(200, json={"results": [{"id": 1}, {"id": 2}]})
    )

    response = await base_client.make_request("/items")

    assert response == {"results": [{"id": 1}, {"id": 2}]}
    assert mock_route.called


@respx.mock
async def test_client_close(base_client: BaseHttpClient) -> None:
    """Test that close closes the HTTP client."""
    respx.get("https://api.example.com/test").mock(
        return_value=httpx.Response(200, json={"data": "test"})
    )

    # Make a request to initialize the client
    await base_client.make_request("/test")

    # Close the client
    await base_client.close()

    # Verify client is closed
    assert base_client._client is None
