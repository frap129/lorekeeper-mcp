# Replace SQLite with Milvus Lite for Vector and Semantic Search

**Change ID**: `replace-sqlite-with-milvus-lite`
**Status**: Proposed
**Created**: 2025-11-28

## Why

The current SQLite-based caching system only supports exact matching and basic filtering. Users cannot perform semantic searches like "find spells that protect against fire" or "monsters similar to a dragon". Milvus Lite provides a fully embedded vector database that runs locally without external services, enabling semantic search while maintaining the simplicity of our current architecture.

This proposal supersedes the earlier Marqo proposal (`replace-sqlite-with-marqo`) which required Docker and an external service. Milvus Lite provides equivalent semantic search capabilities with zero infrastructure overhead.

## What Changes

- **BREAKING**: Replace SQLite cache with Milvus Lite vector database
- Add semantic/vector search capabilities across all entity types
- Implement automatic embedding generation for D&D content using `all-MiniLM-L6-v2` model
- Maintain all existing structured filtering (level, school, CR, type, etc.)
- Add hybrid search combining vector similarity with structured filters
- Remove Docker/external service requirements (Milvus Lite is embedded like SQLite)

## Impact

- **Affected specs**: `entity-cache`, `enhanced-search`, `mcp-tools`
- **Affected code**:
  - `src/lorekeeper_mcp/cache/` - Complete rewrite
  - `src/lorekeeper_mcp/tools/` - Add semantic search parameters
  - `src/lorekeeper_mcp/config.py` - Update configuration
  - `tests/test_cache/` - Rewrite for Milvus Lite
- **Dependencies**:
  - Add `pymilvus>=2.4.0` (includes Milvus Lite - no separate install needed)
  - Add `sentence-transformers>=2.2.0` for embedding generation
  - Note: Install with `pip install pymilvus` - Milvus Lite is included automatically
- **No Docker required**: Milvus Lite runs embedded in the Python process
- **Migration**: Existing cache data will need re-indexing (cache is not source of truth)

## Key Benefits Over Alternatives

| Feature | SQLite (Current) | Marqo (Prior Proposal) | Milvus Lite (This) |
|---------|------------------|------------------------|-------------------|
| External Service | None | Docker required | None (embedded) |
| Semantic Search | No | Yes | Yes |
| Hybrid Search | No | Yes | Yes |
| Setup Complexity | Low | High | Low |
| Deployment | Copy DB file | Docker Compose | Copy DB file |
| Offline Support | Yes | No | Yes |
| Resource Usage | Minimal | ~2-4GB RAM | ~200-500MB RAM |
| Embedding Model | N/A | Server-managed | Local (all-MiniLM-L6-v2) |
| First-run Download | None | Docker images | ~80MB model |
| Python API | Custom | marqo client | pymilvus (same API as full Milvus) |

## Success Criteria

- [ ] All entity types searchable via semantic queries
- [ ] Structured filters work alongside vector search (hybrid search)
- [ ] No external services required (fully embedded)
- [ ] Search latency < 100ms for typical queries
- [ ] Storage footprint < 2x current SQLite size
- [ ] All existing tests pass with new backend
- [ ] Backward compatible: existing tool parameters continue working
- [ ] `CacheProtocol` interface maintained for potential future backend swaps
