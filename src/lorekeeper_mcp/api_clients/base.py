"""Base HTTP client with retry logic and error handling.

This module provides HTTP communication only. Caching is handled by the
repository layer using the cache-aside pattern.

**BREAKING CHANGE (Task 2.10)**: Removed entity cache parameters from
make_request(). Use repository layer for caching instead.
"""

import asyncio
import logging
from typing import Any

import httpx

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError

logger = logging.getLogger(__name__)

# HTTP status code threshold for error responses
HTTP_ERROR_STATUS_CODE = 400


class BaseHttpClient:
    """Base HTTP client providing common functionality for API requests."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 5,
        source_api: str = "api_client",
    ) -> None:
        """Initialize the base HTTP client.

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            source_api: Source API identifier (for logging/tracking)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.source_api = source_api
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "LoreKeeper-MCP/0.1.0"},
            )
        return self._client

    async def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        **kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make HTTP request with retry logic.

        Caching is NOT handled here. Use the repository layer for caching
        via the cache-aside pattern.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            **kwargs: Additional arguments for httpx request (params, json, etc.)

        Returns:
            Parsed JSON response (dict or list of dicts)

        Raises:
            NetworkError: For network-related failures
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"
        retries = self.max_retries
        client = await self._get_client()

        for attempt in range(retries + 1):
            try:
                response = await client.request(method, url, **kwargs)

                if response.status_code >= HTTP_ERROR_STATUS_CODE:
                    raise ApiError(
                        f"API error: {response.status_code}",
                        status_code=response.status_code,
                    )

                result: dict[str, Any] | list[dict[str, Any]] = response.json()
                return result

            except httpx.TimeoutException as e:
                if attempt == retries:
                    raise NetworkError(str(e)) from e
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except httpx.RequestError as e:
                if attempt == retries:
                    raise NetworkError(str(e)) from e
                await asyncio.sleep(2**attempt)

        # Should not reach here
        raise NetworkError("Max retries exceeded")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
