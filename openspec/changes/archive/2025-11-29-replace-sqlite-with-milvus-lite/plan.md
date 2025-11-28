# Replace SQLite with Milvus Lite Implementation Plan

**Goal:** Replace the SQLite cache backend with Milvus Lite to enable semantic/vector search while maintaining all existing structured filtering capabilities.

**Architecture:** Milvus Lite runs embedded in the Python process (like SQLite) using a single `.db` file. Each entity type maps to a separate Milvus collection with entity-specific scalar fields for filtering. The `EmbeddingService` generates 384-dimensional vectors using `all-MiniLM-L6-v2` for semantic search. Hybrid search combines vector similarity with scalar filters in a single query.

**Tech Stack:** pymilvus>=2.4.0 (includes Milvus Lite), sentence-transformers>=2.2.0 (all-MiniLM-L6-v2 model), existing CacheProtocol interface

---

## Task 1: Core Infrastructure

### Task 1.1: Dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add pymilvus and sentence-transformers dependencies**

Edit `pyproject.toml` to add the new dependencies after `edn-format`:

```python
# In pyproject.toml, line 19, after "edn-format>=0.7.5,"
dependencies = [
    "fastmcp>=0.2.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "aiosqlite>=0.19.0",
    "python-dotenv>=1.0.0",
    "click>=8.1.0",
    "edn-format>=0.7.5",
    "pymilvus>=2.4.0",
    "sentence-transformers>=2.2.0",
]
```

**Step 2: Add mypy ignore for new modules**

Edit `pyproject.toml` to add mypy overrides for new dependencies (around line 148):

```toml
[[tool.mypy.overrides]]
module = [
    "fastmcp.*",
    "aiosqlite.*",
    "edn_format.*",
    "pymilvus.*",
    "sentence_transformers.*",
]
ignore_missing_imports = true
```

**Step 3: Run uv sync**

```bash
uv sync
```

Expected: Dependencies install successfully. First run may take longer to download sentence-transformers model dependencies.

**Step 4: Verify imports work**

Create a quick verification script and run it:

```bash
uv run python -c "from pymilvus import MilvusClient; from sentence_transformers import SentenceTransformer; print('Imports OK')"
```

Expected output: `Imports OK`

**Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat(cache): add milvus and sentence-transformers dependencies"
```

---

### Task 1.2: EmbeddingService Implementation

**Files:**
- Create: `src/lorekeeper_mcp/cache/embedding.py`
- Create: `tests/test_cache/test_embedding.py`

#### Step 1: Write test for EmbeddingService initialization

Create `tests/test_cache/test_embedding.py`:

```python
"""Tests for EmbeddingService."""

import pytest


class TestEmbeddingServiceInit:
    """Tests for EmbeddingService initialization."""

    def test_embedding_service_can_be_instantiated(self):
        """Test that EmbeddingService can be created."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        assert service is not None

    def test_embedding_service_model_not_loaded_on_init(self):
        """Test that model is not loaded until first use (lazy loading)."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        # Access internal state - model should be None until used
        assert service._model is None

    def test_embedding_service_default_model_name(self):
        """Test that default model name is all-MiniLM-L6-v2."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        assert service.model_name == "all-MiniLM-L6-v2"

    def test_embedding_service_custom_model_name(self):
        """Test that custom model name can be provided."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService(model_name="custom-model")
        assert service.model_name == "custom-model"
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_embedding.py -v
```

Expected: `ModuleNotFoundError: No module named 'lorekeeper_mcp.cache.embedding'`

**Step 3: Create minimal EmbeddingService class**

Create `src/lorekeeper_mcp/cache/embedding.py`:

```python
"""Embedding service for generating text embeddings using sentence-transformers.

This module provides the EmbeddingService class that generates 384-dimensional
embedding vectors for semantic search. The model is loaded lazily on first use
to avoid startup delays when the cache is not needed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Default embedding model - lightweight, fast, 384 dimensions
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers.

    Uses lazy model loading to avoid ~2s startup delay when cache is not needed.
    The model is loaded on first encode() or encode_batch() call.

    Attributes:
        model_name: Name of the sentence-transformers model to use.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        """Initialize EmbeddingService with model name.

        Args:
            model_name: Name of sentence-transformers model. Defaults to
                all-MiniLM-L6-v2 which produces 384-dimensional vectors.
        """
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
```

**Step 4: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_embedding.py -v
```

Expected: All 4 tests pass.

**Step 5: Write test for encode method**

Add to `tests/test_cache/test_embedding.py`:

```python
class TestEmbeddingServiceEncode:
    """Tests for EmbeddingService.encode method."""

    def test_encode_returns_list_of_floats(self):
        """Test that encode returns a list of floats."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        result = service.encode("test text")

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_encode_returns_384_dimensions(self):
        """Test that encode returns 384-dimensional vector."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        result = service.encode("test text")

        assert len(result) == 384

    def test_encode_loads_model_on_first_call(self):
        """Test that model is loaded on first encode call."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        assert service._model is None

        service.encode("test text")

        assert service._model is not None

    def test_encode_reuses_loaded_model(self):
        """Test that subsequent encode calls reuse the same model."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        service.encode("first call")
        model_after_first = service._model

        service.encode("second call")
        model_after_second = service._model

        assert model_after_first is model_after_second

    def test_encode_different_texts_produce_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        embedding1 = service.encode("fireball spell")
        embedding2 = service.encode("healing potion")

        # Embeddings should be different (not exactly equal)
        assert embedding1 != embedding2

    def test_encode_empty_string(self):
        """Test that encode handles empty string without error."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        result = service.encode("")

        assert isinstance(result, list)
        assert len(result) == 384
```

**Step 6: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_embedding.py::TestEmbeddingServiceEncode -v
```

Expected: `AttributeError: 'EmbeddingService' object has no attribute 'encode'`

**Step 7: Implement encode method**

Add to `src/lorekeeper_mcp/cache/embedding.py`:

```python
    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load and return the embedding model.

        Returns:
            Loaded SentenceTransformer model instance.
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        return self._model

    def encode(self, text: str) -> list[float]:
        """Encode single text to embedding vector.

        Args:
            text: Text to encode.

        Returns:
            List of floats representing the 384-dimensional embedding.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
```

**Step 8: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_embedding.py::TestEmbeddingServiceEncode -v
```

Expected: All 6 tests pass. Note: First run will download the model (~80MB).

**Step 9: Write test for encode_batch method**

Add to `tests/test_cache/test_embedding.py`:

```python
class TestEmbeddingServiceEncodeBatch:
    """Tests for EmbeddingService.encode_batch method."""

    def test_encode_batch_returns_list_of_embeddings(self):
        """Test that encode_batch returns list of embedding lists."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        texts = ["fireball", "ice storm", "lightning bolt"]
        result = service.encode_batch(texts)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(emb, list) for emb in result)
        assert all(len(emb) == 384 for emb in result)

    def test_encode_batch_empty_list(self):
        """Test that encode_batch handles empty list."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        result = service.encode_batch([])

        assert result == []

    def test_encode_batch_single_item(self):
        """Test that encode_batch handles single item list."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        result = service.encode_batch(["single text"])

        assert len(result) == 1
        assert len(result[0]) == 384

    def test_encode_batch_matches_individual_encode(self):
        """Test that batch encoding produces same results as individual encoding."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        texts = ["fireball", "ice storm"]

        batch_result = service.encode_batch(texts)
        individual_results = [service.encode(t) for t in texts]

        # Results should be very close (floating point comparison)
        for batch_emb, ind_emb in zip(batch_result, individual_results):
            for b, i in zip(batch_emb, ind_emb):
                assert abs(b - i) < 1e-6
```

**Step 10: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_embedding.py::TestEmbeddingServiceEncodeBatch -v
```

Expected: `AttributeError: 'EmbeddingService' object has no attribute 'encode_batch'`

**Step 11: Implement encode_batch method**

Add to `src/lorekeeper_mcp/cache/embedding.py`:

```python
    def encode_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Encode multiple texts efficiently in batches.

        Args:
            texts: List of texts to encode.
            batch_size: Number of texts to encode per batch. Defaults to 32.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        return embeddings.tolist()
```

**Step 12: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_embedding.py::TestEmbeddingServiceEncodeBatch -v
```

Expected: All 4 tests pass.

**Step 13: Write test for get_searchable_text method**

Add to `tests/test_cache/test_embedding.py`:

```python
class TestEmbeddingServiceGetSearchableText:
    """Tests for EmbeddingService.get_searchable_text method."""

    def test_get_searchable_text_spell(self):
        """Test searchable text extraction for spells."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Fireball",
            "desc": "A bright streak flashes from your pointing finger.",
            "higher_level": "When cast at 4th level, damage increases.",
        }

        result = service.get_searchable_text(entity, "spells")

        assert "Fireball" in result
        assert "bright streak flashes" in result
        assert "4th level" in result

    def test_get_searchable_text_creature(self):
        """Test searchable text extraction for creatures."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Ancient Red Dragon",
            "desc": "A legendary creature of immense power.",
            "type": "dragon",
            "actions": [
                {"name": "Multiattack"},
                {"name": "Fire Breath"},
            ],
            "special_abilities": [
                {"name": "Legendary Resistance"},
            ],
        }

        result = service.get_searchable_text(entity, "creatures")

        assert "Ancient Red Dragon" in result
        assert "legendary creature" in result
        assert "dragon" in result
        assert "Multiattack" in result
        assert "Fire Breath" in result
        assert "Legendary Resistance" in result

    def test_get_searchable_text_equipment(self):
        """Test searchable text extraction for equipment."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Longsword",
            "desc": "A versatile slashing weapon.",
            "type": "Martial Melee Weapon",
            "properties": ["Versatile"],
        }

        result = service.get_searchable_text(entity, "equipment")

        assert "Longsword" in result
        assert "versatile slashing" in result
        assert "Martial Melee Weapon" in result
        assert "Versatile" in result

    def test_get_searchable_text_character_option(self):
        """Test searchable text extraction for character options."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Fighter",
            "desc": "A master of martial combat.",
        }

        # Character options include classes, races, backgrounds, feats
        result = service.get_searchable_text(entity, "classes")

        assert "Fighter" in result
        assert "martial combat" in result

    def test_get_searchable_text_rules(self):
        """Test searchable text extraction for rules."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Conditions",
            "desc": "Conditions alter a creature's capabilities.",
            "content": "Blinded: A blinded creature can't see.",
        }

        result = service.get_searchable_text(entity, "rules")

        assert "Conditions" in result
        assert "alter a creature" in result
        assert "blinded creature" in result.lower()

    def test_get_searchable_text_minimal_entity(self):
        """Test searchable text with only name field."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {"name": "Unknown Item"}

        result = service.get_searchable_text(entity, "equipment")

        assert result == "Unknown Item"

    def test_get_searchable_text_empty_fields_skipped(self):
        """Test that empty/None fields are skipped."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Test Spell",
            "desc": None,
            "higher_level": "",
        }

        result = service.get_searchable_text(entity, "spells")

        # Should only contain name, no extra whitespace from None/empty
        assert result.strip() == "Test Spell"

    def test_get_searchable_text_unknown_entity_type(self):
        """Test fallback for unknown entity types."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Custom Entity",
            "desc": "Some description.",
        }

        result = service.get_searchable_text(entity, "unknown_type")

        # Should fall back to name + desc
        assert "Custom Entity" in result
        assert "Some description" in result
```

**Step 14: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_embedding.py::TestEmbeddingServiceGetSearchableText -v
```

Expected: `AttributeError: 'EmbeddingService' object has no attribute 'get_searchable_text'`

**Step 15: Implement get_searchable_text method**

Add to `src/lorekeeper_mcp/cache/embedding.py`:

```python
    def get_searchable_text(self, entity: dict[str, Any], entity_type: str) -> str:
        """Extract searchable text from entity for embedding generation.

        Extracts entity-type-specific text fields and concatenates them
        for semantic embedding. Different entity types have different
        relevant fields for search.

        Args:
            entity: Entity dictionary with fields to extract.
            entity_type: Type of entity (spells, creatures, equipment, etc.)

        Returns:
            Concatenated searchable text string.
        """
        text_parts: list[str] = []

        # Always include name
        name = entity.get("name")
        if name:
            text_parts.append(str(name))

        if entity_type == "spells":
            self._extract_spell_text(entity, text_parts)
        elif entity_type in ("creatures", "monsters"):
            self._extract_creature_text(entity, text_parts)
        elif entity_type in ("equipment", "weapons", "armor", "magicitems", "items"):
            self._extract_equipment_text(entity, text_parts)
        elif entity_type in ("rules", "rule_sections", "conditions"):
            self._extract_rule_text(entity, text_parts)
        else:
            # Default: include description
            desc = entity.get("desc")
            if desc:
                text_parts.append(str(desc))

        return " ".join(filter(None, text_parts))

    def _extract_spell_text(
        self, entity: dict[str, Any], text_parts: list[str]
    ) -> None:
        """Extract spell-specific text fields."""
        desc = entity.get("desc")
        if desc:
            text_parts.append(str(desc))

        higher_level = entity.get("higher_level")
        if higher_level:
            text_parts.append(str(higher_level))

    def _extract_creature_text(
        self, entity: dict[str, Any], text_parts: list[str]
    ) -> None:
        """Extract creature-specific text fields."""
        desc = entity.get("desc")
        if desc:
            text_parts.append(str(desc))

        creature_type = entity.get("type")
        if creature_type:
            text_parts.append(str(creature_type))

        # Extract action names
        actions = entity.get("actions", [])
        if actions:
            action_names = [a.get("name", "") for a in actions if isinstance(a, dict)]
            text_parts.extend(filter(None, action_names))

        # Extract special ability names
        abilities = entity.get("special_abilities", [])
        if abilities:
            ability_names = [a.get("name", "") for a in abilities if isinstance(a, dict)]
            text_parts.extend(filter(None, ability_names))

    def _extract_equipment_text(
        self, entity: dict[str, Any], text_parts: list[str]
    ) -> None:
        """Extract equipment-specific text fields."""
        desc = entity.get("desc")
        if desc:
            text_parts.append(str(desc))

        item_type = entity.get("type")
        if item_type:
            text_parts.append(str(item_type))

        properties = entity.get("properties", [])
        if properties:
            if isinstance(properties, list):
                text_parts.extend(str(p) for p in properties if p)

    def _extract_rule_text(
        self, entity: dict[str, Any], text_parts: list[str]
    ) -> None:
        """Extract rule-specific text fields."""
        desc = entity.get("desc")
        if desc:
            text_parts.append(str(desc))

        content = entity.get("content")
        if content:
            text_parts.append(str(content))
```

Also add the import at the top:

```python
from typing import TYPE_CHECKING, Any
```

**Step 16: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_embedding.py::TestEmbeddingServiceGetSearchableText -v
```

Expected: All 8 tests pass.

**Step 17: Run all embedding tests**

```bash
uv run pytest tests/test_cache/test_embedding.py -v
```

Expected: All tests pass (should be ~18 tests).

**Step 18: Run linting and type checking**

```bash
just lint && just type-check
```

Expected: No errors. Fix any issues that arise.

**Step 19: Commit**

```bash
git add src/lorekeeper_mcp/cache/embedding.py tests/test_cache/test_embedding.py
git commit -m "feat(cache): add EmbeddingService with lazy model loading"
```

---

### Task 1.3: MilvusCache Class Implementation

**Files:**
- Create: `src/lorekeeper_mcp/cache/milvus.py`
- Create: `tests/test_cache/test_milvus.py`

#### Step 1: Write test for MilvusCache initialization

Create `tests/test_cache/test_milvus.py`:

```python
"""Tests for MilvusCache implementation."""

import pytest
from pathlib import Path


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
        from lorekeeper_mcp.cache.milvus import MilvusCache
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        assert isinstance(cache._embedding_service, EmbeddingService)
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheInit -v
```

Expected: `ModuleNotFoundError: No module named 'lorekeeper_mcp.cache.milvus'`

**Step 3: Create minimal MilvusCache class**

Create `src/lorekeeper_mcp/cache/milvus.py`:

```python
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
from typing import TYPE_CHECKING, Any

from lorekeeper_mcp.cache.embedding import EmbeddingService

if TYPE_CHECKING:
    from pymilvus import MilvusClient

logger = logging.getLogger(__name__)


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
        self.db_path = Path(db_path).expanduser()
        self._client: MilvusClient | None = None
        self._embedding_service = EmbeddingService()
```

**Step 4: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheInit -v
```

Expected: All 5 tests pass.

**Step 5: Write test for client property (lazy initialization)**

Add to `tests/test_cache/test_milvus.py`:

```python
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
```

**Step 6: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheClient -v
```

Expected: `AttributeError: 'MilvusCache' object has no attribute 'client'`

**Step 7: Implement client property**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
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
```

**Step 8: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheClient -v
```

Expected: All 4 tests pass.

**Step 9: Write test for close method**

Add to `tests/test_cache/test_milvus.py`:

```python
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
```

**Step 10: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheClose -v
```

Expected: `AttributeError: 'MilvusCache' object has no attribute 'close'`

**Step 11: Implement close method**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
    def close(self) -> None:
        """Close the Milvus client connection.

        Safe to call multiple times or when client was never initialized.
        """
        if self._client is not None:
            logger.info("Closing Milvus Lite client")
            self._client.close()
            self._client = None
```

**Step 12: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheClose -v
```

Expected: All 3 tests pass.

**Step 13: Write test for context manager**

Add to `tests/test_cache/test_milvus.py`:

```python
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
```

**Step 14: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheContextManager -v
```

Expected: `TypeError: 'MilvusCache' object does not support the asynchronous context manager protocol`

**Step 15: Implement context manager**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
    async def __aenter__(self) -> "MilvusCache":
        """Enter async context manager.

        Returns:
            This MilvusCache instance.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager, closing the client.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        self.close()
```

**Step 16: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheContextManager -v
```

Expected: All 3 tests pass.

**Step 17: Write test for collection schema definitions**

Add to `tests/test_cache/test_milvus.py`:

```python
class TestMilvusCacheCollectionSchemas:
    """Tests for MilvusCache collection schema definitions."""

    def test_collection_schemas_defined(self, tmp_path: Path):
        """Test that COLLECTION_SCHEMAS constant is defined."""
        from lorekeeper_mcp.cache.milvus import COLLECTION_SCHEMAS

        assert isinstance(COLLECTION_SCHEMAS, dict)
        assert len(COLLECTION_SCHEMAS) > 0

    def test_spells_collection_schema(self, tmp_path: Path):
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

    def test_creatures_collection_schema(self, tmp_path: Path):
        """Test creatures collection has required indexed fields."""
        from lorekeeper_mcp.cache.milvus import COLLECTION_SCHEMAS

        assert "creatures" in COLLECTION_SCHEMAS
        schema = COLLECTION_SCHEMAS["creatures"]

        # Should have challenge_rating, type, size
        field_names = {f["name"] for f in schema["indexed_fields"]}
        assert "challenge_rating" in field_names
        assert "type" in field_names
        assert "size" in field_names

    def test_all_collections_have_document_field(self, tmp_path: Path):
        """Test all collections have document indexed field."""
        from lorekeeper_mcp.cache.milvus import COLLECTION_SCHEMAS

        for name, schema in COLLECTION_SCHEMAS.items():
            field_names = {f["name"] for f in schema["indexed_fields"]}
            assert "document" in field_names, f"{name} missing document field"
```

**Step 18: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheCollectionSchemas -v
```

Expected: `ImportError: cannot import name 'COLLECTION_SCHEMAS' from 'lorekeeper_mcp.cache.milvus'`

**Step 19: Define collection schemas**

Add to `src/lorekeeper_mcp/cache/milvus.py` (at module level, before the class):

```python
from lorekeeper_mcp.cache.embedding import EMBEDDING_DIMENSION

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
```

