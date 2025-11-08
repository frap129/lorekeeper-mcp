# Implement --build-cache Flag for Upfront Cache Population

**Change ID**: `implement-build-cache-flag`
**Status**: Proposed
**Created**: 2025-11-08
**Depends On**: `replace-sqlite-with-marqo`

## Summary

Add a `--build-cache` CLI flag to the MCP server that fetches all available D&D entities from configured APIs and populates the Marqo cache upfront before starting normal server operation. This enables pre-warming the cache for offline usage, testing, or deployment preparation.

## Motivation

After migrating to Marqo, the cache starts empty and populates lazily as users query for entities. This creates several challenges:

**Current Limitations:**
- **Cold start latency**: First queries require API calls, increasing response time
- **Offline usage**: Cannot use MCP server without internet connection until cache is populated
- **Testing friction**: Integration and live tests need pre-populated cache data
- **Deployment complexity**: Production deployments start with empty cache, degrading initial user experience

**Benefits of Upfront Cache Building:**
- **Pre-warmed cache**: All entities available immediately on server start
- **Offline-first operation**: Full functionality without external API dependencies
- **Faster testing**: Pre-build cache once, run tests many times
- **Predictable deployment**: Known cache state, consistent performance from first request
- **Development convenience**: Build cache once, work offline for hours

## Goals

1. **Add CLI flag** `--build-cache` to trigger cache population mode
2. **Fetch all entities** from all configured API clients (Open5e v1, Open5e v2, D&D 5e API)
3. **Populate Marqo indexes** with all available D&D entities
4. **Progress reporting** to show cache building status
5. **Error handling** to continue on partial failures (some API endpoints may fail)
6. **Exit gracefully** after cache build completes (or start server normally if flag omitted)

## Non-Goals

- Automatic cache updates/synchronization (one-time build only)
- Incremental cache building (all-or-nothing fetch)
- Cache versioning or migration
- Differential updates (always full rebuild)
- Scheduled cache refreshes (manual rebuild only)

## Impact Assessment

### Code Impact
- **Low**: Add CLI argument parsing to `__main__.py`
- **Medium**: Implement cache builder module with API orchestration
- **Low**: Update server initialization to support build-cache mode
- **Low**: Add progress logging and error handling

### Files Affected (~5 files)
- `src/lorekeeper_mcp/__main__.py` - Add argparse, `--build-cache` flag
- `src/lorekeeper_mcp/cache_builder.py` - New module for cache building logic
- `src/lorekeeper_mcp/server.py` - Support build-cache mode (skip lifespan for build)
- `tests/test_cache_builder.py` - New tests for cache builder
- `README.md` - Document `--build-cache` usage

### Infrastructure Impact
- **Requirement**: Marqo service must be running before cache build
- **API Load**: Fetches all paginated endpoints from multiple APIs (one-time burst)
- **Time**: Initial cache build may take 2-5 minutes depending on API response times
- **Storage**: Full cache ~10-50MB depending on entity counts

### Breaking Changes
- None - purely additive feature
- Existing server behavior unchanged when flag not used

### Migration Path
No migration needed - this is a new optional feature.

## Success Criteria

- [ ] `uv run lorekeeper-mcp --build-cache` fetches all entity types
- [ ] All 11 entity types populated in Marqo indexes (spells, monsters, weapons, armor, classes, races, backgrounds, feats, conditions, rules, rule_sections)
- [ ] Progress logging shows entity counts per type as they're indexed
- [ ] Partial API failures logged but don't halt entire build
- [ ] Cache builder exits with status code 0 on success, non-zero on critical failure
- [ ] `--help` documents the `--build-cache` flag
- [ ] Tests validate cache builder fetches from all clients

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API rate limiting during bulk fetch | High | Medium | Add rate limiting, exponential backoff, resume logic |
| Single API failure halts entire build | High | Medium | Continue on partial failures, log errors, build what's available |
| Long build time (5+ minutes) | Medium | Low | Show progress bar, allow background building |
| Memory usage during bulk fetch | Medium | Low | Batch indexing (100 docs at a time), streaming fetch |

## Related Specifications

- `cache-builder-cli` - CLI interface and argument parsing
- `cache-builder-orchestration` - Fetch orchestration across multiple APIs
- `cache-builder-progress` - Progress reporting and error handling

## Dependencies

- **Hard Dependency**: `replace-sqlite-with-marqo` (Marqo must be implemented first)
- Marqo service running at configured URL
- Network connectivity to external APIs (Open5e, D&D 5e API)

## Timeline Estimate

- **Design & Spec**: 0.5 days (this document)
- **Core Implementation**: 1.5 days
  - CLI argument parsing: 0.25 days
  - Cache builder orchestration: 0.75 days
  - Progress reporting: 0.25 days
  - Error handling: 0.25 days
- **Testing**: 0.5 days
- **Documentation**: 0.25 days

**Total**: ~2-3 days

## Open Questions

1. **Should we add a `--skip-cache-build` flag to skip cache init entirely?** → No, build-cache is opt-in
2. **Should progress be shown with a progress bar or simple logging?** → Simple logging initially, progress bar in future enhancement
3. **Should we support building cache for specific entity types only?** → No, all-or-nothing for simplicity
4. **Should the server start after cache build completes?** → No, exit after build (user can restart server separately)

## Alternatives Considered

### Background Cache Building on Server Start
- **Pros**: Transparent to users, server starts immediately
- **Cons**: Complexity, race conditions, unclear completion state
- **Decision**: Rejected - prefer explicit opt-in mode

### Separate `lorekeeper-cache-builder` CLI Tool
- **Pros**: Clean separation of concerns
- **Cons**: Extra tooling, installation complexity, duplicated code
- **Decision**: Rejected - prefer single entry point with flag

### Automatic Cache Building on First Request
- **Pros**: No manual step required
- **Cons**: Unpredictable latency, poor UX, hard to test
- **Decision**: Rejected - prefer explicit control

## Approval

- [ ] Technical Review
- [ ] Architecture Review
- [ ] Security Review (if applicable)
- [ ] Performance Review (if applicable)

---

**Next Steps**: Review design.md for implementation details, then proceed to spec deltas and tasks.
