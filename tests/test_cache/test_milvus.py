"""Tests for MilvusCache implementation."""

from pathlib import Path

import pytest


class TestMilvusCacheInit:
    """Tests for MilvusCache initialization."""

    def test_milvus_cache_can_be_instantiated(self, tmp_path: Path):
        """Test that MilvusCache can be created."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        assert cache is not None

    def test_milvus_cache_stores_db_path(self, tmp_path: Path):
        """Test that MilvusCache stores the database path."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        assert cache.db_path == db_path

    def test_milvus_cache_expands_tilde_in_path(self, tmp_path: Path, monkeypatch):
        """Test that MilvusCache expands ~ in path."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        # Monkeypatch home to tmp_path
        monkeypatch.setenv("HOME", str(tmp_path))

        cache = MilvusCache("~/milvus.db")

        assert cache.db_path == tmp_path / "milvus.db"

    def test_milvus_cache_client_not_initialized_on_creation(self, tmp_path: Path):
        """Test that client is not initialized until first use (lazy loading)."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        assert cache._client is None

    def test_milvus_cache_has_embedding_service(self, tmp_path: Path):
        """Test that MilvusCache has an EmbeddingService instance."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        assert isinstance(cache._embedding_service, EmbeddingService)


class TestMilvusCacheClient:
    """Tests for MilvusCache.client property."""

    def test_client_property_initializes_client(self, tmp_path: Path):
        """Test that accessing client property initializes MilvusClient."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        assert cache._client is None
        client = cache.client
        assert client is not None
        assert cache._client is client

    def test_client_property_creates_db_file(self, tmp_path: Path):
        """Test that client property creates database file."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        assert not db_path.exists()
        _ = cache.client
        assert db_path.exists()

    def test_client_property_creates_parent_directory(self, tmp_path: Path):
        """Test that client property creates parent directory if needed."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "subdir" / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        assert not db_path.parent.exists()
        _ = cache.client
        assert db_path.parent.exists()

    def test_client_property_reuses_existing_client(self, tmp_path: Path):
        """Test that multiple accesses return same client instance."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        client1 = cache.client
        client2 = cache.client

        assert client1 is client2


class TestMilvusCacheClose:
    """Tests for MilvusCache.close method."""

    def test_close_closes_client(self, tmp_path: Path):
        """Test that close() closes the client connection."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Initialize client
        _ = cache.client
        assert cache._client is not None

        # Close
        cache.close()
        assert cache._client is None

    def test_close_when_client_not_initialized(self, tmp_path: Path):
        """Test that close() is safe when client was never initialized."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Should not raise
        cache.close()
        assert cache._client is None

    def test_close_can_be_called_multiple_times(self, tmp_path: Path):
        """Test that close() can be called multiple times safely."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        _ = cache.client
        cache.close()
        cache.close()  # Should not raise

        assert cache._client is None


class TestMilvusCacheContextManager:
    """Tests for MilvusCache async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_returns_cache(self, tmp_path: Path):
        """Test that async context manager returns the cache instance."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        async with cache as ctx:
            assert ctx is cache

    @pytest.mark.asyncio
    async def test_context_manager_closes_on_exit(self, tmp_path: Path):
        """Test that context manager closes client on exit."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        async with cache:
            _ = cache.client
            assert cache._client is not None

        assert cache._client is None

    @pytest.mark.asyncio
    async def test_context_manager_closes_on_exception(self, tmp_path: Path):
        """Test that context manager closes client even on exception."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        with pytest.raises(ValueError):
            async with cache:
                _ = cache.client
                raise ValueError("test error")

        assert cache._client is None


