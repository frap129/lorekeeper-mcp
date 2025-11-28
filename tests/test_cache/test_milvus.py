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