**Step 20: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheCollectionSchemas -v
```

Expected: All 4 tests pass.

**Step 21: Write test for _ensure_collection method**

Add to `tests/test_cache/test_milvus.py`:

```python
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
```

**Step 22: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheEnsureCollection -v
```

Expected: `AttributeError: 'MilvusCache' object has no attribute '_ensure_collection'`

**Step 23: Implement _ensure_collection method**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
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
```

**Step 24: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheEnsureCollection -v
```

Expected: All 4 tests pass.

**Step 25: Run all MilvusCache tests**

```bash
uv run pytest tests/test_cache/test_milvus.py -v
```

Expected: All tests pass (should be ~19 tests).

**Step 26: Run linting and type checking**

```bash
just lint && just type-check
```

Expected: No errors. Fix any issues that arise.

**Step 27: Update cache module exports**

Edit `src/lorekeeper_mcp/cache/__init__.py`:

```python
"""Caching module for API responses."""

from lorekeeper_mcp.cache.embedding import EmbeddingService
from lorekeeper_mcp.cache.milvus import MilvusCache
from lorekeeper_mcp.cache.protocol import CacheProtocol
from lorekeeper_mcp.cache.sqlite import SQLiteCache

__all__ = ["CacheProtocol", "EmbeddingService", "MilvusCache", "SQLiteCache"]
```

**Step 28: Run full test suite for cache module**

```bash
uv run pytest tests/test_cache/ -v
```

Expected: All tests pass.

**Step 29: Run quality checks**

```bash
just check
```

Expected: All checks pass.

**Step 30: Commit**

```bash
git add src/lorekeeper_mcp/cache/milvus.py src/lorekeeper_mcp/cache/__init__.py tests/test_cache/test_milvus.py
git commit -m "feat(cache): add MilvusCache class with lazy initialization and collection schemas"
```

---

## Task 1 Complete

At this point, Task 1 (Core Infrastructure) is complete:

- ✅ 1.1 Dependencies: `pymilvus>=2.4.0` and `sentence-transformers>=2.2.0` added
- ✅ 1.2 EmbeddingService: Implemented with lazy loading, encode(), encode_batch(), get_searchable_text()
- ✅ 1.3 MilvusCache: Implemented with lazy client initialization, context manager, collection schemas

The cache module now exports:
- `CacheProtocol` - Interface for cache implementations
- `SQLiteCache` - Existing SQLite implementation
- `MilvusCache` - New Milvus Lite implementation (partial - storage/retrieval methods in Task 2)
- `EmbeddingService` - Embedding generation service

Next tasks will implement:
- Task 2: CacheProtocol Implementation (get_entities, store_entities, semantic_search)
- Task 3: Protocol and Factory Updates
- Task 4: Configuration Updates

---

## Task 2: CacheProtocol Implementation

### Task 2.1: get_entities Method

**Files:**
- Modify: `src/lorekeeper_mcp/cache/milvus.py`
- Modify: `tests/test_cache/test_milvus.py`

#### Step 1: Write test for _build_filter_expression helper

Add to `tests/test_cache/test_milvus.py`:

```python
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
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression -v
```

Expected: `AttributeError: 'MilvusCache' object has no attribute '_build_filter_expression'`

**Step 3: Implement _build_filter_expression method**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
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
            elif isinstance(value, (int, float)):
                expressions.append(f"{field} == {value}")
            elif isinstance(value, list):
                # Handle list of values (IN clause)
                if all(isinstance(v, str) for v in value):
                    quoted = [f'"{v}"' for v in value]
                    expressions.append(f"{field} in [{', '.join(quoted)}]")
                else:
                    expressions.append(f"{field} in {value}")

        return " and ".join(expressions)
```

**Step 4: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression -v
```

Expected: All 8 tests pass.

#### Step 5: Write test for get_entities method

Add to `tests/test_cache/test_milvus.py`:

```python
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
            {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation", "document": "srd"},
            {"slug": "ice-storm", "name": "Ice Storm", "level": 4, "school": "Evocation", "document": "srd"},
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
            {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation", "document": "srd"},
            {"slug": "ice-storm", "name": "Ice Storm", "level": 4, "school": "Evocation", "document": "srd"},
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
```

**Step 6: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheGetEntities -v
```

Expected: `AttributeError: 'MilvusCache' object has no attribute 'get_entities'`

**Step 7: Implement get_entities method**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
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
                results = self.client.query(
                    collection_name=entity_type,
                    filter="",
                    output_fields=["*"],
                )
        except Exception as e:
            logger.warning("Query failed for %s: %s", entity_type, e)
            return []

        # Convert results to dicts, removing embedding field
        entities = []
        for result in results:
            entity = dict(result)
            entity.pop("embedding", None)  # Don't return embeddings
            entities.append(entity)

        return entities
```

**Step 8: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheGetEntities -v
```

Expected: Tests will fail because store_entities is not yet implemented. This is expected - we'll implement store_entities next.

**Step 9: Commit filter expression builder**

```bash
git add src/lorekeeper_mcp/cache/milvus.py tests/test_cache/test_milvus.py
git commit -m "feat(cache): add filter expression builder for MilvusCache"
```

---

### Task 2.2: store_entities Method

**Files:**
- Modify: `src/lorekeeper_mcp/cache/milvus.py`
- Modify: `tests/test_cache/test_milvus.py`

#### Step 1: Write test for store_entities method

Add to `tests/test_cache/test_milvus.py`:

```python
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
        """Test storing empty list returns 0."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        count = await cache.store_entities([], "spells")
        assert count == 0

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
            {"slug": "fireball", "name": "Fireball", "desc": "A bright streak of fire", "document": "srd"},
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
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheStoreEntities -v
```

Expected: `AttributeError: 'MilvusCache' object has no attribute 'store_entities'`

**Step 3: Implement store_entities method**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
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
            return 0

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

        # Prepare entities with embeddings
        for entity, embedding in zip(entities, embeddings):
            prepared = {
                "slug": entity.get("slug", ""),
                "name": entity.get("name", ""),
                "embedding": embedding,
                "source_api": entity.get("source_api", ""),
            }

            # Add entity-specific indexed fields based on collection schema
            schema_def = COLLECTION_SCHEMAS.get(entity_type, DEFAULT_COLLECTION_SCHEMA)
            for field_def in schema_def["indexed_fields"]:
                field_name = field_def["name"]
                if field_name in entity:
                    prepared[field_name] = entity[field_name]
                elif field_name == "document":
                    # Handle document field specially
                    prepared["document"] = entity.get("document", entity.get("document__slug", ""))

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
```

**Step 4: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheStoreEntities -v
```

Expected: All 5 tests pass.

**Step 5: Run get_entities tests again (now that store_entities works)**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheGetEntities -v
```

Expected: All tests pass.

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/milvus.py tests/test_cache/test_milvus.py
git commit -m "feat(cache): add store_entities and get_entities to MilvusCache"
```

---

### Task 2.3: Semantic Search Method

**Files:**
- Modify: `src/lorekeeper_mcp/cache/milvus.py`
- Modify: `tests/test_cache/test_milvus.py`

#### Step 1: Write test for semantic_search method

Add to `tests/test_cache/test_milvus.py`:

```python
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
            {"slug": "fireball", "name": "Fireball", "desc": "A bright streak flashes and explodes into fire", "document": "srd"},
            {"slug": "fire-shield", "name": "Fire Shield", "desc": "Flames surround your body protecting you", "document": "srd"},
            {"slug": "ice-storm", "name": "Ice Storm", "desc": "Hail of ice and snow damages creatures", "document": "srd"},
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
            {"slug": f"spell-{i}", "name": f"Spell {i}", "desc": "A magical spell", "document": "srd"}
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
            {"slug": "fireball", "name": "Fireball", "desc": "Fire explosion", "level": 3, "document": "srd"},
            {"slug": "firebolt", "name": "Fire Bolt", "desc": "Fire attack cantrip", "level": 0, "document": "srd"},
            {"slug": "fire-storm", "name": "Fire Storm", "desc": "Massive fire", "level": 7, "document": "srd"},
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
            {"slug": "custom-fire", "name": "Custom Fire", "desc": "Fire attack", "document": "homebrew"},
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
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheSemanticSearch -v
```

Expected: `AttributeError: 'MilvusCache' object has no attribute 'semantic_search'`

**Step 3: Implement semantic_search method**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
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
                filter=filter_expr if filter_expr else None,
                limit=limit,
                output_fields=["*"],
                search_params=search_params,
            )

            # Extract entities from search results
            entities = []
            if results and len(results) > 0:
                for hit in results[0]:
                    entity = dict(hit["entity"])
                    entity.pop("embedding", None)  # Don't return embeddings
                    entity["_score"] = hit["distance"]  # Include similarity score
                    entities.append(entity)

            return entities

        except Exception as e:
            logger.warning("Semantic search failed for %s: %s, falling back to structured search", entity_type, e)
            return await self.get_entities(entity_type, document=document, **filters)
```

**Step 4: Run test to see it pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheSemanticSearch -v
```

Expected: All 6 tests pass.

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/cache/milvus.py tests/test_cache/test_milvus.py
git commit -m "feat(cache): add semantic_search method with hybrid search support"
```

---

### Task 2.4: Additional Cache Methods

**Files:**
- Modify: `src/lorekeeper_mcp/cache/milvus.py`
- Modify: `tests/test_cache/test_milvus.py`

#### Step 1: Write tests for additional cache methods

Add to `tests/test_cache/test_milvus.py`:

```python
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
```

**Step 2: Run tests to see them fail**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheAdditionalMethods -v
```

Expected: Tests fail due to missing methods.

**Step 3: Implement additional methods**

Add to `src/lorekeeper_mcp/cache/milvus.py`:

```python
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
            return stats.get("row_count", 0)
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
                logger.debug("Failed to query %s for document %s: %s", collection_name, document_key, e)

        return metadata

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get overall cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        collections = self.client.list_collections()
        total_entities = 0
        collection_stats = {}

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
```

**Step 4: Run tests to see them pass**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheAdditionalMethods -v
```

Expected: All 5 tests pass.

**Step 5: Run all MilvusCache tests**

```bash
uv run pytest tests/test_cache/test_milvus.py -v
```

Expected: All tests pass.

**Step 6: Run quality checks**

```bash
just check
```

Expected: All checks pass.

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/cache/milvus.py tests/test_cache/test_milvus.py
git commit -m "feat(cache): add get_entity_count, get_available_documents, get_document_metadata, get_cache_stats to MilvusCache"
```

---

## Task 2 Complete

At this point, Task 2 (CacheProtocol Implementation) is complete:

- ✅ 2.1 get_entities: Filter expression builder, document parameter support
- ✅ 2.2 store_entities: Embedding generation, upsert behavior
- ✅ 2.3 semantic_search: Hybrid search with filters, fallback on errors
- ✅ 2.4 Additional methods: get_entity_count, get_available_documents, get_document_metadata, get_cache_stats

The MilvusCache now fully implements CacheProtocol plus semantic search capabilities.

---

## Task 3: Protocol and Factory Updates

### Task 3.1: CacheProtocol Updates

**Files:**
- Modify: `src/lorekeeper_mcp/cache/protocol.py`
- Modify: `src/lorekeeper_mcp/cache/sqlite.py`
- Modify: `tests/test_cache/test_protocol.py`

#### Step 1: Write test for semantic_search in CacheProtocol

Add to `tests/test_cache/test_protocol.py`:

```python
class TestCacheProtocolSemanticSearch:
    """Tests for semantic_search method in CacheProtocol."""

    def test_protocol_has_semantic_search_method(self):
        """Test that CacheProtocol defines semantic_search method."""
        from lorekeeper_mcp.cache.protocol import CacheProtocol
        import inspect

        # Check that semantic_search is defined in protocol
        assert hasattr(CacheProtocol, "semantic_search")

        # Verify it's a method with correct signature
        sig = inspect.signature(CacheProtocol.semantic_search)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "entity_type" in params
        assert "query" in params
        assert "limit" in params

    def test_milvus_cache_conforms_to_protocol_with_semantic_search(self, tmp_path):
        """Test that MilvusCache conforms to updated CacheProtocol."""
        from lorekeeper_mcp.cache.protocol import CacheProtocol
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Check it has all protocol methods
        assert hasattr(cache, "get_entities")
        assert hasattr(cache, "store_entities")
        assert hasattr(cache, "semantic_search")
        assert callable(cache.get_entities)
        assert callable(cache.store_entities)
        assert callable(cache.semantic_search)

    def test_sqlite_cache_has_semantic_search_stub(self, tmp_path):
        """Test that SQLiteCache has semantic_search stub that raises NotImplementedError."""
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        db_path = tmp_path / "test_sqlite.db"
        cache = SQLiteCache(str(db_path))

        assert hasattr(cache, "semantic_search")
        assert callable(cache.semantic_search)
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_protocol.py::TestCacheProtocolSemanticSearch -v
```

Expected: `AttributeError: type object 'CacheProtocol' has no attribute 'semantic_search'`

**Step 3: Update CacheProtocol with semantic_search method signature**

Edit `src/lorekeeper_mcp/cache/protocol.py` to add the semantic_search method after store_entities:

```python
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
```

**Step 4: Run test to see partial pass**

```bash
uv run pytest tests/test_cache/test_protocol.py::TestCacheProtocolSemanticSearch::test_protocol_has_semantic_search_method -v
```

Expected: Test passes.

**Step 5: Write test for SQLiteCache semantic_search stub**

Add to `tests/test_cache/test_protocol.py`:

```python
class TestSQLiteCacheSemanticSearchStub:
    """Tests for SQLiteCache semantic_search stub."""

    @pytest.mark.asyncio
    async def test_sqlite_cache_semantic_search_raises_not_implemented(self, tmp_path):
        """Test that SQLiteCache.semantic_search raises NotImplementedError."""
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        db_path = tmp_path / "test_sqlite.db"
        cache = SQLiteCache(str(db_path))

        with pytest.raises(NotImplementedError) as exc_info:
            await cache.semantic_search("spells", "fire damage")

        assert "SQLiteCache does not support semantic search" in str(exc_info.value)
```

**Step 6: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_protocol.py::TestSQLiteCacheSemanticSearchStub -v
```

Expected: `AttributeError: 'SQLiteCache' object has no attribute 'semantic_search'`

**Step 7: Add semantic_search stub to SQLiteCache**

Edit `src/lorekeeper_mcp/cache/sqlite.py` to add the semantic_search method:

```python
"""SQLite cache implementation conforming to CacheProtocol."""

from typing import Any

from lorekeeper_mcp.cache.db import bulk_cache_entities, query_cached_entities


class SQLiteCache:
    """SQLite-backed cache implementation conforming to CacheProtocol.

    Wraps existing database functions to provide a cache abstraction layer
    for entity storage and retrieval with filtering support.

    Note: This implementation does not support semantic search. Use MilvusCache
    for semantic/vector search capabilities.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize SQLiteCache with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path

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
        # Add document to filters if provided
        if document is not None:
            filters["document"] = document

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

    async def semantic_search(
        self,
        entity_type: str,
        query: str,
        limit: int = 20,
        document: str | list[str] | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Perform semantic search using vector similarity.

        SQLiteCache does not support semantic search. Use MilvusCache for
        semantic/vector search capabilities.

        Args:
            entity_type: Type of entities to search.
            query: Natural language search query.
            limit: Maximum number of results to return.
            document: Optional document filter.
            **filters: Optional keyword filters.

        Raises:
            NotImplementedError: Always raised as SQLite does not support
                vector search.
        """
        raise NotImplementedError(
            "SQLiteCache does not support semantic search. "
            "Use MilvusCache for semantic/vector search capabilities."
        )
```

**Step 8: Run tests to see them pass**

```bash
uv run pytest tests/test_cache/test_protocol.py -v
```

Expected: All tests pass.

**Step 9: Run quality checks**

```bash
just lint && just type-check
```

Expected: No errors.

**Step 10: Commit**

```bash
git add src/lorekeeper_mcp/cache/protocol.py src/lorekeeper_mcp/cache/sqlite.py tests/test_cache/test_protocol.py
git commit -m "feat(cache): add semantic_search to CacheProtocol with SQLiteCache stub"
```

---

### Task 3.2: Cache Factory

**Files:**
- Create: `src/lorekeeper_mcp/cache/factory.py`
- Create: `tests/test_cache/test_factory.py`

#### Step 1: Write test for cache factory

Create `tests/test_cache/test_factory.py`:

```python
"""Tests for cache factory."""

import pytest
from pathlib import Path


class TestCreateCache:
    """Tests for create_cache factory function."""

    def test_create_cache_milvus_backend(self, tmp_path: Path):
        """Test creating cache with milvus backend."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = create_cache(backend="milvus", db_path=str(db_path))

        assert isinstance(cache, MilvusCache)
        assert cache.db_path == db_path

    def test_create_cache_sqlite_backend(self, tmp_path: Path):
        """Test creating cache with sqlite backend."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        db_path = tmp_path / "test_sqlite.db"
        cache = create_cache(backend="sqlite", db_path=str(db_path))

        assert isinstance(cache, SQLiteCache)
        assert cache.db_path == str(db_path)

    def test_create_cache_invalid_backend(self, tmp_path: Path):
        """Test creating cache with invalid backend raises ValueError."""
        from lorekeeper_mcp.cache.factory import create_cache

        db_path = tmp_path / "test.db"
        with pytest.raises(ValueError) as exc_info:
            create_cache(backend="invalid", db_path=str(db_path))

        assert "Unknown cache backend" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_create_cache_default_backend_is_milvus(self, tmp_path: Path):
        """Test that default backend is milvus."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test.db"
        cache = create_cache(db_path=str(db_path))

        assert isinstance(cache, MilvusCache)

    def test_create_cache_case_insensitive_backend(self, tmp_path: Path):
        """Test that backend parameter is case-insensitive."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.milvus import MilvusCache
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        db_path = tmp_path / "test.db"

        cache1 = create_cache(backend="MILVUS", db_path=str(db_path))
        assert isinstance(cache1, MilvusCache)

        cache2 = create_cache(backend="SQLite", db_path=str(tmp_path / "test2.db"))
        assert isinstance(cache2, SQLiteCache)


class TestGetCacheFromConfig:
    """Tests for get_cache_from_config function."""

    def test_get_cache_from_config_uses_env_backend(self, tmp_path: Path, monkeypatch):
        """Test that get_cache_from_config reads backend from environment."""
        from lorekeeper_mcp.cache.factory import get_cache_from_config
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "sqlite")
        monkeypatch.setenv("LOREKEEPER_SQLITE_DB_PATH", str(tmp_path / "cache.db"))

        cache = get_cache_from_config()

        assert isinstance(cache, SQLiteCache)

    def test_get_cache_from_config_milvus_default(self, tmp_path: Path, monkeypatch):
        """Test that get_cache_from_config defaults to milvus."""
        from lorekeeper_mcp.cache.factory import get_cache_from_config
        from lorekeeper_mcp.cache.milvus import MilvusCache

        # Clear any existing env vars
        monkeypatch.delenv("LOREKEEPER_CACHE_BACKEND", raising=False)
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(tmp_path / "milvus.db"))

        cache = get_cache_from_config()

        assert isinstance(cache, MilvusCache)

    def test_get_cache_from_config_uses_env_milvus_path(self, tmp_path: Path, monkeypatch):
        """Test that get_cache_from_config uses LOREKEEPER_MILVUS_DB_PATH."""
        from lorekeeper_mcp.cache.factory import get_cache_from_config
        from lorekeeper_mcp.cache.milvus import MilvusCache

        custom_path = tmp_path / "custom_milvus.db"
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(custom_path))

        cache = get_cache_from_config()

        assert isinstance(cache, MilvusCache)
        assert cache.db_path == custom_path
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_cache/test_factory.py -v
```

Expected: `ModuleNotFoundError: No module named 'lorekeeper_mcp.cache.factory'`

**Step 3: Create cache factory module**

Create `src/lorekeeper_mcp/cache/factory.py`:

```python
"""Cache factory for creating cache instances based on configuration.

This module provides factory functions for creating cache instances
based on backend configuration. Supports both SQLite (legacy) and
Milvus Lite (default) backends.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorekeeper_mcp.cache.protocol import CacheProtocol

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_MILVUS_DB_PATH = "~/.lorekeeper/milvus.db"
DEFAULT_SQLITE_DB_PATH = "~/.lorekeeper/cache.db"

# Default backend
DEFAULT_CACHE_BACKEND = "milvus"


def create_cache(
    backend: str = DEFAULT_CACHE_BACKEND,
    db_path: str | None = None,
) -> "CacheProtocol":
    """Create a cache instance based on backend type.

    Args:
        backend: Cache backend type ("milvus" or "sqlite"). Defaults to "milvus".
        db_path: Path to database file. If not provided, uses default path
            for the selected backend.

    Returns:
        Cache instance conforming to CacheProtocol.

    Raises:
        ValueError: If backend type is not recognized.
    """
    backend_lower = backend.lower()

    if backend_lower == "milvus":
        from lorekeeper_mcp.cache.milvus import MilvusCache

        if db_path is None:
            db_path = str(Path(DEFAULT_MILVUS_DB_PATH).expanduser())
        logger.info("Creating MilvusCache with db_path: %s", db_path)
        return MilvusCache(db_path)

    elif backend_lower == "sqlite":
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        if db_path is None:
            db_path = str(Path(DEFAULT_SQLITE_DB_PATH).expanduser())
        logger.info("Creating SQLiteCache with db_path: %s", db_path)
        return SQLiteCache(db_path)

    else:
        raise ValueError(
            f"Unknown cache backend: '{backend}'. "
            f"Supported backends: 'milvus', 'sqlite'"
        )


def get_cache_from_config() -> "CacheProtocol":
    """Create a cache instance based on environment configuration.

    Reads configuration from environment variables:
    - LOREKEEPER_CACHE_BACKEND: Backend type ("milvus" or "sqlite")
    - LOREKEEPER_MILVUS_DB_PATH: Path for Milvus database (when backend=milvus)
    - LOREKEEPER_SQLITE_DB_PATH: Path for SQLite database (when backend=sqlite)

    Returns:
        Cache instance conforming to CacheProtocol.
    """
    backend = os.environ.get("LOREKEEPER_CACHE_BACKEND", DEFAULT_CACHE_BACKEND)

    if backend.lower() == "milvus":
        db_path = os.environ.get("LOREKEEPER_MILVUS_DB_PATH", DEFAULT_MILVUS_DB_PATH)
    else:
        db_path = os.environ.get("LOREKEEPER_SQLITE_DB_PATH", DEFAULT_SQLITE_DB_PATH)

    return create_cache(backend=backend, db_path=db_path)
```

**Step 4: Run tests to see them pass**

```bash
uv run pytest tests/test_cache/test_factory.py -v
```

Expected: All 8 tests pass.

**Step 5: Run quality checks**

```bash
just lint && just type-check
```

Expected: No errors.

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/factory.py tests/test_cache/test_factory.py
git commit -m "feat(cache): add cache factory with milvus and sqlite backend support"
```

---

### Task 3.3: Module Exports

**Files:**
- Modify: `src/lorekeeper_mcp/cache/__init__.py`
- Create: `tests/test_cache/test_init.py`

#### Step 1: Write test for module exports

Create `tests/test_cache/test_init.py`:

```python
"""Tests for cache module exports."""

import pytest


class TestCacheModuleExports:
    """Tests for cache module __all__ exports."""

    def test_cache_protocol_exported(self):
        """Test that CacheProtocol is exported from cache module."""
        from lorekeeper_mcp.cache import CacheProtocol

        assert CacheProtocol is not None

    def test_sqlite_cache_exported(self):
        """Test that SQLiteCache is exported from cache module."""
        from lorekeeper_mcp.cache import SQLiteCache

        assert SQLiteCache is not None

    def test_milvus_cache_exported(self):
        """Test that MilvusCache is exported from cache module."""
        from lorekeeper_mcp.cache import MilvusCache

        assert MilvusCache is not None

    def test_embedding_service_exported(self):
        """Test that EmbeddingService is exported from cache module."""
        from lorekeeper_mcp.cache import EmbeddingService

        assert EmbeddingService is not None

    def test_create_cache_exported(self):
        """Test that create_cache is exported from cache module."""
        from lorekeeper_mcp.cache import create_cache

        assert callable(create_cache)

    def test_get_cache_from_config_exported(self):
        """Test that get_cache_from_config is exported from cache module."""
        from lorekeeper_mcp.cache import get_cache_from_config

        assert callable(get_cache_from_config)

    def test_all_exports_are_defined(self):
        """Test that __all__ contains expected exports."""
        from lorekeeper_mcp import cache

        expected_exports = [
            "CacheProtocol",
            "SQLiteCache",
            "MilvusCache",
            "EmbeddingService",
            "create_cache",
            "get_cache_from_config",
        ]

        for export in expected_exports:
            assert export in cache.__all__, f"Missing export: {export}"

    def test_backward_compatibility_sqlite_cache(self):
        """Test that existing SQLiteCache import pattern still works."""
        from lorekeeper_mcp.cache import SQLiteCache

        # Verify class has expected methods
        assert hasattr(SQLiteCache, "get_entities")
        assert hasattr(SQLiteCache, "store_entities")
```

**Step 2: Run test to see partial failures**

```bash
uv run pytest tests/test_cache/test_init.py -v
```

Expected: Some tests fail because not all exports are defined yet.

**Step 3: Update cache module exports**

Edit `src/lorekeeper_mcp/cache/__init__.py`:

```python
"""Caching module for API responses.

This module provides cache implementations for storing and retrieving
D&D entity data. Supports multiple backends:

- MilvusCache: Default backend with semantic/vector search support
- SQLiteCache: Legacy backend with structured filtering only

Use the factory functions to create cache instances:

    from lorekeeper_mcp.cache import create_cache, get_cache_from_config

    # Create with explicit backend
    cache = create_cache(backend="milvus", db_path="~/.lorekeeper/milvus.db")

    # Create from environment configuration
    cache = get_cache_from_config()
"""

from lorekeeper_mcp.cache.embedding import EmbeddingService
from lorekeeper_mcp.cache.factory import create_cache, get_cache_from_config
from lorekeeper_mcp.cache.milvus import MilvusCache
from lorekeeper_mcp.cache.protocol import CacheProtocol
from lorekeeper_mcp.cache.sqlite import SQLiteCache

__all__ = [
    "CacheProtocol",
    "EmbeddingService",
    "MilvusCache",
    "SQLiteCache",
    "create_cache",
    "get_cache_from_config",
]
```

**Step 4: Run tests to see them pass**

```bash
uv run pytest tests/test_cache/test_init.py -v
```

Expected: All 8 tests pass.

**Step 5: Run full cache test suite**

```bash
uv run pytest tests/test_cache/ -v
```

Expected: All tests pass.

**Step 6: Run quality checks**

```bash
just check
```

Expected: All checks pass.

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/cache/__init__.py tests/test_cache/test_init.py
git commit -m "feat(cache): update module exports with MilvusCache, EmbeddingService, and factory functions"
```

---

## Task 3 Complete

At this point, Task 3 (Protocol and Factory Updates) is complete:

- ✅ 3.1 CacheProtocol Updates: Added semantic_search() method signature, SQLiteCache stub
- ✅ 3.2 Cache Factory: Created create_cache() and get_cache_from_config() functions
- ✅ 3.3 Module Exports: Updated __init__.py with all new exports

The cache module now provides:
- `CacheProtocol` - Interface with get_entities, store_entities, semantic_search
- `SQLiteCache` - Legacy backend (raises NotImplementedError for semantic_search)
- `MilvusCache` - New default backend with full semantic search support
- `EmbeddingService` - Embedding generation for semantic search
- `create_cache(backend, db_path)` - Factory function for explicit backend selection
- `get_cache_from_config()` - Factory function reading from environment variables

Next tasks will implement:
- Task 4: Configuration Updates (environment variables, config.py)
- Task 5: Repository Integration (semantic search in repositories)
- Task 6: Tool Updates (semantic_query parameter)

---

## Task 4: Configuration Updates

### Task 4.1: Config Changes

**Files:**
- Modify: `src/lorekeeper_mcp/config.py`
- Create: `tests/test_config_milvus.py`

#### Step 1: Write test for new config fields

Create `tests/test_config_milvus.py`:

```python
"""Tests for Milvus-related configuration settings."""

import pytest
from pathlib import Path


class TestCacheBackendConfig:
    """Tests for LOREKEEPER_CACHE_BACKEND configuration."""

    def test_cache_backend_default_is_milvus(self, monkeypatch):
        """Test that default cache backend is milvus."""
        # Clear any existing env var
        monkeypatch.delenv("LOREKEEPER_CACHE_BACKEND", raising=False)

        # Need to reimport to pick up env changes
        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        assert settings.cache_backend == "milvus"

    def test_cache_backend_from_env(self, monkeypatch):
        """Test that cache backend can be set from environment."""
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "sqlite")

        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        assert settings.cache_backend == "sqlite"

    def test_cache_backend_case_preserved(self, monkeypatch):
        """Test that cache backend value case is preserved."""
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "SQLite")

        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        # Value should be preserved as-is (factory handles case normalization)
        assert settings.cache_backend == "SQLite"