class TestMilvusCacheCollectionSchemas:
    """Tests for MilvusCache collection schema definitions."""

    def test_collection_schemas_defined(self):
        """Test that COLLECTION_SCHEMAS constant is defined."""
        from lorekeeper_mcp.cache.milvus import COLLECTION_SCHEMAS

        assert isinstance(COLLECTION_SCHEMAS, dict)
        assert len(COLLECTION_SCHEMAS) > 0

    def test_spells_collection_schema(self):
        """Test spells collection has required indexed fields."""
        from lorekeeper_mcp.cache.milvus import COLLECTION_SCHEMAS

        assert "spells" in COLLECTION_SCHEMAS
        schema = COLLECTION_SCHEMAS["spells"]

        # Should have level, school, concentration, ritual
        field_names = {f["name"] for f in schema["indexed_fields"]}
        assert "level" in field_names
        assert "school" in field_names
        assert "concentration" in field_names
        assert "ritual" in field_names

    def test_creatures_collection_schema(self):
        """Test creatures collection has required indexed fields."""
        from lorekeeper_mcp.cache.milvus import COLLECTION_SCHEMAS

        assert "creatures" in COLLECTION_SCHEMAS
        schema = COLLECTION_SCHEMAS["creatures"]

        # Should have challenge_rating, type, size
        field_names = {f["name"] for f in schema["indexed_fields"]}
        assert "challenge_rating" in field_names
        assert "type" in field_names
        assert "size" in field_names

    def test_all_collections_have_document_field(self):
        """Test all collections have document indexed field."""
        from lorekeeper_mcp.cache.milvus import COLLECTION_SCHEMAS

        for name, schema in COLLECTION_SCHEMAS.items():
            field_names = {f["name"] for f in schema["indexed_fields"]}
            assert "document" in field_names, f"{name} missing document field"


class TestMilvusCacheEnsureCollection:
    """Tests for MilvusCache._ensure_collection method."""

    def test_ensure_collection_creates_spells_collection(self, tmp_path: Path):
        """Test that _ensure_collection creates a collection."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        cache._ensure_collection("spells")

        # Verify collection exists
        collections = cache.client.list_collections()
        assert "spells" in collections

    def test_ensure_collection_idempotent(self, tmp_path: Path):
        """Test that _ensure_collection can be called multiple times."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        cache._ensure_collection("spells")
        cache._ensure_collection("spells")  # Should not raise

        collections = cache.client.list_collections()
        assert "spells" in collections

    def test_ensure_collection_creates_with_schema(self, tmp_path: Path):
        """Test that collection is created with correct schema."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        cache._ensure_collection("spells")

        # Verify we can describe the collection (it has a schema)
        info = cache.client.describe_collection("spells")
        field_names = {f["name"] for f in info["fields"]}

        # Should have base fields
        assert "slug" in field_names
        assert "name" in field_names
        assert "embedding" in field_names
        assert "document" in field_names

        # Should have spell-specific fields
        assert "level" in field_names
        assert "school" in field_names

    def test_ensure_collection_unknown_type_uses_default(self, tmp_path: Path):
        """Test that unknown entity type uses default schema."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # This entity type is not in COLLECTION_SCHEMAS
        cache._ensure_collection("custom_entities")

        collections = cache.client.list_collections()
        assert "custom_entities" in collections

        # Should have at least document field
        info = cache.client.describe_collection("custom_entities")
        field_names = {f["name"] for f in info["fields"]}
        assert "document" in field_names


