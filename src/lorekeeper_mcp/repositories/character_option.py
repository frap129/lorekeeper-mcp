"""Repository for character options with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.repositories.base import Repository


class CharacterOptionClient(Protocol):
    """Protocol for character option API client."""

    async def get_classes_v2(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch classes from API."""
        ...

    async def get_species(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch species (races) from API."""
        ...

    async def get_backgrounds(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch backgrounds from API."""
        ...

    async def get_feats(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch feats from API."""
        ...

    async def get_conditions(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch conditions from API."""
        ...


class CharacterOptionCache(Protocol):
    """Protocol for character option cache."""

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache."""
        ...

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        ...


class CharacterOptionRepository(Repository[dict[str, Any]]):
    """Repository for D&D 5e character options with cache-aside pattern.

    Handles classes, races, backgrounds, feats, and conditions.
    """

    def __init__(self, client: CharacterOptionClient, cache: CharacterOptionCache) -> None:
        """Initialize CharacterOptionRepository.

        Args:
            client: API client with character option methods
            cache: Cache implementation
        """
        self.client = client
        self.cache = cache

    async def get_all(self) -> list[dict[str, Any]]:
        """Retrieve all character options (not implemented).

        Returns:
            Empty list
        """
        return []

    async def search(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for character options with type routing.

        Args:
            **filters: Must include 'option_type' (class, race, background,
                feat, or condition). Other filters depend on type.

        Returns:
            List of matching character options
        """
        option_type = filters.pop("option_type", None)

        if option_type == "class":
            return await self._search_classes(**filters)
        if option_type == "race":
            return await self._search_races(**filters)
        if option_type == "background":
            return await self._search_backgrounds(**filters)
        if option_type == "feat":
            return await self._search_feats(**filters)
        if option_type == "condition":
            return await self._search_conditions(**filters)
        return []

    async def _search_classes(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for character classes."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        # Note: document filter is kept in filters for cache (cache-only filter)
        cached = await self.cache.get_entities("classes", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Cache miss - fetch from API with filters and limit
        api_filters = dict(filters)
        # Remove document from API filters (cache-only filter)
        api_filters.pop("document", None)
        classes: list[dict[str, Any]] = await self.client.get_classes_v2(limit=limit, **api_filters)

        if classes:
            await self.cache.store_entities(classes, "classes")

        return classes

    async def _search_races(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for races."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        # Note: document filter is kept in filters for cache (cache-only filter)
        cached = await self.cache.get_entities("races", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Cache miss - fetch from API with filters and limit
        api_filters = dict(filters)
        # Remove document from API filters (cache-only filter)
        api_filters.pop("document", None)
        races: list[dict[str, Any]] = await self.client.get_species(limit=limit, **api_filters)

        if races:
            await self.cache.store_entities(races, "races")

        return races

    async def _search_backgrounds(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for backgrounds."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        # Note: document filter is kept in filters for cache (cache-only filter)
        cached = await self.cache.get_entities("backgrounds", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Cache miss - fetch from API with filters and limit
        api_filters = dict(filters)
        # Remove document from API filters (cache-only filter)
        api_filters.pop("document", None)
        backgrounds: list[dict[str, Any]] = await self.client.get_backgrounds(
            limit=limit, **api_filters
        )

        if backgrounds:
            await self.cache.store_entities(backgrounds, "backgrounds")

        return backgrounds

    async def _search_feats(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for feats.

        Uses Open5e v2 client for comprehensive feat data.
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Default to higher limit for feats to get comprehensive results
        api_limit = limit if limit else 100

        # Try cache first with valid filter fields only
        # Note: document filter is kept in filters for cache (cache-only filter)
        cached = await self.cache.get_entities("feats", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Cache miss - fetch from API with filters and limit
        api_filters = dict(filters)
        # Remove document from API filters (cache-only filter)
        api_filters.pop("document", None)

        # Use provided client (Open5e v2 or test mock)
        feats: list[dict[str, Any]] = await self.client.get_feats(limit=api_limit, **api_filters)

        if feats:
            await self.cache.store_entities(feats, "feats")

        return feats[:limit] if limit else feats

    async def _search_conditions(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for conditions."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        # Note: document filter is kept in filters for cache (cache-only filter)
        cached = await self.cache.get_entities("conditions", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Cache miss - fetch from API with filters and limit
        api_filters = dict(filters)
        # Remove document from API filters (cache-only filter)
        api_filters.pop("document", None)
        conditions: list[dict[str, Any]] = await self.client.get_conditions(
            limit=limit, **api_filters
        )

        if conditions:
            await self.cache.store_entities(conditions, "conditions")

        return conditions
