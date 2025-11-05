"""Base HTTP client with retry logic and error handling."""

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
    ) -> None:
        """Initialize the base HTTP client.

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "LoreKeeper-MCP/0.1.0"},
            )
        return self._client

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            max_retries: Override max_retries for this request
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            NetworkError: For network-related failures
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"
        retries = max_retries if max_retries is not None else self.max_retries
        client = await self._get_client()

        for attempt in range(retries + 1):
            try:
                response = await client.request(method, url, **kwargs)

                if response.status_code >= HTTP_ERROR_STATUS_CODE:
                    raise ApiError(
                        f"API error: {response.status_code}",
                        status_code=response.status_code,
                    )

                result: dict[str, Any] = response.json()
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