class TestMilvusDbPathConfig:
    """Tests for LOREKEEPER_MILVUS_DB_PATH configuration."""

    def test_milvus_db_path_default(self, monkeypatch):
        """Test that default Milvus DB path is ~/.lorekeeper/milvus.db."""
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)

        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        expected = Path("~/.lorekeeper/milvus.db").expanduser()
        assert settings.milvus_db_path == expected

    def test_milvus_db_path_from_env(self, tmp_path: Path, monkeypatch):
        """Test that Milvus DB path can be set from environment."""
        custom_path = tmp_path / "custom_milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(custom_path))

        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        assert settings.milvus_db_path == custom_path

    def test_milvus_db_path_expands_tilde(self, monkeypatch):
        """Test that tilde in path is expanded."""
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", "~/custom/milvus.db")

        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        # Should expand tilde to actual home directory
        assert "~" not in str(settings.milvus_db_path)
        assert settings.milvus_db_path.is_absolute()


class TestEmbeddingModelConfig:
    """Tests for LOREKEEPER_EMBEDDING_MODEL configuration."""

    def test_embedding_model_default(self, monkeypatch):
        """Test that default embedding model is all-MiniLM-L6-v2."""
        monkeypatch.delenv("LOREKEEPER_EMBEDDING_MODEL", raising=False)

        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        assert settings.embedding_model == "all-MiniLM-L6-v2"

    def test_embedding_model_from_env(self, monkeypatch):
        """Test that embedding model can be set from environment."""
        monkeypatch.setenv("LOREKEEPER_EMBEDDING_MODEL", "custom-model")

        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        assert settings.embedding_model == "custom-model"


class TestConfigIntegration:
    """Integration tests for configuration with cache factory."""

    def test_config_integrates_with_cache_factory(self, tmp_path: Path, monkeypatch):
        """Test that config values work with cache factory."""
        db_path = tmp_path / "integration_milvus.db"
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))

        import importlib
        import lorekeeper_mcp.config
        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings
        from lorekeeper_mcp.cache.factory import create_cache

        cache = create_cache(
            backend=settings.cache_backend,
            db_path=str(settings.milvus_db_path),
        )

        from lorekeeper_mcp.cache.milvus import MilvusCache
        assert isinstance(cache, MilvusCache)
        assert cache.db_path == db_path
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_config_milvus.py -v
```

Expected: `AttributeError: 'Settings' object has no attribute 'cache_backend'`

**Step 3: Update Settings class with new fields**

Edit `src/lorekeeper_mcp/config.py`:

```python
"""Configuration management using Pydantic Settings."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides.

    Configuration for LoreKeeper MCP including cache backend, database paths,
    and API settings. All settings can be overridden via environment variables
    with the LOREKEEPER_ prefix (handled automatically by pydantic-settings).

    Attributes:
        cache_backend: Cache backend type ("milvus" or "sqlite"). Defaults to "milvus".
        milvus_db_path: Path to Milvus Lite database file.
        embedding_model: Name of sentence-transformers model for embeddings.
        db_path: Legacy SQLite database path.
        cache_ttl_days: TTL for cached responses in days.
        error_cache_ttl_seconds: TTL for cached error responses in seconds.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        debug: Enable debug mode with verbose logging.
        open5e_base_url: Base URL for Open5e API.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="LOREKEEPER_",
    )

    # Cache backend configuration
    cache_backend: str = Field(default="milvus")
    milvus_db_path: Path = Field(default=Path("~/.lorekeeper/milvus.db"))
    embedding_model: str = Field(default="all-MiniLM-L6-v2")

    # Legacy SQLite configuration (for backward compatibility)
    db_path: Path = Field(default=Path("./data/cache.db"))

    # Cache TTL configuration
    cache_ttl_days: int = Field(default=7)
    error_cache_ttl_seconds: int = Field(default=300)

    # Logging configuration
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)

    # API configuration
    open5e_base_url: str = Field(default="https://api.open5e.com")

    @field_validator("milvus_db_path", mode="before")
    @classmethod
    def expand_milvus_path(cls, v: str | Path) -> Path:
        """Expand tilde in Milvus database path."""
        return Path(v).expanduser()

    @field_validator("db_path", mode="before")
    @classmethod
    def expand_db_path(cls, v: str | Path) -> Path:
        """Expand tilde in SQLite database path."""
        return Path(v).expanduser()


# Global settings instance
settings = Settings()
```

**Step 4: Run test to see it pass**

```bash
uv run pytest tests/test_config_milvus.py -v
```

Expected: All 9 tests pass.

**Step 5: Verify existing config tests still pass**

```bash
uv run pytest tests/test_config.py -v
```

Expected: All existing tests pass. If any fail due to env_prefix change, they need to be updated.

**Step 6: Update existing tests if needed**

If existing tests fail because of the new `env_prefix="LOREKEEPER_"`, update them to use the correct environment variable names. The existing settings were using unprefixed env vars, but with the new prefix, `DB_PATH` becomes `LOREKEEPER_DB_PATH`.

Check if `tests/test_config.py` needs updates:

```bash
uv run pytest tests/test_config.py -v 2>&1 | head -50
```

If tests fail, update the test file to use prefixed env vars (e.g., `LOREKEEPER_DB_PATH` instead of `DB_PATH`).

**Step 7: Run linting and type checking**

```bash
just lint && just type-check
```

Expected: No errors. Fix any issues that arise.

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/config.py tests/test_config_milvus.py
git commit -m "feat(config): add cache_backend, milvus_db_path, embedding_model settings"
```

---

### Task 4.2: Documentation

**Files:**
- Modify: `.env.example`
- Modify: `README.md`

#### Step 1: Update .env.example with new variables

Edit `.env.example`:

```bash
# =============================================================================
# LoreKeeper MCP Configuration
# =============================================================================
# All environment variables use the LOREKEEPER_ prefix.
# Copy this file to .env and customize as needed.

# =============================================================================
# Cache Backend Configuration
# =============================================================================

# Cache backend type: "milvus" (default) or "sqlite"
# Milvus Lite provides semantic/vector search capabilities
# SQLite is the legacy backend with structured filtering only
LOREKEEPER_CACHE_BACKEND=milvus

# Path to Milvus Lite database file (when using milvus backend)
# Supports ~ for home directory expansion
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db

# Path to SQLite database file (when using sqlite backend)
# This is also used for legacy compatibility
LOREKEEPER_DB_PATH=./data/cache.db

# =============================================================================
# Embedding Model Configuration
# =============================================================================

# Sentence-transformers model for generating embeddings
# Default: all-MiniLM-L6-v2 (384 dimensions, ~80MB)
# The model is downloaded automatically on first use
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2

# =============================================================================
# Cache TTL Configuration
# =============================================================================

# Default TTL for cached responses (in days)
LOREKEEPER_CACHE_TTL_DAYS=7

# TTL for error responses that should be cached separately (in seconds)
LOREKEEPER_ERROR_CACHE_TTL_SECONDS=300

# =============================================================================
# Logging Configuration
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOREKEEPER_LOG_LEVEL=INFO

# Debug mode - enables verbose logging and other debugging features
LOREKEEPER_DEBUG=false

# =============================================================================
# API Endpoints
# =============================================================================

# Base URL for the Open5e D&D 5e API
LOREKEEPER_OPEN5E_BASE_URL=https://api.open5e.com
```

**Step 2: Update README.md with semantic search documentation**

Add a new section to `README.md` after the existing Configuration section (or update the existing Configuration section). Find the appropriate location and add:

```markdown
### Semantic Search

LoreKeeper MCP uses Milvus Lite as the default cache backend, enabling semantic search across all D&D content. This means you can search using natural language queries like "fire protection spells" or "creatures that can fly" instead of exact name matches.

#### First Run

On first use of semantic search, the embedding model (~80MB) will be downloaded automatically. This is a one-time download that enables the natural language search capabilities.

#### Configuration

```bash
# Use Milvus Lite backend (default)
LOREKEEPER_CACHE_BACKEND=milvus
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db

# Or use legacy SQLite backend (no semantic search)
LOREKEEPER_CACHE_BACKEND=sqlite
LOREKEEPER_DB_PATH=./data/cache.db

# Custom embedding model (advanced)
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### Migrating from SQLite

If you were previously using the SQLite backend, switching to Milvus Lite requires re-importing your content:

1. Update your `.env` file to use `LOREKEEPER_CACHE_BACKEND=milvus`
2. Re-run your import commands to populate the new cache
3. Your existing SQLite cache remains untouched for rollback if needed

To rollback, simply set `LOREKEEPER_CACHE_BACKEND=sqlite` in your `.env` file.
```

**Step 3: Verify documentation renders correctly**

Review the changes visually or use a markdown previewer to ensure the documentation is clear and well-formatted.

**Step 4: Run quality checks**

```bash
just check
```

Expected: All checks pass.

**Step 5: Commit documentation changes**

```bash
git add .env.example README.md
git commit -m "docs: add Milvus cache backend and semantic search configuration"
```

---

## Task 4 Complete

At this point, Task 4 (Configuration Updates) is complete:

- ✅ 4.1 Config Changes:
  - Added `cache_backend` setting with default "milvus"
  - Added `milvus_db_path` setting with default "~/.lorekeeper/milvus.db"
  - Added `embedding_model` setting with default "all-MiniLM-L6-v2"
  - Added path expansion for tilde (~) in database paths
  - Added `LOREKEEPER_` prefix for environment variables

- ✅ 4.2 Documentation:
  - Updated `.env.example` with all new configuration variables
  - Added semantic search documentation to README
  - Documented first-run model download behavior
  - Documented migration from SQLite to Milvus

The configuration now supports:
- `LOREKEEPER_CACHE_BACKEND`: Choose between "milvus" (default) and "sqlite"
- `LOREKEEPER_MILVUS_DB_PATH`: Path to Milvus Lite database file
- `LOREKEEPER_EMBEDDING_MODEL`: Sentence-transformers model for embeddings
- All existing configuration options with LOREKEEPER_ prefix

Next tasks will implement:
- Task 5: Repository Integration (semantic search in repositories)
- Task 6: Tool Updates (semantic_query parameter)

---

## Task 5: Repository Integration

### Task 5.1: Repository Updates

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/base.py`
- Modify: `src/lorekeeper_mcp/repositories/spell.py`
- Modify: `src/lorekeeper_mcp/repositories/monster.py`
- Modify: `src/lorekeeper_mcp/repositories/equipment.py`
- Modify: `src/lorekeeper_mcp/repositories/character_option.py`
- Modify: `src/lorekeeper_mcp/repositories/rule.py`
- Modify: `tests/test_repositories/test_spell.py`
- Modify: `tests/test_repositories/test_creature.py`

#### Step 1: Write test for Repository protocol semantic_query parameter

Add to `tests/test_repositories/test_base.py`:

```python
class TestRepositoryProtocolSemanticSearch:
    """Tests for semantic_query parameter in Repository protocol."""

    def test_repository_protocol_search_accepts_semantic_query(self):
        """Test that Repository.search signature allows semantic_query."""
        from lorekeeper_mcp.repositories.base import Repository
        import inspect

        # Get search method signature
        sig = inspect.signature(Repository.search)

        # Should accept **filters which can include semantic_query
        params = sig.parameters
        assert "filters" in params or any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
```

**Step 2: Run test to see it pass**

```bash
uv run pytest tests/test_repositories/test_base.py::TestRepositoryProtocolSemanticSearch -v
```

Expected: Test passes (Repository already accepts **filters).

#### Step 3: Write test for SpellCache protocol semantic_search method

Add to `tests/test_repositories/test_spell.py`:

```python
class TestSpellRepositorySemanticSearch:
    """Tests for SpellRepository semantic search support."""

    @pytest.mark.asyncio
    async def test_spell_repository_search_with_semantic_query(self):
        """Test that search() uses semantic_search when semantic_query provided."""
        from lorekeeper_mcp.repositories.spell import SpellRepository

        # Create mock client and cache
        class MockClient:
            async def get_spells(self, **filters):
                return []

        class MockCache:
            def __init__(self):
                self.semantic_search_called = False
                self.get_entities_called = False

            async def get_entities(self, entity_type, **filters):
                self.get_entities_called = True
                return []

            async def store_entities(self, entities, entity_type):
                return len(entities)

            async def semantic_search(self, entity_type, query, limit=20, **filters):
                self.semantic_search_called = True
                self.search_query = query
                return []

        cache = MockCache()
        repo = SpellRepository(client=MockClient(), cache=cache)

        # Search with semantic_query
        await repo.search(semantic_query="fire damage spells")

        # Should call semantic_search, not get_entities
        assert cache.semantic_search_called
        assert cache.search_query == "fire damage spells"

    @pytest.mark.asyncio
    async def test_spell_repository_search_without_semantic_query(self):
        """Test that search() uses get_entities when no semantic_query."""
        from lorekeeper_mcp.repositories.spell import SpellRepository

        class MockClient:
            async def get_spells(self, **filters):
                return []

        class MockCache:
            def __init__(self):
                self.semantic_search_called = False
                self.get_entities_called = False

            async def get_entities(self, entity_type, **filters):
                self.get_entities_called = True
                return []

            async def store_entities(self, entities, entity_type):
                return len(entities)

            async def semantic_search(self, entity_type, query, limit=20, **filters):
                self.semantic_search_called = True
                return []

        cache = MockCache()
        repo = SpellRepository(client=MockClient(), cache=cache)

        # Search without semantic_query
        await repo.search(level=3)

        # Should call get_entities, not semantic_search
        assert cache.get_entities_called
        assert not cache.semantic_search_called

    @pytest.mark.asyncio
    async def test_spell_repository_semantic_search_with_filters(self):
        """Test that semantic search combines with scalar filters."""
        from lorekeeper_mcp.repositories.spell import SpellRepository

        class MockClient:
            async def get_spells(self, **filters):
                return []

        class MockCache:
            def __init__(self):
                self.semantic_filters = {}

            async def get_entities(self, entity_type, **filters):
                return []

            async def store_entities(self, entities, entity_type):
                return len(entities)

            async def semantic_search(self, entity_type, query, limit=20, **filters):
                self.semantic_filters = filters
                return []

        cache = MockCache()
        repo = SpellRepository(client=MockClient(), cache=cache)

        # Search with semantic_query AND level filter
        await repo.search(semantic_query="fire", level=3, school="Evocation")

        # Filters should be passed to semantic_search
        assert cache.semantic_filters.get("level") == 3
        assert cache.semantic_filters.get("school") == "Evocation"

    @pytest.mark.asyncio
    async def test_spell_repository_semantic_search_fallback_on_not_implemented(self):
        """Test that semantic search falls back when cache doesn't support it."""
        from lorekeeper_mcp.repositories.spell import SpellRepository
        from lorekeeper_mcp.models import Spell

        class MockClient:
            async def get_spells(self, **filters):
                return []

        class MockCache:
            def __init__(self):
                self.get_entities_called = False

            async def get_entities(self, entity_type, **filters):
                self.get_entities_called = True
                return [{"slug": "fireball", "name": "Fireball", "level": 3}]

            async def store_entities(self, entities, entity_type):
                return len(entities)

            async def semantic_search(self, entity_type, query, limit=20, **filters):
                raise NotImplementedError("SQLiteCache does not support semantic search")

        cache = MockCache()
        repo = SpellRepository(client=MockClient(), cache=cache)

        # Search with semantic_query (should fall back to get_entities)
        results = await repo.search(semantic_query="fire")

        # Should have fallen back to get_entities
        assert cache.get_entities_called
        assert len(results) == 1
