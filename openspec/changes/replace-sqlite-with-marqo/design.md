# Design Document: Replace SQLite with Marqo

## Overview

This document outlines the architectural design for replacing SQLite with Marqo as the caching and search backend for LoreKeeper MCP.

## Architecture

### Current Architecture (SQLite)

```
┌─────────────┐
│ MCP Tools   │
└──────┬──────┘
       │
       v
┌─────────────────┐      ┌──────────────┐
│  API Clients    │─────>│  Open5e API  │
│  (base.py)      │      │  D&D5e API   │
└──────┬──────────┘      └──────────────┘
       │
       v
┌─────────────────┐
│  Cache Layer    │
│  (cache/db.py)  │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│  SQLite DB      │
│  (cache.db)     │
└─────────────────┘
```

### New Architecture (Marqo)

```
┌─────────────┐
│ MCP Tools   │
└──────┬──────┘
       │
       v
┌─────────────────┐      ┌──────────────┐
│  API Clients    │─────>│  Open5e API  │
│  (base.py)      │      │  D&D5e API   │
└──────┬──────────┘      └──────────────┘
       │
       v
┌─────────────────┐
│  Cache Layer    │      ┌──────────────────┐
│ (cache/marqo.py)│─────>│  Marqo Service   │
└─────────────────┘      │  (Docker)        │
                         │  - Vector Store  │
                         │  - Index Engine  │
                         │  - Embeddings    │
                         └──────────────────┘
```

## Design Decisions

### 1. Index Strategy

**Decision**: One index per entity type

**Rationale**:
- Clear separation of concerns
- Different tensor fields per type
- Independent scaling and tuning
- Easier to manage and debug

**Index Naming**: `lorekeeper-{entity_type}`
- `lorekeeper-spells`
- `lorekeeper-monsters`
- `lorekeeper-weapons`
- `lorekeeper-armor`
- `lorekeeper-classes`
- `lorekeeper-races`
- `lorekeeper-backgrounds`
- `lorekeeper-feats`
- `lorekeeper-conditions`
- `lorekeeper-rules`
- `lorekeeper-rule-sections`

### 2. Tensor Fields (Vector Embeddings)

**Decision**: Embed multiple text fields per entity type

**Spell Example**:
```python
tensor_fields = ["name", "description", "higher_level", "components"]
```

**Monster Example**:
```python
tensor_fields = ["name", "desc", "special_abilities", "actions"]
```

**Rationale**:
- Rich semantic search across all relevant text
- Better match quality for complex queries
- Marqo automatically combines multiple fields

### 3. Metadata Fields (Filtering)

**Decision**: Store all entity data as document fields, index filterable fields

**Example Spell Document**:
```python
{
    "_id": "fireball",  # slug
    "name": "Fireball",
    "slug": "fireball",
    "level": 3,
    "school": "Evocation",
    "concentration": False,
    "ritual": False,
    "casting_time": "1 action",
    "range": "150 feet",
    "components": "V, S, M",
    "duration": "Instantaneous",
    "description": "A bright streak flashes...",
    "higher_level": "When you cast this spell...",
    "classes": ["wizard", "sorcerer"],
    "source_api": "open5e",
    # ... full entity data
}
```

**Filtering Support**:
```python
# Structured filter + semantic search
results = mq.index("lorekeeper-spells").search(
    q="protect against fire damage",
    filter_string="level:[1 TO 3] AND school:Abjuration"
)
```

### 4. Embedding Model Selection

**Decision**: Start with `hf/e5-base-v2` (Hugging Face E5 model)

**Alternatives Considered**:
- `ViT-B/32` (CLIP) - Good for multimodal but overkill for text-only
- `sentence-transformers/all-MiniLM-L6-v2` - Smaller but less accurate
- `open_clip/ViT-L-14` - Larger, better quality but slower

**E5 Advantages**:
- Optimized for semantic text search
- Fast inference (important for MCP responsiveness)
- Good balance of quality and performance
- Well-tested in Marqo ecosystem

**Future**: Can upgrade to larger models if quality insufficient

### 5. Cache Miss Handling

**Decision**: Automatic re-indexing on cache miss

**Flow**:
```
1. Query Marqo index
2. If not found:
   a. Fetch from API
   b. Add to Marqo index
   c. Return result
3. If found:
   a. Return cached result
```

