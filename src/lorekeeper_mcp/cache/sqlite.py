"""SQLite cache implementation conforming to CacheProtocol."""

from typing import Any

from lorekeeper_mcp.cache.db import bulk_cache_entities, query_cached_entities


class SQLiteCache:
    """SQLite-backed cache implementation conforming to CacheProtocol.

    Wraps existing database functions to provide a cache abstraction layer
    for entity storage and retrieval with filtering support.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize SQLiteCache with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache by type with optional filters.

        Args:
            entity_type: Type of entities to retrieve (e.g., 'spells',
                'monsters', 'equipment')
            **filters: Optional keyword arguments for filtering entities
                by indexed fields (e.g., level=3, school="Evocation")

        Returns:
            List of entity dictionaries matching the criteria. Returns empty
            list if no entities are found.

        Raises:
            ValueError: If entity_type is invalid or filter field is not
                supported for the entity type.
        """
        return await query_cached_entities(entity_type, self.db_path, **filters)

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store or update entities in cache.

        Args:
            entities: List of entity dictionaries to cache. Each entity
                should have at minimum a 'slug' field for identification
                and a 'name' field for display.
            entity_type: Type of entities being stored (e.g., 'spells',
                'monsters', 'equipment')

        Returns:
            Number of entities successfully stored/updated in the cache.

        Raises:
            ValueError: If entity_type is invalid or entities list is empty.
        """
        if not entities:
            raise ValueError("entities list is empty")

        return await bulk_cache_entities(entities, entity_type, self.db_path)