```

**Step 4: Run test to see it fail**

```bash
uv run pytest tests/test_repositories/test_spell.py::TestSpellRepositorySemanticSearch -v
```

Expected: Tests fail because SpellRepository doesn't handle semantic_query yet.

**Step 5: Update SpellCache protocol to include semantic_search**

Edit `src/lorekeeper_mcp/repositories/spell.py` to update the SpellCache protocol:

```python
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
```

**Step 6: Update SpellRepository.search to handle semantic_query**

Edit `src/lorekeeper_mcp/repositories/spell.py` to update the search method:

```python
    async def search(self, **filters: Any) -> list[Spell]:
        """Search for spells with optional filters using cache-aside pattern.

        Supports both structured filtering and semantic search.

        Args:
            **filters: Optional filters:
                - semantic_query: Natural language search query (uses vector search)
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
        semantic_query = filters.pop("semantic_query", None)

        # Handle semantic search if query provided
        if semantic_query:
            return await self._semantic_search(
                semantic_query, limit=limit, class_key=class_key, **filters
            )

        # Regular structured search (existing behavior)
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

        # Cache miss - fetch from API
        api_filters = dict(filters)
        api_filters.pop("document", None)
        if class_key is not None:
            api_filters["class_key"] = class_key
        api_params = self._map_to_api_params(**api_filters)
        spells: list[Spell] = await self.client.get_spells(limit=limit, **api_params)

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
```

**Step 7: Run tests to see them pass**

```bash
uv run pytest tests/test_repositories/test_spell.py::TestSpellRepositorySemanticSearch -v
```

Expected: All 4 tests pass.

**Step 8: Run existing spell repository tests**

```bash
uv run pytest tests/test_repositories/test_spell.py -v
```

Expected: All tests pass (backward compatible).

**Step 9: Write test for CreatureRepository semantic search**

Add to `tests/test_repositories/test_creature.py`:

```python
class TestCreatureRepositorySemanticSearch:
    """Tests for CreatureRepository semantic search support."""

    @pytest.mark.asyncio
    async def test_creature_repository_search_with_semantic_query(self):
        """Test that search() uses semantic_search when semantic_query provided."""
        from lorekeeper_mcp.repositories.monster import CreatureRepository

        class MockClient:
            async def get_creatures(self, **filters):
                return []

        class MockCache:
            def __init__(self):
                self.semantic_search_called = False

            async def get_entities(self, entity_type, **filters):
                return []

            async def store_entities(self, entities, entity_type):
                return len(entities)

            async def semantic_search(self, entity_type, query, limit=20, **filters):
                self.semantic_search_called = True
                self.search_query = query
                return []

        cache = MockCache()
        repo = CreatureRepository(client=MockClient(), cache=cache)

        await repo.search(semantic_query="fire breathing dragons")

        assert cache.semantic_search_called
        assert cache.search_query == "fire breathing dragons"

    @pytest.mark.asyncio
    async def test_creature_repository_semantic_search_with_cr_filter(self):
        """Test semantic search combines with CR filter."""
        from lorekeeper_mcp.repositories.monster import CreatureRepository

        class MockClient:
            async def get_creatures(self, **filters):
                return []

        class MockCache:
            def __init__(self):
                self.semantic_filters = {}

            async def get_entities(self, entity_type, **filters):
                return []

            async def store_entities(self, entities, entity_type):
                return len(entities)

            async def semantic_search(self, entity_type, query, limit=20, **filters):
                self.semantic_filters = filters
                return []

        cache = MockCache()
        repo = CreatureRepository(client=MockClient(), cache=cache)

        await repo.search(semantic_query="undead monsters", challenge_rating="5")

        assert cache.semantic_filters.get("challenge_rating") == "5"
```

**Step 10: Run test to see it fail**

```bash
uv run pytest tests/test_repositories/test_creature.py::TestCreatureRepositorySemanticSearch -v
```

Expected: Tests fail because CreatureRepository doesn't handle semantic_query yet.

**Step 11: Update CreatureCache protocol to include semantic_search**

Edit `src/lorekeeper_mcp/repositories/monster.py` to update the CreatureCache protocol:

```python
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
```

**Step 12: Update CreatureRepository.search to handle semantic_query**

Edit `src/lorekeeper_mcp/repositories/monster.py` to update the search method:

```python
    async def search(self, **filters: Any) -> list[Creature]:
        """Search for creatures with optional filters using cache-aside pattern.

        Supports both structured filtering and semantic search.

        Args:
            **filters: Optional filters:
                - semantic_query: Natural language search query (uses vector search)
                - challenge_rating, type, size: Structured filters
                - document: Filter by source document
                - limit: Maximum results to return

        Returns:
            List of Creature objects matching the filters
        """
        # Extract special parameters
        limit = filters.pop("limit", None)
        semantic_query = filters.pop("semantic_query", None)

        # Handle semantic search if query provided
        if semantic_query:
            return await self._semantic_search(semantic_query, limit=limit, **filters)

        # Separate cache-compatible filters from API-only filters
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

        # Try cache first
        cached = await self.cache.get_entities("creatures", **cache_filters)

        if cached:
            results = [Creature.model_validate(creature) for creature in cached]
            if api_only_filters:
                results = self._apply_api_filters(results, **api_only_filters)
            return results[:limit] if limit else results

        # Cache miss - fetch from API
        api_filters = dict(filters)
        api_filters.pop("document", None)
        api_params = self._map_to_api_params(**api_filters)
        creatures: list[Creature] = await self.client.get_creatures(limit=limit, **api_params)

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
            k: v for k, v in filters.items()
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

        return [Creature.model_validate(creature) for creature in results][:limit] if limit else [Creature.model_validate(creature) for creature in results]
```

**Step 13: Run tests to see them pass**

```bash
uv run pytest tests/test_repositories/test_creature.py::TestCreatureRepositorySemanticSearch -v
```

Expected: All tests pass.

**Step 14: Update EquipmentCache protocol**

Edit `src/lorekeeper_mcp/repositories/equipment.py` to update the EquipmentCache protocol:

```python
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
```

**Step 15: Update EquipmentRepository.search to handle semantic_query**

Edit `src/lorekeeper_mcp/repositories/equipment.py` to update the search method:

```python
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
            return await self._semantic_search(
                semantic_query, item_type=item_type, **filters
            )

        if item_type == "armor":
            return await self._search_armor(**filters)
        if item_type == "magic-item":
            return await self._search_magic_items(**filters)
        return await self._search_weapons(**filters)

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
            collections = [("armor", Armor)]
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
```

**Step 16: Update CharacterOptionCache protocol**

Edit `src/lorekeeper_mcp/repositories/character_option.py` to update the CharacterOptionCache protocol:

```python
class CharacterOptionCache(Protocol):
    """Protocol for character option cache.

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
```

**Step 17: Update CharacterOptionRepository.search to handle semantic_query**

Edit `src/lorekeeper_mcp/repositories/character_option.py` to update the search method:

```python
    async def search(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for character options with type routing.

        Supports both structured filtering and semantic search.

        Args:
            **filters: Must include 'option_type' (class, race, background,
                feat, or condition). Other filters depend on type.
                - semantic_query: Natural language search query (uses vector search)

        Returns:
            List of matching character options
        """
        option_type = filters.pop("option_type", None)
        semantic_query = filters.pop("semantic_query", None)

        if semantic_query:
            return await self._semantic_search(
                semantic_query, option_type=option_type, **filters
            )

        if option_type == "class":
            return await self._search_classes(**filters)
        if option_type == "race":
            return await self._search_races(**filters)
        if option_type == "background":
            return await self._search_backgrounds(**filters)
        if option_type == "feat":
            return await self._search_feats(**filters)
        if option_type == "condition":
            return await self._search_conditions(**filters)
        return []

    async def _semantic_search(
        self,
        query: str,
        option_type: str | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Perform semantic search for character options.

        Args:
            query: Natural language search query
            option_type: Optional type filter (class, race, background, feat, condition)
            **filters: Additional scalar filters

        Returns:
            List of character options ranked by semantic similarity
        """
        limit = filters.pop("limit", None)
        search_limit = limit or 20

        # Determine which collections to search
        type_to_collection = {
            "class": "classes",
            "race": "races",
            "background": "backgrounds",
            "feat": "feats",
            "condition": "conditions",
        }

        if option_type and option_type in type_to_collection:
            collections = [type_to_collection[option_type]]
        else:
            # Search all character option types
            collections = list(type_to_collection.values())

        all_results: list[dict[str, Any]] = []

        for collection_name in collections:
            try:
                results = await self.cache.semantic_search(
                    collection_name, query, limit=search_limit, **filters
                )
                all_results.extend(results)
            except NotImplementedError:
                # Fall back to structured search
                cached = await self.cache.get_entities(collection_name, name=query, **filters)
                all_results.extend(cached)

        return all_results[:limit] if limit else all_results
```

**Step 18: Update RuleCache protocol**

Edit `src/lorekeeper_mcp/repositories/rule.py` to update the RuleCache protocol:

```python
class RuleCache(Protocol):
    """Protocol for rule cache.

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
```

**Step 19: Update RuleRepository.search to handle semantic_query**

Edit `src/lorekeeper_mcp/repositories/rule.py` to update the search method:

```python
    async def search(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for rules with type routing.

        Supports both structured filtering and semantic search.

        Args:
            **filters: Must include 'rule_type' (rule, condition, damage-type,
                weapon-property, skill, ability-score, magic-school, language,
                proficiency, or alignment).
                - semantic_query: Natural language search query (uses vector search)

        Returns:
            List of matching rules
        """
        rule_type = filters.pop("rule_type", None)
        semantic_query = filters.pop("semantic_query", None)

        if semantic_query:
            return await self._semantic_search(
                semantic_query, rule_type=rule_type, **filters
            )

        if rule_type == "rule":
            return await self._search_rules(**filters)
        if rule_type == "condition":
            return await self._search_conditions(**filters)
        if rule_type == "damage-type":
            return await self._search_damage_types(**filters)
        if rule_type == "weapon-property":
            return await self._search_weapon_properties(**filters)
        if rule_type == "skill":
            return await self._search_skills(**filters)
        if rule_type == "ability-score":
            return await self._search_ability_scores(**filters)
        if rule_type == "magic-school":
            return await self._search_magic_schools(**filters)
        if rule_type == "language":
            return await self._search_languages(**filters)
        if rule_type == "proficiency":
            return await self._search_proficiencies(**filters)
        if rule_type == "alignment":
            return await self._search_alignments(**filters)
        return []

    async def _semantic_search(
        self,
        query: str,
        rule_type: str | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Perform semantic search for rules.

        Args:
            query: Natural language search query
            rule_type: Optional type filter
            **filters: Additional scalar filters

        Returns:
            List of rules ranked by semantic similarity
        """
        limit = filters.pop("limit", None)
        search_limit = limit or 20

        # Map rule types to collection names
        type_to_collection = {
            "rule": "rules",
            "condition": "conditions",
            "damage-type": "damagetypes",
            "weapon-property": "weapon_properties",
            "skill": "skills",
            "ability-score": "ability_scores",
            "magic-school": "magic_schools",
            "language": "languages",
            "proficiency": "proficiencies",
            "alignment": "alignments",
        }

        if rule_type and rule_type in type_to_collection:
            collections = [type_to_collection[rule_type]]
        else:
            # Search all rule types
            collections = list(type_to_collection.values())

        all_results: list[dict[str, Any]] = []

        for collection_name in collections:
            try:
                results = await self.cache.semantic_search(
                    collection_name, query, limit=search_limit, **filters
                )
                all_results.extend(results)
            except NotImplementedError:
                # Fall back to structured search
                cached = await self.cache.get_entities(collection_name, name=query, **filters)
                all_results.extend(cached)

        return all_results[:limit] if limit else all_results
```

**Step 20: Run all repository tests**

```bash
uv run pytest tests/test_repositories/ -v
```

Expected: All tests pass.

**Step 21: Run quality checks**

```bash
just lint && just type-check
```

Expected: No errors. Fix any issues that arise.

**Step 22: Commit repository updates**

```bash
git add src/lorekeeper_mcp/repositories/ tests/test_repositories/
git commit -m "feat(repositories): add semantic_query parameter support to all repositories"
```

---

### Task 5.2: Repository Factory

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/factory.py`
- Modify: `tests/test_repositories/test_factory.py`

#### Step 1: Write test for repository factory using cache factory

Add to `tests/test_repositories/test_factory.py`:

```python
class TestRepositoryFactoryCacheIntegration:
    """Tests for repository factory cache backend integration."""

    def test_factory_uses_cache_factory_default(self, tmp_path, monkeypatch):
        """Test that factory uses cache factory with default backend."""
        from lorekeeper_mcp.repositories.factory import RepositoryFactory
        from lorekeeper_mcp.cache.milvus import MilvusCache

        # Set Milvus path to tmp_path
        db_path = tmp_path / "milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")

        # Clear cached instance
        RepositoryFactory._cache_instance = None

        # Create a repository
        repo = RepositoryFactory.create_spell_repository()

        # Cache should be MilvusCache
        assert isinstance(RepositoryFactory._cache_instance, MilvusCache)

    def test_factory_uses_sqlite_when_configured(self, tmp_path, monkeypatch):
        """Test that factory uses SQLite when configured."""
        from lorekeeper_mcp.repositories.factory import RepositoryFactory
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        # Set SQLite backend
        db_path = tmp_path / "cache.db"
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "sqlite")
        monkeypatch.setenv("LOREKEEPER_SQLITE_DB_PATH", str(db_path))

        # Clear cached instance
        RepositoryFactory._cache_instance = None

        # Create a repository
        repo = RepositoryFactory.create_spell_repository()

        # Cache should be SQLiteCache
        assert isinstance(RepositoryFactory._cache_instance, SQLiteCache)

    def test_factory_reuses_cache_instance(self, tmp_path, monkeypatch):
        """Test that factory reuses the same cache instance."""
        from lorekeeper_mcp.repositories.factory import RepositoryFactory

        db_path = tmp_path / "milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")

        # Clear cached instance
        RepositoryFactory._cache_instance = None

        # Create multiple repositories
        spell_repo = RepositoryFactory.create_spell_repository()
        creature_repo = RepositoryFactory.create_monster_repository()

        # Should use same cache instance
        assert spell_repo.cache is creature_repo.cache

    def test_factory_reset_cache(self, tmp_path, monkeypatch):
        """Test that factory cache can be reset."""
        from lorekeeper_mcp.repositories.factory import RepositoryFactory

        db_path = tmp_path / "milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))

        # Clear cached instance
        RepositoryFactory._cache_instance = None

        # Create a repository
        RepositoryFactory.create_spell_repository()
        first_cache = RepositoryFactory._cache_instance

        # Reset cache
        RepositoryFactory.reset_cache()

        # Create another repository
        RepositoryFactory.create_spell_repository()
        second_cache = RepositoryFactory._cache_instance

        # Should be different instances
        assert first_cache is not second_cache
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_repositories/test_factory.py::TestRepositoryFactoryCacheIntegration -v
```

Expected: Tests fail because factory doesn't use cache factory yet.

**Step 3: Update RepositoryFactory to use cache factory**

Edit `src/lorekeeper_mcp/repositories/factory.py`:

```python
"""Factory for creating repository instances with dependency injection."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.factory import get_cache_from_config
from lorekeeper_mcp.repositories.character_option import CharacterOptionRepository
from lorekeeper_mcp.repositories.equipment import EquipmentRepository
from lorekeeper_mcp.repositories.monster import MonsterRepository
from lorekeeper_mcp.repositories.rule import RuleRepository
from lorekeeper_mcp.repositories.spell import SpellRepository


class _CacheProtocol(Protocol):
    """Protocol for cache implementations used by factory."""

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


class RepositoryFactory:
    """Factory for creating repository instances with dependency injection.

    Provides static factory methods for creating properly configured repository
    instances. Supports optional client and cache overrides for testing.

    Uses the cache factory to create cache instances based on environment
    configuration (LOREKEEPER_CACHE_BACKEND).
    """

    _cache_instance: _CacheProtocol | None = None

    @staticmethod
    def _get_cache() -> _CacheProtocol:
        """Get or create the shared cache instance.

        Creates cache based on environment configuration:
        - LOREKEEPER_CACHE_BACKEND=milvus (default): MilvusCache with semantic search
        - LOREKEEPER_CACHE_BACKEND=sqlite: SQLiteCache (legacy, no semantic search)

        Returns:
            A cache instance implementing the CacheProtocol.
        """
        if RepositoryFactory._cache_instance is None:
            RepositoryFactory._cache_instance = get_cache_from_config()
        assert RepositoryFactory._cache_instance is not None
        return RepositoryFactory._cache_instance

    @staticmethod
    def reset_cache() -> None:
        """Reset the cached cache instance.

        Useful for testing or when configuration changes require a new cache.
        """
        RepositoryFactory._cache_instance = None

    @staticmethod
    def create_spell_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> SpellRepository:
        """Create a SpellRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured SpellRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return SpellRepository(client=client, cache=cache)

    @staticmethod
    def create_monster_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> MonsterRepository:
        """Create a MonsterRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured MonsterRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return MonsterRepository(client=client, cache=cache)

    @staticmethod
    def create_equipment_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> EquipmentRepository:
        """Create an EquipmentRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured EquipmentRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return EquipmentRepository(client=client, cache=cache)  # type: ignore[arg-type]

    @staticmethod
    def create_character_option_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> CharacterOptionRepository:
        """Create a CharacterOptionRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured CharacterOptionRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return CharacterOptionRepository(client=client, cache=cache)

    @staticmethod
    def create_rule_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> RuleRepository:
        """Create a RuleRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured RuleRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return RuleRepository(client=client, cache=cache)
```

**Step 4: Run tests to see them pass**

```bash
uv run pytest tests/test_repositories/test_factory.py::TestRepositoryFactoryCacheIntegration -v
```

Expected: All 4 tests pass.

**Step 5: Run all repository factory tests**

```bash
uv run pytest tests/test_repositories/test_factory.py -v
```

Expected: All tests pass.

**Step 6: Run full repository test suite**

```bash
uv run pytest tests/test_repositories/ -v
```

Expected: All tests pass.

**Step 7: Run quality checks**

```bash
just check
```

Expected: All checks pass.

**Step 8: Commit factory updates**

```bash
git add src/lorekeeper_mcp/repositories/factory.py tests/test_repositories/test_factory.py
git commit -m "feat(repositories): update factory to use cache factory with backend selection"
```

---

## Task 5 Complete

At this point, Task 5 (Repository Integration) is complete:

- ✅ 5.1 Repository Updates:
  - Added `semantic_query` parameter to search methods in all repositories
  - Updated SpellRepository with semantic search support and fallback
  - Updated CreatureRepository with semantic search support and fallback
  - Updated EquipmentRepository with semantic search support and fallback
  - Updated CharacterOptionRepository with semantic search support and fallback
  - Updated RuleRepository with semantic search support and fallback
  - All cache protocols now include semantic_search method signature

- ✅ 5.2 Repository Factory:
  - Updated to use `get_cache_from_config()` instead of hardcoded SQLiteCache
  - Added `reset_cache()` method for testing
  - Updated `_CacheProtocol` to include semantic_search method
  - Repositories now work with both MilvusCache and SQLiteCache backends

The repositories now support:
- `semantic_query="fire spells"` - Uses vector similarity search when MilvusCache is configured
- Automatic fallback to structured search when SQLiteCache is used
- Combining semantic search with scalar filters (level, school, etc.)
- Backward compatibility - existing code without semantic_query continues to work

Next task will implement:
- Task 6: Tool Updates (semantic_query parameter in MCP tools)

---

## Task 6: Tool Updates

### Task 6.1: Spell Lookup Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py`
- Modify: `tests/test_tools/test_spell_lookup.py`

#### Step 1: Write test for semantic_query parameter

Add to `tests/test_tools/test_spell_lookup.py`:

```python
class TestSpellLookupSemanticQuery:
    """Tests for spell lookup semantic_query parameter."""

    @pytest.mark.asyncio
    async def test_lookup_spell_passes_semantic_query_to_repository(self):
        """Test that semantic_query is passed to repository search."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_spell(semantic_query="fire damage spells")
            assert repo.search_kwargs.get("semantic_query") == "fire damage spells"
        finally:
            _repository_context.clear()

    @pytest.mark.asyncio
    async def test_lookup_spell_semantic_query_with_filters(self):
        """Test that semantic_query combines with other filters."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_spell(semantic_query="fire", level=3, school="evocation")
            assert repo.search_kwargs.get("semantic_query") == "fire"
            assert repo.search_kwargs.get("level") == 3
            assert repo.search_kwargs.get("school") == "evocation"
        finally:
            _repository_context.clear()

    @pytest.mark.asyncio
    async def test_lookup_spell_semantic_query_none_by_default(self):
        """Test that semantic_query is not passed when not provided."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_spell(level=3)
            assert "semantic_query" not in repo.search_kwargs
        finally:
            _repository_context.clear()
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_tools/test_spell_lookup.py::TestSpellLookupSemanticQuery -v
```

Expected: `TypeError: lookup_spell() got an unexpected keyword argument 'semantic_query'`

**Step 3: Add semantic_query parameter to lookup_spell**

Edit `src/lorekeeper_mcp/tools/spell_lookup.py` to add the `semantic_query` parameter:

```python
async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    level_min: int | None = None,
    level_max: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    casting_time: str | None = None,
    damage_type: str | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring with semantic_query documentation**

Add to the docstring Args section:

```python
        semantic_query: Natural language search query for semantic/conceptual search.
            Uses vector similarity to find spells matching the meaning of your query,
            not just exact keyword matches. Requires Milvus cache backend.
            Examples: "fire damage spells", "healing allies", "crowd control",
            "buff party members", "escape danger"
```

**Step 5: Pass semantic_query to repository**

Update the params building section:

```python
    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name
    if level is not None:
        params["level"] = level
    if level_min is not None:
        params["level_min"] = level_min
    if level_max is not None:
        params["level_max"] = level_max
    if school is not None:
        params["school"] = school
    if class_key is not None:
        params["class_key"] = class_key
    if concentration is not None:
        params["concentration"] = concentration
    if ritual is not None:
        params["ritual"] = ritual
    if casting_time is not None:
        params["casting_time"] = casting_time
    if damage_type is not None:
        params["damage_type"] = damage_type
    if documents is not None:
        params["document"] = documents
    if semantic_query is not None:
        params["semantic_query"] = semantic_query
```

**Step 6: Run test to see it pass**

```bash
uv run pytest tests/test_tools/test_spell_lookup.py::TestSpellLookupSemanticQuery -v
```

Expected: All 3 tests pass.

**Step 7: Run all spell lookup tests**

```bash
uv run pytest tests/test_tools/test_spell_lookup.py -v
```

Expected: All tests pass.

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/spell_lookup.py tests/test_tools/test_spell_lookup.py
git commit -m "feat(tools): add semantic_query parameter to spell lookup"
```

---

### Task 6.2: Creature Lookup Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py`
- Modify: `tests/test_tools/test_creature_lookup.py`

#### Step 1: Write test for semantic_query parameter

Add to `tests/test_tools/test_creature_lookup.py`:

```python
class TestCreatureLookupSemanticQuery:
    """Tests for creature lookup semantic_query parameter."""

    @pytest.mark.asyncio
    async def test_lookup_creature_passes_semantic_query_to_repository(self):
        """Test that semantic_query is passed to repository search."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_creature(semantic_query="fire breathing dragons")
            assert repo.search_kwargs.get("semantic_query") == "fire breathing dragons"
        finally:
            _repository_context.clear()

    @pytest.mark.asyncio
    async def test_lookup_creature_semantic_query_with_filters(self):
        """Test that semantic_query combines with other filters."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_creature(semantic_query="undead", cr_min=5, type="undead")
            assert repo.search_kwargs.get("semantic_query") == "undead"
            assert repo.search_kwargs.get("cr_min") == 5
            assert repo.search_kwargs.get("type") == "undead"
        finally:
            _repository_context.clear()
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_tools/test_creature_lookup.py::TestCreatureLookupSemanticQuery -v
```

Expected: `TypeError: lookup_creature() got an unexpected keyword argument 'semantic_query'`

**Step 3: Add semantic_query parameter to lookup_creature**

Edit `src/lorekeeper_mcp/tools/creature_lookup.py` to add the `semantic_query` parameter:

```python
async def lookup_creature(
    name: str | None = None,
    cr: float | None = None,
    cr_min: float | None = None,
    cr_max: float | None = None,
    type: str | None = None,  # noqa: A002
    size: str | None = None,
    armor_class_min: int | None = None,
    hit_points_min: int | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring with semantic_query documentation**

Add to the docstring Args section:

```python
          semantic_query: Natural language search query for semantic/conceptual search.
              Uses vector similarity to find creatures matching the meaning of your query.
              Requires Milvus cache backend.
              Examples: "fire breathing dragons", "undead hordes", "flying monsters",
              "creatures that can grapple", "boss monsters"
```

**Step 5: Pass semantic_query to repository**

Update the params building section:

```python
    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name
    if cr is not None:
        params["challenge_rating"] = float(cr)
    if cr_min is not None:
        params["cr_min"] = cr_min
    if cr_max is not None:
        params["cr_max"] = cr_max
    if type is not None:
        params["type"] = type
    if size is not None:
        params["size"] = size
    if armor_class_min is not None:
        params["armor_class_min"] = armor_class_min
    if hit_points_min is not None:
        params["hit_points_min"] = hit_points_min
    if documents is not None:
        params["document"] = documents
    if semantic_query is not None:
        params["semantic_query"] = semantic_query
```

**Step 6: Run test to see it pass**

```bash
uv run pytest tests/test_tools/test_creature_lookup.py::TestCreatureLookupSemanticQuery -v
```

Expected: All 2 tests pass.

**Step 7: Run all creature lookup tests**

```bash
uv run pytest tests/test_tools/test_creature_lookup.py -v
```

Expected: All tests pass.

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/creature_lookup.py tests/test_tools/test_creature_lookup.py
git commit -m "feat(tools): add semantic_query parameter to creature lookup"
```

---

### Task 6.3: Equipment Lookup Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py`
- Modify: `tests/test_tools/test_equipment_lookup.py`

#### Step 1: Write test for semantic_query parameter

Add to `tests/test_tools/test_equipment_lookup.py`:

```python
class TestEquipmentLookupSemanticQuery:
    """Tests for equipment lookup semantic_query parameter."""

    @pytest.mark.asyncio
    async def test_lookup_equipment_passes_semantic_query_to_repository(self):
        """Test that semantic_query is passed to repository search."""
        from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_calls = []

            async def search(self, **kwargs):
                self.search_calls.append(kwargs)
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_equipment(type="weapon", semantic_query="slashing weapons")
            assert len(repo.search_calls) == 1
            assert repo.search_calls[0].get("semantic_query") == "slashing weapons"
        finally:
            _repository_context.clear()

    @pytest.mark.asyncio
    async def test_lookup_equipment_semantic_query_with_all_types(self):
        """Test that semantic_query is passed for all equipment types."""
        from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_calls = []

            async def search(self, **kwargs):
                self.search_calls.append(kwargs)
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_equipment(type="all", semantic_query="magical protection")
            # Should have 3 calls (weapon, armor, magic-item)
            assert len(repo.search_calls) == 3
            for call in repo.search_calls:
                assert call.get("semantic_query") == "magical protection"
        finally:
            _repository_context.clear()
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_tools/test_equipment_lookup.py::TestEquipmentLookupSemanticQuery -v
```

Expected: `TypeError: lookup_equipment() got an unexpected keyword argument 'semantic_query'`

**Step 3: Add semantic_query parameter to lookup_equipment**

Edit `src/lorekeeper_mcp/tools/equipment_lookup.py` to add the `semantic_query` parameter:

```python
async def lookup_equipment(
    type: EquipmentType = "all",  # noqa: A002
    name: str | None = None,
    rarity: str | None = None,
    damage_dice: str | None = None,
    is_simple: bool | None = None,
    requires_attunement: str | None = None,
    cost_min: int | float | None = None,
    cost_max: int | float | None = None,
    weight_max: float | None = None,
    is_finesse: bool | None = None,
    is_light: bool | None = None,
    is_magic: bool | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring with semantic_query documentation**

Add to the docstring Args section:

```python
            semantic_query: Natural language search query for semantic/conceptual search.
                Uses vector similarity to find equipment matching the meaning of your query.
                Requires Milvus cache backend.
                Examples: "slashing weapons", "protective armor", "magical healing items",
                "stealth gear", "ranged weapons"
```

**Step 5: Pass semantic_query to repository in all search paths**

Update the weapon filters section:

```python
    if type in ("weapon", "all"):
        weapon_filters: dict[str, Any] = {"item_type": "weapon"}
        if name is not None:
            weapon_filters["name"] = name
        if damage_dice is not None:
            weapon_filters["damage_dice"] = damage_dice
        if is_simple is not None:
            weapon_filters["is_simple"] = is_simple
        if cost_min is not None:
            weapon_filters["cost_min"] = cost_min
        if cost_max is not None:
            weapon_filters["cost_max"] = cost_max
        if weight_max is not None:
            weapon_filters["weight_max"] = weight_max
        if is_finesse is not None:
            weapon_filters["is_finesse"] = is_finesse
        if is_light is not None:
            weapon_filters["is_light"] = is_light
        if is_magic is not None:
            weapon_filters["is_magic"] = is_magic
        if documents is not None:
            weapon_filters["document"] = documents
        if semantic_query is not None:
            weapon_filters["semantic_query"] = semantic_query
```

Update the armor filters section:

```python
    if type in ("armor", "all"):
        armor_filters: dict[str, Any] = {"item_type": "armor"}
        if name is not None:
            armor_filters["name"] = name
        if cost_min is not None:
            armor_filters["cost_min"] = cost_min
        if cost_max is not None:
            armor_filters["cost_max"] = cost_max
        if documents is not None:
            armor_filters["document"] = documents
        if semantic_query is not None:
            armor_filters["semantic_query"] = semantic_query
```

Update the magic item filters section:

```python
    if type in ("magic-item", "all"):
        magic_item_filters: dict[str, Any] = {"item_type": "magic-item"}
        if name is not None:
            magic_item_filters["name"] = name
        if rarity is not None:
            magic_item_filters["rarity"] = rarity
        if requires_attunement is not None:
            if requires_attunement.lower() in ("yes", "true", "1"):
                magic_item_filters["requires_attunement"] = True
            else:
                magic_item_filters["requires_attunement"] = False
        if documents is not None:
            magic_item_filters["document"] = documents
        if semantic_query is not None:
            magic_item_filters["semantic_query"] = semantic_query
```

**Step 6: Run test to see it pass**

```bash
uv run pytest tests/test_tools/test_equipment_lookup.py::TestEquipmentLookupSemanticQuery -v
```

Expected: All 2 tests pass.

**Step 7: Run all equipment lookup tests**

```bash
uv run pytest tests/test_tools/test_equipment_lookup.py -v
```

Expected: All tests pass.

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/equipment_lookup.py tests/test_tools/test_equipment_lookup.py
git commit -m "feat(tools): add semantic_query parameter to equipment lookup"
```

---

### Task 6.4: Character Option Lookup Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/character_option_lookup.py`
- Modify: `tests/test_tools/test_character_option_lookup.py`

#### Step 1: Write test for semantic_query parameter

Add to `tests/test_tools/test_character_option_lookup.py`:

```python
class TestCharacterOptionLookupSemanticQuery:
    """Tests for character option lookup semantic_query parameter."""

    @pytest.mark.asyncio
    async def test_lookup_character_option_passes_semantic_query(self):
        """Test that semantic_query is passed to repository search."""
        from lorekeeper_mcp.tools.character_option_lookup import (
            lookup_character_option,
            _repository_context,
        )

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_character_option(type="class", semantic_query="spellcasting classes")
            assert repo.search_kwargs.get("semantic_query") == "spellcasting classes"
        finally:
            _repository_context.clear()

    @pytest.mark.asyncio
    async def test_lookup_character_option_semantic_query_with_name_filter(self):
        """Test that semantic_query combines with name filter."""
        from lorekeeper_mcp.tools.character_option_lookup import (
            lookup_character_option,
            _repository_context,
        )

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return [{"name": "Fighter"}]

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_character_option(
                type="class", semantic_query="martial combat", name="fighter"
            )
            assert repo.search_kwargs.get("semantic_query") == "martial combat"
        finally:
            _repository_context.clear()
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_tools/test_character_option_lookup.py::TestCharacterOptionLookupSemanticQuery -v
```

Expected: `TypeError: lookup_character_option() got an unexpected keyword argument 'semantic_query'`

**Step 3: Add semantic_query parameter to lookup_character_option**

Edit `src/lorekeeper_mcp/tools/character_option_lookup.py` to add the `semantic_query` parameter:

```python
async def lookup_character_option(
    type: OptionType,  # noqa: A002
    name: str | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring with semantic_query documentation**

Add to the docstring Args section:

```python
        semantic_query: Natural language search query for semantic/conceptual search.
            Uses vector similarity to find options matching the meaning of your query.
            Requires Milvus cache backend.
            Examples: "spellcasting classes", "stealthy races", "combat-focused backgrounds",
            "defensive feats", "magical abilities"
```

**Step 5: Pass semantic_query to repository**

Update the params building section:

```python
    params: dict[str, Any] = {
        "option_type": type,
        "limit": limit,
    }
    if documents is not None:
        params["document"] = documents
    if semantic_query is not None:
        params["semantic_query"] = semantic_query
```

**Step 6: Run test to see it pass**

```bash
uv run pytest tests/test_tools/test_character_option_lookup.py::TestCharacterOptionLookupSemanticQuery -v
```

Expected: All 2 tests pass.

**Step 7: Run all character option lookup tests**

```bash
uv run pytest tests/test_tools/test_character_option_lookup.py -v
```

Expected: All tests pass.

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/character_option_lookup.py tests/test_tools/test_character_option_lookup.py
git commit -m "feat(tools): add semantic_query parameter to character option lookup"
```

---

### Task 6.5: Rule Lookup Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/rule_lookup.py`
- Modify: `tests/test_tools/test_rule_lookup.py`

#### Step 1: Write test for semantic_query parameter

Add to `tests/test_tools/test_rule_lookup.py`:

```python
class TestRuleLookupSemanticQuery:
    """Tests for rule lookup semantic_query parameter."""

    @pytest.mark.asyncio
    async def test_lookup_rule_passes_semantic_query_to_repository(self):
        """Test that semantic_query is passed to repository search."""
        from lorekeeper_mcp.tools.rule_lookup import lookup_rule, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_rule(rule_type="condition", semantic_query="movement restrictions")
            assert repo.search_kwargs.get("semantic_query") == "movement restrictions"
        finally:
            _repository_context.clear()

    @pytest.mark.asyncio
    async def test_lookup_rule_semantic_query_with_name_filter(self):
        """Test that semantic_query combines with name filter."""
        from lorekeeper_mcp.tools.rule_lookup import lookup_rule, _repository_context

        class MockRepository:
            def __init__(self):
                self.search_kwargs = {}

            async def search(self, **kwargs):
                self.search_kwargs = kwargs
                return []

        repo = MockRepository()
        _repository_context["repository"] = repo

        try:
            await lookup_rule(
                rule_type="condition", semantic_query="can't move", name="grappled"
            )
            assert repo.search_kwargs.get("semantic_query") == "can't move"
            assert repo.search_kwargs.get("name") == "grappled"
        finally:
            _repository_context.clear()
```

**Step 2: Run test to see it fail**

```bash
uv run pytest tests/test_tools/test_rule_lookup.py::TestRuleLookupSemanticQuery -v
```

Expected: `TypeError: lookup_rule() got an unexpected keyword argument 'semantic_query'`

**Step 3: Add semantic_query parameter to lookup_rule**

Edit `src/lorekeeper_mcp/tools/rule_lookup.py` to add the `semantic_query` parameter:

```python
async def lookup_rule(
    rule_type: RuleType,
    name: str | None = None,
    section: str | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring with semantic_query documentation**

Add to the docstring Args section:

```python
        semantic_query: Natural language search query for semantic/conceptual search.
            Uses vector similarity to find rules matching the meaning of your query.
            Requires Milvus cache backend.
            Examples: "movement restrictions", "attack of opportunity", "concentration checks",
            "death saving throws", "stealth rules"
```

**Step 5: Pass semantic_query to repository**

Update the params building section:

```python
    params: dict[str, Any] = {"rule_type": rule_type}
    if name is not None:
        params["name"] = name
    if limit is not None:
        params["limit"] = limit
    if rule_type == "rule" and section is not None:
        params["section"] = section
    if documents is not None:
        params["document"] = documents
    if semantic_query is not None:
        params["semantic_query"] = semantic_query
    return await repository.search(**params)
```

**Step 6: Run test to see it pass**

```bash
uv run pytest tests/test_tools/test_rule_lookup.py::TestRuleLookupSemanticQuery -v
```

Expected: All 2 tests pass.

**Step 7: Run all rule lookup tests**

```bash
uv run pytest tests/test_tools/test_rule_lookup.py -v
```

Expected: All tests pass.

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/rule_lookup.py tests/test_tools/test_rule_lookup.py
git commit -m "feat(tools): add semantic_query parameter to rule lookup"
```

---

### Task 6.6: Search DnD Content Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/search_dnd_content.py`
- Modify: `tests/test_tools/test_search_dnd_content.py`

#### Step 1: Write test for semantic=false parameter

Add to `tests/test_tools/test_search_dnd_content.py`:

```python
class TestSearchDndContentSemanticControl:
    """Tests for search_dnd_content semantic search control."""

    @pytest.mark.asyncio
    async def test_search_dnd_content_semantic_default_true(self, respx_mock):
        """Test that enable_semantic defaults to True."""
        from lorekeeper_mcp.tools.search_dnd_content import search_dnd_content

        # Mock the API call
        respx_mock.get("https://api.open5e.com/v2/search/").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        await search_dnd_content(query="fireball")

        # Check that vector=true was passed
        call = respx_mock.calls.last
        assert call.request.url.params.get("vector") == "true"

    @pytest.mark.asyncio
    async def test_search_dnd_content_semantic_false_disables_vector(self, respx_mock):
        """Test that enable_semantic=False disables vector search."""
        from lorekeeper_mcp.tools.search_dnd_content import search_dnd_content

        respx_mock.get("https://api.open5e.com/v2/search/").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        await search_dnd_content(query="fireball", enable_semantic=False)

        call = respx_mock.calls.last
        assert call.request.url.params.get("vector") == "false"

    @pytest.mark.asyncio
    async def test_search_dnd_content_combines_semantic_and_fuzzy(self, respx_mock):
        """Test that semantic and fuzzy can be combined."""
        from lorekeeper_mcp.tools.search_dnd_content import search_dnd_content

        respx_mock.get("https://api.open5e.com/v2/search/").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        await search_dnd_content(query="firbal", enable_fuzzy=True, enable_semantic=True)

        call = respx_mock.calls.last
        assert call.request.url.params.get("fuzzy") == "true"
        assert call.request.url.params.get("vector") == "true"
```

**Step 2: Run test to verify existing behavior**

```bash
uv run pytest tests/test_tools/test_search_dnd_content.py::TestSearchDndContentSemanticControl -v
```

Expected: Tests should pass since enable_semantic already exists (defaults to True).

**Step 3: Update docstring to clarify semantic search behavior**

Edit `src/lorekeeper_mcp/tools/search_dnd_content.py` to update the docstring:

```python
        enable_semantic: Enable semantic/vector search for conceptual matching.
            When True (default), uses the Open5e API's vector search to find
            conceptually related content even if keywords don't match exactly.
            Set to False for structured-only search based on keywords.
            Examples:
            - enable_semantic=True: "healing magic" finds Cure Wounds, Healing Word
            - enable_semantic=False: "healing magic" only finds exact keyword matches
```

**Step 4: Run all search tests**

```bash
uv run pytest tests/test_tools/test_search_dnd_content.py -v
```

Expected: All tests pass.

**Step 5: Run quality checks**

```bash
just lint && just type-check
```

Expected: No errors.

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/tools/search_dnd_content.py tests/test_tools/test_search_dnd_content.py
git commit -m "docs(tools): clarify semantic search control in search_dnd_content"
```

---

### Task 6.7: Final Tool Tests and Quality Checks

**Step 1: Run all tool tests**

```bash
uv run pytest tests/test_tools/ -v
```

Expected: All tests pass.

**Step 2: Run full test suite**

```bash
just test
```

Expected: All tests pass.

**Step 3: Run quality checks**

```bash
just check
```

Expected: All checks pass.

**Step 4: Run live tests**

```bash
uv run pytest tests/test_tools/test_live_mcp.py -v --run-live
```

Expected: All live tests pass (CRITICAL - rule #1).

**Step 5: Commit any final fixes**

```bash
git add -A
git commit -m "test(tools): ensure all tool tests pass with semantic_query support"
```

---

## Task 6 Complete

At this point, Task 6 (Tool Updates) is complete:

- ✅ 6.1 Spell Lookup Tool:
  - Added `semantic_query: str | None` parameter
  - Updated docstring with semantic search documentation
  - Passes semantic_query to repository search

- ✅ 6.2 Creature Lookup Tool:
  - Added `semantic_query: str | None` parameter
  - Updated docstring with semantic search documentation
  - Passes semantic_query to repository search

- ✅ 6.3 Equipment Lookup Tool:
  - Added `semantic_query: str | None` parameter
  - Updated docstring with semantic search documentation
  - Passes semantic_query to all equipment type searches

- ✅ 6.4 Character Option Lookup Tool:
  - Added `semantic_query: str | None` parameter
  - Updated docstring with semantic search documentation
  - Passes semantic_query to repository search

- ✅ 6.5 Rule Lookup Tool:
  - Added `semantic_query: str | None` parameter
  - Updated docstring with semantic search documentation
  - Passes semantic_query to repository search

- ✅ 6.6 Search DnD Content Tool:
  - Already supports `enable_semantic` parameter
  - Updated docstring to clarify semantic search behavior
  - Supports `enable_semantic=False` for structured-only search

The tools now support:
- `semantic_query="fire damage spells"` - Natural language search using vector similarity
- Combining semantic search with existing filters (level, school, cr, type, etc.)
- Backward compatibility - tools work without semantic_query parameter
- Automatic fallback to structured search when SQLiteCache is used

---

## Task 7: Testing

### Task 7.1: Unit Tests for MilvusCache

**Files:**
- Modify: `tests/test_cache/test_milvus.py`

#### Step 1: Write comprehensive initialization tests

Add to `tests/test_cache/test_milvus.py`:

```python
class TestMilvusCacheInitializationComprehensive:
    """Comprehensive tests for MilvusCache initialization and lifecycle."""

    def test_milvus_cache_custom_embedding_model(self, tmp_path: Path):
        """Test that custom embedding model can be specified."""
        from lorekeeper_mcp.cache.milvus import MilvusCache
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path), embedding_model="custom-model")

        assert cache._embedding_service.model_name == "custom-model"

    def test_milvus_cache_creates_db_directory(self, tmp_path: Path):
        """Test that nested directories are created for db path."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "nested" / "dir" / "milvus.db"
        cache = MilvusCache(str(db_path))

        # Access client to trigger lazy init
        _ = cache.client

        assert db_path.parent.exists()

    def test_milvus_cache_multiple_instances_same_path(self, tmp_path: Path):
        """Test behavior with multiple cache instances for same path."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "shared_milvus.db"
        cache1 = MilvusCache(str(db_path))
        cache2 = MilvusCache(str(db_path))

        # Both should work (Milvus Lite supports multiple connections)
        _ = cache1.client
        _ = cache2.client

        assert cache1.db_path == cache2.db_path

    @pytest.mark.asyncio
    async def test_milvus_cache_context_manager_multiple_operations(self, tmp_path: Path):
        """Test context manager with multiple store/retrieve operations."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"

        async with MilvusCache(str(db_path)) as cache:
            entities = [
                {"slug": "fireball", "name": "Fireball", "document": "srd"},
                {"slug": "ice-storm", "name": "Ice Storm", "document": "srd"},
            ]
            await cache.store_entities(entities, "spells")

            result = await cache.get_entities("spells")
            assert len(result) == 2
```

**Step 2: Run tests**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheInitializationComprehensive -v
```

Expected: All tests pass.

#### Step 3: Write tests for error handling

Add to `tests/test_cache/test_milvus.py`:

```python
class TestMilvusCacheErrorHandling:
    """Tests for MilvusCache error handling."""

    @pytest.mark.asyncio
    async def test_get_entities_nonexistent_collection(self, tmp_path: Path):
        """Test get_entities creates collection if not exists."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Should return empty list, not raise
        result = await cache.get_entities("nonexistent_type")
        assert result == []

    @pytest.mark.asyncio
    async def test_store_entities_invalid_slug(self, tmp_path: Path):
        """Test store_entities handles entities without slug."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Entity without slug - should use empty string
        entities = [{"name": "No Slug Entity", "document": "srd"}]
        count = await cache.store_entities(entities, "spells")

        # Should still store successfully
        assert count == 1

    @pytest.mark.asyncio
    async def test_semantic_search_invalid_query_type(self, tmp_path: Path):
        """Test semantic_search handles edge cases gracefully."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Empty string query should fall back to get_entities
        result = await cache.semantic_search("spells", "")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_semantic_search_whitespace_only_query(self, tmp_path: Path):
        """Test semantic_search handles whitespace-only query."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Whitespace query should fall back to get_entities
        result = await cache.semantic_search("spells", "   ")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_entity_count_after_store(self, tmp_path: Path):
        """Test entity count accuracy after storing entities."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        initial_count = await cache.get_entity_count("spells")
        assert initial_count == 0

        entities = [
            {"slug": f"spell-{i}", "name": f"Spell {i}", "document": "srd"}
            for i in range(5)
        ]
        await cache.store_entities(entities, "spells")

        final_count = await cache.get_entity_count("spells")
        assert final_count == 5
