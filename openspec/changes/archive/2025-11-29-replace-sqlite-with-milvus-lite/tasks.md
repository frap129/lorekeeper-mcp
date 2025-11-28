# Tasks: Replace SQLite with Milvus Lite

## 1. Core Infrastructure

### 1.1 Dependencies
- [x] 1.1.1 Add `pymilvus>=2.4.0` to pyproject.toml
- [x] 1.1.2 Add `sentence-transformers>=2.2.0` to pyproject.toml
- [x] 1.1.3 Run `uv sync` to verify dependencies install correctly
- [x] 1.1.4 Verify Milvus Lite works with `from pymilvus import MilvusClient`

### 1.2 EmbeddingService Implementation
- [x] 1.2.1 Create `src/lorekeeper_mcp/cache/embedding.py`
- [x] 1.2.2 Implement `EmbeddingService` class with lazy model loading
- [x] 1.2.3 Implement `encode(text: str) -> list[float]` method
- [x] 1.2.4 Implement `encode_batch(texts: list[str]) -> list[list[float]]` method
- [x] 1.2.5 Implement `get_searchable_text(entity: dict, entity_type: str) -> str` method
- [x] 1.2.6 Add entity-type-specific text extraction (spells, creatures, equipment, etc.)
- [x] 1.2.7 Create unit tests in `tests/test_cache/test_embedding.py`

### 1.3 MilvusCache Class Implementation
- [x] 1.3.1 Create `src/lorekeeper_mcp/cache/milvus.py`
- [x] 1.3.2 Implement `MilvusCache.__init__(db_path: str)` with lazy client init
- [x] 1.3.3 Implement `client` property with lazy initialization
- [x] 1.3.4 Implement `close()` method for cleanup
- [x] 1.3.5 Implement context manager (`__aenter__`, `__aexit__`)
- [x] 1.3.6 Define collection schemas for each entity type
- [x] 1.3.7 Implement `_ensure_collections()` for auto-creation
- [x] 1.3.8 Implement index configuration (IVF_FLAT, COSINE)

## 2. CacheProtocol Implementation

### 2.1 get_entities Method
- [x] 2.1.1 Implement `get_entities(entity_type, document, **filters)` method
- [x] 2.1.2 Implement filter expression builder for scalar fields
- [x] 2.1.3 Support `document` parameter as string or list
- [x] 2.1.4 Support `name` filter with case-insensitive matching
- [x] 2.1.5 Support entity-specific filters (level, school, cr, type, etc.)
- [x] 2.1.6 Return results in same format as SQLiteCache

### 2.2 store_entities Method
- [x] 2.2.1 Implement `store_entities(entities, entity_type)` method
- [x] 2.2.2 Extract searchable text for each entity
- [x] 2.2.3 Generate embeddings for batch of entities
- [x] 2.2.4 Upsert entities into Milvus collection
- [x] 2.2.5 Handle duplicate slugs (upsert behavior)
- [x] 2.2.6 Return count of entities stored

### 2.3 Semantic Search Method
- [x] 2.3.1 Implement `semantic_search(entity_type, query, limit, **filters)` method
- [x] 2.3.2 Generate query embedding from search text
- [x] 2.3.3 Combine vector search with scalar filters (hybrid search)
- [x] 2.3.4 Return results ranked by similarity score
- [x] 2.3.5 Handle empty query gracefully (fall back to get_entities)

### 2.4 Additional Cache Methods
- [x] 2.4.1 Implement `get_entity_count(entity_type)` method
- [x] 2.4.2 Implement `get_available_documents()` method
- [x] 2.4.3 Implement `get_document_metadata(document_key)` method
- [x] 2.4.4 Implement `get_cache_stats()` method

## 3. Protocol and Factory Updates

### 3.1 CacheProtocol Updates
- [x] 3.1.1 Add `semantic_search()` method signature to CacheProtocol
- [x] 3.1.2 Ensure SQLiteCache has stub implementation (raise NotImplementedError)
- [x] 3.1.3 Update protocol docstrings

### 3.2 Cache Factory
- [x] 3.2.1 Create `src/lorekeeper_mcp/cache/factory.py`
- [x] 3.2.2 Implement `create_cache(backend: str, **kwargs)` function
- [x] 3.2.3 Support "milvus" and "sqlite" backend strings
- [x] 3.2.4 Read backend choice from config/environment

### 3.3 Module Exports
- [x] 3.3.1 Update `src/lorekeeper_mcp/cache/__init__.py` exports
- [x] 3.3.2 Export `MilvusCache`, `EmbeddingService`, `create_cache`
- [x] 3.3.3 Keep `SQLiteCache` exported for backward compatibility

## 4. Configuration Updates

### 4.1 Config Changes
- [x] 4.1.1 Add `LOREKEEPER_CACHE_BACKEND` environment variable
- [x] 4.1.2 Add `LOREKEEPER_MILVUS_DB_PATH` environment variable
- [x] 4.1.3 Add `LOREKEEPER_EMBEDDING_MODEL` environment variable
- [x] 4.1.4 Update `src/lorekeeper_mcp/config.py` with new settings
- [x] 4.1.5 Add sensible defaults (milvus, ~/.lorekeeper/milvus.db, all-MiniLM-L6-v2)

### 4.2 Documentation
- [x] 4.2.1 Update `.env.example` with new variables
- [x] 4.2.2 Document first-run model download in README
- [x] 4.2.3 Document semantic search usage

## 5. Repository Integration

### 5.1 Repository Updates
- [x] 5.1.1 Update `BaseRepository` to support semantic search
- [x] 5.1.2 Add `semantic_query` parameter to `search()` method
- [x] 5.1.3 Update `SpellRepository` with semantic search support
- [x] 5.1.4 Update `CreatureRepository` with semantic search support
- [x] 5.1.5 Update `EquipmentRepository` with semantic search support
- [x] 5.1.6 Update `CharacterOptionRepository` with semantic search support
- [x] 5.1.7 Update `RuleRepository` with semantic search support

