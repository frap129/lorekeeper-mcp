"""Repository for monsters with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.models.monster import Monster
from lorekeeper_mcp.repositories.base import Repository


class MonsterClient(Protocol):
    """Protocol for monster API client."""

    async def get_monsters(self, **filters: Any) -> list[Monster]:
        """Fetch monsters from API with optional filters."""
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
            client: API client with get_monsters() method
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
        cached = await self.cache.get_entities("monsters")

        if cached:
            return [Monster.model_validate(monster) for monster in cached]

        # Cache miss - fetch from API
        monsters: list[Monster] = await self.client.get_monsters()

        # Store in cache
        monster_dicts = [monster.model_dump() for monster in monsters]
        await self.cache.store_entities(monster_dicts, "monsters")

        return monsters

    async def search(self, **filters: Any) -> list[Monster]:
        """Search for monsters with optional filters using cache-aside pattern.

        Args:
            **filters: Optional filters (type, size, challenge_rating, etc.)

        Returns:
            List of Monster objects matching the filters
        """
        # Try cache first with filters
        cached = await self.cache.get_entities("monsters", **filters)

        if cached:
            return [Monster.model_validate(monster) for monster in cached]

        # Cache miss - fetch from API with filters
        monsters: list[Monster] = await self.client.get_monsters(**filters)

        # Store in cache if we got results
        if monsters:
            monster_dicts = [monster.model_dump() for monster in monsters]
            await self.cache.store_entities(monster_dicts, "monsters")

        return monsters