class TestMilvusCacheBuildFilterExpression:
    """Tests for MilvusCache._build_filter_expression method."""

    def test_build_filter_empty_filters(self, tmp_path: Path):
        """Test filter expression with no filters returns empty string."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = cache._build_filter_expression({})
        assert result == ""

    def test_build_filter_single_string_filter(self, tmp_path: Path):
        """Test filter expression with single string value."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = cache._build_filter_expression({"school": "Evocation"})
        assert result == 'school == "Evocation"'

    def test_build_filter_single_int_filter(self, tmp_path: Path):
        """Test filter expression with single int value."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = cache._build_filter_expression({"level": 3})
        assert result == "level == 3"

    def test_build_filter_single_bool_filter(self, tmp_path: Path):
        """Test filter expression with bool value."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = cache._build_filter_expression({"concentration": True})
        assert result == "concentration == true"

    def test_build_filter_multiple_filters(self, tmp_path: Path):
        """Test filter expression with multiple filters."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = cache._build_filter_expression({"level": 3, "school": "Evocation"})
        # Order may vary, check both parts are present
        assert "level == 3" in result
        assert 'school == "Evocation"' in result
        assert " and " in result

    def test_build_filter_document_string(self, tmp_path: Path):
        """Test filter expression with document as string."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = cache._build_filter_expression({"document": "srd"})
        assert result == 'document == "srd"'

    def test_build_filter_document_list(self, tmp_path: Path):
        """Test filter expression with document as list."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = cache._build_filter_expression({"document": ["srd", "phb"]})
        assert 'document in ["srd", "phb"]' in result

    def test_build_filter_skips_none_values(self, tmp_path: Path):
        """Test that None values are skipped."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = cache._build_filter_expression({"level": 3, "school": None})
        assert result == "level == 3"


