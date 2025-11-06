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

    async def get_rules(
        self,
        section: str | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Get rules from D&D 5e API.

        Args:
            section: Filter by rule section (adventuring, combat, equipment,
                     spellcasting, using-ability-scores, appendix)
            **filters: Additional API parameters

        Returns:
            List of rule dictionaries with hierarchical organization

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        # Build endpoint
        endpoint = f"/rules/{section}" if section else "/rules/"

        params = {k: v for k, v in filters.items() if v is not None}

        # Make request without entity cache (will implement proper caching in cache integration tests)
        response = await self._make_request(endpoint, params=params)

        # Handle both paginated and single entity responses
        if "results" in response and isinstance(response["results"], list):
            return response["results"]
        return [response]
