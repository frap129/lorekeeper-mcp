# Replace SQLite with Marqo for Vector Similarity Search

**Change ID**: `2025-11-08-replace-sqlite-with-marqo`
**Status**: Proposed
**Created**: 2025-11-08

## Summary

Replace the current SQLite-based caching system with Marqo, an end-to-end vector search engine. This change enables semantic search capabilities while maintaining all existing structured filtering functionality.

## Motivation

The current SQLite cache supports exact matching and basic filtering (level, school, CR, etc.) but lacks semantic search capabilities. Users must know exact spell names or specific criteria to find relevant D&D content.

**Current Limitations:**
- No semantic search: "spells that protect against fire" requires manual filtering
- Substring matching only: searching "protection" won't find semantically related defensive spells
- No similarity-based recommendations: can't find "items similar to this magic sword"
- No natural language queries: can't ask "find healing spells for low-level clerics"

**Marqo Advantages:**
- **Vector embeddings**: Automatic semantic understanding of D&D content
- **Unified storage**: Single system for caching AND vector search (vs SQLite + separate vector DB)
- **Built-in models**: Pre-trained embeddings without manual ML pipeline
- **Metadata filtering**: Supports structured filters (level, school, CR) alongside vector search
- **Multimodal**: Can handle text and images (future: monster/item artwork)
- **Simple API**: Cleaner interface than SQLite for document storage

## Goals

1. **Replace all SQLite functionality** with Marqo for entity caching
2. **Add semantic search** for spells, monsters, equipment, and other D&D content
3. **Maintain structured filtering** (level, school, CR, type, etc.) using Marqo's filtering
4. **Improve search UX** with natural language queries and similarity matching
5. **Simplify architecture** by consolidating caching and search into one system

## Non-Goals

- Supporting both SQLite and Marqo simultaneously (full replacement only)
- Implementing custom embedding models (use Marqo's built-in models)
- Migrating existing SQLite data automatically (manual re-indexing from APIs)
- Building a web UI for search (CLI/MCP server only)

## Impact Assessment

### Code Impact
- **High**: Complete replacement of `cache/` module (db.py, schema.py)
- **Medium**: Update all API clients using cache functions
- **Medium**: Modify server initialization for Marqo
- **High**: Rewrite all cache-related tests

### Files Affected (~15 files)
- `src/lorekeeper_mcp/cache/db.py` - Rewrite with Marqo client
- `src/lorekeeper_mcp/cache/schema.py` - Replace with Marqo index definitions
- `src/lorekeeper_mcp/config.py` - Add Marqo connection settings
- `src/lorekeeper_mcp/server.py` - Update initialization
- `src/lorekeeper_mcp/api_clients/base.py` - Update cache calls
- All tool files (`tools/*.py`) - Update to use semantic search
- All test files (`tests/test_cache/*.py`, `tests/test_api_clients/*.py`)

### Infrastructure Impact
- **New Requirement**: Docker/Podman for running Marqo service
- **Port Usage**: Default 8882 for Marqo
- **Storage**: Marqo uses disk for index storage (~similar to SQLite)
- **Dependencies**: Add `marqo` Python client to pyproject.toml

### Breaking Changes
- Database file format incompatible (SQLite → Marqo indexes)
- Cache functions have different signatures
- Configuration variables change (`DB_PATH` → `MARQO_URL`)
- Requires Marqo service running (vs embedded SQLite)

### Migration Path
1. Deploy Marqo service via Docker
2. Update configuration with Marqo URL
3. Deploy new code (auto re-indexes from APIs on first use)
4. Old SQLite cache becomes obsolete (can be archived)

## Success Criteria

- [ ] All entity types (spells, monsters, etc.) cached in Marqo indexes
- [ ] Structured filtering works (level=3, school="Evocation")
- [ ] Semantic search returns relevant results for natural language queries
- [ ] Search performance ≤ 100ms for cached queries
- [ ] All existing tests pass with Marqo backend
- [ ] Documentation updated with Marqo setup instructions
- [ ] Docker Compose file provided for easy Marqo deployment

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Marqo service unavailable | High - no caching | Low | Provide health check, fallback to API |
| Performance slower than SQLite | Medium | Medium | Benchmark early, optimize indexes |
| Docker requirement barrier | Medium | Medium | Document setup clearly, provide docker-compose |
| Semantic search quality low | Medium | Low | Test with diverse queries, tune parameters |
| Breaking existing integrations | High | High | Version bump, migration guide, backward compat layer |

## Related Specifications

- `marqo-cache-implementation` - Core caching with Marqo
- `marqo-semantic-search` - Semantic/vector search features
- `marqo-infrastructure` - Deployment and configuration

## Dependencies

- Marqo service (Docker container)
- `marqo` Python client library
- Updated configuration management
- New test fixtures for Marqo

## Timeline Estimate

- **Design & Spec**: 1 day (this document)
- **Core Implementation**: 3-4 days
  - Replace cache module: 1 day
  - Update API clients: 1 day
  - Add semantic search: 1 day
  - Infrastructure setup: 0.5 day
- **Testing**: 2 days
  - Unit tests: 1 day
  - Integration tests: 1 day
- **Documentation**: 1 day

**Total**: ~7-8 days

## Open Questions

1. ~~Which embedding model to use?~~ → Start with default (e5-base-v2), optimize later
2. ~~How to handle Marqo downtime?~~ → Graceful degradation to direct API calls
3. ~~Index naming convention?~~ → `lorekeeper-{entity_type}` (e.g., `lorekeeper-spells`)
4. ~~Multi-tenancy?~~ → Single instance for now, no tenant isolation needed

## Alternatives Considered

### Keep SQLite + Add Separate Vector DB
- **Pros**: No breaking changes, incremental adoption
- **Cons**: Complexity of two systems, data sync issues, more dependencies
- **Decision**: Rejected - prefer unified solution

### Use Elasticsearch/OpenSearch
- **Pros**: Mature ecosystem, widely adopted
- **Cons**: Heavier infrastructure, manual embedding pipeline, more complex setup
- **Decision**: Rejected - Marqo simpler for vector search use case

### Build Custom Vector Search with FAISS
- **Pros**: Maximum control, no external service
- **Cons**: High implementation cost, reinventing the wheel, maintenance burden
- **Decision**: Rejected - not core competency

### Use Pinecone/Weaviate (Cloud Vector DBs)
- **Pros**: Managed service, no ops burden
- **Cons**: Vendor lock-in, cost, external dependency
- **Decision**: Rejected - prefer self-hosted for MCP server use case

## Approval

- [ ] Technical Review
- [ ] Architecture Review
- [ ] Security Review (if applicable)
- [ ] Performance Review (if applicable)

---

**Next Steps**: Review design.md for architectural decisions, then proceed to implementation tasks.
