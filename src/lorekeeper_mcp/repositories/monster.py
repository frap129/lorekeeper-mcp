"""Repository for monsters with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.models.monster import Monster
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.repositories.base import Repository


class MonsterClient(Protocol):
    """Protocol for monster API client."""

    async def get_creatures(self, **filters: Any) -> list[Monster]:
        """Fetch creatures from API with optional filters."""
        ...


class MonsterCache(Protocol):
    """Protocol for monster cache."""

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache."""
        ...

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        ...


class MonsterRepository(Repository[Monster]):
    """Repository for D&D 5e monsters with cache-aside pattern.

    Implements cache-aside pattern:
    1. Try to get from cache
    2. On cache miss, fetch from API
    3. Store fetched results in cache
    4. Return results
    """

    def __init__(self, client: MonsterClient, cache: MonsterCache) -> None:
        """Initialize MonsterRepository.

        Args:
            client: API client with get_creatures() method
            cache: Cache implementation conforming to CacheProtocol
        """
        self.client = client
        self.cache = cache

    async def get_all(self) -> list[Monster]:
        """Retrieve all monsters using cache-aside pattern.

        Returns:
            List of all Monster objects
        """
        # Try cache first
        cached = await self.cache.get_entities("creatures")

        if cached:
            return [Monster.model_validate(monster) for monster in cached]

        # Cache miss - fetch from API
        monsters: list[Monster] = await self.client.get_creatures()

        # Store in cache
        monster_dicts = [monster.model_dump() for monster in monsters]
        await self.cache.store_entities(monster_dicts, "creatures")

        return monsters

    async def search(self, **filters: Any) -> list[Monster]:
        """Search for monsters with optional filters using cache-aside pattern.

        Args:
            **filters: Optional filters (type, size, challenge_rating, etc.)

        Returns:
            List of Monster objects matching the filters
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Separate cache-compatible filters from API-only filters
        # Cache allows: challenge_rating, name, size, slug, source_api, type, document
        cache_filters = {}
        api_only_filters = {}

        cache_allowed_fields = {
            "challenge_rating",
            "name",
            "size",
            "slug",
            "source_api",
            "type",
            "document",
        }

        for key, value in filters.items():
            if key in cache_allowed_fields:
                cache_filters[key] = value
            else:
                api_only_filters[key] = value

        # Try cache first with cache-compatible filter fields only
        cached = await self.cache.get_entities("creatures", **cache_filters)

        if cached:
            results = [Monster.model_validate(monster) for monster in cached]
            # Apply API-only filters client-side if needed
            if api_only_filters:
                results = self._apply_api_filters(results, **api_only_filters)
            return results[:limit] if limit else results

        # Cache miss - fetch from API with all filters
        api_params = self._map_to_api_params(**filters)
        monsters: list[Monster] = await self.client.get_creatures(limit=limit, **api_params)

        # Store in cache if we got results
        if monsters:
            monster_dicts = [monster.model_dump() for monster in monsters]
            await self.cache.store_entities(monster_dicts, "creatures")
        return monsters

    def _map_to_api_params(self, **filters: Any) -> dict[str, Any]:
        """Map repository parameters to API-specific filter operators.

        Converts repository-level filter parameters to API-specific operators
        based on the client type. Open5e v2 uses operators like `challenge_rating_decimal__gte`
        and `challenge_rating_decimal__lte`, while v1 uses `challenge_rating`.

        Args:
            **filters: Repository-level filter parameters

        Returns:
            Dictionary of API-specific parameters ready for API calls
        """
        params: dict[str, Any] = {}

        if isinstance(self.client, Open5eV2Client):
            # Map to Open5e v2 filter operators
            if "armor_class_min" in filters:
                params["armor_class__gte"] = filters["armor_class_min"]
            if "hit_points_min" in filters:
                params["hit_points__gte"] = filters["hit_points_min"]
            if "cr_min" in filters:
                params["challenge_rating_decimal__gte"] = filters["cr_min"]
            if "cr_max" in filters:
                params["challenge_rating_decimal__lte"] = filters["cr_max"]
            if "cr" in filters:
                params["challenge_rating_decimal"] = float(filters["cr"])
            if "challenge_rating" in filters:
                params["challenge_rating_decimal"] = float(filters["challenge_rating"])
            if "name" in filters:
                params["name__icontains"] = filters["name"]
            # Map type and size to lowercase (API expects 'type' and 'size', not __key variants)
            if "type" in filters:
                params["type"] = filters["type"].lower()
            if "size" in filters:
                params["size"] = filters["size"].lower()
            # Pass through API-specific parameters
            for key in ["name__icontains"]:
                if key in filters:
                    params[key] = filters[key]

        elif isinstance(self.client, Open5eV1Client):
            # V1 API: pass through filters as-is
            params = dict(filters)

        else:
            # For unknown client types, pass through filters as-is
            params = dict(filters)

        return params

    def _apply_api_filters(self, monsters: list[Monster], **api_filters: Any) -> list[Monster]:
        """Apply API-only filters client-side to cached results.

        Args:
            monsters: List of Monster objects from cache
            **api_filters: API-only filter parameters

        Returns:
            Filtered list of Monster objects
        """
        filtered = monsters

        # Apply name__icontains filter (case-insensitive substring search)
        if "name__icontains" in api_filters:
            search_term = api_filters["name__icontains"].lower()
            filtered = [m for m in filtered if search_term in m.name.lower()]

        # Apply challenge_rating_decimal__gte filter
        if "challenge_rating_decimal__gte" in api_filters:
            min_cr = api_filters["challenge_rating_decimal__gte"]
            filtered = [
                m
                for m in filtered
                if m.challenge_rating_decimal is not None and m.challenge_rating_decimal >= min_cr
            ]

        # Apply challenge_rating_decimal__lte filter
        if "challenge_rating_decimal__lte" in api_filters:
            max_cr = api_filters["challenge_rating_decimal__lte"]
            filtered = [
                m
                for m in filtered
                if m.challenge_rating_decimal is not None and m.challenge_rating_decimal <= max_cr
            ]

        # Apply armor_class__gte filter
        if "armor_class__gte" in api_filters:
            min_ac = api_filters["armor_class__gte"]
            filtered = [
                m for m in filtered if m.armor_class is not None and m.armor_class >= min_ac
            ]

        # Apply hit_points__gte filter
        if "hit_points__gte" in api_filters:
            min_hp = api_filters["hit_points__gte"]
            filtered = [m for m in filtered if m.hit_points is not None and m.hit_points >= min_hp]

        return filtered
