## 1. Implementation

### 1.1 Cache Layer Filter Operators
- [ ] 1.1.1 Add `FilterOperator` enum to cache/db.py (EQ, ILIKE, LIKE, IN, GTE, LTE)
- [ ] 1.1.2 Modify `query_cached_entities()` to accept filter operators alongside values
- [ ] 1.1.3 Implement case-insensitive matching with `LOWER(field) = LOWER(?)`
- [ ] 1.1.4 Implement wildcard detection (*, %) and LIKE query generation
- [ ] 1.1.5 Add unit tests for new filter operators

### 1.2 Database Indexes
- [ ] 1.2.1 Add `LOWER(name)` index creation to `init_entity_cache()` in schema.py
- [ ] 1.2.2 Create migration function for existing databases
- [ ] 1.2.3 Verify index usage with EXPLAIN QUERY PLAN tests

### 1.3 Repository Layer Enhancements
- [ ] 1.3.1 Update base repository to use case-insensitive name filter by default
- [ ] 1.3.2 Implement automatic slug fallback when name search returns empty
- [ ] 1.3.3 Add wildcard character detection before passing to cache
- [ ] 1.3.4 Unit tests for repository search with wildcards and fallback

### 1.4 Integration Tests
- [ ] 1.4.1 Test case-insensitive search end-to-end via MCP tools
- [ ] 1.4.2 Test wildcard partial matching (fire*, *bolt, *fire*)
- [ ] 1.4.3 Test slug fallback behavior
- [ ] 1.4.4 Performance test: verify index usage

## 2. Validation
- [ ] 2.1 All existing tests pass
- [ ] 2.2 Live tests pass with enhanced search features
- [ ] 2.3 Performance benchmarks show index utilization
