# Implementation Tasks: Replace SQLite with Marqo

## Overview

This document breaks down the implementation into concrete, ordered tasks. Each task is small, verifiable, and includes validation criteria.

## Task Categories

- **Phase 1**: Infrastructure & Configuration (1 day)
- **Phase 2**: Core Cache Implementation (2 days)
- **Phase 3**: Semantic Search Features (1 day)
- **Phase 4**: Testing & Migration (2 days)
- **Phase 5**: Documentation & Cleanup (1 day)

---

## Phase 1: Infrastructure & Configuration

### Task 1.1: Add Marqo Dependencies
**Estimated**: 15 minutes

**Actions**:
- Add `marqo` to `pyproject.toml` dependencies
- Run `uv sync` to install
- Verify import works: `python -c "import marqo"`

**Files**:
- `pyproject.toml`

**Validation**:
```bash
uv add marqo
uv run python -c "import marqo; print(marqo.__version__)"
```

**Success Criteria**:
- Marqo package installed successfully
- Import works without errors

---

### Task 1.2: Create Docker Compose for Marqo
**Estimated**: 30 minutes

**Actions**:
- Create `docker-compose.yml` in project root
- Define Marqo service with proper ports and volumes
- Add health check configuration
- Document startup instructions

**Files**:
- `docker-compose.yml` (new)
- `README.md` (update with Marqo setup)

**Example `docker-compose.yml`**:
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
    volumes:
      - marqo-data:/opt/marqo/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8882/health"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  marqo-data:
```

**Validation**:
```bash
docker-compose up -d marqo
curl http://localhost:8882/health
docker-compose down
```

**Success Criteria**:
- Marqo starts successfully
- Health endpoint returns 200
- Service accessible on port 8882

---

### Task 1.3: Update Configuration Settings
**Estimated**: 20 minutes

**Actions**:
- Add `marqo_url`, `marqo_timeout`, `marqo_batch_size` to `Settings` class
- Remove SQLite-specific fields (`db_path`, `cache_ttl_days`)
- Update `.env.example` with Marqo configuration
- Add default values for local development

**Files**:
- `src/lorekeeper_mcp/config.py`
- `.env.example`

**Changes**:
```python
# config.py
class Settings(BaseSettings):
    # Remove:
    # db_path: Path = Field(default=Path("./data/cache.db"))
    # cache_ttl_days: int = Field(default=7)

    # Add:
    marqo_url: str = Field(default="http://localhost:8882")
    marqo_timeout: int = Field(default=30)
    marqo_batch_size: int = Field(default=100)
    marqo_model: str = Field(default="hf/e5-base-v2")
```

**Validation**:
```python
from lorekeeper_mcp.config import settings
assert settings.marqo_url == "http://localhost:8882"
assert settings.marqo_model == "hf/e5-base-v2"
```

**Success Criteria**:
- New configuration fields accessible
- Old SQLite fields removed
- Environment variables load correctly

---

## Phase 2: Core Cache Implementation

### Task 2.1: Create Marqo Client Manager
**Estimated**: 1 hour

**Actions**:
- Create `src/lorekeeper_mcp/cache/marqo_client.py`
- Implement singleton `MarqoClientManager` class
- Add connection management (get_client, close)
- Add health check function

**Files**:
- `src/lorekeeper_mcp/cache/marqo_client.py` (new)

**Implementation**:
```python
"""Marqo client management."""
import logging
import marqo
from lorekeeper_mcp.config import settings

logger = logging.getLogger(__name__)

class MarqoClientManager:
    """Singleton manager for Marqo client."""

    _instance: marqo.Client | None = None

    @classmethod
    def get_client(cls) -> marqo.Client:
        """Get or create Marqo client."""
        if cls._instance is None:
            cls._instance = marqo.Client(url=settings.marqo_url)
            logger.info(f"Marqo client connected to {settings.marqo_url}")
        return cls._instance

    @classmethod
    def close(cls) -> None:
        """Close Marqo client."""
        cls._instance = None
        logger.info("Marqo client closed")

async def check_marqo_health() -> bool:
    """Check if Marqo service is healthy."""
    try:
        client = MarqoClientManager.get_client()
        client.get_indexes()
        return True
    except Exception as e:
        logger.warning(f"Marqo health check failed: {e}")
        return False
