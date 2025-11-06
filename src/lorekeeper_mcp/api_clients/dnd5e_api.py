"""Client for D&D 5e API (rules, reference data)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient


class Dnd5eApiClient(BaseHttpClient):
    """Client for D&D 5e API endpoints."""

    def __init__(
        self,
        base_url: str = "https://www.dnd5eapi.co/api/2014",
        cache_ttl: int = 604800,  # 7 days default
        source_api: str = "dnd5e_api",
        **kwargs: Any,
    ) -> None:
        """Initialize D&D 5e API client.

        Args:
            base_url: Base URL for API requests (includes version)
            cache_ttl: Cache time-to-live in seconds (default 7 days)
            source_api: Source API identifier for cache metadata
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(
            base_url=base_url,
            cache_ttl=cache_ttl,
            source_api=source_api,
            **kwargs,
        )
