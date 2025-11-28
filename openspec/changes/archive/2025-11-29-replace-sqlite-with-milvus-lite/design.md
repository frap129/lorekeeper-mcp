# Design: Replace SQLite with Milvus Lite

## Context

LoreKeeper MCP currently uses SQLite for caching API responses and entity data. While SQLite provides excellent structured query support and reliability, it lacks semantic/vector search capabilities. Users must know exact terms or use specific filters to find content.

Milvus Lite is an embedded vector database that:
- Runs entirely in-process (like SQLite)
- Supports hybrid search (structured filters + vector similarity)
- Requires no external services (no Docker, no server)
- Uses the same PyMilvus API as the full Milvus server
- Stores data in a local `.db` file that can be copied/backed up

## Goals / Non-Goals

**Goals:**
- Enable semantic search across all D&D entity types
- Maintain all existing structured filtering capabilities
- Keep deployment as simple as current SQLite approach
- Provide backward compatibility for existing users
- Conform to existing `CacheProtocol` interface

**Non-Goals:**
- Supporting multiple embedding models simultaneously
- Real-time model training/fine-tuning
- Multi-tenancy or user isolation
- Cloud deployment (Zilliz Cloud integration)
- GPU acceleration (CPU-only is sufficient for our scale)

## Decisions

### 1. Embedding Model: all-MiniLM-L6-v2

**Decision:** Use `sentence-transformers/all-MiniLM-L6-v2` as the default embedding model.

**Rationale:**
- Lightweight (~80MB model size)
- Fast inference (~14,000 sentences/sec on CPU)
- 384-dimensional vectors (good balance of quality vs storage)
- Well-tested for semantic similarity tasks
- No GPU required
- MIT licensed

**Alternatives Considered:**
- `BAAI/bge-large-en-v1.5`: Higher quality but 1024 dimensions, 3x larger model
- OpenAI embeddings: Better quality but requires API key, not offline-capable
- `nomic-embed-text-v1.5`: Good quality but larger (768 dims)
- `TaylorAI/gte-tiny`: Smaller (384 dims) but less tested

**Configuration:**
```python
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
```

### 2. Storage: Single Database File with Multiple Collections

**Decision:** Use a single Milvus Lite database file (`~/.lorekeeper/milvus.db`) with one collection per entity type.

**Collections:**
- `spells` - Spell entities with level, school filters
- `creatures` - Creature entities with CR, type, size filters
- `equipment` - Weapons, armor, magic items with type filters
- `character_options` - Classes, races, backgrounds, feats
- `rules` - Rules and conditions
- `documents` - Document metadata

**Rationale:**
- Single file simplifies backup/restore and deployment
- Collections mirror current SQLite table structure
- MilvusClient API handles collection management automatically
- Easier to debug with single connection point

### 3. Collection Schema Design

**Decision:** Each collection has a consistent schema with entity-specific scalar fields for filtering.

**Base Schema (all collections):**
```python
schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
schema.add_field(field_name="slug", datatype=DataType.VARCHAR, max_length=256, is_primary=True)
schema.add_field(field_name="name", datatype=DataType.VARCHAR, max_length=256)
schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=384)
schema.add_field(field_name="document", datatype=DataType.VARCHAR, max_length=128)
schema.add_field(field_name="source_api", datatype=DataType.VARCHAR, max_length=64)
# Dynamic fields store full entity JSON
```

**Spells Collection (additional indexed fields):**
```python
schema.add_field(field_name="level", datatype=DataType.INT64)
schema.add_field(field_name="school", datatype=DataType.VARCHAR, max_length=64)
schema.add_field(field_name="concentration", datatype=DataType.BOOL)
schema.add_field(field_name="ritual", datatype=DataType.BOOL)
```

**Creatures Collection (additional indexed fields):**
```python
schema.add_field(field_name="challenge_rating", datatype=DataType.VARCHAR, max_length=16)
schema.add_field(field_name="type", datatype=DataType.VARCHAR, max_length=64)
schema.add_field(field_name="size", datatype=DataType.VARCHAR, max_length=32)
```

**Rationale:**
- `enable_dynamic_field=True` stores full entity JSON without schema changes
- Indexed scalar fields enable efficient filtering
- VARCHAR for slug allows natural document IDs (not auto-generated)

