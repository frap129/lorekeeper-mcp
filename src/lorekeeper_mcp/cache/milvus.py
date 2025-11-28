"""Milvus Lite cache implementation for vector and semantic search.

This module provides the MilvusCache class that implements CacheProtocol
using Milvus Lite as the storage backend. It supports:
- Structured filtering (same as SQLiteCache)
- Semantic/vector search via embeddings
- Hybrid search combining both approaches
"""

from __future__ import annotations

import logging
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any

from lorekeeper_mcp.cache.embedding import EMBEDDING_DIMENSION, EmbeddingService

if TYPE_CHECKING:
    from pymilvus import MilvusClient

logger = logging.getLogger(__name__)

# Collection schemas for each entity type
# Each schema defines indexed scalar fields for filtering
# Base fields (slug, name, embedding, document, source_api) are always present
COLLECTION_SCHEMAS: dict[str, dict[str, Any]] = {
    "spells": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "level", "type": "INT64"},
            {"name": "school", "type": "VARCHAR", "max_length": 64},
            {"name": "concentration", "type": "BOOL"},
            {"name": "ritual", "type": "BOOL"},
        ],
    },
    "creatures": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "challenge_rating", "type": "VARCHAR", "max_length": 16},
            {"name": "type", "type": "VARCHAR", "max_length": 64},
            {"name": "size", "type": "VARCHAR", "max_length": 32},
        ],
    },
    "monsters": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "challenge_rating", "type": "VARCHAR", "max_length": 16},
            {"name": "type", "type": "VARCHAR", "max_length": 64},
            {"name": "size", "type": "VARCHAR", "max_length": 32},
        ],
    },
    "equipment": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "item_type", "type": "VARCHAR", "max_length": 64},
            {"name": "rarity", "type": "VARCHAR", "max_length": 32},
        ],
    },
    "weapons": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "category", "type": "VARCHAR", "max_length": 64},
            {"name": "damage_type", "type": "VARCHAR", "max_length": 64},
        ],
    },
    "armor": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "category", "type": "VARCHAR", "max_length": 64},
            {"name": "armor_class", "type": "INT64"},
        ],
    },
    "magicitems": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "type", "type": "VARCHAR", "max_length": 64},
            {"name": "rarity", "type": "VARCHAR", "max_length": 32},
            {"name": "requires_attunement", "type": "BOOL"},
        ],
    },
    "classes": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "hit_die", "type": "INT64"},
        ],
    },
    "races": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "size", "type": "VARCHAR", "max_length": 32},
        ],
    },
    "backgrounds": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
        ],
    },
    "feats": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
        ],
    },
    "conditions": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
        ],
    },
    "rules": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "parent", "type": "VARCHAR", "max_length": 256},
        ],
    },
    "rule_sections": {
        "indexed_fields": [
            {"name": "document", "type": "VARCHAR", "max_length": 128},
            {"name": "parent", "type": "VARCHAR", "max_length": 256},
        ],
    },
}

# Default schema for entity types not explicitly defined
DEFAULT_COLLECTION_SCHEMA: dict[str, Any] = {
    "indexed_fields": [
        {"name": "document", "type": "VARCHAR", "max_length": 128},
    ],
}