```

**Step 4: Run error handling tests**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheErrorHandling -v
```

Expected: All tests pass.

#### Step 5: Write tests for hybrid search

Add to `tests/test_cache/test_milvus.py`:

```python
class TestMilvusCacheHybridSearch:
    """Tests for MilvusCache hybrid search (semantic + filters)."""

    @pytest.mark.asyncio
    async def test_hybrid_search_semantic_and_level(self, tmp_path: Path):
        """Test combining semantic query with level filter."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "desc": "Fire explosion", "level": 3, "document": "srd"},
            {"slug": "fire-bolt", "name": "Fire Bolt", "desc": "Fire cantrip", "level": 0, "document": "srd"},
            {"slug": "fire-storm", "name": "Fire Storm", "desc": "Massive fire", "level": 7, "document": "srd"},
        ]
        await cache.store_entities(entities, "spells")

        # Search for fire spells at level 3
        result = await cache.semantic_search("spells", "fire magic", level=3)

        assert len(result) == 1
        assert result[0]["slug"] == "fireball"

    @pytest.mark.asyncio
    async def test_hybrid_search_semantic_and_document_list(self, tmp_path: Path):
        """Test combining semantic query with document list filter."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "desc": "Fire", "document": "srd"},
            {"slug": "custom-fire", "name": "Custom Fire", "desc": "Fire spell", "document": "homebrew"},
            {"slug": "ice-storm", "name": "Ice Storm", "desc": "Ice", "document": "phb"},
        ]
        await cache.store_entities(entities, "spells")

        # Search for fire spells in srd or homebrew
        result = await cache.semantic_search("spells", "fire", document=["srd", "homebrew"])

        slugs = {r["slug"] for r in result}
        assert "fireball" in slugs
        assert "custom-fire" in slugs
        assert "ice-storm" not in slugs

    @pytest.mark.asyncio
    async def test_hybrid_search_semantic_and_bool_filter(self, tmp_path: Path):
        """Test combining semantic query with boolean filter."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        entities = [
            {"slug": "fireball", "name": "Fireball", "desc": "Fire explosion", "concentration": False, "document": "srd"},
            {"slug": "flame-shield", "name": "Flame Shield", "desc": "Fire protection", "concentration": True, "document": "srd"},
        ]
        await cache.store_entities(entities, "spells")

        # Search for fire spells that require concentration
        result = await cache.semantic_search("spells", "fire", concentration=True)

        assert len(result) == 1
        assert result[0]["slug"] == "flame-shield"
```

