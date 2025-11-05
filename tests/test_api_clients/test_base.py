"""Tests for BaseHttpClient."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError


@pytest.fixture
def base_client() -> BaseHttpClient:
    """Create a BaseHttpClient instance for testing."""
    return BaseHttpClient(base_url="https://api.example.com", timeout=5.0)


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