class MilvusCache:
    """Milvus Lite-backed cache implementation with semantic search support.

    Implements CacheProtocol while adding semantic_search() for vector similarity.
    Uses lazy initialization to avoid startup delays when cache is not needed.

    Attributes:
        db_path: Path to the Milvus Lite database file.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize MilvusCache with database path.

        Args:
            db_path: Path to Milvus Lite database file. Supports ~ expansion.
        """
        self.db_path: Path = Path(db_path).expanduser()
        self._client: MilvusClient | None = None
        self._embedding_service: EmbeddingService = EmbeddingService()

    @property
    def client(self) -> MilvusClient:
        """Lazy-initialize and return the Milvus client.

        Creates parent directories and database file if they don't exist.
        Also ensures required collections are created.

        Returns:
            Initialized MilvusClient instance.
        """
        if self._client is None:
            from pymilvus import MilvusClient

            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info("Initializing Milvus Lite client: %s", self.db_path)
            self._client = MilvusClient(str(self.db_path))
            logger.info("Milvus Lite client initialized")

        return self._client

    def close(self) -> None:
        """Close the Milvus client connection.

        Safe to call multiple times or when client was never initialized.
        """
        if self._client is not None:
            logger.info("Closing Milvus Lite client")
            self._client.close()
            self._client = None

    async def __aenter__(self) -> MilvusCache:
        """Enter async context manager.

        Returns:
            This MilvusCache instance.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager, closing the client.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        self.close()

    def _ensure_collection(self, entity_type: str) -> None:
        """Ensure a collection exists for the given entity type.

        Creates the collection with appropriate schema if it doesn't exist.
        Safe to call multiple times (idempotent).

        Args:
            entity_type: Type of entity (spells, creatures, etc.)
        """
        from pymilvus import DataType

        # Check if collection already exists
        if self.client.has_collection(entity_type):
            return

        logger.info("Creating collection: %s", entity_type)

        # Get schema for this entity type (or default)
        schema_def = COLLECTION_SCHEMAS.get(entity_type, DEFAULT_COLLECTION_SCHEMA)

        # Create schema
        schema = self.client.create_schema(auto_id=False, enable_dynamic_field=True)

        # Add base fields
        schema.add_field(
            field_name="slug",
            datatype=DataType.VARCHAR,
            max_length=256,
            is_primary=True,
        )
        schema.add_field(
            field_name="name",
            datatype=DataType.VARCHAR,
            max_length=256,
        )
        schema.add_field(
            field_name="embedding",
            datatype=DataType.FLOAT_VECTOR,
            dim=EMBEDDING_DIMENSION,
        )
        schema.add_field(
            field_name="source_api",
            datatype=DataType.VARCHAR,
            max_length=64,
        )

        # Add indexed fields from schema definition
        for field_def in schema_def["indexed_fields"]:
            field_name = field_def["name"]
            field_type = field_def["type"]

            if field_type == "VARCHAR":
                schema.add_field(
                    field_name=field_name,
                    datatype=DataType.VARCHAR,
                    max_length=field_def.get("max_length", 256),
                )
            elif field_type == "INT64":
                schema.add_field(
                    field_name=field_name,
                    datatype=DataType.INT64,
                )
            elif field_type == "BOOL":
                schema.add_field(
                    field_name=field_name,
                    datatype=DataType.BOOL,
                )
            elif field_type == "FLOAT":
                schema.add_field(
                    field_name=field_name,
                    datatype=DataType.FLOAT,
                )

        # Create index parameters for vector field
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128},
        )

        # Create the collection
        self.client.create_collection(
            collection_name=entity_type,
            schema=schema,
            index_params=index_params,
        )

        logger.info("Collection created: %s", entity_type)

    def _build_filter_expression(self, filters: dict[str, Any]) -> str:
        """Build Milvus filter expression from keyword filters.

        Converts Python filter dict to Milvus boolean expression syntax.
        Example: {"level": 3, "school": "Evocation"} -> 'level == 3 and school == "Evocation"'

        Args:
            filters: Dictionary of field names to filter values.

        Returns:
            Milvus filter expression string, or empty string if no filters.
        """
        expressions: list[str] = []

        for field, value in filters.items():
            if value is None:
                continue

            if isinstance(value, str):
                expressions.append(f'{field} == "{value}"')
            elif isinstance(value, bool):
                # Milvus uses lowercase boolean literals
                expressions.append(f"{field} == {str(value).lower()}")
            elif isinstance(value, int | float):
                expressions.append(f"{field} == {value}")
            elif isinstance(value, list):
                # Handle list of values (IN clause)
                if all(isinstance(v, str) for v in value):
                    quoted = [f'"{v}"' for v in value]
                    expressions.append(f"{field} in [{', '.join(quoted)}]")
                else:
                    expressions.append(f"{field} in {value}")

        return " and ".join(expressions)

    async def store_entities(
        self,
        entities: list[dict[str, Any]],
        entity_type: str,
    ) -> int:
        """Store or update entities in cache with auto-generated embeddings.

        Args:
            entities: List of entity dictionaries to cache.
            entity_type: Type of entities being stored.

        Returns:
            Number of entities successfully stored/updated.
        """
        if not entities:
            raise ValueError("entities list is empty")

        self._ensure_collection(entity_type)

        # Prepare entities with embeddings
        prepared_entities = []
        texts_to_embed = []

        for entity in entities:
            # Extract searchable text
            text = self._embedding_service.get_searchable_text(entity, entity_type)
            texts_to_embed.append(text)

        # Batch encode all texts
        embeddings = self._embedding_service.encode_batch(texts_to_embed)

        # Get schema for this entity type (or default)
        schema_def = COLLECTION_SCHEMAS.get(entity_type, DEFAULT_COLLECTION_SCHEMA)

        # Build a mapping of field name to default value based on type
        field_defaults: dict[str, Any] = {}
        for field_def in schema_def["indexed_fields"]:
            field_name = field_def["name"]
            field_type = field_def["type"]
            if field_type == "VARCHAR":
                field_defaults[field_name] = ""
            elif field_type == "INT64":
                field_defaults[field_name] = 0
            elif field_type == "BOOL":
                field_defaults[field_name] = False
            elif field_type == "FLOAT":
                field_defaults[field_name] = 0.0

        # Prepare entities with embeddings
        for entity, embedding in zip(entities, embeddings, strict=True):
            prepared = {
                "slug": entity.get("slug", ""),
                "name": entity.get("name", ""),
                "embedding": embedding,
                "source_api": entity.get("source_api", ""),
            }

            # Add ALL indexed fields with proper defaults
            for field_name, default_value in field_defaults.items():
                if field_name in entity:
                    prepared[field_name] = entity[field_name]
                elif field_name == "document":
                    # Handle document field specially
                    prepared["document"] = entity.get(
                        "document", entity.get("document__slug", default_value)
                    )
                else:
                    prepared[field_name] = default_value

            # Store full entity data in dynamic fields
            prepared["entity_data"] = entity

            prepared_entities.append(prepared)

        # Upsert to Milvus
        try:
            self.client.upsert(
                collection_name=entity_type,
                data=prepared_entities,
            )
            logger.info("Stored %d entities in %s", len(prepared_entities), entity_type)
            return len(prepared_entities)
        except Exception as e:
            logger.error("Failed to store entities in %s: %s", entity_type, e)
            raise

    async def get_entities(
        self,
        entity_type: str,
        document: str | list[str] | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Retrieve entities from cache by type with optional filters.

        Args:
            entity_type: Type of entities to retrieve (e.g., 'spells', 'creatures')
            document: Optional document filter (string or list of strings)
            **filters: Optional keyword arguments for filtering entities

        Returns:
            List of entity dictionaries matching the criteria.
        """
        self._ensure_collection(entity_type)

        # Add document to filters if provided
        if document is not None:
            filters["document"] = document

        # Build filter expression
        filter_expr = self._build_filter_expression(filters)

        # Query the collection
        try:
            if filter_expr:
                results = self.client.query(
                    collection_name=entity_type,
                    filter=filter_expr,
                    output_fields=["*"],
                )
            else:
                # Empty filter requires limit in Milvus Lite
                results = self.client.query(
                    collection_name=entity_type,
                    filter="",
                    output_fields=["*"],
                    limit=10000,  # Large limit to get all entities
                )
        except Exception as e:
            logger.warning("Query failed for %s: %s", entity_type, e)
            return []

        # Convert results to dicts, reconstructing from entity_data if available
        entities = []
        for result in results:
            # If entity_data is stored, use it as the base and merge with indexed fields
            if "entity_data" in result and isinstance(result["entity_data"], dict):
                entity = dict(result["entity_data"])
            else:
                entity = dict(result)
                entity.pop("embedding", None)  # Don't return embeddings
            entities.append(entity)

        return entities

    async def semantic_search(
        self,
        entity_type: str,
        query: str,
        limit: int = 20,
        document: str | list[str] | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Perform semantic search using vector similarity.

        Combines vector similarity search with optional scalar filters
        for hybrid search functionality.

        Args:
            entity_type: Type of entities to search (e.g., 'spells', 'creatures')
            query: Natural language search query
            limit: Maximum number of results to return (default 20)
            document: Optional document filter (string or list of strings)
            **filters: Optional keyword filters for hybrid search

        Returns:
            List of entity dictionaries ranked by similarity score.
        """
        # Handle empty query - fall back to get_entities
        if not query or not query.strip():
            return await self.get_entities(entity_type, document=document, **filters)

        self._ensure_collection(entity_type)

        # Generate query embedding
        query_embedding = self._embedding_service.encode(query)

        # Add document to filters if provided
        if document is not None:
            filters["document"] = document

        # Build filter expression
        filter_expr = self._build_filter_expression(filters)

        # Execute vector search
        try:
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 16},
            }

            results = self.client.search(
                collection_name=entity_type,
                data=[query_embedding],
                filter=filter_expr if filter_expr else "",
                limit=limit,
                output_fields=["*"],
                search_params=search_params,
            )

            # Extract entities from search results
            entities = []
            if results and len(results) > 0:
                for hit in results[0]:
                    hit_entity = hit["entity"]
                    # If entity_data is stored, use it as the base
                    if "entity_data" in hit_entity and isinstance(hit_entity["entity_data"], dict):
                        entity = dict(hit_entity["entity_data"])
                    else:
                        entity = dict(hit_entity)
                        entity.pop("embedding", None)  # Don't return embeddings
                    entity["_score"] = hit["distance"]  # Include similarity score
                    entities.append(entity)

            return entities

        except Exception as e:
            logger.warning(
                "Semantic search failed for %s: %s, falling back to structured search",
                entity_type,
                e,
            )
            return await self.get_entities(entity_type, document=document, **filters)

    async def get_entity_count(self, entity_type: str) -> int:
        """Get count of entities in a collection.

        Args:
            entity_type: Type of entities to count.

        Returns:
            Number of entities in the collection.
        """
        self._ensure_collection(entity_type)

        try:
            stats = self.client.get_collection_stats(entity_type)
            return int(stats.get("row_count", 0))
        except Exception as e:
            logger.warning("Failed to get entity count for %s: %s", entity_type, e)
            return 0

    async def get_available_documents(self) -> list[str]:
        """Get list of available document keys across all collections.

        Returns:
            List of unique document keys.
        """
        documents: set[str] = set()

        for collection_name in self.client.list_collections():
            try:
                results = self.client.query(
                    collection_name=collection_name,
                    filter="",
                    output_fields=["document"],
                    limit=10000,
                )
                for result in results:
                    doc = result.get("document")
                    if doc:
                        documents.add(doc)
            except Exception as e:
                logger.debug("Failed to query documents from %s: %s", collection_name, e)

        return sorted(documents)

    async def get_document_metadata(self, document_key: str) -> dict[str, int]:
        """Get entity counts per type for a specific document.

        Args:
            document_key: Document key to get metadata for.

        Returns:
            Dictionary mapping entity types to counts.
        """
        metadata: dict[str, int] = {}

        for collection_name in self.client.list_collections():
            try:
                results = self.client.query(
                    collection_name=collection_name,
                    filter=f'document == "{document_key}"',
                    output_fields=["slug"],
                )
                count = len(results)
                if count > 0:
                    metadata[collection_name] = count
            except Exception as e:
                logger.debug(
                    "Failed to query %s for document %s: %s", collection_name, document_key, e
                )

        return metadata

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get overall cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        collections = self.client.list_collections()
        total_entities = 0
        collection_stats: dict[str, int] = {}

        for collection_name in collections:
            try:
                stats = self.client.get_collection_stats(collection_name)
                count = stats.get("row_count", 0)
                collection_stats[collection_name] = count
                total_entities += count
            except Exception as e:
                logger.debug("Failed to get stats for %s: %s", collection_name, e)

        return {
            "collections": collection_stats,
            "total_entities": total_entities,
            "db_path": str(self.db_path),
        }