```

**Validation**:
```python
# Start Marqo first
from lorekeeper_mcp.cache.marqo_client import MarqoClientManager, check_marqo_health
client = MarqoClientManager.get_client()
assert await check_marqo_health() is True
```

**Success Criteria**:
- Client singleton works
- Health check passes when Marqo is running
- Health check fails gracefully when Marqo is down

---

### Task 2.2: Define Index Schemas
**Estimated**: 1.5 hours

**Actions**:
- Replace `cache/schema.py` with Marqo index definitions
- Define entity types and their tensor fields
- Create index settings per entity type
- Implement `init_indexes()` function

**Files**:
- `src/lorekeeper_mcp/cache/schema.py` (rewrite)

**Implementation Structure**:
```python
"""Marqo index schema definitions."""

ENTITY_TYPES = [
    "spells", "monsters", "weapons", "armor",
    "classes", "races", "backgrounds", "feats",
    "conditions", "rules", "rule-sections"
]

# Tensor fields per entity type
TENSOR_FIELDS = {
    "spells": ["name", "desc", "higher_level"],
    "monsters": ["name", "desc", "special_abilities"],
    "weapons": ["name", "desc"],
    # ... etc
}

# Index settings per entity type
def get_index_settings(entity_type: str) -> dict:
    """Get Marqo index settings for entity type."""
    return {
        "model": "hf/e5-base-v2",
        "normalizeEmbeddings": True,
        "textPreprocessing": {
            "splitLength": 2,
            "splitOverlap": 0,
            "splitMethod": "sentence"
        }
    }

async def init_indexes() -> None:
    """Initialize all Marqo indexes."""
    # Create indexes for each entity type
```

**Validation**:
```bash
uv run python -c "from lorekeeper_mcp.cache.schema import ENTITY_TYPES; print(len(ENTITY_TYPES))"
```

**Success Criteria**:
- All entity types defined
- Tensor fields specified for each type
- Index settings function works

---

### Task 2.3: Implement Core Cache Functions
**Estimated**: 3 hours

**Actions**:
- Rewrite `cache/db.py` with Marqo operations
- Implement `bulk_cache_entities()` using Marqo `add_documents`
- Implement `get_cached_entity()` using Marqo `get_document`
- Implement `query_cached_entities()` using Marqo `search` with filters
- Implement `get_entity_count()` using Marqo `get_stats`
- Remove all SQLite code

**Files**:
- `src/lorekeeper_mcp/cache/db.py` (rewrite)

**Key Functions**:
```python
async def bulk_cache_entities(
    entities: list[dict[str, Any]],
    entity_type: str,
    source_api: str = "unknown",
) -> int:
    """Bulk index entities in Marqo."""
    # Use mq.index(index_name).add_documents()

async def get_cached_entity(
    entity_type: str,
    slug: str,
) -> dict[str, Any] | None:
    """Get entity by slug from Marqo."""
    # Use mq.index(index_name).get_document(slug)

async def query_cached_entities(
    entity_type: str,
    **filters: Any,
) -> list[dict[str, Any]]:
    """Query entities with filters."""
    # Use mq.index(index_name).search() with filter_string
```

**Validation**:
```python
# Test bulk indexing
entities = [{"slug": "fireball", "name": "Fireball", "desc": "A bright streak..."}]
count = await bulk_cache_entities(entities, "spells")
assert count == 1

# Test retrieval
spell = await get_cached_entity("spells", "fireball")
assert spell["name"] == "Fireball"

# Test query
spells = await query_cached_entities("spells", level=3)
assert len(spells) >= 0
```

**Success Criteria**:
- All cache functions work with Marqo
- No SQLite dependencies remain
- Functions match original signatures (drop-in replacement)

---

### Task 2.4: Update Server Initialization
**Estimated**: 30 minutes

**Actions**:
- Replace `init_db()` with `init_indexes()` in `server.py`
- Update imports from `cache.db` to use new functions
- Add Marqo health check on startup

**Files**:
- `src/lorekeeper_mcp/server.py`

**Changes**:
```python
from lorekeeper_mcp.cache.db import init_indexes
from lorekeeper_mcp.cache.marqo_client import check_marqo_health

@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncGenerator[None]:
    """Initialize resources on startup."""
    # Check Marqo health
    if not await check_marqo_health():
        logger.warning("Marqo unavailable - cache will fallback to API")

    # Initialize indexes
    await init_indexes()

    yield
