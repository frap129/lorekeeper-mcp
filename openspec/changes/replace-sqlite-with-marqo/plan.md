# Replace SQLite with Marqo Implementation Plan

**Goal:** Replace SQLite-based entity caching with Marqo to enable semantic search while maintaining all existing structured filtering functionality.

**Architecture:** Replace synchronous SQLite operations with async-wrapped Marqo client calls. Maintain drop-in compatibility with existing cache API. Add new semantic search and similarity functions.

**Tech Stack:** Marqo (vector search engine), marqo Python client, Docker/Podman, hf/e5-base-v2 embeddings

---

## Critical Architecture Note

⚠️ **IMPORTANT**: The Marqo Python client is **SYNCHRONOUS**. All Marqo operations must be wrapped with `asyncio.to_thread()` to maintain compatibility with our async codebase.

```python
# WRONG (blocks event loop):
result = client.index("my-index").search("query")

# CORRECT (runs in thread pool):
result = await asyncio.to_thread(client.index("my-index").search, "query")
```

---

## Phase 1: Infrastructure & Configuration

### Task 1.1: Add Marqo Python Client Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add marqo to dependencies**

Edit `pyproject.toml` and add `marqo` to dependencies section:

```toml
dependencies = [
    "marqo>=2.0.0",
    # ... existing dependencies
]
```

**Step 2: Install dependencies**

Run: `uv sync`
Expected: Package resolves and installs without conflicts

**Step 3: Verify installation**

Run: `uv run python -c "import marqo; print(f'Marqo version: {marqo.__version__}')"`
Expected: Prints Marqo version without errors

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add marqo dependency for vector search"
```

---

### Task 1.2: Create Docker Compose Configuration

**Files:**
- Create: `docker-compose.yml`
- Modify: `README.md`
- Modify: `.gitignore`

**Step 1: Write docker-compose.yml**

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  marqo:
    image: marqoai/marqo:latest
    container_name: lorekeeper-marqo
    ports:
      - "8882:8882"
    environment:
      - MARQO_ENABLE_BATCH_APIS=TRUE
      - MARQO_MAX_DOCUMENTS_BATCH_SIZE=100
    volumes:
      - marqo-data:/opt/vespa/var
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8882/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  marqo-data:
    driver: local
```

**Step 2: Update .gitignore**

Add to `.gitignore`:

```
# Marqo data (if running locally without Docker)
.marqo/
```

**Step 3: Update README with Marqo setup**

Add section to `README.md`:

````markdown
### Marqo Setup

LoreKeeper uses Marqo for semantic search and caching. Start Marqo with Docker:

```bash
# Start Marqo service
docker-compose up -d marqo

# Check health
curl http://localhost:8882/health

# View logs
docker-compose logs -f marqo

# Stop service
docker-compose down
```

Marqo will be available at `http://localhost:8882`.
````

**Step 4: Test Docker setup**

Run: `docker-compose up -d marqo`
Expected: Marqo container starts successfully

Run: `sleep 10 && curl http://localhost:8882/health`
Expected: Returns HTTP 200 with health status

Run: `docker-compose down`
Expected: Container stops cleanly

**Step 5: Commit**

```bash
git add docker-compose.yml README.md .gitignore
git commit -m "feat: add docker-compose config for marqo service"
```

---

### Task 1.3: Update Configuration Settings

**Files:**
- Modify: `src/lorekeeper_mcp/config.py:18-19`
- Modify: `.env.example`

**Step 1: Update Settings class**

Replace SQLite settings with Marqo settings in `config.py`:

```python
class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Remove these lines:
    # db_path: Path = Field(default=Path("./data/cache.db"))
    # cache_ttl_days: int = Field(default=7)

    # Add these lines:
    marqo_url: str = Field(default="http://localhost:8882")
    marqo_timeout: int = Field(default=30)
    marqo_batch_size: int = Field(default=100)
    marqo_model: str = Field(default="hf/e5-base-v2")

    # Keep existing fields:
    error_cache_ttl_seconds: int = Field(default=300)
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    open5e_base_url: str = Field(default="https://api.open5e.com")
    dnd5e_base_url: str = Field(default="https://www.dnd5eapi.co/api")
```

**Step 2: Update .env.example**

Replace SQLite variables with Marqo variables:

```bash
# Marqo Configuration
MARQO_URL=http://localhost:8882
MARQO_TIMEOUT=30
MARQO_BATCH_SIZE=100
MARQO_MODEL=hf/e5-base-v2

# API Configuration
OPEN5E_BASE_URL=https://api.open5e.com
DND5E_BASE_URL=https://www.dnd5eapi.co/api

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

**Step 3: Write test for new config**

Create `tests/test_config_marqo.py`:

```python
"""Test Marqo configuration settings."""

from lorekeeper_mcp.config import Settings


def test_marqo_settings_defaults():
    """Test default Marqo settings."""
    settings = Settings()

    assert settings.marqo_url == "http://localhost:8882"
    assert settings.marqo_timeout == 30
    assert settings.marqo_batch_size == 100
    assert settings.marqo_model == "hf/e5-base-v2"


def test_marqo_settings_from_env(monkeypatch):
    """Test Marqo settings can be overridden from environment."""
    monkeypatch.setenv("MARQO_URL", "http://marqo-prod:8882")
    monkeypatch.setenv("MARQO_TIMEOUT", "60")
    monkeypatch.setenv("MARQO_BATCH_SIZE", "200")

    settings = Settings()

    assert settings.marqo_url == "http://marqo-prod:8882"
    assert settings.marqo_timeout == 60
    assert settings.marqo_batch_size == 200
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_config_marqo.py -v`
Expected: Tests fail (config not updated yet or pass if already updated)

**Step 5: Apply the config changes if test failed**

(Apply the changes from Step 1)

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_config_marqo.py -v`
Expected: All tests pass

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/config.py .env.example tests/test_config_marqo.py
git commit -m "feat: add marqo configuration settings"
```

---

## Phase 2: Core Marqo Client & Index Setup

### Task 2.1: Create Marqo Client Manager Module

**Files:**
- Create: `src/lorekeeper_mcp/cache/marqo_client.py`

**Step 1: Write failing test for client manager**

Create `tests/test_cache/test_marqo_client.py`:

```python
"""Tests for Marqo client management."""

import pytest
from unittest.mock import MagicMock, patch

from lorekeeper_mcp.cache.marqo_client import MarqoClientManager, check_marqo_health


