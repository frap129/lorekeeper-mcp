"""Repository for equipment with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.models import Armor, MagicItem, Weapon
from lorekeeper_mcp.repositories.base import Repository


class EquipmentClient(Protocol):
    """Protocol for equipment API client."""

    async def get_weapons(self, **filters: Any) -> list[Weapon]:
        """Fetch weapons from API with optional filters."""
        ...

    async def get_armor(self, **filters: Any) -> list[Armor]:
        """Fetch armor from API with optional filters."""
        ...

    async def get_magic_items(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch magic items from API with optional filters."""
        ...


class EquipmentCache(Protocol):
    """Protocol for equipment cache.

    Supports both structured filtering via get_entities() and
    semantic search via semantic_search() for Milvus backend.
    """

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache."""
        ...

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        ...

    async def semantic_search(
        self,
        entity_type: str,
        query: str,
        limit: int = 20,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Perform semantic search (optional - may raise NotImplementedError)."""
        ...


class EquipmentRepository(Repository[Weapon | Armor | MagicItem]):
    """Repository for D&D 5e equipment with cache-aside pattern.

    Handles weapons, armor, and magic items with type routing.
    Implements cache-aside pattern for all item types.
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
        # Store in cache
        armor_dicts = [armor.model_dump() for armor in armors]
        await self.cache.store_entities(armor_dicts, "armor")

        return armors

    async def get_magic_items(self) -> list[MagicItem]:
        """Retrieve all magic items using cache-aside pattern.

        Returns:
            List of all MagicItem objects
        """
        # Try cache first
        cached = await self.cache.get_entities("magic-items")

        if cached:
            return [MagicItem.model_validate(item) for item in cached]

        # Cache miss - fetch from API
        items: list[dict[str, Any]] = await self.client.get_magic_items()

        # Convert to MagicItem objects
        magic_items = [MagicItem.model_validate(item) for item in items]

        # Store in cache
        item_dicts = [item.model_dump() for item in magic_items]
        await self.cache.store_entities(item_dicts, "magic-items")

        return magic_items

    async def get_all(self) -> list[Weapon | Armor | MagicItem]:
        """Retrieve all equipment (weapons, armor, and magic items).

        Returns:
            List of all Weapon, Armor, and MagicItem objects
        """
        weapons = await self.get_weapons()
        armors = await self.get_armor()
        magic_items = await self.get_magic_items()
        return weapons + armors + magic_items

    async def search(self, **filters: Any) -> list[Weapon | Armor | MagicItem]:
        """Search for equipment with optional filters using cache-aside pattern.

        Supports both structured filtering and semantic search.

        Args:
            **filters: Optional filters:
                - semantic_query: Natural language search query (uses vector search)
                - item_type: 'weapon', 'armor', or 'magic-item'
                - document: Filter by source document
                - limit: Maximum results to return

        Returns:
            List of Weapon, Armor, or MagicItem objects matching the filters
        """
        item_type = filters.pop("item_type", None)
        semantic_query = filters.pop("semantic_query", None)

        if semantic_query:
            return await self._semantic_search(semantic_query, item_type=item_type, **filters)

        if item_type == "armor":
            return await self._search_armor(**filters)  # type: ignore[return-value]
        if item_type == "magic-item":
            return await self._search_magic_items(**filters)  # type: ignore[return-value]
        return await self._search_weapons(**filters)  # type: ignore[return-value]

    async def _semantic_search(
        self,
        query: str,
        item_type: str | None = None,
        **filters: Any,
    ) -> list[Weapon | Armor | MagicItem]:
        """Perform semantic search for equipment.

        Args:
            query: Natural language search query
            item_type: Optional item type filter
            **filters: Additional scalar filters

        Returns:
            List of equipment items ranked by semantic similarity
        """
        limit = filters.pop("limit", None)
        search_limit = limit or 20

        # Determine which collections to search
        if item_type == "armor":
            collections: list[tuple[str, type[Weapon] | type[Armor] | type[MagicItem]]] = [
                ("armor", Armor)
            ]
        elif item_type == "magic-item":
            collections = [("magic-items", MagicItem)]
        elif item_type == "weapon":
            collections = [("weapons", Weapon)]
        else:
            # Search all equipment types
            collections = [
                ("weapons", Weapon),
                ("armor", Armor),
                ("magic-items", MagicItem),
            ]

        all_results: list[Weapon | Armor | MagicItem] = []

        for collection_name, model_class in collections:
            try:
                results = await self.cache.semantic_search(
                    collection_name, query, limit=search_limit, **filters
                )
                all_results.extend(model_class.model_validate(r) for r in results)
            except NotImplementedError:
                # Fall back to structured search
                cached = await self.cache.get_entities(collection_name, name=query, **filters)
                all_results.extend(model_class.model_validate(r) for r in cached)

        return all_results[:limit] if limit else all_results

    async def _search_weapons(self, **filters: Any) -> list[Weapon]:
        """Search for weapons with optional filters.

        Args:
            **filters: Optional weapon filters

        Returns:
            List of Weapon objects matching the filters
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        # (document is kept in filters for cache filtering)
        cached = await self.cache.get_entities("weapons", **filters)

        if cached:
            results = [Weapon.model_validate(weapon) for weapon in cached]
            return results[:limit] if limit else results

        # Cache miss - fetch from API with filters and limit
        # Remove document from API filters (cache-only filter)
        api_filters = dict(filters)
        api_filters.pop("document", None)
        weapons = await self.client.get_weapons(limit=limit, **api_filters)

        # Store in cache if we got results
        if weapons:
            # Convert to dicts for caching
            weapon_dicts = [weapon.model_dump() for weapon in weapons]
            await self.cache.store_entities(weapon_dicts, "weapons")

        # Return the weapons
        return weapons

    async def _search_armor(self, **filters: Any) -> list[Armor]:
        """Search for armor with optional filters.

        Args:
            **filters: Optional armor filters

        Returns:
            List of Armor objects matching the filters
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        # (document is kept in filters for cache filtering)
        cached = await self.cache.get_entities("armor", **filters)

        if cached:
            results = [Armor.model_validate(armor) for armor in cached]
            return results[:limit] if limit else results

        # Cache miss - fetch from API with filters and limit
        # Remove document from API filters (cache-only filter)
        api_filters = dict(filters)
        api_filters.pop("document", None)
        armors = await self.client.get_armor(limit=limit, **api_filters)

        # Store in cache if we got results
        if armors:
            # Convert to dicts for caching
            armor_dicts = [armor.model_dump() for armor in armors]
            await self.cache.store_entities(armor_dicts, "armor")

        # Return the armor
        return armors

    async def _search_magic_items(self, **filters: Any) -> list[MagicItem]:
        """Search for magic items with optional filters.

        Args:
            **filters: Optional magic item filters

        Returns:
            List of MagicItem objects matching the filters
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        # (document is kept in filters for cache filtering)
        cached = await self.cache.get_entities("magic-items", **filters)

        if cached:
            results = [MagicItem.model_validate(item) for item in cached]
            return results[:limit] if limit else results

        # Cache miss - fetch from API with filters and limit
        # Remove document from API filters (cache-only filter)
        api_filters = dict(filters)
        api_filters.pop("document", None)
        items: list[dict[str, Any]] = await self.client.get_magic_items(limit=limit, **api_filters)

        # Convert to MagicItem objects
        magic_items = [MagicItem.model_validate(item) for item in items]

        # Store in cache if we got results
        if magic_items:
            item_dicts = [item.model_dump() for item in magic_items]
            await self.cache.store_entities(item_dicts, "magic-items")

        return magic_items