```

**Validation**:
```bash
uv run python -m lorekeeper_mcp
# Should start without errors
```

**Success Criteria**:
- Server starts successfully
- Indexes created on startup
- Health check runs

---

## Phase 3: Semantic Search Features

### Task 3.1: Implement Semantic Search Function
**Estimated**: 2 hours

**Actions**:
- Add `search_entities()` function to `cache/db.py`
- Support natural language queries
- Support filter combination
- Handle pagination and limits

**Files**:
- `src/lorekeeper_mcp/cache/db.py`

**Implementation**:
```python
async def search_entities(
    entity_type: str,
    query: str,
    filters: dict[str, Any] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Semantic search for entities.

    Args:
        entity_type: Type of entity
        query: Natural language search query
        filters: Optional filters (level, school, etc.)
        limit: Maximum results

    Returns:
        List of matching entities with scores
    """
    # Build filter string
    # Perform vector search
    # Return results
```

**Validation**:
```python
# Semantic search
results = await search_entities("spells", "protect from fire", limit=5)
assert len(results) > 0
assert all("_score" in r for r in results)

# Filtered semantic search
results = await search_entities(
    "spells",
    "healing magic",
    filters={"level": 2},
    limit=5
)
```

**Success Criteria**:
- Semantic search returns relevant results
- Filtering works alongside search
- Results include relevance scores

---

### Task 3.2: Implement Similarity Search
**Estimated**: 1 hour

**Actions**:
- Add `find_similar_entities()` function
- Support finding similar items by reference
- Use Marqo context vectors

**Files**:
- `src/lorekeeper_mcp/cache/db.py`

**Implementation**:
```python
async def find_similar_entities(
    entity_type: str,
    reference_slug: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find entities similar to reference entity."""
    # Get reference document with embeddings
    # Search using context vector
    # Return similar entities
```

**Validation**:
```python
# Find similar spells
similar = await find_similar_entities("spells", "fireball", limit=5)
assert len(similar) > 0
assert "fireball" not in [s["slug"] for s in similar]  # Don't include self
```

**Success Criteria**:
- Similarity search works
- Returns different entities (not reference)
- Results semantically related

---

### Task 3.3: Update Tool Functions for Semantic Search
**Estimated**: 2 hours

**Actions**:
- Update all tool files to use `search_entities()`
- Prefer semantic search over exact matching
- Maintain backward compatibility with existing filters

**Files**:
- `src/lorekeeper_mcp/tools/spell_lookup.py`
- `src/lorekeeper_mcp/tools/creature_lookup.py`
- `src/lorekeeper_mcp/tools/equipment_lookup.py`
- `src/lorekeeper_mcp/tools/character_option_lookup.py`
- `src/lorekeeper_mcp/tools/rule_lookup.py`

**Example Changes**:
```python
# spell_lookup.py - Before
if name:
    params["search"] = name

# After
if name:
    # Use semantic search instead of API filtering
    return await search_entities(
        "spells",
        query=name,
        filters={k: v for k, v in {"level": level, "school": school}.items() if v},
        limit=limit
    )
```

**Validation**:
```python
# Test updated tools
spells = await lookup_spell(name="protect from fire", level=3)
assert len(spells) > 0
```

**Success Criteria**:
- All tools use semantic search
- Filters still work
- Results more relevant than before

---

## Phase 4: Testing & Migration

### Task 4.1: Write Unit Tests for Cache Functions
**Estimated**: 3 hours

**Actions**:
- Rewrite `tests/test_cache/test_db.py` for Marqo
- Mock Marqo client for unit tests
- Test all cache functions (bulk, get, query, search)
- Test error handling and edge cases

**Files**:
- `tests/test_cache/test_db.py` (rewrite)
- `tests/conftest.py` (add mock fixtures)

**Test Structure**:
```python
@pytest.fixture
def mock_marqo_client(monkeypatch):
    """Mock Marqo client."""
    mock = MagicMock()
    monkeypatch.setattr(
        "lorekeeper_mcp.cache.marqo_client.MarqoClientManager.get_client",
        lambda: mock
    )
    return mock

async def test_bulk_cache_entities(mock_marqo_client):
    """Test bulk indexing."""
    # Test implementation

async def test_search_entities(mock_marqo_client):
    """Test semantic search."""
    # Test implementation
```

**Validation**:
```bash
uv run pytest tests/test_cache/test_db.py -v
```

**Success Criteria**:
- All unit tests pass
- ≥90% code coverage for cache module
- Edge cases handled

---

### Task 4.2: Write Integration Tests with Real Marqo
**Estimated**: 2 hours

**Actions**:
- Create integration test fixture that starts Marqo
- Test real indexing and search operations
- Test filter combinations
- Test semantic search quality

**Files**:
- `tests/test_cache/test_integration.py` (new)
- `tests/conftest.py` (add Marqo container fixture)

**Test Fixture**:
```python
@pytest.fixture(scope="session")
def marqo_container():
    """Start Marqo container for integration tests."""
    container = DockerContainer("marqoai/marqo:latest")
    container.with_exposed_ports(8882)
    container.start()

    # Wait for health
    wait_for_marqo()

    yield container

    container.stop()
```

**Validation**:
```bash
# Requires Docker
uv run pytest tests/test_cache/test_integration.py -v --integration
```

**Success Criteria**:
- Integration tests pass with real Marqo
- Search quality validated
- Performance within limits (<100ms)

---

### Task 4.3: Update API Client Tests
**Estimated**: 2 hours

**Actions**:
- Update all `tests/test_api_clients/*.py` files
- Replace SQLite cache mocks with Marqo mocks
- Ensure cache integration still works

**Files**:
- `tests/test_api_clients/test_base.py`
- `tests/test_api_clients/test_open5e_v1.py`
- `tests/test_api_clients/test_open5e_v2.py`
- `tests/test_api_clients/test_dnd5e_api.py`

**Validation**:
```bash
uv run pytest tests/test_api_clients/ -v
```

**Success Criteria**:
- All API client tests pass
- Cache integration verified
- No SQLite dependencies

---

## Phase 5: Documentation & Cleanup

### Task 5.1: Update Documentation
**Estimated**: 2 hours

**Actions**:
- Update `docs/cache.md` for Marqo
- Add Marqo setup instructions to `README.md`
- Create `docs/semantic-search.md` guide
- Update architecture diagrams

**Files**:
- `docs/cache.md` (rewrite)
- `README.md` (update)
- `docs/semantic-search.md` (new)
- `docs/architecture.md` (update)

**Content**:
- Marqo installation and setup
- Docker Compose usage
- Semantic search examples
- Filter syntax guide
- Troubleshooting

**Validation**:
- Documentation builds correctly
- Examples work when copy-pasted

**Success Criteria**:
- Complete Marqo documentation
- Clear setup instructions
- Usage examples provided

---

### Task 5.2: Remove SQLite Code
**Estimated**: 30 minutes

**Actions**:
- Remove old SQLite schema code
- Remove SQLite dependencies from tests
- Clean up unused imports
- Archive SQLite database file

**Files**:
- Remove: SQLite-specific test fixtures
- Update: All imports

**Validation**:
```bash
rg "aiosqlite|sqlite3" src/ tests/
# Should return no matches
```

**Success Criteria**:
- No SQLite code remains
- All tests still pass
- No dead code

---

### Task 5.3: Update Dependencies
**Estimated**: 15 minutes

**Actions**:
- Remove `aiosqlite` from dependencies
- Ensure `marqo` properly pinned
- Update `uv.lock`

**Files**:
- `pyproject.toml`

**Validation**:
```bash
uv sync
uv run pytest
```

**Success Criteria**:
- `aiosqlite` removed
- All tests pass with final dependencies

---

### Task 5.4: Final Validation & QA
**Estimated**: 2 hours

**Actions**:
- Run full test suite
- Validate all tools work end-to-end
- Performance benchmark
- Security review

**Validation Checklist**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All live MCP tests pass
- [ ] Semantic search quality acceptable
- [ ] Performance meets targets (<100ms)
- [ ] Documentation complete
- [ ] No SQLite dependencies
- [ ] Configuration updated

**Success Criteria**:
- 100% tests passing
- All success criteria met
- Ready for production

---

## Summary

**Total Estimated Time**: ~20-24 hours (3-4 working days)

**Critical Path**:
1. Infrastructure setup (Phase 1)
2. Core cache implementation (Phase 2)
3. Testing (Phase 4)

**Parallel Work Opportunities**:
- Documentation can start early
- Semantic search features can be added incrementally
- Tests can be written alongside implementation

**Rollback Plan**:
- Keep SQLite code in git history
- Feature flag to toggle Marqo/SQLite (if needed)
- Migration script reversible

---

## Next Steps

1. Review and approve this task breakdown
2. Set up development environment with Marqo
3. Begin Phase 1 tasks
4. Proceed sequentially through phases
5. Validate at each checkpoint
