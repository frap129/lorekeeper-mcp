"""Repository for equipment with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon
from lorekeeper_mcp.repositories.base import Repository


class EquipmentClient(Protocol):
    """Protocol for equipment API client."""

    async def get_weapons(self, **filters: Any) -> list[Weapon]:
        """Fetch weapons from API with optional filters."""
        ...

    async def get_armor(self, **filters: Any) -> list[Armor]:
        """Fetch armor from API with optional filters."""
        ...


class EquipmentCache(Protocol):
    """Protocol for equipment cache."""

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache."""
        ...

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        ...


class EquipmentRepository(Repository[Weapon | Armor]):
    """Repository for D&D 5e equipment with cache-aside pattern.

    Handles both weapons and armor with type routing.
    Implements cache-aside pattern for both item types.
    """

    def __init__(self, client: EquipmentClient, cache: EquipmentCache) -> None:
        """Initialize EquipmentRepository.

        Args:
            client: API client with get_weapons() and get_armor() methods
            cache: Cache implementation conforming to CacheProtocol
        """
        self.client = client
        self.cache = cache

    async def get_weapons(self) -> list[Weapon]:
        """Retrieve all weapons using cache-aside pattern.

        Returns:
            List of all Weapon objects
        """
        # Try cache first
        cached = await self.cache.get_entities("weapons")

        if cached:
            return [Weapon.model_validate(weapon) for weapon in cached]

        # Cache miss - fetch from API
        weapons: list[Weapon] = await self.client.get_weapons()

        # Store in cache
        weapon_dicts = [weapon.model_dump() for weapon in weapons]
        await self.cache.store_entities(weapon_dicts, "weapons")

        return weapons

    async def get_armor(self) -> list[Armor]:
        """Retrieve all armor using cache-aside pattern.

        Returns:
            List of all Armor objects
        """
        # Try cache first
        cached = await self.cache.get_entities("armor")

        if cached:
            return [Armor.model_validate(armor) for armor in cached]

        # Cache miss - fetch from API
        armors: list[Armor] = await self.client.get_armor()

        # Store in cache
        armor_dicts = [armor.model_dump() for armor in armors]
        await self.cache.store_entities(armor_dicts, "armor")

        return armors

    async def get_all(self) -> list[Weapon | Armor]:
        """Retrieve all equipment (weapons and armor).

        Returns:
            List of all Weapon and Armor objects
        """
        weapons = await self.get_weapons()
        armors = await self.get_armor()
        return weapons + armors

    async def search(self, **filters: Any) -> list[Weapon | Armor]:
        """Search for equipment with optional filters using cache-aside pattern.

        Args:
            **filters: Optional filters. Must include 'item_type' to specify
                'weapon' or 'armor'. Other filters depend on item type.

        Returns:
            List of Weapon or Armor objects matching the filters
        """
        item_type = filters.pop("item_type", None)

        if item_type == "armor":
            return await self._search_armor(**filters)  # type: ignore[return-value]
        return await self._search_weapons(**filters)  # type: ignore[return-value]

    async def _search_weapons(self, **filters: Any) -> list[Weapon]:
        """Search for weapons with optional filters.

        Args:
            **filters: Optional weapon filters

        Returns:
            List of Weapon objects matching the filters
        """
        # Try cache first with filters
        cached = await self.cache.get_entities("weapons", **filters)

        if cached:
            return [Weapon.model_validate(weapon) for weapon in cached]

        # Cache miss - fetch from API with filters
        weapons: list[Weapon] = await self.client.get_weapons(**filters)

        # Store in cache if we got results
        if weapons:
            weapon_dicts = [weapon.model_dump() for weapon in weapons]
            await self.cache.store_entities(weapon_dicts, "weapons")

        return weapons

    async def _search_armor(self, **filters: Any) -> list[Armor]:
        """Search for armor with optional filters.

        Args:
            **filters: Optional armor filters

        Returns:
            List of Armor objects matching the filters
        """
        # Try cache first with filters
        cached = await self.cache.get_entities("armor", **filters)

        if cached:
            return [Armor.model_validate(armor) for armor in cached]

        # Cache miss - fetch from API with filters
        armors: list[Armor] = await self.client.get_armor(**filters)

        # Store in cache if we got results
        if armors:
            armor_dicts = [armor.model_dump() for armor in armors]
            await self.cache.store_entities(armor_dicts, "armor")

        return armors
