"""Cache protocol definition for entity-based caching abstraction.

This module defines the CacheProtocol interface that any cache implementation
must conform to. It allows for swappable cache backends (SQLite, Redis, etc.)
while maintaining a consistent interface for the repository layer.
"""

from typing import Any

from typing_extensions import Protocol


class CacheProtocol(Protocol):
    """Protocol defining the cache interface for entity storage and retrieval.

    Any cache implementation (SQLite, Redis, etc.) must provide methods
    conforming to this protocol to be used with the repository layer.
    """

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
        ...

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
        ...