### 5.2 Repository Factory
- [x] 5.2.1 Update repository factory to use new cache factory
- [x] 5.2.2 Ensure repositories work with both cache backends

## 6. Tool Updates

### 6.1 Spell Lookup Tool
- [x] 6.1.1 Add `semantic_query: str | None` parameter
- [x] 6.1.2 Use semantic search when `semantic_query` provided
- [x] 6.1.3 Combine with existing filters (level, school, etc.)
- [x] 6.1.4 Update tool docstring and description

### 6.2 Creature Lookup Tool
- [x] 6.2.1 Add `semantic_query: str | None` parameter
- [x] 6.2.2 Use semantic search when `semantic_query` provided
- [x] 6.2.3 Combine with existing filters (cr, type, etc.)
- [x] 6.2.4 Update tool docstring and description

### 6.3 Equipment Lookup Tool
- [x] 6.3.1 Add `semantic_query: str | None` parameter
- [x] 6.3.2 Use semantic search when `semantic_query` provided
- [x] 6.3.3 Update tool docstring and description

### 6.4 Character Option Lookup Tool
- [x] 6.4.1 Add `semantic_query: str | None` parameter
- [x] 6.4.2 Use semantic search when `semantic_query` provided
- [x] 6.4.3 Update tool docstring and description

### 6.5 Rule Lookup Tool
- [x] 6.5.1 Add `semantic_query: str | None` parameter
- [x] 6.5.2 Use semantic search when `semantic_query` provided
- [x] 6.5.3 Update tool docstring and description

### 6.6 Search DnD Content Tool
- [x] 6.6.1 Update to use semantic search by default
- [x] 6.6.2 Support `semantic=false` parameter for structured-only search
- [x] 6.6.3 Update tool docstring and description

## 7. Testing

### 7.1 Unit Tests
- [ ] 7.1.1 Create `tests/test_cache/test_milvus.py`
- [ ] 7.1.2 Test MilvusCache initialization and cleanup
- [ ] 7.1.3 Test store_entities with various entity types
- [ ] 7.1.4 Test get_entities with filters
- [ ] 7.1.5 Test semantic_search basic functionality
- [ ] 7.1.6 Test hybrid search (semantic + filters)
- [ ] 7.1.7 Test error handling (connection, schema, embedding)

### 7.2 EmbeddingService Tests
- [ ] 7.2.1 Test lazy model loading
- [ ] 7.2.2 Test single text encoding
- [ ] 7.2.3 Test batch encoding
- [ ] 7.2.4 Test searchable text extraction per entity type
- [ ] 7.2.5 Test handling of empty/missing text fields

### 7.3 Integration Tests
- [ ] 7.3.1 Test end-to-end spell storage and retrieval
- [ ] 7.3.2 Test semantic search quality (fire spells find Fire Shield)
- [ ] 7.3.3 Test hybrid search accuracy
- [ ] 7.3.4 Test with real Open5e data

### 7.4 Repository Tests
- [ ] 7.4.1 Update existing repository tests to work with MilvusCache
- [ ] 7.4.2 Add semantic search tests to repository test suites
- [ ] 7.4.3 Ensure all existing tests pass

### 7.5 Tool Tests
- [ ] 7.5.1 Add semantic_query parameter tests for each tool
- [ ] 7.5.2 Test semantic + filter combinations
- [ ] 7.5.3 Test backward compatibility (tools work without semantic_query)

### 7.6 Performance Tests
- [ ] 7.6.1 Benchmark semantic search latency (<100ms target)
- [ ] 7.6.2 Benchmark bulk storage performance
- [ ] 7.6.3 Compare storage size with SQLite

## 8. Migration and Documentation

### 8.1 Migration Guide
- [ ] 8.1.1 Document breaking changes
- [ ] 8.1.2 Explain that cache data needs re-indexing
- [ ] 8.1.3 Provide migration commands/steps
- [ ] 8.1.4 Document rollback procedure (switch to sqlite backend)

### 8.2 User Documentation
- [ ] 8.2.1 Update docs/cache.md with Milvus Lite details
- [ ] 8.2.2 Update docs/tools.md with semantic search examples
- [ ] 8.2.3 Add semantic search examples to README
- [ ] 8.2.4 Document environment variables

### 8.3 Code Documentation
- [ ] 8.3.1 Add docstrings to all new classes and methods
- [ ] 8.3.2 Update existing docstrings with semantic search info
- [ ] 8.3.3 Add inline comments for complex logic

## 9. Cleanup and Finalization

### 9.1 Code Quality
- [ ] 9.1.1 Run `just lint` and fix all issues
- [ ] 9.1.2 Run `just format` to ensure consistent formatting
- [ ] 9.1.3 Run `just type-check` and fix all type errors
- [ ] 9.1.4 Run `just test` and ensure all tests pass
- [ ] 9.1.5 Run `just check` for full quality validation

### 9.2 Final Verification
- [ ] 9.2.1 Verify live tests pass with real APIs
- [ ] 9.2.2 Manual testing of semantic search with varied queries
- [ ] 9.2.3 Test with fresh install (no existing cache)
- [ ] 9.2.4 Test upgrade from SQLite to Milvus
- [ ] 9.2.5 Verify all existing live tests continue to pass (CRITICAL - rule #1)
- [ ] 9.2.6 Test semantic search quality with real D&D content

### 9.3 Archive Previous Proposal
- [ ] 9.3.1 Archive `replace-sqlite-with-marqo` proposal (superseded)
- [ ] 9.3.2 Update any references to Marqo proposal