**Step 6: Run hybrid search tests**

```bash
uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheHybridSearch -v
```

Expected: All tests pass.

**Step 7: Commit**

```bash
git add tests/test_cache/test_milvus.py
git commit -m "test(cache): add comprehensive MilvusCache unit tests"
```

---

### Task 7.2: EmbeddingService Tests

**Files:**
- Modify: `tests/test_cache/test_embedding.py`

#### Step 1: Write additional embedding service tests

Add to `tests/test_cache/test_embedding.py`:

```python
class TestEmbeddingServiceEdgeCases:
    """Edge case tests for EmbeddingService."""

    def test_encode_very_long_text(self):
        """Test encoding of very long text."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        long_text = "magic spell " * 1000  # ~12000 characters

        result = service.encode(long_text)

        assert isinstance(result, list)
        assert len(result) == 384

    def test_encode_special_characters(self):
        """Test encoding text with special characters."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        special_text = "Fireball™ ® © ♦ ★ → ← ↑ ↓ • € £ ¥"

        result = service.encode(special_text)

        assert isinstance(result, list)
        assert len(result) == 384

    def test_encode_unicode_text(self):
        """Test encoding text with unicode characters."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        unicode_text = "火球 氷嵐 雷撃 魔法"

        result = service.encode(unicode_text)

        assert isinstance(result, list)
        assert len(result) == 384

    def test_encode_batch_preserves_order(self):
        """Test that batch encoding preserves input order."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        texts = ["first", "second", "third", "fourth", "fifth"]

        batch_results = service.encode_batch(texts)
        individual_results = [service.encode(t) for t in texts]

        for i, (batch_emb, ind_emb) in enumerate(zip(batch_results, individual_results)):
            # Compare first few dimensions to verify order
            for b, i_val in zip(batch_emb[:5], ind_emb[:5]):
                assert abs(b - i_val) < 1e-5, f"Mismatch at index {i}"

    def test_encode_batch_large_batch(self):
        """Test batch encoding with large number of texts."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        texts = [f"Spell number {i} description" for i in range(100)]

        result = service.encode_batch(texts)

        assert len(result) == 100
        assert all(len(emb) == 384 for emb in result)


class TestEmbeddingServiceSearchableTextExtraction:
    """Tests for get_searchable_text with various entity structures."""

    def test_get_searchable_text_spell_with_components(self):
        """Test spell text extraction includes components."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Fireball",
            "desc": "A bright streak flashes.",
            "higher_level": "More damage at higher levels.",
            "components": "V, S, M (a tiny ball of bat guano and sulfur)",
        }

        result = service.get_searchable_text(entity, "spells")

        assert "Fireball" in result
        assert "bright streak" in result
        assert "higher levels" in result

    def test_get_searchable_text_creature_with_legendary_actions(self):
        """Test creature text extraction includes legendary actions."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Ancient Dragon",
            "desc": "A legendary beast.",
            "type": "dragon",
            "legendary_actions": [
                {"name": "Detect"},
                {"name": "Tail Attack"},
                {"name": "Wing Attack"},
            ],
        }

        result = service.get_searchable_text(entity, "creatures")

        assert "Ancient Dragon" in result
        assert "legendary" in result
        assert "dragon" in result

    def test_get_searchable_text_magic_item(self):
        """Test magic item text extraction."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        entity = {
            "name": "Flametongue",
            "desc": "A sword that bursts into flame on command.",
            "type": "Weapon (any sword)",
            "rarity": "Rare",
        }

        result = service.get_searchable_text(entity, "magicitems")

        assert "Flametongue" in result
        assert "flame" in result
        assert "sword" in result.lower()
```

**Step 2: Run embedding service tests**

```bash
uv run pytest tests/test_cache/test_embedding.py -v
```

Expected: All tests pass.

**Step 3: Commit**

```bash
git add tests/test_cache/test_embedding.py
git commit -m "test(cache): add EmbeddingService edge case and extraction tests"
```

---

### Task 7.3: Integration Tests with Real Embeddings

**Files:**
- Create: `tests/test_cache/test_milvus_integration.py`

#### Step 1: Write integration tests

Create `tests/test_cache/test_milvus_integration.py`:

```python
"""Integration tests for MilvusCache with real embeddings."""

import pytest
from pathlib import Path


class TestMilvusCacheIntegrationSpells:
    """Integration tests for spell storage and semantic search."""

    @pytest.mark.asyncio
    async def test_semantic_search_finds_related_spells(self, tmp_path: Path):
        """Test that semantic search finds conceptually related spells."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store spells with different themes
        spells = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "desc": "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame.",
                "level": 3,
                "school": "Evocation",
                "document": "srd",
            },
            {
                "slug": "fire-shield",
                "name": "Fire Shield",
                "desc": "Thin and wispy flames wreathe your body for the duration, shedding bright light. The flames provide you with protection against cold or fire.",
                "level": 4,
                "school": "Evocation",
                "document": "srd",
            },
            {
                "slug": "ice-storm",
                "name": "Ice Storm",
                "desc": "A hail of rock-hard ice pounds to the ground in a 20-foot-radius, 40-foot-high cylinder centered on a point within range.",
                "level": 4,
                "school": "Evocation",
                "document": "srd",
            },
            {
                "slug": "cure-wounds",
                "name": "Cure Wounds",
                "desc": "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier.",
                "level": 1,
                "school": "Evocation",
                "document": "srd",
            },
        ]
        await cache.store_entities(spells, "spells")

        # Search for fire-related spells
        results = await cache.semantic_search("spells", "fire damage spells")

        # Fire spells should rank higher than healing/ice spells
        top_two = [r["slug"] for r in results[:2]]
        assert "fireball" in top_two or "fire-shield" in top_two

    @pytest.mark.asyncio
    async def test_semantic_search_healing_spells(self, tmp_path: Path):
        """Test semantic search for healing-related content."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        spells = [
            {
                "slug": "cure-wounds",
                "name": "Cure Wounds",
                "desc": "A creature you touch regains hit points.",
                "document": "srd",
            },
            {
                "slug": "healing-word",
                "name": "Healing Word",
                "desc": "A creature of your choice that you can see regains hit points.",
                "document": "srd",
            },
            {
                "slug": "fireball",
                "name": "Fireball",
                "desc": "An explosion of flame damages creatures.",
                "document": "srd",
            },
        ]
        await cache.store_entities(spells, "spells")

        results = await cache.semantic_search("spells", "restore health to allies")

        # Healing spells should rank first
        assert results[0]["slug"] in ["cure-wounds", "healing-word"]


class TestMilvusCacheIntegrationCreatures:
    """Integration tests for creature storage and semantic search."""

    @pytest.mark.asyncio
    async def test_semantic_search_finds_dragon_types(self, tmp_path: Path):
        """Test semantic search for dragon-related creatures."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        creatures = [
            {
                "slug": "ancient-red-dragon",
                "name": "Ancient Red Dragon",
                "desc": "A legendary dragon known for its fiery breath.",
                "type": "dragon",
                "document": "srd",
            },
            {
                "slug": "young-white-dragon",
                "name": "Young White Dragon",
                "desc": "A dragon that breathes cold and lives in icy regions.",
                "type": "dragon",
                "document": "srd",
            },
            {
                "slug": "goblin",
                "name": "Goblin",
                "desc": "A small humanoid creature.",
                "type": "humanoid",
                "document": "srd",
            },
        ]
        await cache.store_entities(creatures, "creatures")

        results = await cache.semantic_search("creatures", "fire breathing flying beast")

        # Dragon should rank higher
        assert "dragon" in results[0]["slug"]

    @pytest.mark.asyncio
    async def test_semantic_search_with_cr_filter(self, tmp_path: Path):
        """Test semantic search combined with challenge rating filter."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        creatures = [
            {"slug": "goblin", "name": "Goblin", "desc": "Weak humanoid", "challenge_rating": "1/4", "document": "srd"},
            {"slug": "orc", "name": "Orc", "desc": "Strong humanoid warrior", "challenge_rating": "1/2", "document": "srd"},
            {"slug": "ogre", "name": "Ogre", "desc": "Large brutal humanoid", "challenge_rating": "2", "document": "srd"},
        ]
        await cache.store_entities(creatures, "creatures")

        results = await cache.semantic_search("creatures", "humanoid", challenge_rating="2")

        assert len(results) == 1
        assert results[0]["slug"] == "ogre"


class TestMilvusCacheIntegrationEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_workflow_store_search_retrieve(self, tmp_path: Path):
        """Test complete workflow: store, semantic search, structured retrieve."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"

        async with MilvusCache(str(db_path)) as cache:
            # Store entities
            spells = [
                {"slug": "fireball", "name": "Fireball", "desc": "Fire explosion", "level": 3, "document": "srd"},
                {"slug": "lightning-bolt", "name": "Lightning Bolt", "desc": "Lightning damage", "level": 3, "document": "srd"},
            ]
            stored = await cache.store_entities(spells, "spells")
            assert stored == 2

            # Semantic search
            semantic_results = await cache.semantic_search("spells", "electrical attack")
            assert any(r["slug"] == "lightning-bolt" for r in semantic_results)

            # Structured retrieve
            structured_results = await cache.get_entities("spells", level=3)
            assert len(structured_results) == 2

            # Stats
            stats = await cache.get_cache_stats()
            assert stats["total_entities"] >= 2

    @pytest.mark.asyncio
    async def test_upsert_updates_embeddings(self, tmp_path: Path):
        """Test that upsert updates embeddings when description changes."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store initial version
        await cache.store_entities(
            [{"slug": "spell-1", "name": "Spell", "desc": "Fire damage spell", "document": "srd"}],
            "spells",
        )

        # Search for fire
        results1 = await cache.semantic_search("spells", "fire")
        assert len(results1) == 1

        # Update to ice
        await cache.store_entities(
            [{"slug": "spell-1", "name": "Spell", "desc": "Ice cold freezing spell", "document": "srd"}],
            "spells",
        )

        # Search for ice - should find it now
        results2 = await cache.semantic_search("spells", "ice cold")
        assert len(results2) == 1
        assert results2[0]["slug"] == "spell-1"
```

**Step 2: Run integration tests**

```bash
uv run pytest tests/test_cache/test_milvus_integration.py -v
```

Expected: All tests pass.

**Step 3: Commit**

```bash
git add tests/test_cache/test_milvus_integration.py
git commit -m "test(cache): add MilvusCache integration tests with real embeddings"
```

---

### Task 7.4: Repository Tests Update

**Files:**
- Modify: `tests/test_repositories/test_spell.py`
- Modify: `tests/test_repositories/test_creature.py`

#### Step 1: Add semantic search integration tests to spell repository

Add to `tests/test_repositories/test_spell.py`:

```python
class TestSpellRepositoryWithMilvusCache:
    """Tests for SpellRepository with MilvusCache backend."""

    @pytest.mark.asyncio
    async def test_spell_repository_semantic_search_integration(self, tmp_path: Path):
        """Integration test: SpellRepository with real MilvusCache."""
        from lorekeeper_mcp.repositories.spell import SpellRepository
        from lorekeeper_mcp.cache.milvus import MilvusCache
        from lorekeeper_mcp.models import Spell

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Pre-populate cache with spell data
        spell_data = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "desc": "A bright streak of fire",
                "level": 3,
                "school": "Evocation",
                "document": "srd",
            },
            {
                "slug": "ice-storm",
                "name": "Ice Storm",
                "desc": "A hail of ice",
                "level": 4,
                "school": "Evocation",
                "document": "srd",
            },
        ]
        await cache.store_entities(spell_data, "spells")

        class MockClient:
            async def get_spells(self, **filters):
                return []

        repo = SpellRepository(client=MockClient(), cache=cache)

        # Semantic search should find fire-related spell
        results = await repo.search(semantic_query="fire damage")

        assert len(results) > 0
        assert any(s.slug == "fireball" for s in results)
```

**Step 2: Add semantic search integration tests to creature repository

Add to `tests/test_repositories/test_creature.py`:

```python
class TestCreatureRepositoryWithMilvusCache:
    """Tests for CreatureRepository with MilvusCache backend."""

    @pytest.mark.asyncio
    async def test_creature_repository_semantic_search_integration(self, tmp_path: Path):
        """Integration test: CreatureRepository with real MilvusCache."""
        from lorekeeper_mcp.repositories.monster import CreatureRepository
        from lorekeeper_mcp.cache.milvus import MilvusCache
        from lorekeeper_mcp.models import Creature

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Pre-populate cache with creature data
        creature_data = [
            {
                "slug": "ancient-red-dragon",
                "name": "Ancient Red Dragon",
                "desc": "A legendary fire-breathing dragon",
                "type": "dragon",
                "challenge_rating": "24",
                "document": "srd",
            },
            {
                "slug": "goblin",
                "name": "Goblin",
                "desc": "A small humanoid creature",
                "type": "humanoid",
                "challenge_rating": "1/4",
                "document": "srd",
            },
        ]
        await cache.store_entities(creature_data, "creatures")

        class MockClient:
            async def get_creatures(self, **filters):
                return []

        repo = CreatureRepository(client=MockClient(), cache=cache)

        # Semantic search should find dragon
        results = await repo.search(semantic_query="fire breathing beast")

        assert len(results) > 0
        assert any(c.slug == "ancient-red-dragon" for c in results)
```

**Step 3: Run repository tests**

```bash
uv run pytest tests/test_repositories/test_spell.py tests/test_repositories/test_creature.py -v
```

Expected: All tests pass.

**Step 4: Commit**

```bash
git add tests/test_repositories/test_spell.py tests/test_repositories/test_creature.py
git commit -m "test(repositories): add MilvusCache integration tests for repositories"
```

---

### Task 7.5: Tool Tests with semantic_query

**Files:**
- Modify: `tests/test_tools/test_spell_lookup.py`
- Modify: `tests/test_tools/test_creature_lookup.py`

#### Step 1: Add end-to-end tool tests with semantic search

Add to `tests/test_tools/test_spell_lookup.py`:

```python
class TestSpellLookupSemanticQueryIntegration:
    """Integration tests for spell lookup with semantic_query."""

    @pytest.mark.asyncio
    async def test_lookup_spell_semantic_query_end_to_end(self, tmp_path: Path):
        """End-to-end test: lookup_spell with semantic_query and MilvusCache."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell, _repository_context
        from lorekeeper_mcp.repositories.spell import SpellRepository
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Pre-populate cache
        await cache.store_entities(
            [
                {"slug": "fireball", "name": "Fireball", "desc": "Fire explosion", "level": 3, "document": "srd"},
                {"slug": "cure-wounds", "name": "Cure Wounds", "desc": "Healing touch", "level": 1, "document": "srd"},
            ],
            "spells",
        )

        class MockClient:
            async def get_spells(self, **filters):
                return []

        repo = SpellRepository(client=MockClient(), cache=cache)
        _repository_context["repository"] = repo

        try:
            results = await lookup_spell(semantic_query="fire damage")
            assert len(results) > 0
            assert any(r["slug"] == "fireball" for r in results)
        finally:
            _repository_context.clear()

    @pytest.mark.asyncio
    async def test_lookup_spell_semantic_query_with_level_filter(self, tmp_path: Path):
        """Test semantic_query combined with level filter."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell, _repository_context
        from lorekeeper_mcp.repositories.spell import SpellRepository
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        await cache.store_entities(
            [
                {"slug": "fireball", "name": "Fireball", "desc": "Fire explosion", "level": 3, "document": "srd"},
                {"slug": "fire-bolt", "name": "Fire Bolt", "desc": "Fire cantrip", "level": 0, "document": "srd"},
            ],
            "spells",
        )

        class MockClient:
            async def get_spells(self, **filters):
                return []

        repo = SpellRepository(client=MockClient(), cache=cache)
        _repository_context["repository"] = repo

        try:
            results = await lookup_spell(semantic_query="fire", level=3)
            assert len(results) == 1
            assert results[0]["slug"] == "fireball"
        finally:
            _repository_context.clear()
```

**Step 2: Add similar tests for creature lookup

Add to `tests/test_tools/test_creature_lookup.py`:

```python
class TestCreatureLookupSemanticQueryIntegration:
    """Integration tests for creature lookup with semantic_query."""

    @pytest.mark.asyncio
    async def test_lookup_creature_semantic_query_end_to_end(self, tmp_path: Path):
        """End-to-end test: lookup_creature with semantic_query and MilvusCache."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature, _repository_context
        from lorekeeper_mcp.repositories.monster import CreatureRepository
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        await cache.store_entities(
            [
                {"slug": "ancient-red-dragon", "name": "Ancient Red Dragon", "desc": "Fire breathing dragon", "type": "dragon", "document": "srd"},
                {"slug": "goblin", "name": "Goblin", "desc": "Small humanoid", "type": "humanoid", "document": "srd"},
            ],
            "creatures",
        )

        class MockClient:
            async def get_creatures(self, **filters):
                return []

        repo = CreatureRepository(client=MockClient(), cache=cache)
        _repository_context["repository"] = repo

        try:
            results = await lookup_creature(semantic_query="flying fire beast")
            assert len(results) > 0
            assert any(r["slug"] == "ancient-red-dragon" for r in results)
        finally:
            _repository_context.clear()
```

**Step 3: Run tool tests**

```bash
uv run pytest tests/test_tools/test_spell_lookup.py tests/test_tools/test_creature_lookup.py -v
```

Expected: All tests pass.

**Step 4: Commit**

```bash
git add tests/test_tools/test_spell_lookup.py tests/test_tools/test_creature_lookup.py
git commit -m "test(tools): add semantic_query integration tests for lookup tools"
```

---

### Task 7.6: Performance Tests

**Files:**
- Create: `tests/test_cache/test_milvus_performance.py`

#### Step 1: Write performance benchmarks

Create `tests/test_cache/test_milvus_performance.py`:

```python
"""Performance tests for MilvusCache."""

import pytest
import time
from pathlib import Path


class TestMilvusCachePerformance:
    """Performance benchmarks for MilvusCache operations."""

    @pytest.mark.asyncio
    async def test_semantic_search_latency(self, tmp_path: Path):
        """Benchmark: Semantic search should complete in <100ms."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "perf_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store 100 spells
        spells = [
            {
                "slug": f"spell-{i}",
                "name": f"Spell {i}",
                "desc": f"A magical spell that does thing number {i}",
                "level": i % 9,
                "document": "srd",
            }
            for i in range(100)
        ]
        await cache.store_entities(spells, "spells")

        # Warm up (first search loads model)
        await cache.semantic_search("spells", "warmup query")

        # Measure latency
        start = time.perf_counter()
        await cache.semantic_search("spells", "fire damage explosion")
        elapsed = time.perf_counter() - start

        assert elapsed < 0.1, f"Semantic search took {elapsed:.3f}s, expected <100ms"

    @pytest.mark.asyncio
    async def test_bulk_storage_performance(self, tmp_path: Path):
        """Benchmark: Bulk storage of 500 entities should complete in <30s."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "perf_milvus.db"
        cache = MilvusCache(str(db_path))

        # Create 500 entities
        entities = [
            {
                "slug": f"entity-{i}",
                "name": f"Entity {i}",
                "desc": f"Description for entity number {i} with some text",
                "document": "srd",
            }
            for i in range(500)
        ]

        start = time.perf_counter()
        count = await cache.store_entities(entities, "bulk_test")
        elapsed = time.perf_counter() - start

        assert count == 500
        assert elapsed < 30.0, f"Bulk storage took {elapsed:.1f}s, expected <30s"

    @pytest.mark.asyncio
    async def test_get_entities_performance(self, tmp_path: Path):
        """Benchmark: Structured query should complete in <50ms."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "perf_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store entities
        entities = [
            {"slug": f"spell-{i}", "name": f"Spell {i}", "level": i % 9, "document": "srd"}
            for i in range(200)
        ]
        await cache.store_entities(entities, "spells")

        # Measure latency
        start = time.perf_counter()
        results = await cache.get_entities("spells", level=3)
        elapsed = time.perf_counter() - start

        assert len(results) > 0
        assert elapsed < 0.05, f"get_entities took {elapsed:.3f}s, expected <50ms"

    @pytest.mark.asyncio
    async def test_hybrid_search_performance(self, tmp_path: Path):
        """Benchmark: Hybrid search should complete in <150ms."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "perf_milvus.db"
        cache = MilvusCache(str(db_path))

        # Store entities
        entities = [
            {
                "slug": f"spell-{i}",
                "name": f"Spell {i}",
                "desc": f"A spell with various effects including fire, ice, and lightning",
                "level": i % 9,
                "document": "srd",
            }
            for i in range(200)
        ]
        await cache.store_entities(entities, "spells")

        # Warm up
        await cache.semantic_search("spells", "warmup")

        # Measure hybrid search latency
        start = time.perf_counter()
        await cache.semantic_search("spells", "fire damage", level=3)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.15, f"Hybrid search took {elapsed:.3f}s, expected <150ms"


class TestEmbeddingServicePerformance:
    """Performance benchmarks for EmbeddingService."""

    def test_single_encode_latency(self):
        """Benchmark: Single text encoding should complete in <50ms (after warmup)."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()

        # Warm up (first call loads model)
        service.encode("warmup text")

        # Measure latency
        start = time.perf_counter()
        service.encode("A fireball spell that deals fire damage to creatures in an area")
        elapsed = time.perf_counter() - start

        assert elapsed < 0.05, f"Single encode took {elapsed:.3f}s, expected <50ms"

    def test_batch_encode_efficiency(self):
        """Benchmark: Batch encoding should be faster than individual encoding."""
        from lorekeeper_mcp.cache.embedding import EmbeddingService

        service = EmbeddingService()
        texts = [f"Spell number {i} with description" for i in range(50)]

        # Warm up
        service.encode("warmup")

        # Measure batch
        start_batch = time.perf_counter()
        service.encode_batch(texts)
        batch_time = time.perf_counter() - start_batch

        # Measure individual
        start_individual = time.perf_counter()
        for text in texts:
            service.encode(text)
        individual_time = time.perf_counter() - start_individual

        # Batch should be faster
        assert batch_time < individual_time, f"Batch ({batch_time:.2f}s) not faster than individual ({individual_time:.2f}s)"
```

**Step 2: Run performance tests**

```bash
uv run pytest tests/test_cache/test_milvus_performance.py -v
```

Expected: All tests pass with acceptable performance.

**Step 3: Commit**

```bash
git add tests/test_cache/test_milvus_performance.py
git commit -m "test(cache): add performance benchmarks for MilvusCache and EmbeddingService"
```

---

### Task 7.7: Run Full Test Suite and Live Tests

**Step 1: Run all cache tests**

```bash
uv run pytest tests/test_cache/ -v
```

Expected: All tests pass.

**Step 2: Run all repository tests**

```bash
uv run pytest tests/test_repositories/ -v
```

Expected: All tests pass.

**Step 3: Run all tool tests**

```bash
uv run pytest tests/test_tools/ -v
```

Expected: All tests pass.

**Step 4: Run full test suite**

```bash
just test
```

Expected: All tests pass.

**Step 5: Run quality checks**

```bash
just check
```

Expected: All checks pass.

**Step 6: Run live tests (CRITICAL)**

```bash
uv run pytest tests/test_tools/test_live_mcp.py -v --run-live
```

Expected: All live tests pass. This is CRITICAL per rule #1.

**Step 7: Commit any final fixes**

```bash
git add -A
git commit -m "test: ensure all tests pass including live tests"
```

---

## Task 7 Complete

At this point, Task 7 (Testing) is complete:

- ✅ 7.1 Unit Tests for MilvusCache:
  - Comprehensive initialization tests
  - Error handling tests
  - Hybrid search tests
  - Context manager tests

- ✅ 7.2 EmbeddingService Tests:
  - Edge case tests (long text, unicode, special characters)
  - Batch encoding order preservation
  - Searchable text extraction for various entity types

- ✅ 7.3 Integration Tests:
  - End-to-end spell storage and semantic search
  - Creature semantic search with filters
  - Full workflow tests (store → search → retrieve)
  - Upsert behavior verification

- ✅ 7.4 Repository Tests:
  - SpellRepository with MilvusCache integration
  - CreatureRepository with MilvusCache integration
  - Semantic search fallback behavior

- ✅ 7.5 Tool Tests:
  - End-to-end lookup_spell with semantic_query
  - End-to-end lookup_creature with semantic_query
  - Combined semantic + filter tests

- ✅ 7.6 Performance Tests:
  - Semantic search latency (<100ms target)
  - Bulk storage performance (<30s for 500 entities)
  - Structured query performance (<50ms)
  - Hybrid search performance (<150ms)
  - Embedding batch efficiency

- ✅ 7.7 Full Test Suite:
  - All unit tests passing
  - All integration tests passing
  - All live tests passing (CRITICAL)
  - Quality checks passing

---

## Task 8: Migration and Documentation

### Task 8.1: Migration Guide

**Files:**
- Create: `docs/migrations/2025-XX-XX-milvus-migration.md`

#### Step 1: Create migration guide document

Create `docs/migrations/2025-XX-XX-milvus-migration.md`:

```markdown
# Migration Guide: SQLite to Milvus Lite Cache Backend

This guide covers migrating from the SQLite cache backend to the new Milvus Lite backend with semantic search capabilities.

## Breaking Changes

### Cache Backend Change

The default cache backend has changed from SQLite to Milvus Lite. This enables semantic/vector search capabilities but requires re-indexing your cached data.

**What's affected:**
- All cached entity data (spells, creatures, equipment, etc.)
- Cache database file location and format

**What's NOT affected:**
- API endpoints and tool interfaces (backward compatible)
- Configuration via environment variables (new variables added, old still work)

### Environment Variables

New environment variables:
- `LOREKEEPER_CACHE_BACKEND` - Set to "milvus" (default) or "sqlite"
- `LOREKEEPER_MILVUS_DB_PATH` - Path to Milvus database file
- `LOREKEEPER_EMBEDDING_MODEL` - Embedding model name (default: all-MiniLM-L6-v2)

Existing variables still work for SQLite backend:
- `LOREKEEPER_DB_PATH` - SQLite database path

## Migration Steps

### Step 1: Update Environment Configuration

Update your `.env` file:

```bash
# New Milvus backend (default)
LOREKEEPER_CACHE_BACKEND=milvus
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Step 2: Re-Index Your Data