def test_get_client_creates_singleton():
    """Test that get_client returns singleton instance."""
    MarqoClientManager._instance = None

    with patch("marqo.Client") as mock_client_class:
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance

        client1 = MarqoClientManager.get_client()
        client2 = MarqoClientManager.get_client()

        assert client1 is client2
        assert mock_client_class.call_count == 1


def test_get_client_uses_config_url():
    """Test that client connects to configured URL."""
    MarqoClientManager._instance = None

    with patch("marqo.Client") as mock_client_class:
        with patch("lorekeeper_mcp.cache.marqo_client.settings") as mock_settings:
            mock_settings.marqo_url = "http://test:8882"

            MarqoClientManager.get_client()

            mock_client_class.assert_called_once_with(url="http://test:8882")


def test_close_clears_instance():
    """Test that close clears the singleton."""
    MarqoClientManager._instance = MagicMock()

    MarqoClientManager.close()

    assert MarqoClientManager._instance is None


@pytest.mark.asyncio
async def test_check_marqo_health_success():
    """Test health check returns True when Marqo is available."""
    with patch.object(MarqoClientManager, "get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_indexes.return_value = {"results": []}
        mock_get_client.return_value = mock_client

        result = await check_marqo_health()

        assert result is True
        mock_client.get_indexes.assert_called_once()


@pytest.mark.asyncio
async def test_check_marqo_health_failure():
    """Test health check returns False when Marqo is unavailable."""
    with patch.object(MarqoClientManager, "get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_indexes.side_effect = Exception("Connection refused")
        mock_get_client.return_value = mock_client

        result = await check_marqo_health()

        assert result is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_client.py -v`
Expected: FAIL - module does not exist

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/cache/marqo_client.py`:

```python
"""Marqo client management and health checks."""

import asyncio
import logging

import marqo

from lorekeeper_mcp.config import settings

logger = logging.getLogger(__name__)


class MarqoClientManager:
    """Singleton manager for Marqo client lifecycle.

    The Marqo client is synchronous, so all operations must be wrapped
    with asyncio.to_thread() when called from async code.
    """

    _instance: marqo.Client | None = None

    @classmethod
    def get_client(cls) -> marqo.Client:
        """Get or create Marqo client singleton.

        Returns:
            Marqo client instance
        """
        if cls._instance is None:
            cls._instance = marqo.Client(url=settings.marqo_url)
            logger.info(f"Marqo client connected to {settings.marqo_url}")
        return cls._instance

    @classmethod
    def close(cls) -> None:
        """Close Marqo client and clear singleton.

        Note: The Marqo client does not have a close method,
        so this just clears the singleton reference.
        """
        cls._instance = None
        logger.info("Marqo client closed")


async def check_marqo_health() -> bool:
    """Check if Marqo service is healthy.

    Returns:
        True if Marqo is available and responsive, False otherwise
    """
    try:
        client = MarqoClientManager.get_client()
        # Synchronous call - run in thread pool
        await asyncio.to_thread(client.get_indexes)
        return True
    except Exception as e:
        logger.warning(f"Marqo health check failed: {e}")
        return False
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/cache/marqo_client.py tests/test_cache/test_marqo_client.py
git commit -m "feat: add marqo client manager with singleton pattern"
```

---

### Task 2.2: Rewrite Schema Module for Marqo Indexes

**Files:**
- Modify: `src/lorekeeper_mcp/cache/schema.py` (complete rewrite)

**Step 1: Write failing test for schema definitions**

Create `tests/test_cache/test_marqo_schema.py`:

```python
"""Tests for Marqo index schema definitions."""

import pytest

from lorekeeper_mcp.cache.schema import (
    ENTITY_TYPES,
    TENSOR_FIELDS,
    get_index_name,
    get_index_settings,
    get_tensor_fields,
)


def test_entity_types_defined():
    """Test that all entity types are defined."""
    expected_types = [
        "spells",
        "monsters",
        "weapons",
        "armor",
        "classes",
        "races",
        "backgrounds",
        "feats",
        "conditions",
        "rules",
        "rule_sections",
    ]

    assert set(ENTITY_TYPES) == set(expected_types)


def test_get_index_name():
    """Test index name generation."""
    assert get_index_name("spells") == "lorekeeper-spells"
    assert get_index_name("monsters") == "lorekeeper-monsters"


def test_get_index_name_invalid_type():
    """Test that invalid entity type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid entity type"):
        get_index_name("invalid_type")


def test_get_tensor_fields_spells():
    """Test tensor fields for spells."""
    fields = get_tensor_fields("spells")

    assert "name" in fields
    assert "desc" in fields
    assert "higher_level" in fields


def test_get_tensor_fields_monsters():
    """Test tensor fields for monsters."""
    fields = get_tensor_fields("monsters")

    assert "name" in fields
    assert "desc" in fields


def test_get_tensor_fields_invalid_type():
    """Test that invalid entity type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid entity type"):
        get_tensor_fields("invalid_type")


def test_get_index_settings():
    """Test index settings generation."""
    settings = get_index_settings("spells")

    assert settings["model"] == "hf/e5-base-v2"
    assert settings["normalizeEmbeddings"] is True
    assert "textPreprocessing" in settings
    assert settings["textPreprocessing"]["splitMethod"] == "sentence"


def test_tensor_fields_coverage():
    """Test that all entity types have tensor fields defined."""
    for entity_type in ENTITY_TYPES:
        fields = TENSOR_FIELDS.get(entity_type)
        assert fields is not None, f"Missing tensor fields for {entity_type}"
        assert len(fields) > 0, f"Empty tensor fields for {entity_type}"
        assert "name" in fields, f"'name' field missing for {entity_type}"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_schema.py -v`
Expected: FAIL - functions don't exist

**Step 3: Write minimal implementation**

Rewrite `src/lorekeeper_mcp/cache/schema.py`:

```python
"""Marqo index schema definitions and configuration."""

SCHEMA_VERSION = 2  # Incremented from SQLite schema version

ENTITY_TYPES = [
    "spells",
    "monsters",
    "weapons",
    "armor",
    "classes",
    "races",
    "backgrounds",
    "feats",
    "conditions",
    "rules",
    "rule_sections",
]

# Tensor fields per entity type (fields to embed as vectors)
TENSOR_FIELDS = {
    "spells": ["name", "desc", "higher_level"],
    "monsters": ["name", "desc"],
    "weapons": ["name", "desc"],
    "armor": ["name", "desc"],
    "classes": ["name", "desc"],
    "races": ["name", "desc", "traits"],
    "backgrounds": ["name", "desc"],
    "feats": ["name", "desc"],
    "conditions": ["name", "desc"],
    "rules": ["name", "desc"],
    "rule_sections": ["name", "desc"],
}

# Filterable fields per entity type (for structured queries)
FILTERABLE_FIELDS = {
    "spells": ["level", "school", "concentration", "ritual"],
    "monsters": ["challenge_rating", "type", "size"],
    "weapons": ["category", "damage_type"],
    "armor": ["category", "armor_class"],
    "classes": ["hit_die"],
    "races": ["size"],
    "backgrounds": [],
    "feats": [],
    "conditions": [],
    "rules": ["parent"],
    "rule_sections": ["parent"],
}


def get_index_name(entity_type: str) -> str:
    """Get Marqo index name for entity type.

    Args:
        entity_type: Type of entity (spells, monsters, etc.)

    Returns:
        Marqo index name with lorekeeper- prefix

    Raises:
        ValueError: If entity_type is invalid
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    return f"lorekeeper-{entity_type}"


def get_tensor_fields(entity_type: str) -> list[str]:
    """Get tensor fields for entity type.

    These are the fields that will be embedded as vectors for semantic search.

    Args:
        entity_type: Type of entity

    Returns:
        List of field names to embed

    Raises:
        ValueError: If entity_type is invalid
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    return TENSOR_FIELDS[entity_type]


def get_filterable_fields(entity_type: str) -> list[str]:
    """Get filterable fields for entity type.

    These are fields that can be used in filter_string for structured queries.

    Args:
        entity_type: Type of entity

    Returns:
        List of filterable field names

    Raises:
        ValueError: If entity_type is invalid
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    return FILTERABLE_FIELDS[entity_type]


def get_index_settings(entity_type: str) -> dict[str, any]:
    """Get Marqo index settings for entity type.

    Args:
        entity_type: Type of entity

    Returns:
        Dictionary of index settings for create_index

    Raises:
        ValueError: If entity_type is invalid
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    return {
        "model": "hf/e5-base-v2",
        "normalizeEmbeddings": True,
        "textPreprocessing": {
            "splitLength": 2,
            "splitOverlap": 0,
            "splitMethod": "sentence",
        },
    }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_schema.py -v`
Expected: PASS

**Step 5: Update __init__.py exports**

Update `src/lorekeeper_mcp/cache/__init__.py`:

```python
"""Cache module for LoreKeeper MCP."""

from lorekeeper_mcp.cache.marqo_client import MarqoClientManager, check_marqo_health
from lorekeeper_mcp.cache.schema import (
    ENTITY_TYPES,
    FILTERABLE_FIELDS,
    SCHEMA_VERSION,
    TENSOR_FIELDS,
    get_filterable_fields,
    get_index_name,
    get_index_settings,
    get_tensor_fields,
)

__all__ = [
    "MarqoClientManager",
    "check_marqo_health",
    "ENTITY_TYPES",
    "TENSOR_FIELDS",
    "FILTERABLE_FIELDS",
    "SCHEMA_VERSION",
    "get_index_name",
    "get_tensor_fields",
    "get_filterable_fields",
    "get_index_settings",
]
```

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/schema.py src/lorekeeper_mcp/cache/__init__.py tests/test_cache/test_marqo_schema.py
git commit -m "feat: rewrite schema module for marqo indexes"
```

---

### Task 2.3: Implement Index Initialization

**Files:**
- Modify: `src/lorekeeper_mcp/cache/schema.py` (add init_indexes function)

**Step 1: Write failing test for init_indexes**

Add to `tests/test_cache/test_marqo_schema.py`:

```python
@pytest.mark.asyncio
async def test_init_indexes_creates_all_indexes(mock_marqo_client):
    """Test that init_indexes creates all entity type indexes."""
    from lorekeeper_mcp.cache.schema import init_indexes

    mock_client = MagicMock()
    mock_marqo_client.return_value = mock_client

    # Mock get_indexes to return empty list (no existing indexes)
    mock_client.get_indexes.return_value = {"results": []}

    await init_indexes()

    # Should create index for each entity type
    assert mock_client.create_index.call_count == len(ENTITY_TYPES)


@pytest.mark.asyncio
async def test_init_indexes_skips_existing(mock_marqo_client):
    """Test that init_indexes skips already existing indexes."""
    from lorekeeper_mcp.cache.schema import init_indexes

    mock_client = MagicMock()
    mock_marqo_client.return_value = mock_client

    # Mock some indexes already exist
    mock_client.get_indexes.return_value = {
        "results": [
            {"index_name": "lorekeeper-spells"},
            {"index_name": "lorekeeper-monsters"},
        ]
    }

    await init_indexes()

    # Should only create missing indexes
    expected_calls = len(ENTITY_TYPES) - 2
    assert mock_client.create_index.call_count == expected_calls


@pytest.fixture
def mock_marqo_client(monkeypatch):
    """Mock MarqoClientManager.get_client."""
    with patch("lorekeeper_mcp.cache.schema.MarqoClientManager.get_client") as mock:
        yield mock
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_schema.py::test_init_indexes_creates_all_indexes -v`
Expected: FAIL - init_indexes doesn't exist

**Step 3: Implement init_indexes function**

Add to `src/lorekeeper_mcp/cache/schema.py`:

```python
import asyncio
import logging

from lorekeeper_mcp.cache.marqo_client import MarqoClientManager

logger = logging.getLogger(__name__)


async def init_indexes() -> None:
    """Initialize all Marqo indexes for entity types.

    Creates indexes for all entity types defined in ENTITY_TYPES.
    Skips indexes that already exist.

    Raises:
        Exception: If index creation fails
    """
    client = MarqoClientManager.get_client()

    # Get existing indexes (synchronous call - run in thread)
    try:
        indexes_response = await asyncio.to_thread(client.get_indexes)
        existing_indexes = {idx["index_name"] for idx in indexes_response.get("results", [])}
    except Exception as e:
        logger.warning(f"Failed to get existing indexes: {e}")
        existing_indexes = set()

    # Create missing indexes
    for entity_type in ENTITY_TYPES:
        index_name = get_index_name(entity_type)

        if index_name in existing_indexes:
            logger.debug(f"Index {index_name} already exists, skipping")
            continue

        logger.info(f"Creating index: {index_name}")
        settings = get_index_settings(entity_type)

        try:
            # Synchronous call - run in thread
            await asyncio.to_thread(
                client.create_index,
                index_name,
                settings_dict=settings
            )
            logger.info(f"Created index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            raise
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_schema.py::test_init_indexes_creates_all_indexes -v`
Expected: PASS

**Step 5: Run all schema tests**

Run: `uv run pytest tests/test_cache/test_marqo_schema.py -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/schema.py tests/test_cache/test_marqo_schema.py
git commit -m "feat: add init_indexes function for marqo"
```

---

## Phase 3: Core Cache Operations

### Task 3.1: Implement bulk_cache_entities

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py` (rewrite for Marqo)

**Step 1: Write failing test**

Create new test file `tests/test_cache/test_marqo_db.py`:

```python
"""Tests for Marqo-based cache database operations."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from lorekeeper_mcp.cache.db import bulk_cache_entities


@pytest.mark.asyncio
async def test_bulk_cache_entities_success():
    """Test bulk indexing entities in Marqo."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "desc": "A bright streak flashes..."},
        {"slug": "magic-missile", "name": "Magic Missile", "desc": "You create three glowing..."},
    ]

    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.add_documents.return_value = {"items": [{"status": 200}, {"status": 200}]}
        mock_get_client.return_value = mock_client

        count = await bulk_cache_entities(entities, "spells", source_api="test")

        assert count == 2
        mock_index.add_documents.assert_called_once()
        call_args = mock_index.add_documents.call_args
        assert len(call_args[0][0]) == 2  # 2 documents
        assert call_args[1]["tensor_fields"] == ["name", "desc", "higher_level"]


@pytest.mark.asyncio
async def test_bulk_cache_entities_empty_list():
    """Test that empty list returns 0."""
    count = await bulk_cache_entities([], "spells")
    assert count == 0


@pytest.mark.asyncio
async def test_bulk_cache_entities_invalid_type():
    """Test that invalid entity type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid entity type"):
        await bulk_cache_entities([{"slug": "test"}], "invalid_type")


@pytest.mark.asyncio
async def test_bulk_cache_entities_skips_missing_slug():
    """Test that entities without slug are skipped."""
    entities = [
        {"name": "No Slug"},  # Missing slug
        {"slug": "has-slug", "name": "Has Slug"},
    ]

    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.add_documents.return_value = {"items": [{"status": 200}]}
        mock_get_client.return_value = mock_client

        count = await bulk_cache_entities(entities, "spells")

        assert count == 1
        call_args = mock_index.add_documents.call_args
        assert len(call_args[0][0]) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_bulk_cache_entities_success -v`
Expected: FAIL - function not implemented

**Step 3: Write minimal implementation**

Rewrite `src/lorekeeper_mcp/cache/db.py` with bulk_cache_entities:

```python
"""Marqo-based cache database operations."""

import asyncio
import logging
from typing import Any

from lorekeeper_mcp.cache.marqo_client import MarqoClientManager
from lorekeeper_mcp.cache.schema import (
    ENTITY_TYPES,
    get_index_name,
    get_tensor_fields,
)

logger = logging.getLogger(__name__)


async def bulk_cache_entities(
    entities: list[dict[str, Any]],
    entity_type: str,
    source_api: str = "unknown",
) -> int:
    """Bulk index entities in Marqo.

    Args:
        entities: List of entity dictionaries (must have 'slug' field)
        entity_type: Type of entities (spells, monsters, etc.)
        source_api: Source API identifier

    Returns:
        Number of entities successfully indexed

    Raises:
        ValueError: If entity_type is invalid
    """
    if not entities:
        return 0

    # Validate entity type
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    # Prepare documents for indexing
    documents = []
    for entity in entities:
        slug = entity.get("slug")
        if not slug:
            logger.warning(f"Skipping entity without slug: {entity.get('name', 'unknown')}")
            continue

        # Add metadata
        doc = {**entity}
        doc["_id"] = slug  # Use slug as Marqo document ID
        doc["source_api"] = source_api

        documents.append(doc)

    if not documents:
        return 0

    # Index documents in Marqo
    client = MarqoClientManager.get_client()
    index_name = get_index_name(entity_type)
    tensor_fields = get_tensor_fields(entity_type)

    try:
        # Synchronous Marqo call - run in thread pool
        response = await asyncio.to_thread(
            client.index(index_name).add_documents,
            documents,
            tensor_fields=tensor_fields
        )

        # Count successful indexing
        items = response.get("items", [])
        success_count = sum(1 for item in items if item.get("status") in [200, 201])

        logger.info(f"Indexed {success_count}/{len(documents)} {entity_type} in Marqo")
        return success_count

    except Exception as e:
        logger.error(f"Failed to bulk index {entity_type}: {e}")
        return 0
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_bulk_cache_entities_success -v`
Expected: PASS

**Step 5: Run all bulk_cache tests**

Run: `uv run pytest tests/test_cache/test_marqo_db.py -k bulk_cache -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_marqo_db.py
git commit -m "feat: implement bulk_cache_entities with marqo"
```

---

### Task 3.2: Implement get_cached_entity

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py`

**Step 1: Write failing test**

Add to `tests/test_cache/test_marqo_db.py`:

```python
from lorekeeper_mcp.cache.db import get_cached_entity


@pytest.mark.asyncio
async def test_get_cached_entity_found():
    """Test retrieving an existing entity by slug."""
    expected_entity = {
        "_id": "fireball",
        "slug": "fireball",
        "name": "Fireball",
        "desc": "A bright streak...",
    }

    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.get_document.return_value = expected_entity
        mock_get_client.return_value = mock_client

        entity = await get_cached_entity("spells", "fireball")

        assert entity == expected_entity
        mock_index.get_document.assert_called_once_with("fireball")


@pytest.mark.asyncio
async def test_get_cached_entity_not_found():
    """Test that missing entity returns None."""
    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.get_document.side_effect = Exception("Document not found")
        mock_get_client.return_value = mock_client

        entity = await get_cached_entity("spells", "nonexistent")

        assert entity is None


@pytest.mark.asyncio
async def test_get_cached_entity_invalid_type():
    """Test that invalid entity type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid entity type"):
        await get_cached_entity("invalid_type", "some-slug")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_get_cached_entity_found -v`
Expected: FAIL - function not implemented

**Step 3: Implement get_cached_entity**

Add to `src/lorekeeper_mcp/cache/db.py`:

```python
async def get_cached_entity(
    entity_type: str,
    slug: str,
) -> dict[str, Any] | None:
    """Retrieve a single cached entity by slug.

    Args:
        entity_type: Type of entity
        slug: Entity slug (used as document ID)

    Returns:
        Entity data dictionary or None if not found

    Raises:
        ValueError: If entity_type is invalid
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    client = MarqoClientManager.get_client()
    index_name = get_index_name(entity_type)

    try:
        # Synchronous Marqo call - run in thread pool
        document = await asyncio.to_thread(
            client.index(index_name).get_document,
            slug
        )
        return document
    except Exception as e:
        logger.debug(f"Entity {slug} not found in {entity_type}: {e}")
        return None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_get_cached_entity_found -v`
Expected: PASS

**Step 5: Run all get_cached tests**

Run: `uv run pytest tests/test_cache/test_marqo_db.py -k get_cached -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_marqo_db.py
git commit -m "feat: implement get_cached_entity with marqo"
```

---

### Task 3.3: Implement query_cached_entities

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py`

**Step 1: Write failing test**

Add to `tests/test_cache/test_marqo_db.py`:

```python
from lorekeeper_mcp.cache.db import query_cached_entities


@pytest.mark.asyncio
async def test_query_cached_entities_with_filters():
    """Test querying entities with filters."""
    mock_results = {
        "hits": [
            {"_id": "fireball", "slug": "fireball", "name": "Fireball", "level": 3, "_score": 1.0},
            {"_id": "lightning-bolt", "slug": "lightning-bolt", "name": "Lightning Bolt", "level": 3, "_score": 0.95},
        ]
    }

    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.search.return_value = mock_results
        mock_get_client.return_value = mock_client

        results = await query_cached_entities("spells", level=3, school="Evocation")

        assert len(results) == 2
        assert results[0]["slug"] == "fireball"

        # Verify filter string was built correctly
        call_args = mock_index.search.call_args
        filter_string = call_args[1]["filter_string"]
        assert "level:3" in filter_string
        assert "school:Evocation" in filter_string


@pytest.mark.asyncio
async def test_query_cached_entities_no_filters():
    """Test querying without filters returns all entities."""
    mock_results = {
        "hits": [
            {"_id": "spell1", "slug": "spell1", "name": "Spell 1", "_score": 1.0},
            {"_id": "spell2", "slug": "spell2", "name": "Spell 2", "_score": 1.0},
        ]
    }

    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.search.return_value = mock_results
        mock_get_client.return_value = mock_client

        results = await query_cached_entities("spells")

        assert len(results) == 2

        # Should use empty query to get all docs
        call_args = mock_index.search.call_args
        assert call_args[0][0] == "" or call_args[0][0] == "*"


@pytest.mark.asyncio
async def test_query_cached_entities_invalid_filter():
    """Test that invalid filter field raises ValueError."""
    with pytest.raises(ValueError, match="Invalid filter field"):
        await query_cached_entities("spells", invalid_field="value")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_query_cached_entities_with_filters -v`
Expected: FAIL - function not implemented

**Step 3: Implement query_cached_entities**

Add to `src/lorekeeper_mcp/cache/db.py`:

```python
from lorekeeper_mcp.cache.schema import get_filterable_fields


async def query_cached_entities(
    entity_type: str,
    limit: int = 100,
    **filters: Any,
) -> list[dict[str, Any]]:
    """Query cached entities with optional filters.

    Args:
        entity_type: Type of entities to query
        limit: Maximum number of results to return
        **filters: Field filters (e.g., level=3, school="Evocation")

    Returns:
        List of matching entity dictionaries

    Raises:
        ValueError: If entity_type is invalid or filter field is not allowed
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    # Validate filter keys
    allowed_fields = set(get_filterable_fields(entity_type))
    for field in filters:
        if field not in allowed_fields:
            raise ValueError(
                f"Invalid filter field '{field}' for entity type '{entity_type}'. "
                f"Allowed fields: {sorted(allowed_fields) if allowed_fields else 'none'}"
            )

    # Build Marqo filter string
    filter_clauses = []
    for field, value in filters.items():
        if isinstance(value, str):
            filter_clauses.append(f"{field}:{value}")
        elif isinstance(value, (int, float)):
            filter_clauses.append(f"{field}:{value}")
        elif isinstance(value, bool):
            filter_clauses.append(f"{field}:{str(value).lower()}")
        elif isinstance(value, list):
            # Range filter for lists
            if len(value) == 2:
                filter_clauses.append(f"{field}:[{value[0]} TO {value[1]}]")
            else:
                # OR filter for multiple values
                or_values = " OR ".join(str(v) for v in value)
                filter_clauses.append(f"{field}:({or_values})")

    filter_string = " AND ".join(filter_clauses) if filter_clauses else None

    # Query Marqo
    client = MarqoClientManager.get_client()
    index_name = get_index_name(entity_type)

    try:
        # Use empty query to match all documents, filtered by filter_string
        search_args = {
            "q": "*",  # Match all
            "limit": limit,
        }
        if filter_string:
            search_args["filter_string"] = filter_string

        # Synchronous Marqo call - run in thread pool
        response = await asyncio.to_thread(
            client.index(index_name).search,
            **search_args
        )

        hits = response.get("hits", [])
        return hits

    except Exception as e:
        logger.error(f"Failed to query {entity_type}: {e}")
        return []
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_query_cached_entities_with_filters -v`
Expected: PASS

**Step 5: Run all query tests**

Run: `uv run pytest tests/test_cache/test_marqo_db.py -k query_cached -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_marqo_db.py
git commit -m "feat: implement query_cached_entities with marqo filtering"
```

---

### Task 3.4: Implement get_entity_count

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py`

**Step 1: Write failing test**

Add to `tests/test_cache/test_marqo_db.py`:

```python
from lorekeeper_mcp.cache.db import get_entity_count


@pytest.mark.asyncio
async def test_get_entity_count():
    """Test getting entity count from index stats."""
    mock_stats = {"numberOfDocuments": 42}

    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.get_stats.return_value = mock_stats
        mock_get_client.return_value = mock_client

        count = await get_entity_count("spells")

        assert count == 42


@pytest.mark.asyncio
async def test_get_entity_count_no_index():
    """Test that missing index returns 0."""
    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.get_stats.side_effect = Exception("Index not found")
        mock_get_client.return_value = mock_client

        count = await get_entity_count("spells")

        assert count == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_get_entity_count -v`
Expected: FAIL - function not implemented

**Step 3: Implement get_entity_count**

Add to `src/lorekeeper_mcp/cache/db.py`:

```python
async def get_entity_count(entity_type: str) -> int:
    """Get count of cached entities for a type.

    Args:
        entity_type: Type of entities to count

    Returns:
        Number of cached entities, or 0 if index doesn't exist
    """
    if entity_type not in ENTITY_TYPES:
        return 0

    client = MarqoClientManager.get_client()
    index_name = get_index_name(entity_type)

    try:
        # Synchronous Marqo call - run in thread pool
        stats = await asyncio.to_thread(
            client.index(index_name).get_stats
        )
        return stats.get("numberOfDocuments", 0)
    except Exception as e:
        logger.debug(f"Failed to get count for {entity_type}: {e}")
        return 0
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_get_entity_count -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_marqo_db.py
git commit -m "feat: implement get_entity_count with marqo stats"
```

---

## Phase 4: Semantic Search Features

### Task 4.1: Implement search_entities for Semantic Search

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py`

**Step 1: Write failing test**

Add to `tests/test_cache/test_marqo_db.py`:

```python
from lorekeeper_mcp.cache.db import search_entities


@pytest.mark.asyncio
async def test_search_entities_semantic():
    """Test semantic search for entities."""
    mock_results = {
        "hits": [
            {"_id": "protection-from-energy", "name": "Protection from Energy", "_score": 0.92},
            {"_id": "fire-shield", "name": "Fire Shield", "_score": 0.87},
        ]
    }

    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.search.return_value = mock_results
        mock_get_client.return_value = mock_client

        results = await search_entities("spells", query="protect from fire damage", limit=10)

        assert len(results) == 2
        assert results[0]["name"] == "Protection from Energy"
        assert results[0]["_score"] == 0.92

        # Verify semantic search was called with query
        call_args = mock_index.search.call_args
        assert call_args[1]["q"] == "protect from fire damage"
        assert call_args[1]["limit"] == 10


@pytest.mark.asyncio
async def test_search_entities_with_filters():
    """Test semantic search combined with filters."""
    mock_results = {
        "hits": [
            {"_id": "lesser-restoration", "name": "Lesser Restoration", "level": 2, "_score": 0.88},
        ]
    }

    with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_index = MagicMock()
        mock_client.index.return_value = mock_index
        mock_index.search.return_value = mock_results
        mock_get_client.return_value = mock_client

        results = await search_entities(
            "spells",
            query="healing magic",
            filters={"level": 2, "school": "Abjuration"},
            limit=5
        )

        assert len(results) == 1

        # Verify filter was applied
        call_args = mock_index.search.call_args
        filter_string = call_args[1]["filter_string"]
        assert "level:2" in filter_string
        assert "school:Abjuration" in filter_string
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_search_entities_semantic -v`
Expected: FAIL - function not implemented

**Step 3: Implement search_entities**

Add to `src/lorekeeper_mcp/cache/db.py`:

```python
async def search_entities(
    entity_type: str,
    query: str,
    filters: dict[str, Any] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Semantic search for entities using natural language query.

    Args:
        entity_type: Type of entities to search
        query: Natural language search query
        filters: Optional structured filters (level, school, etc.)
        limit: Maximum number of results

    Returns:
        List of matching entities with relevance scores

    Raises:
        ValueError: If entity_type is invalid or filter field is not allowed
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    # Validate and build filter string
    filter_string = None
    if filters:
        allowed_fields = set(get_filterable_fields(entity_type))
        filter_clauses = []

        for field, value in filters.items():
            if field not in allowed_fields:
                raise ValueError(
                    f"Invalid filter field '{field}' for entity type '{entity_type}'. "
                    f"Allowed fields: {sorted(allowed_fields) if allowed_fields else 'none'}"
                )

            if isinstance(value, str):
                filter_clauses.append(f"{field}:{value}")
            elif isinstance(value, (int, float)):
                filter_clauses.append(f"{field}:{value}")
            elif isinstance(value, bool):
                filter_clauses.append(f"{field}:{str(value).lower()}")
            elif isinstance(value, list):
                if len(value) == 2:
                    filter_clauses.append(f"{field}:[{value[0]} TO {value[1]}]")
                else:
                    or_values = " OR ".join(str(v) for v in value)
                    filter_clauses.append(f"{field}:({or_values})")

        if filter_clauses:
            filter_string = " AND ".join(filter_clauses)

    # Perform semantic search
    client = MarqoClientManager.get_client()
    index_name = get_index_name(entity_type)

    try:
        search_args = {
            "q": query,
            "limit": limit,
        }
        if filter_string:
            search_args["filter_string"] = filter_string

        # Synchronous Marqo call - run in thread pool
        response = await asyncio.to_thread(
            client.index(index_name).search,
            **search_args
        )

        hits = response.get("hits", [])
        logger.debug(f"Semantic search for '{query}' returned {len(hits)} results")
        return hits

    except Exception as e:
        logger.error(f"Semantic search failed for {entity_type}: {e}")
        return []
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_search_entities_semantic -v`
Expected: PASS

**Step 5: Run all search_entities tests**

Run: `uv run pytest tests/test_cache/test_marqo_db.py -k search_entities -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_marqo_db.py
git commit -m "feat: implement search_entities for semantic search"
```

---

### Task 4.2: Implement find_similar_entities

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py`

**Step 1: Write failing test**

Add to `tests/test_cache/test_marqo_db.py`:

```python
from lorekeeper_mcp.cache.db import find_similar_entities


@pytest.mark.asyncio
async def test_find_similar_entities():
    """Test finding similar entities by reference."""
    # Mock getting reference document
    reference_doc = {
        "_id": "fireball",
        "slug": "fireball",
        "name": "Fireball",
        "desc": "A bright streak...",
    }

    # Mock search results
    mock_results = {
        "hits": [
            {"_id": "lightning-bolt", "name": "Lightning Bolt", "_score": 0.89},
            {"_id": "cone-of-cold", "name": "Cone of Cold", "_score": 0.85},
        ]
    }

    with patch("lorekeeper_mcp.cache.db.get_cached_entity") as mock_get:
        with patch("lorekeeper_mcp.cache.db.MarqoClientManager.get_client") as mock_get_client:
            mock_get.return_value = reference_doc

            mock_client = MagicMock()
            mock_index = MagicMock()
            mock_client.index.return_value = mock_index
            mock_index.search.return_value = mock_results
            mock_get_client.return_value = mock_client

            results = await find_similar_entities("spells", "fireball", limit=5)

            assert len(results) == 2
            assert results[0]["name"] == "Lightning Bolt"
            # Fireball should not be in results
            assert all(r["_id"] != "fireball" for r in results)


@pytest.mark.asyncio
async def test_find_similar_entities_not_found():
    """Test that missing reference returns empty list."""
    with patch("lorekeeper_mcp.cache.db.get_cached_entity") as mock_get:
        mock_get.return_value = None

        results = await find_similar_entities("spells", "nonexistent")

        assert results == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_find_similar_entities -v`
Expected: FAIL - function not implemented

**Step 3: Implement find_similar_entities**

Add to `src/lorekeeper_mcp/cache/db.py`:

```python
async def find_similar_entities(
    entity_type: str,
    reference_slug: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find entities similar to a reference entity.

    Uses the reference entity's embedding to find nearest neighbors.

    Args:
        entity_type: Type of entities to search
        reference_slug: Slug of reference entity
        limit: Maximum number of similar entities to return

    Returns:
        List of similar entities (excluding the reference entity)

    Raises:
        ValueError: If entity_type is invalid
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    # Get reference entity
    reference = await get_cached_entity(entity_type, reference_slug)
    if not reference:
        logger.warning(f"Reference entity {reference_slug} not found")
        return []

    # Use reference entity's text fields to find similar documents
    # We'll search using the reference entity's description
    tensor_fields = get_tensor_fields(entity_type)

    # Build search query from reference entity's tensor fields
    query_parts = []
    for field in tensor_fields:
        value = reference.get(field, "")
        if value:
            query_parts.append(str(value))

    if not query_parts:
        logger.warning(f"No searchable content in reference entity {reference_slug}")
        return []

    query = " ".join(query_parts)

    # Search for similar entities
    client = MarqoClientManager.get_client()
    index_name = get_index_name(entity_type)

    try:
        # Request limit+1 to account for filtering out the reference
        search_args = {
            "q": query,
            "limit": limit + 1,
        }

        # Synchronous Marqo call - run in thread pool
        response = await asyncio.to_thread(
            client.index(index_name).search,
            **search_args
        )

        hits = response.get("hits", [])

        # Filter out the reference entity and limit results
        similar = [hit for hit in hits if hit.get("_id") != reference_slug][:limit]

        logger.debug(f"Found {len(similar)} entities similar to {reference_slug}")
        return similar

    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        return []
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_marqo_db.py::test_find_similar_entities -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_marqo_db.py
git commit -m "feat: implement find_similar_entities for similarity search"
```

---

### Task 4.3: Update Cache Module Exports

**Files:**
- Modify: `src/lorekeeper_mcp/cache/__init__.py`

**Step 1: Update exports**

Replace content of `src/lorekeeper_mcp/cache/__init__.py`:

```python
"""Cache module for LoreKeeper MCP using Marqo."""

from lorekeeper_mcp.cache.db import (
    bulk_cache_entities,
    find_similar_entities,
    get_cached_entity,
    get_entity_count,
    query_cached_entities,
    search_entities,
)
from lorekeeper_mcp.cache.marqo_client import MarqoClientManager, check_marqo_health
from lorekeeper_mcp.cache.schema import (
    ENTITY_TYPES,
    FILTERABLE_FIELDS,
    SCHEMA_VERSION,
    TENSOR_FIELDS,
    get_filterable_fields,
    get_index_name,
    get_index_settings,
    get_tensor_fields,
    init_indexes,
)

__all__ = [
    # Client management
    "MarqoClientManager",
    "check_marqo_health",
    # Schema
    "ENTITY_TYPES",
    "TENSOR_FIELDS",
    "FILTERABLE_FIELDS",
    "SCHEMA_VERSION",
    "get_index_name",
    "get_tensor_fields",
    "get_filterable_fields",
    "get_index_settings",
    "init_indexes",
    # Cache operations
    "bulk_cache_entities",
    "get_cached_entity",
    "query_cached_entities",
    "get_entity_count",
    # Semantic search
    "search_entities",
    "find_similar_entities",
]
```

**Step 2: Test imports**

Run: `uv run python -c "from lorekeeper_mcp.cache import search_entities, find_similar_entities; print('OK')"`
Expected: Prints "OK"

**Step 3: Commit**

```bash
git add src/lorekeeper_mcp/cache/__init__.py
git commit -m "feat: update cache module exports with semantic search"
```

---

## Phase 5: Server Integration

### Task 5.1: Update Server Initialization

**Files:**
- Modify: `src/lorekeeper_mcp/server.py`

**Step 1: Read current server.py**

(You already have this from earlier)

**Step 2: Update imports and lifespan function**

Replace database initialization in server.py:

```python
# OLD imports to remove:
# from lorekeeper_mcp.cache.db import init_db

# NEW imports to add:
from lorekeeper_mcp.cache import check_marqo_health, init_indexes


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncGenerator[None]:
    """Initialize resources on startup, cleanup on shutdown."""
    logger.info("Starting LoreKeeper MCP server")

    # Check Marqo health
    marqo_available = await check_marqo_health()
    if not marqo_available:
        logger.warning(
            "Marqo service unavailable - cache operations will be limited. "
            "Start Marqo with: docker-compose up -d marqo"
        )
    else:
        logger.info("Marqo service is healthy")

    # Initialize Marqo indexes
    try:
        await init_indexes()
        logger.info("Marqo indexes initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Marqo indexes: {e}")
        logger.warning("Server will continue but caching may not work")

    yield

    logger.info("Shutting down LoreKeeper MCP server")
```

**Step 3: Write test for server startup**

Create `tests/test_server_marqo.py`:

```python
"""Test server initialization with Marqo."""

import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_server_startup_with_marqo():
    """Test that server starts successfully with Marqo available."""
    with patch("lorekeeper_mcp.server.check_marqo_health") as mock_health:
        with patch("lorekeeper_mcp.server.init_indexes") as mock_init:
            mock_health.return_value = True
            mock_init.return_value = None

            # Import after patching
            from lorekeeper_mcp.server import lifespan, mcp

            # Simulate lifespan context
            async with lifespan(mcp):
                pass

            mock_health.assert_called_once()
            mock_init.assert_called_once()


@pytest.mark.asyncio
async def test_server_startup_without_marqo():
    """Test that server starts with warning when Marqo unavailable."""
    with patch("lorekeeper_mcp.server.check_marqo_health") as mock_health:
        with patch("lorekeeper_mcp.server.init_indexes") as mock_init:
            mock_health.return_value = False
            mock_init.return_value = None

            from lorekeeper_mcp.server import lifespan, mcp

            # Should not raise exception
            async with lifespan(mcp):
                pass

            mock_health.assert_called_once()
            # init_indexes should still be called
            mock_init.assert_called_once()
```

**Step 4: Run test**

Run: `uv run pytest tests/test_server_marqo.py -v`
Expected: Tests pass after applying changes

**Step 5: Apply server changes**

(Apply the changes from Step 2)

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/server.py tests/test_server_marqo.py
git commit -m "feat: update server initialization to use marqo"
```

---

## Phase 6: Update Tool Functions

### Task 6.1: Update Spell Lookup Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py`

**Step 1: Read current implementation**

(Review existing spell_lookup.py to understand current structure)

**Step 2: Update to use semantic search**

Modify the lookup function to use `search_entities`:

```python
# Add import at top
from lorekeeper_mcp.cache import search_entities

# Update lookup_spell function
@mcp.tool()
async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Look up D&D spells using semantic search or filters.

    Args:
        name: Spell name or natural language description (e.g., "fire damage", "healing magic")
        level: Spell level (0-9)
        school: School of magic (Abjuration, Conjuration, etc.)
        class_key: Character class (wizard, cleric, etc.)
        limit: Maximum results to return

    Returns:
        List of matching spell dictionaries
    """
    # If name provided, use semantic search
    if name:
        filters = {}
        if level is not None:
            filters["level"] = level
        if school:
            filters["school"] = school

        # Semantic search with filters
        results = await search_entities(
            "spells",
            query=name,
            filters=filters if filters else None,
            limit=limit
        )

        # Filter by class if specified (post-search filter)
        if class_key and results:
            results = [
                spell for spell in results
                if class_key in spell.get("classes", [])
            ][:limit]

        return results

    # Otherwise use structured query
    filters = {}
    if level is not None:
        filters["level"] = level
    if school:
        filters["school"] = school

    results = await query_cached_entities("spells", limit=limit, **filters)

    # Post-filter by class
    if class_key and results:
        results = [
            spell for spell in results
            if class_key in spell.get("classes", [])
        ][:limit]

    return results[:limit]
```

**Step 3: Write test for updated function**

Update or create test to verify semantic search works.

**Step 4: Run tests**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py -v`
Expected: Tests pass

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/tools/spell_lookup.py
git commit -m "feat: update spell_lookup to use semantic search"
```

---

### Task 6.2: Update Other Tool Functions

**Files:**
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py`
- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py`
- Modify: `src/lorekeeper_mcp/tools/character_option_lookup.py`
- Modify: `src/lorekeeper_mcp/tools/rule_lookup.py`

**Step 1: Update each tool similarly to spell_lookup**

Apply the same pattern to each tool:
1. Import `search_entities` and `query_cached_entities`
2. Use semantic search when name/query provided
3. Use structured query for filters only

**Step 2: Test each tool**

Run: `uv run pytest tests/test_tools/ -v`
Expected: All tool tests pass

**Step 3: Commit each tool**

```bash
git add src/lorekeeper_mcp/tools/creature_lookup.py
git commit -m "feat: update creature_lookup to use semantic search"

git add src/lorekeeper_mcp/tools/equipment_lookup.py
git commit -m "feat: update equipment_lookup to use semantic search"

# ... and so on
```

---

## Phase 7: Testing & Documentation

### Task 7.1: Write Integration Tests

**Files:**
- Create: `tests/test_cache/test_marqo_integration.py`

**Step 1: Write integration test (requires real Marqo)**

Create comprehensive integration test that:
1. Starts Marqo container (or uses existing)
2. Initializes indexes
3. Indexes test data
4. Performs searches
5. Verifies results

Mark as `@pytest.mark.integration` to run separately.

**Step 2: Run integration tests**

Run: `docker-compose up -d marqo && uv run pytest tests/test_cache/test_marqo_integration.py -v -m integration`
Expected: Tests pass with real Marqo

**Step 3: Commit**

```bash
git add tests/test_cache/test_marqo_integration.py
git commit -m "test: add marqo integration tests"
```

---

### Task 7.2: Update Documentation

**Files:**
- Modify: `docs/cache.md`
- Modify: `docs/architecture.md`
- Create: `docs/semantic-search.md`
- Modify: `README.md`

**Step 1: Rewrite docs/cache.md for Marqo**

Document:
- Marqo architecture
- Index structure
- Cache operations
- Configuration

**Step 2: Create semantic-search.md**

Document:
- How semantic search works
- Query examples
- Filter syntax
- Performance tips

**Step 3: Update architecture.md**

Replace SQLite diagram with Marqo architecture.

**Step 4: Update README.md**

Add Marqo setup prominently in Quick Start.

**Step 5: Commit**

```bash
git add docs/ README.md
git commit -m "docs: update documentation for marqo migration"
```

---

### Task 7.3: Clean Up SQLite Code

**Files:**
- Remove: Old SQLite test fixtures
- Remove: aiosqlite dependency

**Step 1: Remove aiosqlite**

Run: `uv remove aiosqlite`

**Step 2: Verify no SQLite references remain**

Run: `rg "aiosqlite|sqlite3" src/ tests/`
Expected: No matches

**Step 3: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: remove sqlite dependencies"
```

---

### Task 7.4: Final Validation

**Files:**
- Run full test suite
- Run linting
- Run type checking

**Step 1: Run all tests**

Run: `uv run pytest`
Expected: All tests pass

**Step 2: Run linting**

Run: `uv run ruff check src/ tests/`
Expected: No issues

**Step 3: Run type checking**

Run: `uv run mypy src/`
Expected: No type errors

**Step 4: Run pre-commit hooks**

Run: `uv run pre-commit run --all-files`
Expected: All checks pass

**Step 5: Final commit if fixes needed**

```bash
git add .
git commit -m "fix: address linting and type issues"
```

---

## Summary

This plan replaces SQLite with Marqo in ~40 bite-sized tasks organized into 7 phases:

1. **Phase 1**: Infrastructure (Docker, config)
2. **Phase 2**: Marqo client & indexes
3. **Phase 3**: Core cache operations
4. **Phase 4**: Semantic search features
5. **Phase 5**: Server integration
6. **Phase 6**: Update tools
7. **Phase 7**: Testing & docs

**Key Architecture Decisions:**
- Wrap synchronous Marqo calls with `asyncio.to_thread()`
- Use slug as Marqo document `_id`
- Maintain API compatibility with existing cache functions
- Add new `search_entities()` and `find_similar_entities()` functions
- Store full entity as document, not just in `data` field

**Testing Strategy:**
- Unit tests with mocked Marqo client
- Integration tests with real Marqo (Docker)
- TDD throughout: test → fail → implement → pass → commit

**Total Estimated Time**: 20-24 hours (3-4 days)