class TestMilvusCacheGetEntities:
    """Tests for MilvusCache.get_entities method."""

    @pytest.mark.asyncio
    async def test_get_entities_empty_collection(self, tmp_path: Path):
        """Test get_entities returns empty list for empty collection."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = await cache.get_entities("spells")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_entities_returns_stored_entities(self, tmp_path: Path):
        """Test get_entities returns previously stored entities."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store some entities first
        entities = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "level": 3,
                "school": "Evocation",
                "document": "srd",
            },
            {
                "slug": "ice-storm",
                "name": "Ice Storm",
                "level": 4,
                "school": "Evocation",
                "document": "srd",
            },
        ]
        await cache.store_entities(entities, "spells")

        # Retrieve them
        result = await cache.get_entities("spells")
        assert len(result) == 2
        slugs = {e["slug"] for e in result}
        assert slugs == {"fireball", "ice-storm"}

    @pytest.mark.asyncio
    async def test_get_entities_with_filter(self, tmp_path: Path):
        """Test get_entities with level filter."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "level": 3,
                "school": "Evocation",
                "document": "srd",
            },
            {
                "slug": "ice-storm",
                "name": "Ice Storm",
                "level": 4,
                "school": "Evocation",
                "document": "srd",
            },
        ]
        await cache.store_entities(entities, "spells")

        result = await cache.get_entities("spells", level=3)
        assert len(result) == 1
        assert result[0]["slug"] == "fireball"

    @pytest.mark.asyncio
    async def test_get_entities_with_document_filter(self, tmp_path: Path):
        """Test get_entities with document filter."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "level": 3, "document": "srd"},
            {"slug": "custom-spell", "name": "Custom Spell", "level": 1, "document": "homebrew"},
        ]
        await cache.store_entities(entities, "spells")

        result = await cache.get_entities("spells", document="srd")
        assert len(result) == 1
        assert result[0]["slug"] == "fireball"

    @pytest.mark.asyncio
    async def test_get_entities_with_document_list(self, tmp_path: Path):
        """Test get_entities with document as list."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "document": "srd"},
            {"slug": "custom-spell", "name": "Custom Spell", "document": "homebrew"},
            {"slug": "other-spell", "name": "Other Spell", "document": "other"},
        ]
        await cache.store_entities(entities, "spells")

        result = await cache.get_entities("spells", document=["srd", "homebrew"])
        assert len(result) == 2
        slugs = {e["slug"] for e in result}
        assert slugs == {"fireball", "custom-spell"}


class TestMilvusCacheStoreEntities:
    """Tests for MilvusCache.store_entities method."""

    @pytest.mark.asyncio
    async def test_store_entities_returns_count(self, tmp_path: Path):
        """Test that store_entities returns count of stored entities."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "desc": "A bright streak", "document": "srd"},
        ]

        count = await cache.store_entities(entities, "spells")
        assert count == 1

    @pytest.mark.asyncio
    async def test_store_entities_multiple(self, tmp_path: Path):
        """Test storing multiple entities."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "document": "srd"},
            {"slug": "ice-storm", "name": "Ice Storm", "document": "srd"},
            {"slug": "lightning-bolt", "name": "Lightning Bolt", "document": "srd"},
        ]

        count = await cache.store_entities(entities, "spells")
        assert count == 3

    @pytest.mark.asyncio
    async def test_store_entities_empty_list(self, tmp_path: Path):
        """Test storing empty list raises ValueError."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        with pytest.raises(ValueError, match="entities list is empty"):
            await cache.store_entities([], "spells")

    @pytest.mark.asyncio
    async def test_store_entities_upsert_behavior(self, tmp_path: Path):
        """Test that storing same slug updates existing entity."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store initial
        await cache.store_entities(
            [{"slug": "fireball", "name": "Fireball", "level": 3, "document": "srd"}],
            "spells",
        )

        # Update with same slug
        await cache.store_entities(
            [{"slug": "fireball", "name": "Fireball Updated", "level": 4, "document": "srd"}],
            "spells",
        )

        # Should still be 1 entity with updated values
        results = await cache.get_entities("spells")
        assert len(results) == 1
        assert results[0]["name"] == "Fireball Updated"
        assert results[0]["level"] == 4

    @pytest.mark.asyncio
    async def test_store_entities_generates_embeddings(self, tmp_path: Path):
        """Test that embeddings are generated for stored entities."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "desc": "A bright streak of fire",
                "document": "srd",
            },
        ]

        await cache.store_entities(entities, "spells")

        # Query with output including embedding
        results = cache.client.query(
            collection_name="spells",
            filter='slug == "fireball"',
            output_fields=["embedding"],
        )

        assert len(results) == 1
        assert "embedding" in results[0]
        assert len(results[0]["embedding"]) == 384

    @pytest.mark.asyncio
    async def test_store_entities_preserves_full_data(self, tmp_path: Path):
        """Test that full entity data is preserved and retrievable."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))
        entities = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "desc": "A bright streak flashes from your finger",
                "level": 3,
                "document": "srd",
                "extra_field": "should be preserved",
            }
        ]
        await cache.store_entities(entities, "spells")
        results = await cache.get_entities("spells")

        assert len(results) == 1
        assert results[0]["desc"] == "A bright streak flashes from your finger"
        assert results[0]["extra_field"] == "should be preserved"


class TestMilvusCacheSemanticSearch:
    """Tests for MilvusCache.semantic_search method."""

    @pytest.mark.asyncio
    async def test_semantic_search_empty_collection(self, tmp_path: Path):
        """Test semantic search returns empty list for empty collection."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        result = await cache.semantic_search("spells", "fire damage")
        assert result == []

    @pytest.mark.asyncio
    async def test_semantic_search_returns_similar_entities(self, tmp_path: Path):
        """Test semantic search finds similar entities."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store spells with different themes
        entities = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "desc": "A bright streak flashes and explodes into fire",
                "document": "srd",
            },
            {
                "slug": "fire-shield",
                "name": "Fire Shield",
                "desc": "Flames surround your body protecting you",
                "document": "srd",
            },
            {
                "slug": "ice-storm",
                "name": "Ice Storm",
                "desc": "Hail of ice and snow damages creatures",
                "document": "srd",
            },
        ]
        await cache.store_entities(entities, "spells")

        # Search for fire-related spells
        result = await cache.semantic_search("spells", "fire protection flames")

        assert len(result) > 0
        # Fire-related spells should rank higher
        top_slugs = [r["slug"] for r in result[:2]]
        assert "fireball" in top_slugs or "fire-shield" in top_slugs

    @pytest.mark.asyncio
    async def test_semantic_search_with_limit(self, tmp_path: Path):
        """Test semantic search respects limit parameter."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {
                "slug": f"spell-{i}",
                "name": f"Spell {i}",
                "desc": "A magical spell",
                "document": "srd",
            }
            for i in range(10)
        ]
        await cache.store_entities(entities, "spells")

        result = await cache.semantic_search("spells", "magical spell", limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(self, tmp_path: Path):
        """Test semantic search with scalar filters (hybrid search)."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "desc": "Fire explosion",
                "level": 3,
                "document": "srd",
            },
            {
                "slug": "firebolt",
                "name": "Fire Bolt",
                "desc": "Fire attack cantrip",
                "level": 0,
                "document": "srd",
            },
            {
                "slug": "fire-storm",
                "name": "Fire Storm",
                "desc": "Massive fire",
                "level": 7,
                "document": "srd",
            },
        ]
        await cache.store_entities(entities, "spells")

        # Search for fire spells but only level 3
        result = await cache.semantic_search("spells", "fire", level=3)

        assert len(result) == 1
        assert result[0]["slug"] == "fireball"

    @pytest.mark.asyncio
    async def test_semantic_search_with_document_filter(self, tmp_path: Path):
        """Test semantic search with document filter."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "desc": "Fire explosion", "document": "srd"},
            {
                "slug": "custom-fire",
                "name": "Custom Fire",
                "desc": "Fire attack",
                "document": "homebrew",
            },
        ]
        await cache.store_entities(entities, "spells")

        result = await cache.semantic_search("spells", "fire", document="srd")

        assert len(result) == 1
        assert result[0]["slug"] == "fireball"

    @pytest.mark.asyncio
    async def test_semantic_search_empty_query_falls_back(self, tmp_path: Path):
        """Test semantic search with empty query falls back to get_entities."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "document": "srd"},
            {"slug": "ice-storm", "name": "Ice Storm", "document": "srd"},
        ]
        await cache.store_entities(entities, "spells")

        # Empty query should return all entities
        result = await cache.semantic_search("spells", "")
        assert len(result) == 2


class TestMilvusCacheAdditionalMethods:
    """Tests for additional MilvusCache methods."""

    @pytest.mark.asyncio
    async def test_get_entity_count_empty(self, tmp_path: Path):
        """Test get_entity_count returns 0 for empty collection."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        count = await cache.get_entity_count("spells")
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_entity_count_with_entities(self, tmp_path: Path):
        """Test get_entity_count returns correct count."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "document": "srd"},
            {"slug": "ice-storm", "name": "Ice Storm", "document": "srd"},
        ]
        await cache.store_entities(entities, "spells")

        count = await cache.get_entity_count("spells")
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_available_documents(self, tmp_path: Path):
        """Test get_available_documents returns list of document keys."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store entities from different documents
        entities = [
            {"slug": "fireball", "name": "Fireball", "document": "srd"},
            {"slug": "custom-spell", "name": "Custom Spell", "document": "homebrew"},
        ]
        await cache.store_entities(entities, "spells")

        docs = await cache.get_available_documents()
        assert "srd" in docs
        assert "homebrew" in docs

    @pytest.mark.asyncio
    async def test_get_document_metadata(self, tmp_path: Path):
        """Test get_document_metadata returns entity counts per type."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store entities from srd document
        await cache.store_entities(
            [{"slug": "fireball", "name": "Fireball", "document": "srd"}],
            "spells",
        )
        await cache.store_entities(
            [{"slug": "goblin", "name": "Goblin", "document": "srd"}],
            "creatures",
        )

        metadata = await cache.get_document_metadata("srd")
        assert "spells" in metadata
        assert metadata["spells"] >= 1

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, tmp_path: Path):
        """Test get_cache_stats returns cache statistics."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        await cache.store_entities(
            [{"slug": "fireball", "name": "Fireball", "document": "srd"}],
            "spells",
        )

        stats = await cache.get_cache_stats()
        assert "collections" in stats
        assert "total_entities" in stats
        assert stats["total_entities"] >= 1