### 4. Index Configuration

**Decision:** Use IVF_FLAT index with COSINE similarity metric for vector search.

**Index Parameters:**
```python
index_params = client.prepare_index_params()
index_params.add_index(
    field_name="embedding",
    index_type="IVF_FLAT",
    metric_type="COSINE",
    params={"nlist": 128}
)
```

**Search Parameters:**
```python
search_params = {
    "metric_type": "COSINE",
    "params": {"nprobe": 16}
}
```

**Rationale:**
- IVF_FLAT offers good recall with reasonable speed for ~10K-100K entities
- COSINE similarity is standard for sentence embeddings (normalized vectors)
- `nlist=128` creates 128 clusters (works well for <100K vectors)
- `nprobe=16` searches ~12% of clusters for good recall/speed tradeoff

**Alternative Considered:**
- FLAT (brute force): Best recall but slower for large collections
- HNSW: Faster but more memory; overkill for our scale
- AUTOINDEX: Let Milvus choose; less predictable

### 5. Hybrid Search Strategy

**Decision:** Implement hybrid search combining scalar filters with optional vector similarity.

**API Design:**
```python
class MilvusCache:
    async def get_entities(
        self,
        entity_type: str,
        document: str | list[str] | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Existing filter-based retrieval (backward compatible)."""
        ...

    async def semantic_search(
        self,
        entity_type: str,
        query: str,
        limit: int = 20,
        document: str | list[str] | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """New semantic search with optional filters."""
        ...

    async def store_entities(
        self,
        entities: list[dict[str, Any]],
        entity_type: str,
    ) -> int:
        """Store entities with auto-generated embeddings."""
        ...
```

**Implementation:**
```python
async def semantic_search(
    self,
    entity_type: str,
    query: str,
    limit: int = 20,
    **filters: Any,
) -> list[dict[str, Any]]:
    # Generate query embedding
    query_embedding = self.embedding_service.encode(query)

    # Build filter expression
    filter_expr = self._build_filter_expression(filters)

    # Execute hybrid search
    results = self.client.search(
        collection_name=entity_type,
        data=[query_embedding],
        filter=filter_expr,  # Scalar filtering
        limit=limit,
        output_fields=["*"],  # Return all fields
        search_params={"metric_type": "COSINE", "params": {"nprobe": 16}}
    )

    return [hit.entity.to_dict() for hit in results[0]]
```

**Rationale:**
- Maintains full backward compatibility with existing `CacheProtocol`
- Filter expressions use Milvus boolean syntax: `level == 3 AND school == "Evocation"`
- Semantic search is opt-in via new method

### 6. Text Fields for Embedding Generation

**Decision:** Generate embeddings from concatenated searchable text fields specific to each entity type.

| Entity Type | Fields Used for Embedding |
|-------------|---------------------------|
| Spells | `name`, `desc`, `higher_level` |
| Creatures | `name`, `desc`, `type`, `actions` (names), `special_abilities` (names) |
| Equipment | `name`, `desc`, `type`, `properties` |
| Character Options | `name`, `desc` |
| Rules | `name`, `desc`, `content` |

**Implementation:**
```python
class EmbeddingService:
    def get_searchable_text(self, entity: dict, entity_type: str) -> str:
        """Extract text for embedding generation."""
        text_parts = [entity.get("name", "")]

        if entity_type == "spells":
            text_parts.extend([
                entity.get("desc", ""),
                entity.get("higher_level", ""),
            ])
        elif entity_type == "creatures":
            text_parts.extend([
                entity.get("desc", ""),
                entity.get("type", ""),
                # Extract ability names for semantic matching
                " ".join(a.get("name", "") for a in entity.get("actions", [])),
                " ".join(a.get("name", "") for a in entity.get("special_abilities", [])),
            ])
        # ... other entity types

        return " ".join(filter(None, text_parts))
```

**Rationale:**
- Includes most semantically relevant content
- Excludes mechanical data (numbers, stats) that don't benefit from embeddings
- Keeps text length reasonable (~500-2000 chars typically)
- Model handles truncation automatically (max 256 tokens)

### 7. EmbeddingService Architecture