**Implementation**:
```python
async def get_cached_entity(entity_type: str, slug: str) -> dict | None:
    """Get entity from Marqo, fetch from API if missing."""
    # Try Marqo first
    try:
        doc = await marqo_client.index(f"lorekeeper-{entity_type}").get_document(slug)
        return doc
    except Exception:
        pass

    # Cache miss - fetch from API
    entity = await api_client.fetch_entity(entity_type, slug)

    # Index in Marqo
    await bulk_cache_entities([entity], entity_type)

    return entity
```

### 6. Semantic Search API

**Decision**: Add new search function alongside existing exact-match retrieval

**New Interface**:
```python
# Exact match (by slug)
spell = await get_cached_entity("spells", "fireball")

# Semantic search
spells = await search_entities(
    entity_type="spells",
    query="protect against fire damage",
    filters={"level": [1, 2, 3], "school": "Abjuration"},
    limit=10
)

# Similarity search (find similar entities)
similar_spells = await find_similar_entities(
    entity_type="spells",
    reference_slug="fireball",
    limit=5
)
```

### 7. Connection Management

**Decision**: Singleton Marqo client with lazy initialization

**Implementation**:
```python
class MarqoClientManager:
    """Manages Marqo client lifecycle."""

    _instance: marqo.Client | None = None

    @classmethod
    def get_client(cls) -> marqo.Client:
        """Get or create Marqo client."""
        if cls._instance is None:
            cls._instance = marqo.Client(url=settings.marqo_url)
        return cls._instance

    @classmethod
    async def close(cls) -> None:
        """Close Marqo client."""
        # Marqo client is synchronous, no async cleanup needed
        cls._instance = None
```

**Rationale**:
- Connection reuse across requests
- Lazy initialization for testing
- Simple lifecycle management

### 8. Error Handling

**Decision**: Graceful degradation to API when Marqo unavailable

**Implementation**:
```python
async def get_cached_entity(entity_type: str, slug: str) -> dict | None:
    """Get entity with fallback to API."""
    try:
        # Try Marqo
        return await _get_from_marqo(entity_type, slug)
    except MarqoConnectionError:
        logger.warning("Marqo unavailable, fetching from API")
        return await _fetch_from_api(entity_type, slug)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

**Health Check**:
```python
async def check_marqo_health() -> bool:
    """Check if Marqo service is healthy."""
    try:
        client = MarqoClientManager.get_client()
        # Try to list indexes
        client.get_indexes()
        return True
    except Exception:
        return False
```

### 9. Testing Strategy

**Decision**: Use Docker-based test fixtures for integration tests

**Test Levels**:

1. **Unit Tests**: Mock Marqo client
```python
@pytest.fixture
def mock_marqo_client(monkeypatch):
    """Mock Marqo client for unit tests."""
    mock = MagicMock()
    monkeypatch.setattr("lorekeeper_mcp.cache.marqo.MarqoClientManager.get_client", lambda: mock)
    return mock
```

2. **Integration Tests**: Real Marqo container
```python
@pytest.fixture(scope="session")
async def marqo_service():
    """Start Marqo container for integration tests."""
    container = DockerContainer("marqoai/marqo:latest")
    container.with_exposed_ports(8882)
    container.start()

    yield container

    container.stop()
```

3. **Live Tests**: Optional, require manual Marqo setup

### 10. Migration Strategy

**Decision**: No automatic migration - re-index from APIs

**Rationale**:
- SQLite data is just a cache (not source of truth)
- APIs are the canonical source
- Simplifies migration logic
- Ensures clean start with optimal embeddings

**Migration Steps**:
1. Deploy Marqo service
2. Update configuration (`MARQO_URL`)
3. Deploy new code
4. On first query, data auto-indexes from APIs
5. Archive old SQLite file

**Pre-warming** (optional):
```python
async def prewarm_cache():
    """Pre-populate Marqo indexes from APIs."""
    for entity_type in ENTITY_TYPES:
        logger.info(f"Pre-warming {entity_type}")
        entities = await api_client.fetch_all(entity_type)
        await bulk_cache_entities(entities, entity_type)
```

## Data Flow Examples

### Example 1: Spell Lookup by Name

```python
# User request
spell = await lookup_spell(name="fireball")

# Flow
1. Call search_entities("spells", query="fireball", limit=1)
2. Marqo performs vector search
3. Returns exact match (high score)
4. Return to user
```

### Example 2: Semantic Search

```python
# User request
spells = await lookup_spell(name="protect from fire")

