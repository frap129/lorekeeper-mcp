"""Base HTTP client with retry logic and error handling."""

import asyncio
import logging
from typing import Any

import httpx

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.cache.db import (
    bulk_cache_entities,
    get_cached,
    query_cached_entities,
    set_cached,
)

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
        self._background_tasks: set[asyncio.Task[Any]] = set()
        self._in_flight_refreshes: set[str] = set()

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
        use_entity_cache: bool = False,
        entity_type: str | None = None,
        cache_filters: dict[str, Any] | None = None,
        cache_first: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make HTTP request with caching and retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            use_cache: Whether to use legacy URL-based cache (deprecated)
            use_entity_cache: Whether to use entity-based cache
            entity_type: Type of entities for entity cache
            cache_filters: Filters for cache query
            cache_first: Return cache immediately, refresh in background
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response or list of entities

        Raises:
            NetworkError: For network-related failures (when not using offline fallback)
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"
        cache_filters = cache_filters or {}

        # Cache-first mode: return cache immediately, refresh async
        if cache_first and use_entity_cache and entity_type:
            # Query cache immediately
            cached_entities = await self._query_cache_parallel(entity_type, **cache_filters)

            # Create unique key for this refresh to prevent redundant refreshes
            refresh_key = f"{entity_type}:{endpoint}:{sorted(cache_filters.items())!s}"

            # Only start background refresh if not already in progress
            if refresh_key not in self._in_flight_refreshes:
                # Start background refresh task
                async def background_refresh() -> None:
                    self._in_flight_refreshes.add(refresh_key)
                    try:
                        response = await self._make_request(endpoint, method, **kwargs)
                        entities = self._extract_entities(response, entity_type)
                        await self._cache_api_entities(entities, entity_type)
                        logger.debug(f"Background refresh completed for {entity_type}")
                    except Exception as e:
                        logger.warning(f"Background refresh failed: {e}")
                    finally:
                        self._in_flight_refreshes.discard(refresh_key)

                # Fire and forget (store reference to prevent premature garbage collection)
                task = asyncio.create_task(background_refresh())
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

            return cached_entities

        # Start parallel cache query if entity cache enabled
        cache_task = None
        if use_entity_cache and entity_type:
            cache_task = asyncio.create_task(
                self._query_cache_parallel(entity_type, **cache_filters)
            )

        # Legacy URL-based cache check
        if use_cache and method == "GET" and not use_entity_cache:
            cached = await self._get_cached_response(url)
            if cached is not None:
                logger.debug(f"Cache hit: {url}")
                return cached

        # Make API request
        try:
            response = await self._make_request(endpoint, method, **kwargs)

            # Extract and cache entities if using entity cache
            if use_entity_cache and entity_type:
                entities = self._extract_entities(response, entity_type)
                await self._cache_api_entities(entities, entity_type)

                # Merge with cache results if available
                if cache_task:
                    try:
                        cached_entities = await cache_task
                        # For now, API takes precedence, just return API results
                        # (merging logic can be enhanced later)
                        return entities
                    except Exception:
                        return entities

                return entities

            # Legacy URL-based cache storage
            if use_cache and method == "GET":
                await self._cache_response(url, response)

            return response

        except NetworkError as e:
            # Offline fallback: return cached entities
            if use_entity_cache and entity_type and cache_task:
                logger.warning(f"Network error, falling back to cache: {e}")
                try:
                    cached_entities = await cache_task
                    if cached_entities:
                        logger.info(f"Returning {len(cached_entities)} cached {entity_type}")
                        return cached_entities
                    logger.warning(f"No cached {entity_type} available for offline mode")
                    return []
                except Exception as cache_error:
                    logger.error(f"Cache fallback failed: {cache_error}")
                    return []

            # No fallback available, re-raise
            raise

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

    async def _query_cache_parallel(
        self,
        entity_type: str,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Query cache for entities in parallel.

        Args:
            entity_type: Type of entities to query
            **filters: Filter parameters

        Returns:
            List of cached entities, or empty list on error
        """
        try:
            return await query_cached_entities(entity_type, **filters)
        except Exception as e:
            logger.warning(f"Cache query failed: {e}")
            return []

    def _extract_entities(
        self,
        response: dict[str, Any],
        entity_type: str,
    ) -> list[dict[str, Any]]:
        """Extract entities from API response.

        Handles both paginated responses with 'results' and direct entities.

        Args:
            response: API response dictionary
            entity_type: Type of entities

        Returns:
            List of entity dictionaries
        """
        # Check if paginated response
        if "results" in response and isinstance(response["results"], list):
            return response["results"]

        # Check if direct entity (has slug)
        if "slug" in response:
            return [response]

        # Unknown format
        return []

    async def _cache_api_entities(
        self,
        entities: list[dict[str, Any]],
        entity_type: str,
    ) -> None:
        """Cache entities from API response.

        Args:
            entities: List of entity dictionaries
            entity_type: Type of entities
        """
        if not entities:
            return

        try:
            await bulk_cache_entities(
                entities,
                entity_type,
                source_api=self.source_api,
            )
            logger.debug(f"Cached {len(entities)} {entity_type}")
        except Exception as e:
            logger.warning(f"Failed to cache entities: {e}")
            # Non-fatal - continue without caching

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
