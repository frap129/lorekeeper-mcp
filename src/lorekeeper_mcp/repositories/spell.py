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
            **filters: Optional filters (level, school, etc.)

        Returns:
            List of Spell objects matching the filters
        """
        # Try cache first with filters
        cached = await self.cache.get_entities("spells", **filters)

        if cached:
            return [Spell.model_validate(spell) for spell in cached]

        # Cache miss - fetch from API with filters
        spells: list[Spell] = await self.client.get_spells(**filters)

        # Store in cache if we got results
        if spells:
            spell_dicts = [spell.model_dump() for spell in spells]
            await self.cache.store_entities(spell_dicts, "spells")

        return spells