# Flow
1. Call search_entities("spells", query="protect from fire", limit=20)
2. Marqo computes query embedding
3. Searches against all spell embeddings
4. Returns semantically similar spells:
   - Protection from Energy
   - Fire Shield
   - Absorb Elements
   - etc.
5. Return ranked results
```

### Example 3: Filtered Semantic Search

```python
# User request
spells = await lookup_spell(
    name="healing magic",
    level=2,
    class_key="cleric"
)

# Flow
1. Call search_entities(
    "spells",
    query="healing magic",
    filters={"level": 2, "classes": "cleric"}
)
2. Marqo applies filter: level=2 AND classes contains "cleric"
3. Performs vector search within filtered set
4. Returns:
   - Lesser Restoration
   - Prayer of Healing
   - Healing Spirit
5. Return results
```

### Example 4: Find Similar Items

```python
# User request
similar = await find_similar_entities("weapons", "longsword", limit=5)

# Flow
1. Get longsword document from Marqo
2. Extract its embedding vector
3. Search for nearest neighbors in weapons index
4. Returns:
   - Greatsword
   - Shortsword
   - Scimitar
   - Rapier
5. Return results
```

## Configuration

### New Environment Variables

```bash
# Marqo connection
MARQO_URL=http://localhost:8882
MARQO_TIMEOUT=30  # seconds
MARQO_BATCH_SIZE=100  # for bulk indexing

# Index settings
MARQO_MODEL=hf/e5-base-v2
MARQO_NORMALIZE_EMBEDDINGS=true

# Removed (SQLite-specific)
# DB_PATH=./data/cache.db
# CACHE_TTL_DAYS=7
```

### Index Configuration

```python
INDEX_SETTINGS = {
    "spells": {
        "model": "hf/e5-base-v2",
        "normalizeEmbeddings": True,
        "textPreprocessing": {
            "splitLength": 2,
            "splitOverlap": 0,
            "splitMethod": "sentence"
        },
        "tensorFields": ["name", "description", "higher_level"],
    },
    "monsters": {
        "model": "hf/e5-base-v2",
        "normalizeEmbeddings": True,
        "tensorFields": ["name", "desc", "special_abilities", "actions"],
    },
    # ... other entity types
}
```

## Performance Considerations

### Indexing Performance

- **Batch Size**: 100 documents per request (Marqo recommendation)
- **Parallel Indexing**: Index different entity types concurrently
- **Initial Index Time**: ~30-60s for full spell library (~2000 spells)

### Query Performance

- **Target**: < 100ms for cached queries
- **Expected**: 20-50ms for vector search
- **Optimization**: Enable embedding normalization, use appropriate batch sizes

### Storage

- **Estimate**: ~2-3x SQLite size due to vector embeddings
- **Example**: 2000 spells × 768-dim vectors × 4 bytes ≈ 6MB + text data

## Security Considerations

### Network Security

- Marqo should run on localhost or private network
- No authentication required for local development
- Production: Consider firewall rules, VPN, or reverse proxy

### Data Privacy

- D&D content is public (SRD/OGL)
- No user data stored in Marqo
- Cache contains only API responses

### Input Validation

- Validate entity_type against allowlist (prevent injection)
- Sanitize filter strings
- Validate document structure before indexing

## Monitoring & Observability

### Metrics to Track

```python
# Cache performance
- marqo_query_duration_ms
- marqo_index_duration_ms
- marqo_cache_hit_ratio
- marqo_connection_errors

# Search quality
- marqo_search_result_count
- marqo_avg_search_score
- marqo_semantic_vs_exact_ratio
```

### Health Checks

```python
async def health_check() -> dict:
    """Check system health."""
    return {
        "marqo": await check_marqo_health(),
        "indexes": await list_indexes(),
        "stats": await get_index_stats(),
    }
```

## Rollback Plan

If Marqo proves problematic:

1. Keep SQLite code in git history
2. Feature flag to enable/disable Marqo
3. Revert to SQLite if needed
4. Lessons learned document

## Future Enhancements

1. **Multimodal Search**: Add image search for monster/item artwork
2. **Hybrid Search**: Combine BM25 (keyword) + vector search
3. **Custom Models**: Fine-tune embeddings on D&D corpus
4. **Query Expansion**: Auto-expand queries with synonyms
5. **Personalization**: User-specific search ranking

## Conclusion

Marqo provides a clean, unified solution for caching and semantic search. The architecture maintains simplicity while adding powerful vector search capabilities. Migration is straightforward due to cache-aside pattern, and the system gracefully degrades when Marqo is unavailable.