**Decision:** Create a dedicated `EmbeddingService` class for embedding generation with lazy model loading.

**Implementation:**
```python
class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    _model: SentenceTransformer | None = None
    _model_name: str = "all-MiniLM-L6-v2"

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if cls._model is None:
            cls._model = SentenceTransformer(cls._model_name)
        return cls._model

    def encode(self, text: str) -> list[float]:
        """Encode single text to embedding vector."""
        model = self.get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts efficiently."""
        model = self.get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32)
        return embeddings.tolist()
```

**Rationale:**
- Lazy loading avoids ~2s startup delay when cache not needed
- Singleton pattern ensures model loaded only once
- Batch encoding for efficient bulk operations
- Class methods allow easy mocking in tests

### 8. Connection and Lifecycle Management

**Decision:** Use `MilvusClient` with context manager pattern for automatic resource cleanup.

**Implementation:**
```python
class MilvusCache:
    def __init__(self, db_path: str = "~/.lorekeeper/milvus.db"):
        self.db_path = Path(db_path).expanduser()
        self._client: MilvusClient | None = None
        self._embedding_service = EmbeddingService()

    @property
    def client(self) -> MilvusClient:
        """Lazy-initialize Milvus client."""
        if self._client is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._client = MilvusClient(str(self.db_path))
            self._ensure_collections()
        return self._client

    def close(self) -> None:
        """Close Milvus connection."""
        if self._client is not None:
            self._client.close()
            self._client = None

    async def __aenter__(self) -> "MilvusCache":
        return self

    async def __aexit__(self, *args) -> None:
        self.close()
```

**Rationale:**
- Lazy initialization speeds up startup when cache not immediately needed
- Context manager ensures proper cleanup
- Single client instance per cache object
- Path expansion handles `~` in paths

### 9. Error Handling Strategy

**Decision:** Graceful degradation with logging when Milvus operations fail.

**Error Types:**
- `MilvusConnectionError`: Database file issues
- `MilvusSchemaError`: Collection/field issues
- `EmbeddingError`: Model loading/encoding issues

**Implementation:**
```python
async def semantic_search(self, entity_type: str, query: str, **filters) -> list[dict]:
    try:
        query_embedding = self._embedding_service.encode(query)
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}, falling back to name search")
        # Fall back to structured search with name filter
        return await self.get_entities(entity_type, name=query, **filters)

    try:
        results = self.client.search(...)
        return [hit.entity.to_dict() for hit in results[0]]
    except Exception as e:
        logger.error(f"Milvus search failed: {e}")
        raise CacheError(f"Search failed: {e}") from e
```

**Rationale:**
- Semantic search failures fall back to structured search
- Connection errors surface to caller (cache is required)
- Detailed logging for debugging

### 10. Testing Strategy

**Decision:** Use in-memory Milvus Lite for unit tests, file-based for integration tests.

**Unit Tests:**
```python
@pytest.fixture
def milvus_cache(tmp_path):
    """Create temporary Milvus cache for testing."""
    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))
    yield cache
    cache.close()

@pytest.fixture
def mock_embedding_service(monkeypatch):
    """Mock embedding service for deterministic tests."""
    def mock_encode(text):
        # Return deterministic embedding based on text hash
        return [hash(text) % 100 / 100.0] * 384

    monkeypatch.setattr(EmbeddingService, "encode", mock_encode)
```

**Integration Tests:**
```python
@pytest.mark.integration
async def test_semantic_spell_search(milvus_cache):
    """Test semantic search finds semantically related spells."""
    # Store some spells
    await milvus_cache.store_entities([
        {"slug": "fireball", "name": "Fireball", "desc": "A bright streak flashes..."},
        {"slug": "fire-shield", "name": "Fire Shield", "desc": "Flames surround you..."},
        {"slug": "ice-storm", "name": "Ice Storm", "desc": "Hail rains down..."},
    ], "spells")

    # Semantic search for fire protection
    results = await milvus_cache.semantic_search("spells", "protect from fire")

    # Fire Shield should rank higher than Ice Storm
    assert results[0]["slug"] in ["fireball", "fire-shield"]
```

**Rationale:**
- Temporary files ensure test isolation
- Mock embeddings make unit tests deterministic and fast
- Integration tests use real embeddings to verify quality

