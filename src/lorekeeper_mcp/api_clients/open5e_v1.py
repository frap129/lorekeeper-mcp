"""Client for Open5e API v1 (monsters, classes, races, magic items)."""

from typing import Any, cast

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.models.monster import Monster


class Open5eV1Client(BaseHttpClient):
    """Client for Open5e API v1 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v1 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v1", **kwargs)

    async def get_monsters(
        self,
        challenge_rating: str | None = None,
        **filters: Any,
    ) -> list[Monster]:
        """Get monsters from Open5e API v1.

        Args:
            challenge_rating: Filter by CR (e.g., "1/4", "5")
            **filters: Additional API parameters

        Returns:
            List of monster dictionaries
        """
        # Build cache filters for indexed fields
        cache_filters = {}
        if challenge_rating:
            cache_filters["challenge_rating"] = challenge_rating

        # Include challenge_rating in API params if provided
        params = {k: v for k, v in filters.items() if v is not None}
        if challenge_rating:
            params["challenge_rating"] = challenge_rating

        result = await self.make_request(
            "/monsters/",
            use_entity_cache=True,
            entity_type="monsters",
            cache_filters=cache_filters,
            params=params,
        )

        # Handle both list and dict response formats
        entities = result if isinstance(result, list) else result.get("results", [])

        # Convert dictionaries to Monster objects
        return [Monster(**monster_data) for monster_data in entities]

    async def get_classes(self, **filters: Any) -> list[dict[str, Any]]:
        """Get character classes from Open5e API v1.

        Returns:
            List of class dictionaries
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/classes/",
            use_entity_cache=True,
            entity_type="classes",
            params=params,
        )

        if isinstance(result, list):
            return result

        return cast(list[dict[str, Any]], result.get("results", []))

    async def get_races(self, **filters: Any) -> list[dict[str, Any]]:
        """Get character races from Open5e API v1.

        Returns:
            List of race dictionaries
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/races/",
            use_entity_cache=True,
            entity_type="races",
            params=params,
        )

        if isinstance(result, list):
            return result

        return cast(list[dict[str, Any]], result.get("results", []))

    async def get_magic_items(
        self,
        name: str | None = None,
        item_type: str | None = None,
        rarity: str | None = None,
        requires_attunement: bool | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Get magic items from Open5e API v1.

        Args:
            name: Filter by item name
            item_type: Filter by item type (e.g., "ring", "wondrous item")
            rarity: Filter by rarity (e.g., "uncommon", "rare")
            requires_attunement: Filter by attunement requirement
            **filters: Additional API parameters

        Returns:
            List of magic item dictionaries
        """
        # Build cache filters for indexed fields
        cache_filters: dict[str, Any] = {}
        if item_type is not None:
            cache_filters["type"] = item_type
        if rarity is not None:
            cache_filters["rarity"] = rarity
        if requires_attunement is not None:
            cache_filters["requires_attunement"] = requires_attunement

        # Build API params with all provided filters
        params = {k: v for k, v in filters.items() if v is not None}
        if name is not None:
            params["name"] = name
        if item_type is not None:
            params["type"] = item_type
        if rarity is not None:
            params["rarity"] = rarity
        if requires_attunement is not None:
            params["requires_attunement"] = requires_attunement

        result = await self.make_request(
            "/magicitems/",
            use_entity_cache=True,
            entity_type="magicitems",
            cache_filters=cache_filters,
            params=params,
        )

        if isinstance(result, list):
            return result

        return cast(list[dict[str, Any]], result.get("results", []))
