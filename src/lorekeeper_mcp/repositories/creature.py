"""Repository for creatures with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.models import Creature
from lorekeeper_mcp.repositories.base import Repository


class CreatureClient(Protocol):
    """Protocol for creature API client."""

    async def get_creatures(self, **filters: Any) -> list[Creature]:
        """Fetch creatures from API with optional filters."""
        ...


class CreatureCache(Protocol):
    """Protocol for creature cache.

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


class CreatureRepository(Repository[Creature]):
    """Repository for D&D 5e creatures with cache-aside pattern.

    Implements cache-aside pattern:
    1. Try to get from cache
    2. On cache miss, fetch from API
    3. Store fetched results in cache
    4. Return results
    """

    def __init__(self, client: CreatureClient, cache: CreatureCache) -> None:
        """Initialize CreatureRepository.

        Args:
            client: API client with get_creatures() method
            cache: Cache implementation conforming to CacheProtocol
        """
        self.client = client
        self.cache = cache

    async def get_all(self) -> list[Creature]:
        """Retrieve all creatures using cache-aside pattern.

        Returns:
            List of all Creature objects
        """
        # Try cache first
        cached = await self.cache.get_entities("creatures")

        if cached:
            return [Creature.model_validate(creature) for creature in cached]

        # Cache miss - fetch from API
        creatures: list[Creature] = await self.client.get_creatures()

        # Store in cache
        creature_dicts = [creature.model_dump() for creature in creatures]
        await self.cache.store_entities(creature_dicts, "creatures")

        return creatures

    async def search(self, **filters: Any) -> list[Creature]:
        """Search for creatures with optional filters using cache-aside pattern.

        Supports both structured filtering and semantic search.

        Args:
            **filters: Optional filters:
                - search: Natural language search query (uses vector search)
                - challenge_rating, type, size: Structured filters
                - document: Filter by source document
                - limit: Maximum results to return

        Returns:
            List of Creature objects matching the filters
        """
        # Extract special parameters
        limit = filters.pop("limit", None)
        search = filters.pop("search", None)

        # Handle semantic search if query provided
        if search:
            return await self._semantic_search(search, limit=limit, **filters)

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
            results = [Creature.model_validate(creature) for creature in cached]
            # Apply API-only filters client-side if needed
            if api_only_filters:
                results = self._apply_api_filters(results, **api_only_filters)
            return results[:limit] if limit else results

        # Cache miss - fetch from API with filters
        api_filters = dict(filters)
        # Remove document from API filters (cache-only filter)
        api_filters.pop("document", None)
        api_params = self._map_to_api_params(**api_filters)
        creatures: list[Creature] = await self.client.get_creatures(limit=limit, **api_params)

        # Store in cache if we got results
        if creatures:
            creature_dicts = [creature.model_dump() for creature in creatures]
            await self.cache.store_entities(creature_dicts, "creatures")
        return creatures

    async def _semantic_search(
        self,
        query: str,
        limit: int | None = None,
        **filters: Any,
    ) -> list[Creature]:
        """Perform semantic search for creatures.

        Args:
            query: Natural language search query
            limit: Maximum results to return
            **filters: Additional scalar filters (challenge_rating, type, etc.)

        Returns:
            List of Creature objects ranked by semantic similarity
        """
        search_limit = limit or 20

        # Filter to cache-allowed fields only
        cache_filters = {
            k: v
            for k, v in filters.items()
            if k in {"challenge_rating", "name", "size", "slug", "source_api", "type", "document"}
        }

        try:
            results = await self.cache.semantic_search(
                "creatures", query, limit=search_limit, **cache_filters
            )
        except NotImplementedError:
            # Fall back to structured search
            cache_filters["name"] = query
            cached = await self.cache.get_entities("creatures", **cache_filters)
            results = cached if cached else []

        creatures = [Creature.model_validate(creature) for creature in results]
        return creatures[:limit] if limit else creatures

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

    def _apply_api_filters(self, creatures: list[Creature], **api_filters: Any) -> list[Creature]:
        """Apply API-only filters client-side to cached results.

        Args:
            creatures: List of Creature objects from cache
            **api_filters: API-only filter parameters

        Returns:
            Filtered list of Creature objects
        """
        filtered = creatures

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