## Data Flow

### Store Entity Flow
```
1. Tool/Repository calls cache.store_entities([entity], "spells")
2. MilvusCache extracts searchable text from entity
3. EmbeddingService generates 384-dim embedding vector
4. Entity + embedding inserted into Milvus collection
5. Return count of stored entities
```

### Semantic Search Flow
```
1. Tool calls cache.semantic_search("spells", "fire protection", level=3)
2. EmbeddingService encodes "fire protection" query
3. MilvusCache builds filter expression: "level == 3"
4. Milvus executes hybrid search:
   a. Filter to level=3 spells
   b. Vector similarity search within filtered set
5. Return ranked results with similarity scores
```

### Structured Query Flow (Backward Compatible)
```
1. Tool calls cache.get_entities("spells", level=3, school="Evocation")
2. MilvusCache builds filter expression
3. Milvus executes query with filter (no vector search)
4. Return matching entities
```

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Larger storage footprint | ~1.5KB per entity for embeddings | Acceptable for desktop; <2x SQLite |
| Initial indexing slow | ~5-10s for 1000 entities | Batch embedding; show progress bar |
| Model download on first use | ~80MB download, ~2s load time | Document requirement; lazy loading |
| Embedding quality varies | Some queries may not find relevant results | Test with diverse D&D queries; allow model override |
| Breaking change for existing users | Requires re-caching all data | Cache is not source of truth; provide migration docs |
| PyMilvus dependency size | Adds ~50MB to installation | Acceptable for the functionality gained |

## Migration Plan

### Phase 1: Infrastructure (Week 1)
1. Add `pymilvus>=2.4.0` and `sentence-transformers>=2.2.0` to dependencies
2. Create `MilvusCache` class implementing `CacheProtocol`
3. Create `EmbeddingService` class
4. Add unit tests for new classes

### Phase 2: Feature Parity (Week 2)
1. Implement all `CacheProtocol` methods in `MilvusCache`
2. Add collection schemas for all entity types
3. Implement filter expression builder
4. Ensure all existing tests pass with `MilvusCache`

### Phase 3: Semantic Search (Week 3)
1. Add `semantic_search()` method to `MilvusCache`
2. Update `CacheProtocol` with optional semantic search method
3. Add integration tests for semantic search quality
4. Performance benchmarking

### Phase 4: Tool Integration (Week 4)
1. Add `semantic_query` parameter to lookup tools
2. Update tool documentation
3. Test with real D&D queries
4. Update CLI help text

### Phase 5: Default Migration (Week 5)
1. Make Milvus Lite the default backend
2. Update configuration documentation
3. Add migration guide for existing users
4. Archive SQLite implementation (keep for reference)

## Configuration

### Environment Variables
```bash
# Cache backend (default: milvus)
LOREKEEPER_CACHE_BACKEND=milvus  # or "sqlite" for backward compatibility

# Milvus Lite settings
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db

# Embedding model (default: all-MiniLM-L6-v2)
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Legacy SQLite (deprecated)
LOREKEEPER_SQLITE_DB_PATH=~/.lorekeeper/cache.db
```

### Config Class
```python
@dataclass
class CacheConfig:
    backend: str = "milvus"  # "milvus" or "sqlite"
    milvus_db_path: str = "~/.lorekeeper/milvus.db"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # SQLite legacy
    sqlite_db_path: str = "~/.lorekeeper/cache.db"
```

## Open Questions (Resolved)

1. **Should we support custom embedding models via config?**
   - **Yes.** Add `LOREKEEPER_EMBEDDING_MODEL` environment variable.
   - Default to `all-MiniLM-L6-v2` but allow override.

2. **How to handle entities without good text descriptions?**
   - Use `name + type` as minimum fallback.
   - Log warning for entities with very short text (<20 chars).

3. **Should semantic search be enabled by default in tools?**
   - **No.** Keep structured search as default for backward compatibility.
   - Add explicit `semantic_query` parameter to tools.
   - Semantic search opt-in per query.

4. **How to handle the first-run model download?**
   - Lazy loading: model downloads on first semantic search.
   - Log info message about download size and progress.
   - Document in README that first semantic search may be slow.
