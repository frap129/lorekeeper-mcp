"""Repository for spells with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.models.spell import Spell
from lorekeeper_mcp.repositories.base import Repository


class SpellClient(Protocol):
    """Protocol for spell API client."""

    async def get_spells(self, **filters: Any) -> list[Spell]:
        """Fetch spells from API with optional filters."""
        ...


class SpellCache(Protocol):
    """Protocol for spell cache."""

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache."""
        ...

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        ...


class SpellRepository(Repository[Spell]):
    """Repository for D&D 5e spells with cache-aside pattern.

    Implements cache-aside pattern:
    1. Try to get from cache
    2. On cache miss, fetch from API
    3. Store fetched results in cache
    4. Return results
    """

    def __init__(self, client: SpellClient, cache: SpellCache) -> None:
        """Initialize SpellRepository.

        Args:
            client: API client with get_spells() method
            cache: Cache implementation conforming to CacheProtocol
        """
        self.client = client
        self.cache = cache

    async def get_all(self) -> list[Spell]:
        """Retrieve all spells using cache-aside pattern.

        Returns:
            List of all Spell objects
        """
        # Try cache first
        cached = await self.cache.get_entities("spells")

        if cached:
            return [Spell.model_validate(spell) for spell in cached]

        # Cache miss - fetch from API
        spells: list[Spell] = await self.client.get_spells()

        # Store in cache
        spell_dicts = [spell.model_dump() for spell in spells]
        await self.cache.store_entities(spell_dicts, "spells")

        return spells

    async def search(self, **filters: Any) -> list[Spell]:
        """Search for spells with optional filters using cache-aside pattern.

        Args:
            **filters: Optional filters (level, school, document, etc.)

        Returns:
            List of Spell objects matching the filters
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Extract class_key as it's not a cacheable field
        # (spells have multiple classes, not a simple scalar field)
        class_key = filters.pop("class_key", None)

        # Try cache first with valid cache filter fields only
        # Note: document filter is kept in filters for cache (cache-only filter)
        cached = await self.cache.get_entities("spells", **filters)

        if cached:
            results = [Spell.model_validate(spell) for spell in cached]
            # Client-side filter by class_key if specified
            if class_key:
                results = [
                    spell
                    for spell in results
                    if hasattr(spell, "classes")
                    and class_key.lower() in [c.lower() for c in spell.classes]
                ]
            return results[:limit] if limit else results

        # Cache miss - fetch from API with filters and limit
        # Pass class_key to API for server-side filtering
        api_filters = dict(filters)
        # Remove document from API filters (cache-only filter)
        api_filters.pop("document", None)
        if class_key is not None:
            api_filters["class_key"] = class_key
        api_params = self._map_to_api_params(**api_filters)
        spells: list[Spell] = await self.client.get_spells(limit=limit, **api_params)

        # Store in cache if we got results
        if spells:
            spell_dicts = [spell.model_dump() for spell in spells]
            await self.cache.store_entities(spell_dicts, "spells")

        return spells

    def _map_to_api_params(self, **filters: Any) -> dict[str, Any]:
        """Map repository parameters to API-specific filter operators.

        Converts repository-level filter parameters to Open5e v2 API operators.
        Open5e uses operators like `name__icontains` and `school__key`.

        Args:
            **filters: Repository-level filter parameters

        Returns:
            Dictionary of API-specific parameters ready for API calls
        """
        params: dict[str, Any] = {}

        # Map to Open5e v2 filter operators
        if "name" in filters:
            params["name__icontains"] = filters["name"]
        if "school" in filters:
            params["school__key"] = filters["school"].lower()
        if "class_key" in filters:
            # Classes in Open5e API use srd_ prefix (e.g., srd_wizard, srd_cleric)
            class_key = filters["class_key"].lower()
            params["classes__key"] = f"srd_{class_key}"
        if "level_min" in filters:
            params["level__gte"] = filters["level_min"]
        if "level_max" in filters:
            params["level__lte"] = filters["level_max"]
        if "damage_type" in filters:
            params["damage_type__icontains"] = filters["damage_type"]
        # Pass through exact matches
        for key in ["level", "concentration", "ritual", "casting_time"]:
            if key in filters:
                params[key] = filters[key]

        return params
