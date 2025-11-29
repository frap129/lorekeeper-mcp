"""Repository for spells with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.models import Spell
from lorekeeper_mcp.repositories.base import Repository


class SpellClient(Protocol):
    """Protocol for spell API client."""

    async def get_spells(self, **filters: Any) -> list[Spell]:
        """Fetch spells from API with optional filters."""
        ...


class SpellCache(Protocol):
    """Protocol for spell cache.

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

        Supports both structured filtering and semantic search.

        Args:
            **filters: Optional filters:
                - search: Natural language search query (uses vector search)
                - level, school, concentration, ritual: Structured filters
                - class_key: Filter by class (e.g., "wizard", "cleric")
                - document: Filter by source document
                - limit: Maximum results to return

        Returns:
            List of Spell objects matching the filters
        """
        # Extract special parameters
        limit = filters.pop("limit", None)
        class_key = filters.pop("class_key", None)
        search = filters.pop("search", None)

        # Handle semantic search if query provided
        if search:
            return await self._semantic_search(search, limit=limit, class_key=class_key, **filters)

        # Regular structured search (existing behavior)
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

    async def _semantic_search(
        self,
        query: str,
        limit: int | None = None,
        class_key: str | None = None,
        **filters: Any,
    ) -> list[Spell]:
        """Perform semantic search for spells.

        Args:
            query: Natural language search query
            limit: Maximum results to return
            class_key: Optional class filter (applied client-side)
            **filters: Additional scalar filters (level, school, etc.)

        Returns:
            List of Spell objects ranked by semantic similarity
        """
        search_limit = limit or 20

        try:
            results = await self.cache.semantic_search(
                "spells", query, limit=search_limit, **filters
            )
        except NotImplementedError:
            # Fall back to structured search if cache doesn't support semantic search
            return await self._fallback_structured_search(
                query, limit=limit, class_key=class_key, **filters
            )

        spells = [Spell.model_validate(spell) for spell in results]

        # Apply class_key filter client-side if specified
        if class_key:
            spells = [
                spell
                for spell in spells
                if hasattr(spell, "classes")
                and class_key.lower() in [c.lower() for c in spell.classes]
            ]

        return spells[:limit] if limit else spells

    async def _fallback_structured_search(
        self,
        query: str,
        limit: int | None = None,
        class_key: str | None = None,
        **filters: Any,
    ) -> list[Spell]:
        """Fall back to structured search using name filter.

        Args:
            query: Search query (used as name filter)
            limit: Maximum results to return
            class_key: Optional class filter
            **filters: Additional filters

        Returns:
            List of Spell objects matching name filter
        """
        # Use query as name filter for fallback
        filters["name"] = query
        cached = await self.cache.get_entities("spells", **filters)

        if cached:
            results = [Spell.model_validate(spell) for spell in cached]
            if class_key:
                results = [
                    spell
                    for spell in results
                    if hasattr(spell, "classes")
                    and class_key.lower() in [c.lower() for c in spell.classes]
                ]
            return results[:limit] if limit else results

        return []

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
