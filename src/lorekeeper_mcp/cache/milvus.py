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