Your existing SQLite cache data will NOT be automatically migrated. You need to re-import your data:

```bash
# Re-import from Open5e
lorekeeper import --source open5e

# Or re-import specific document
lorekeeper import --source open5e --document srd
```

**Note:** The first import will take longer as it downloads the embedding model (~80MB).

### Step 3: Verify Migration

Test that your data is accessible:

```bash
# Test spell lookup
lorekeeper lookup spell --name "Fireball"

# Test semantic search (new feature!)
lorekeeper lookup spell --semantic "fire damage spells"
```

## Rollback Procedure

If you need to roll back to SQLite:

### Step 1: Update Environment

```bash
LOREKEEPER_CACHE_BACKEND=sqlite
LOREKEEPER_DB_PATH=./data/cache.db
```

### Step 2: Restart Application

The application will use your existing SQLite cache. No data migration needed for rollback since SQLite data wasn't deleted.

**Note:** Semantic search (`--semantic`) will not work with SQLite backend.

## First-Run Model Download

On first use of semantic search, the embedding model will be downloaded automatically:
- Model: `all-MiniLM-L6-v2`
- Size: ~80MB
- Location: Cached by sentence-transformers in `~/.cache/torch/sentence_transformers/`

This is a one-time download. Subsequent runs use the cached model.

## Performance Considerations

- **First search:** ~2-3 seconds (model loading)
- **Subsequent searches:** <100ms
- **Bulk import:** ~30s for 500 entities (includes embedding generation)
- **Storage size:** Slightly larger than SQLite due to embeddings

## Troubleshooting

### "Model not found" error

The embedding model couldn't be downloaded. Check:
- Internet connectivity
- Disk space in `~/.cache`
- Firewall/proxy settings

### "Semantic search not available" error

You're using SQLite backend. Switch to Milvus:
```bash
LOREKEEPER_CACHE_BACKEND=milvus
```

### Slow first search

This is normal - the embedding model needs to load. Subsequent searches will be fast.
```

**Step 2: Commit migration guide**

```bash
git add docs/migrations/
git commit -m "docs: add SQLite to Milvus migration guide"
```

---

### Task 8.2: User Documentation

**Files:**
- Modify: `docs/cache.md`
- Modify: `docs/tools.md`
- Modify: `README.md`

#### Step 1: Update docs/cache.md with Milvus Lite details

Edit `docs/cache.md` to add Milvus Lite section:

```markdown
## Cache Backends

LoreKeeper supports two cache backends:

### Milvus Lite (Default)

Milvus Lite is the default cache backend, providing:
- **Semantic Search:** Find content using natural language queries
- **Vector Embeddings:** Content is indexed with 384-dimensional embeddings
- **Hybrid Search:** Combine semantic search with structured filters
- **Embedded Operation:** No separate database server required

Configuration:
```bash
LOREKEEPER_CACHE_BACKEND=milvus
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### SQLite (Legacy)

SQLite is available for backward compatibility:
- **Structured Filtering:** Filter by level, school, CR, etc.
- **No Semantic Search:** Only exact/structured queries
- **Lightweight:** Minimal dependencies

Configuration:
```bash
LOREKEEPER_CACHE_BACKEND=sqlite
LOREKEEPER_DB_PATH=./data/cache.db
```

## Semantic Search

Semantic search uses vector embeddings to find conceptually related content:

```python
# Find healing-related spells (even if "heal" isn't in the name)
results = await cache.semantic_search("spells", "restore health to allies")

# Combine with filters
results = await cache.semantic_search("spells", "fire damage", level=3)
```

### How It Works

1. **Indexing:** When entities are stored, searchable text is extracted and converted to 384-dimensional embeddings using the `all-MiniLM-L6-v2` model.

2. **Querying:** Search queries are also converted to embeddings.

3. **Matching:** Milvus finds entities whose embeddings are closest (cosine similarity) to the query embedding.

4. **Filtering:** Optional scalar filters (level, school, etc.) are applied during the vector search.

### Entity-Specific Text Extraction

Different entity types have different fields extracted for embedding:

| Entity Type | Extracted Fields |
|-------------|------------------|
| Spells | name, desc, higher_level |
| Creatures | name, desc, type, action names, ability names |
| Equipment | name, desc, type, properties |
| Rules | name, desc, content |
| Character Options | name, desc |
```

**Step 2: Update docs/tools.md with semantic search examples**

Edit `docs/tools.md` to add semantic search examples to each tool:

```markdown
## Semantic Search

All lookup tools support a `semantic_query` parameter for natural language search:

### Spell Lookup

```python
# Traditional filter
await lookup_spell(name="Fireball")

# Semantic search
await lookup_spell(semantic_query="fire damage spells")

# Combined: semantic + filter
await lookup_spell(semantic_query="healing", level=1)
```

### Creature Lookup

```python
# Traditional filter
await lookup_creature(type="dragon")

# Semantic search
await lookup_creature(semantic_query="fire breathing flying beast")

# Combined: semantic + CR filter
await lookup_creature(semantic_query="undead", cr_min=5)
```

### Equipment Lookup

```python
# Traditional filter
await lookup_equipment(type="weapon", name="Longsword")

# Semantic search
await lookup_equipment(type="all", semantic_query="magical protection")
```

### Character Option Lookup

```python
# Traditional filter
await lookup_character_option(type="class", name="Fighter")

# Semantic search
await lookup_character_option(type="class", semantic_query="spellcasting classes")
```

### Rule Lookup

```python
# Traditional filter
await lookup_rule(rule_type="condition", name="Grappled")

# Semantic search
await lookup_rule(rule_type="condition", semantic_query="movement restrictions")
```

## Search DnD Content

The unified search tool supports both fuzzy and semantic search:

```python
# Semantic search (default)
await search_dnd_content(query="healing magic")

# Disable semantic for keyword-only search
await search_dnd_content(query="fireball", enable_semantic=False)

# Combined fuzzy + semantic
await search_dnd_content(query="firbal", enable_fuzzy=True, enable_semantic=True)
```
```

**Step 3: Add semantic search examples to README.md**

Edit `README.md` to add semantic search usage examples in the appropriate section:

```markdown
### Semantic Search (New!)

Search using natural language queries:

```bash
# Find fire-related spells
lorekeeper lookup spell --semantic "fire damage spells"

# Find healing content
lorekeeper lookup spell --semantic "restore health to allies"

# Find flying creatures
lorekeeper lookup creature --semantic "flying monsters"

# Combine semantic + filters
lorekeeper lookup spell --semantic "fire" --level 3
```

Semantic search requires the Milvus cache backend (default). On first use, an embedding model (~80MB) will be downloaded.
```

**Step 4: Update .env.example with documented comments**

Ensure `.env.example` has clear documentation for all cache-related variables (if not already done in Task 4):

```bash
# =============================================================================
# Cache Backend Configuration
# =============================================================================

# Cache backend type: "milvus" (default) or "sqlite"
# - milvus: Enables semantic/vector search (recommended)
# - sqlite: Legacy backend, structured filtering only
LOREKEEPER_CACHE_BACKEND=milvus

# Path to Milvus Lite database file
# The embedding model (~80MB) will be downloaded on first use
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db

# Embedding model for semantic search
# Default: all-MiniLM-L6-v2 (384 dimensions, good balance of speed/quality)
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Legacy SQLite database path (when CACHE_BACKEND=sqlite)
LOREKEEPER_DB_PATH=./data/cache.db
```

**Step 5: Commit documentation updates**

```bash
git add docs/cache.md docs/tools.md README.md .env.example
git commit -m "docs: update documentation with Milvus cache and semantic search"
```

---

### Task 8.3: Code Documentation

**Files:**
- Modify: `src/lorekeeper_mcp/cache/milvus.py`
- Modify: `src/lorekeeper_mcp/cache/embedding.py`
- Modify: `src/lorekeeper_mcp/cache/factory.py`

#### Step 1: Verify all public methods have complete docstrings

Review and update docstrings in `src/lorekeeper_mcp/cache/milvus.py`:

```python
class MilvusCache:
    """Milvus Lite-backed cache implementation with semantic search support.

    This class implements the CacheProtocol interface using Milvus Lite as the
    storage backend. It provides:

    - **Structured Filtering:** Same filtering capabilities as SQLiteCache
    - **Semantic Search:** Vector similarity search using embeddings
    - **Hybrid Search:** Combine semantic queries with scalar filters
    - **Lazy Initialization:** Resources are loaded on first use

    The cache uses 384-dimensional embeddings generated by the all-MiniLM-L6-v2
    model (configurable). Each entity type is stored in a separate Milvus
    collection with entity-specific scalar fields for filtering.

    Example:
        ```python
        async with MilvusCache("~/.lorekeeper/milvus.db") as cache:
            # Store entities
            await cache.store_entities(spells, "spells")

            # Structured query
            results = await cache.get_entities("spells", level=3)

            # Semantic search
            results = await cache.semantic_search("spells", "fire damage")

            # Hybrid search
            results = await cache.semantic_search("spells", "fire", level=3)
        ```

    Attributes:
        db_path: Path to the Milvus Lite database file.

    See Also:
        - EmbeddingService: Generates embeddings for semantic search
        - CacheProtocol: Interface this class implements
        - SQLiteCache: Alternative backend without semantic search
    """
```

**Step 2: Add inline comments for complex logic**

Review `src/lorekeeper_mcp/cache/milvus.py` and add comments for:

```python
def _build_filter_expression(self, filters: dict[str, Any]) -> str:
    """Build Milvus filter expression from keyword filters.

    Milvus uses a SQL-like expression syntax for filtering:
    - String equality: field == "value"
    - Numeric equality: field == 123
    - Boolean: field == true/false (lowercase)
    - IN clause: field in ["a", "b", "c"]

    Multiple conditions are joined with 'and'.
    """
    expressions: list[str] = []

    for field, value in filters.items():
        if value is None:
            continue

        # String values need quotes
        if isinstance(value, str):
            expressions.append(f'{field} == "{value}"')
        # Milvus uses lowercase boolean literals
        elif isinstance(value, bool):
            expressions.append(f"{field} == {str(value).lower()}")
        # Numeric values are unquoted
        elif isinstance(value, (int, float)):
            expressions.append(f"{field} == {value}")
        # List values use IN clause syntax
        elif isinstance(value, list):
            if all(isinstance(v, str) for v in value):
                quoted = [f'"{v}"' for v in value]
                expressions.append(f"{field} in [{', '.join(quoted)}]")
            else:
                expressions.append(f"{field} in {value}")

    return " and ".join(expressions)
```

**Step 3: Update EmbeddingService docstrings**

Verify `src/lorekeeper_mcp/cache/embedding.py` has complete documentation:

```python
class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers.

    This service converts text into 384-dimensional embedding vectors that
    capture semantic meaning. Similar texts will have embeddings that are
    close together in vector space, enabling semantic search.

    The embedding model is loaded lazily on first use to avoid startup delays
    when the cache is not needed. The model is cached by sentence-transformers
    in ~/.cache/torch/sentence_transformers/.

    Example:
        ```python
        service = EmbeddingService()

        # Single text
        embedding = service.encode("A fireball spell")
        # Returns: [0.123, -0.456, ...] (384 floats)

        # Batch encoding (more efficient)
        embeddings = service.encode_batch(["Spell 1", "Spell 2", "Spell 3"])
        # Returns: [[...], [...], [...]]

        # Extract searchable text from entity
        text = service.get_searchable_text(spell_dict, "spells")
        ```

    Attributes:
        model_name: Name of the sentence-transformers model.

    Note:
        The default model (all-MiniLM-L6-v2) requires ~80MB download on first use.
        Consider using a smaller model for resource-constrained environments.
    """
```

**Step 4: Run documentation linting**

```bash
just lint
```

Expected: No docstring-related warnings.

**Step 5: Commit code documentation**

```bash
git add src/lorekeeper_mcp/cache/
git commit -m "docs(cache): add comprehensive docstrings and inline comments"
```

---

## Task 8 Complete

At this point, Task 8 (Migration and Documentation) is complete:

- ✅ 8.1 Migration Guide:
  - Documented breaking changes
  - Provided step-by-step migration instructions
  - Documented re-indexing requirements
  - Provided rollback procedure

- ✅ 8.2 User Documentation:
  - Updated docs/cache.md with Milvus Lite details
  - Updated docs/tools.md with semantic search examples
  - Updated README.md with semantic search usage
  - Updated .env.example with clear documentation

- ✅ 8.3 Code Documentation:
  - Added comprehensive docstrings to MilvusCache class
  - Added comprehensive docstrings to EmbeddingService class
  - Added inline comments for complex logic
  - Ensured all public methods are documented

---

## Task 9: Cleanup and Finalization

### Task 9.1: Code Quality

**Step 1: Run linting**

```bash
just lint
```

Expected: No lint errors. Fix any issues that arise.

**Step 2: Run formatting**

```bash
just format
```

Expected: Code is properly formatted. Commit any changes.

**Step 3: Run type checking**

```bash
just type-check
```

Expected: No type errors. Fix any issues that arise.

**Step 4: Run full test suite**

```bash
just test
```

Expected: All tests pass.

**Step 5: Run full quality checks**

```bash
just check
```

Expected: All quality checks pass (lint, format, type-check, test combined).

**Step 6: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve lint, format, and type-check issues"
```

---

### Task 9.2: Final Verification

**Step 1: Run live tests (CRITICAL)**

```bash
uv run pytest tests/test_tools/test_live_mcp.py -v --run-live
```

Expected: All live tests pass. This is CRITICAL per rule #1.

**Step 2: Manual testing of semantic search**

Test semantic search with varied queries manually:

```bash
# Test spell semantic search
uv run python -c "
import asyncio
from lorekeeper_mcp.cache.milvus import MilvusCache

async def test():
    cache = MilvusCache('~/.lorekeeper/milvus.db')
    results = await cache.semantic_search('spells', 'fire damage explosion')
    print(f'Found {len(results)} fire spells')
    for r in results[:3]:
        print(f'  - {r.get(\"name\")}')

asyncio.run(test())
"
```

Expected: Returns relevant fire-related spells.

**Step 3: Test with fresh install**

```bash
# Remove existing cache
rm -rf ~/.lorekeeper/milvus.db

# Re-import data
lorekeeper import --source open5e --document srd

# Verify data is accessible
lorekeeper lookup spell --name "Fireball"
```

Expected: Import succeeds and lookup returns results.

**Step 4: Test upgrade from SQLite**

```bash
# Ensure SQLite cache exists (if not, create one)
LOREKEEPER_CACHE_BACKEND=sqlite lorekeeper import --source open5e --document srd --limit 10

# Switch to Milvus backend
export LOREKEEPER_CACHE_BACKEND=milvus

# Verify Milvus cache is empty (fresh start)
lorekeeper stats

# Re-import for Milvus
lorekeeper import --source open5e --document srd --limit 10

# Verify both backends work by switching between them
LOREKEEPER_CACHE_BACKEND=sqlite lorekeeper lookup spell --name "Fireball"
LOREKEEPER_CACHE_BACKEND=milvus lorekeeper lookup spell --name "Fireball"
```

Expected: Both backends work independently, Milvus supports semantic search.

**Step 5: Verify all existing live tests continue to pass**

```bash
# Run all live tests
uv run pytest -v --run-live
```

Expected: ALL live tests pass. This is CRITICAL per rule #1.

**Step 6: Test semantic search quality with real D&D content**

```bash
# Test various semantic queries
uv run python -c "
import asyncio
from lorekeeper_mcp.cache.milvus import MilvusCache

async def test_queries():
    cache = MilvusCache('~/.lorekeeper/milvus.db')

    queries = [
        ('spells', 'healing magic'),
        ('spells', 'area of effect damage'),
        ('spells', 'buff allies'),
        ('creatures', 'undead monsters'),
        ('creatures', 'flying beasts'),
    ]

    for entity_type, query in queries:
        results = await cache.semantic_search(entity_type, query, limit=3)
        print(f'{query}: {[r.get(\"name\") for r in results]}')

asyncio.run(test_queries())
"
```

Expected: Results are semantically relevant to queries.

**Step 7: Commit verification results**

```bash
git add -A
git commit -m "test: verify all live tests and semantic search quality"
```

---

### Task 9.3: Archive Previous Proposal

**Step 1: Move replace-sqlite-with-marqo proposal to archive**

```bash
# Create archive directory if needed
mkdir -p openspec/changes/archive/2025-11-replace-sqlite-with-marqo

# Move the proposal
mv openspec/changes/replace-sqlite-with-marqo/* openspec/changes/archive/2025-11-replace-sqlite-with-marqo/

# Remove empty directory
rmdir openspec/changes/replace-sqlite-with-marqo
```

**Step 2: Update any references to Marqo proposal**

Search for references to the Marqo proposal and update them:

```bash
rg -l "replace-sqlite-with-marqo" --type md
```

Update any found references to point to the archived location or remove them.

**Step 3: Commit archive**

```bash
git add openspec/changes/
git commit -m "chore: archive superseded replace-sqlite-with-marqo proposal"
```

---

## Task 9 Complete

At this point, Task 9 (Cleanup and Finalization) is complete:

- ✅ 9.1 Code Quality:
  - Ran `just lint` and fixed all issues
  - Ran `just format` to ensure consistent formatting
  - Ran `just type-check` and fixed all type errors
  - Ran `just test` and ensured all tests pass
  - Ran `just check` for full quality validation

- ✅ 9.2 Final Verification:
  - Verified live tests pass with real APIs (CRITICAL)
  - Manual testing of semantic search with varied queries
  - Tested with fresh install (no existing cache)
  - Tested upgrade from SQLite to Milvus
  - Verified all existing live tests continue to pass
  - Tested semantic search quality with real D&D content

- ✅ 9.3 Archive Previous Proposal:
  - Archived `replace-sqlite-with-marqo` proposal (superseded)
  - Updated any references to Marqo proposal

---

## Plan Complete

### Summary

This implementation plan replaced the SQLite cache backend with Milvus Lite, enabling semantic/vector search capabilities while maintaining full backward compatibility.

### Key Deliverables

1. **MilvusCache Implementation**
   - Full CacheProtocol implementation
   - Semantic search with 384-dimensional embeddings
   - Hybrid search (semantic + scalar filters)
   - Lazy initialization for performance

2. **EmbeddingService**
   - Lazy model loading (all-MiniLM-L6-v2)
   - Single and batch text encoding
   - Entity-type-specific text extraction

3. **Cache Factory**
   - Backend selection via environment variable
   - Support for both Milvus and SQLite backends
   - Configuration-based cache creation

4. **Tool Updates**
   - `semantic_query` parameter added to all lookup tools
   - Backward compatible (works without semantic_query)
   - Automatic fallback when using SQLite backend

5. **Configuration**
   - `LOREKEEPER_CACHE_BACKEND` - Backend selection
   - `LOREKEEPER_MILVUS_DB_PATH` - Database path
   - `LOREKEEPER_EMBEDDING_MODEL` - Model selection

6. **Documentation**
   - Migration guide from SQLite to Milvus
   - User documentation with examples
   - Comprehensive code documentation

7. **Testing**
   - Unit tests for MilvusCache and EmbeddingService
   - Integration tests with real embeddings
   - Performance benchmarks
   - All live tests passing (CRITICAL)

### Total Steps

- **Task 1 (Core Infrastructure):** 30 steps
- **Task 2 (CacheProtocol Implementation):** 24 steps
- **Task 3 (Protocol and Factory Updates):** 20 steps
- **Task 4 (Configuration Updates):** 10 steps
- **Task 5 (Repository Integration):** 22 steps
- **Task 6 (Tool Updates):** 35 steps
- **Task 7 (Testing):** 28 steps
- **Task 8 (Migration and Documentation):** 15 steps
- **Task 9 (Cleanup and Finalization):** 10 steps

**Total: ~194 steps**
