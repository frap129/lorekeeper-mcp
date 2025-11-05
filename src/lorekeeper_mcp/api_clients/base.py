"""Base HTTP client with retry logic and error handling."""

import asyncio
import logging
from typing import Any

import httpx

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.cache.db import get_cached, set_cached

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
        cache_ttl: int = 604800,  # 7 days default
        source_api: str = "api_client",
    ) -> None:
        """Initialize the base HTTP client.

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            cache_ttl: Cache time-to-live in seconds (default 7 days)
            source_api: Source API identifier for cache metadata
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
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

    async def _get_cached_response(self, cache_key: str) -> dict[str, Any] | None:
        """Get cached response if available.

        Args:
            cache_key: Cache key (typically full URL)

        Returns:
            Cached response or None if not found/expired
        """
        try:
            return await get_cached(cache_key)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
            return None

    async def _cache_response(self, cache_key: str, data: dict[str, Any]) -> None:
        """Cache response data.

        Args:
            cache_key: Cache key (typically full URL)
            data: Response data to cache
        """
        try:
            await set_cached(
                key=cache_key,
                data=data,
                content_type="api_response",
                ttl_seconds=self.cache_ttl,
                source_api=self.source_api,
            )
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
            # Non-fatal - continue without caching

    async def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        use_cache: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with caching and retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            use_cache: Whether to use cache for this request
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            NetworkError: For network-related failures
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"

        # Check cache first
        if use_cache and method == "GET":
            cached = await self._get_cached_response(url)
            if cached is not None:
                logger.debug(f"Cache hit: {url}")
                return cached

        # Make request (delegates to _make_request)
        response = await self._make_request(endpoint, method, **kwargs)

        # Cache successful response
        if use_cache and method == "GET":
            await self._cache_response(url, response)

        return response

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
