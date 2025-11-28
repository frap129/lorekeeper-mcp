"""Cache protocol definition for entity-based caching abstraction.

This module defines the CacheProtocol interface that any cache implementation
must conform to. It allows for swappable cache backends (SQLite, Redis, etc.)
while maintaining a consistent interface for the repository layer.
"""

from typing import Any

from typing_extensions import Protocol


class CacheProtocol(Protocol):
    """Protocol defining the cache interface for entity storage and retrieval.

    Any cache implementation (SQLite, Redis, Milvus, etc.) must provide methods
    conforming to this protocol to be used with the repository layer.

    The protocol supports both structured filtering via get_entities() and
    semantic/vector search via semantic_search() for implementations that
    support embeddings (e.g., MilvusCache).
    """

    async def get_entities(
        self,
        entity_type: str,
        document: str | list[str] | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Retrieve entities from cache by type with optional filters.

        Args:
            entity_type: Type of entities to retrieve (e.g., 'spells',
                'monsters', 'equipment')
            document: Optional document filter (string or list of strings)
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

    async def semantic_search(
        self,
        entity_type: str,
        query: str,
        limit: int = 20,
        document: str | list[str] | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Perform semantic search using vector similarity.

        Searches for entities using natural language query, optionally
        combined with scalar filters for hybrid search. Implementations
        that do not support vector search should raise NotImplementedError.

        Args:
            entity_type: Type of entities to search (e.g., 'spells', 'creatures')
            query: Natural language search query
            limit: Maximum number of results to return (default 20)
            document: Optional document filter (string or list of strings)
            **filters: Optional keyword filters for hybrid search

        Returns:
            List of entity dictionaries ranked by similarity score.
            May include a '_score' field indicating similarity.

        Raises:
            NotImplementedError: If the cache backend does not support
                semantic search (e.g., SQLiteCache).
        """
        ...
