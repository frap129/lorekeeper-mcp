"""Repository for spells with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.models.spell import Spell
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
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
            **filters: Optional filters (level, school, etc.)

        Returns:
            List of Spell objects matching the filters
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("spells", **filters)

        if cached:
            results = [Spell.model_validate(spell) for spell in cached]
            return results[:limit] if limit else results

        # Cache miss - fetch from API with filters and limit
        spells: list[Spell] = await self.client.get_spells(limit=limit, **filters)

        # Store in cache if we got results
        if spells:
            spell_dicts = [spell.model_dump() for spell in spells]
            await self.cache.store_entities(spell_dicts, "spells")

        return spells

    def _map_to_api_params(self, **filters: Any) -> dict[str, Any]:
        """Map repository parameters to API-specific filter operators.

        Converts repository-level filter parameters to API-specific operators
        based on the client type. Open5e uses operators like `name__icontains`
        and `school__key`, while D&D 5e API uses different parameter names.

        Args:
            **filters: Repository-level filter parameters

        Returns:
            Dictionary of API-specific parameters ready for API calls
        """
        params: dict[str, Any] = {}

        if isinstance(self.client, Open5eV2Client):
            # Map to Open5e filter operators
            if "name" in filters:
                params["name__icontains"] = filters["name"]
            if "school" in filters:
                params["school__key"] = filters["school"]
            if "level_min" in filters:
                params["level__gte"] = filters["level_min"]
            if "level_max" in filters:
                params["level__lte"] = filters["level_max"]
            # Pass through exact matches
            for key in ["level", "concentration", "ritual", "casting_time"]:
                if key in filters:
                    params[key] = filters[key]

        elif isinstance(self.client, Dnd5eApiClient):
            # D&D API uses name directly (built-in partial match)
            if "name" in filters:
                params["name"] = filters["name"]
            # Handle multi-value level ranges
            if "level_min" in filters and "level_max" in filters:
                # Convert range to comma-separated list
                levels = list(range(filters["level_min"], filters["level_max"] + 1))
                params["level"] = ",".join(map(str, levels))
            elif "level" in filters:
                params["level"] = filters["level"]
            # Pass through other filters
            for key in ["school"]:
                if key in filters:
                    params[key] = filters[key]

        return params
