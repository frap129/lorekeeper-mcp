# Implementation Tasks

## Overview
Ordered list of implementation tasks to fix the critical MCP tool filtering issues. Tasks are sequenced to minimize risk and validate progress incrementally.

## Phase 1: Critical Performance Fix (URGENT)

### 1. Remove Client-Side Filtering Performance Bug
**File:** `src/lorekeeper_mcp/tools/creature_lookup.py`
**Task:** Eliminate 11x over-fetching by removing client-side filtering
**Description:** Fix immediate performance issue by converting to database filtering.

**Validation:**
- [ ] `lookup_creature(limit=20)` fetches exactly 20 items, not 220
- [ ] Memory usage reduced by 90% for filtered queries
- [ ] Query time improved by 5x or more
- [ ] No client-side filtering loops remain

### 2. Enhanced Database Layer Foundation
**File:** `src/lorekeeper_mcp/cache/db.py`
**Task:** Add enhanced case-insensitive filtering to `query_cached_entities()`
**Description:** Support case-insensitive, wildcard, and automatic slug fallback without changing parameters.

**Validation:**
- [ ] Case-insensitive filtering works with existing `name` parameter
- [ ] Wildcard matching works when `*` or `%` present in `name`
- [ ] Automatic slug fallback triggers when name search fails
- [ ] Legacy `name` parameter behavior preserved for backward compatibility

### 3. Case-Insensitive Indexes
**File:** `src/lorekeeper_mcp/cache/db.py`
**Task:** Add essential case-insensitive indexes only
**Description:** Create `LOWER(name)` indexes to support case-insensitive queries efficiently.

**Validation:**
- [ ] Case-insensitive indexes improve query performance
- [ ] `EXPLAIN QUERY PLAN` shows index usage for `LOWER(name)` queries
- [ ] Performance tests confirm sub-100ms query times with indexes
- [ ] No unnecessary composite indexes created

### 4. Automatic Slug Fallback Implementation
**File:** `src/lorekeeper_mcp/cache/db.py`
**Task:** Implement transparent slug fallback for name searches
**Description:** Add automatic slug search when name search returns no results.

**Validation:**
- [ ] Fallback triggers only when name search returns empty results
- [ ] Fallback uses existing slug PRIMARY KEY for optimal performance
- [ ] Fallback improves match rates without breaking existing behavior
- [ ] No parameter changes required - automatic behavior

### 5. Enhanced Database Layer Tests
**File:** `tests/test_cache/test_db.py`
**Task:** Add comprehensive tests for enhanced filtering
**Description:** Create unit tests covering enhanced behavior with existing parameters only.

**Validation:**
- [ ] Tests for case-insensitive exact matching with existing `name` parameter pass
- [ ] Tests for wildcard matching with `*` and `%` pass
- [ ] Tests for automatic slug fallback pass
- [ ] Tests for backward compatibility with legacy filters pass
- [ ] Tests for SQL injection protection pass

## Phase 2: Tool Layer Migration (High Priority)

### 6. Spell Lookup Tool Enhancement
**File:** `src/lorekeeper_mcp/tools/spell_lookup.py`
**Task:** Enable enhanced case-insensitive and automatic slug fallback
**Description:** Update `lookup_spell` to use enhanced database filtering.

**Validation:**
- [ ] `name="fireball"` finds "Fireball" via case-insensitive search
- [ ] `name="fire*"` performs partial matching with wildcards
- [ ] `name="fireball"` falls back to slug search if name match fails
- [ ] All filtering occurs at database level
- [ ] No new parameters added

### 7. Rule Lookup Tool Enhancement
**File:** `src/lorekeeper_mcp/tools/rule_lookup.py`
**Task:** Enable case-insensitive and enhanced filtering
**Description:** Update `lookup_rule` to support enhanced `name` parameter behavior.

**Validation:**
- [ ] Case-insensitive rule searching works automatically with `name` parameter
- [ ] Wildcard matching works with `name="*attack*"`
- [ ] Automatic rule slug fallback functions properly
- [ ] Database-level filtering eliminates client-side processing
- [ ] Backward compatibility with existing parameters maintained

### 8. Creature Lookup Tool Migration
**File:** `src/lorekeeper_mcp/tools/creature_lookup.py`
**Task:** Remove client-side filtering completely and enable enhanced behavior
**Description:** Migrate `lookup_creature` from client-side filtering to efficient database filtering.

**Validation:**
- [ ] Client-side filtering code is completely removed
- [ ] All filtering now occurs at database level
- [ ] Memory usage reduced by 90% for filtered queries
- [ ] Enhanced `name` parameter works with case-insensitive, wildcards, and slug fallback
- [ ] Performance tests show 5x improvement
- [ ] Backward compatibility maintained

### 9. Equipment Lookup Tool Migration
**File:** `src/lorekeeper_mcp/tools/equipment_lookup.py`
**Task:** Remove client-side filtering across all equipment types completely
**Description:** Migrate `lookup_equipment` from client-side filtering to database-level filtering.

**Validation:**
- [ ] Client-side filtering loops completely removed from all equipment types
- [ ] Database-level filtering works for weapons, armor, and magic-items
- [ ] No over-fetching occurs (respect exact limit parameter instead of 11x)
- [ ] Enhanced `name` parameter works with case-insensitive, wildcards, and slug fallback
- [ ] Performance improvements verified
- [ ] No new parameters added

### 10. Character Option Lookup Tool Migration
**File:** `src/lorekeeper_mcp/tools/character_option_lookup.py`
**Task:** Remove client-side filtering and enable enhanced filtering
**Description:** Migrate `lookup_character_option` from client-side filtering to database-level filtering.

**Validation:**
- [ ] Client-side filtering completely eliminated
- [ ] Database-level filtering works for all character option types
- [ ] Enhanced `name` parameter works with case-insensitive, wildcards, and slug fallback
- [ ] Memory usage optimized
- [ ] Performance improvements confirmed
- [ ] No new parameters added

## Phase 3: Testing and Validation (Medium Priority)

### 11. Enhanced Tool Tests
**Files:** `tests/test_tools/test_*.py`
**Task:** Add tests for enhanced search behavior with existing parameters
**Description:** Create comprehensive tests for enhanced `name` parameter across all 5 MCP tools.

**Validation:**
- [ ] Tests for case-insensitive behavior in all 5 tools pass
- [ ] Tests for wildcard matching with `*` and `%` pass
- [ ] Tests for automatic slug fallback in all tools pass
- [ ] Tests for backward compatibility with existing parameters pass
- [ ] Performance tests confirm database-level filtering
- [ ] Integration tests verify end-to-end functionality

### 12. Performance Benchmarking
**File:** `tests/test_tools/test_performance.py`
**Task:** Create performance tests to validate 11x over-fetching elimination
**Description:** Implement benchmark tests to compare before/after performance and verify efficiency gains.

**Validation:**
- [ ] Test verifies `lookup_creature(limit=20)` fetches exactly 20 items, not 220
- [ ] Test confirms memory usage reduction of ≥90% for filtered queries
- [ ] Test validates query execution time improvement of ≥5x
- [ ] Test measures single database query (not multiple client-side operations)
- [ ] Test includes before/after performance comparison
- [ ] Database queries return exactly `limit` results (not `limit * 11`)
- [ ] Memory usage reduced by 90% or more for filtered queries
- [ ] Query execution time improved by factor of 5 or more
- [ ] Client CPU usage for filtering eliminated completely
- [ ] Network transfer reduced significantly for all affected tools

### 13. Cross-Tool Consistency Tests
**File:** `tests/test_tools/test_consistency.py`
**Task:** Verify consistent enhanced behavior across all tools
**Description:** Create tests to ensure all tools behave consistently with enhanced `name` parameter.

**Validation:**
- [ ] All tools support the same enhanced `name` parameter behavior
- [ ] Parameter validation remains consistent across tools
- [ ] Error handling follows the same pattern as before
- [ ] Performance characteristics are similar and optimized
- [ ] User experience is predictable and consistent

## Phase 4: Quality Assurance and Documentation (Medium Priority)

### 14. Code Quality Verification
**Task:** Run linting, formatting, and type checking
**Description:** Ensure all code meets project quality standards.

**Validation:**
- [ ] `uv run ruff check src/ tests/` passes without warnings
- [ ] `uv run ruff format src/ tests/` makes no changes
- [ ] `uv run mypy src/` passes without type errors
- [ ] `uv run pre-commit run --all-files` passes
- [ ] All existing tests continue to pass

### 15. Integration Testing
**File:** `tests/test_tools/test_integration.py`
**Task:** Test complete workflows with enhanced filtering
**Description:** Create integration tests that simulate real usage scenarios with the enhanced filtering capabilities.

**Validation:**
- [ ] Multi-parameter searches work correctly across all tools
- [ ] Complex filtering scenarios function properly
- [ ] Error conditions are handled gracefully
- [ ] Database transactions work correctly
- [ ] Concurrent access functions properly

### 16. Documentation Updates
**File:** `docs/`
**Task:** Update documentation to reflect enhanced capabilities
**Description:** Update relevant documentation to describe new search parameters and behavior.

**Validation:**
- [ ] API documentation updated with new parameters
- [ ] Usage examples provided for enhanced search
- [ ] Migration guide for existing users created
- [ ] Performance improvements documented
- [ ] Architectural changes explained

## Phase 5: Final Validation and Deployment (Low Priority)

### 17. End-to-End Testing
**File:** `tests/test_tools/test_end_to_end.py`
**Task:** Complete workflow testing with enhanced behavior
**Description:** Test the complete system end-to-end with realistic data volumes and enhanced query patterns.

**Validation:**
- [ ] All critical user workflows function correctly with enhanced behavior
- [ ] Performance meets or exceeds expectations (11x over-fetching eliminated)
- [ ] No regressions in existing functionality
- [ ] Error recovery works properly
- [ ] System stability under load confirmed

### 18. Live MCP Server Testing
**File:** `tests/test_tools/test_live_mcp.py`
**Task:** Test enhanced filtering with actual MCP protocol client
**Description:** Verify that enhanced filtering works correctly through the MCP protocol interface.

**Validation:**
- [ ] MCP protocol discovery shows unchanged parameters
- [ ] Tool invocation through MCP protocol works with enhanced behavior
- [ ] Parameter validation via FastMCP works as before
- [ ] Response formatting remains consistent
- [ ] Error handling through MCP protocol works unchanged

### 19. Production Readiness Validation
**Task:** Final validation for production deployment
**Description:** Comprehensive validation to ensure the enhanced filtering changes are ready for production deployment.

**Validation:**
- [ ] All tests pass in production-like environment
- [ ] Performance benchmarks meet requirements (11x over-fetching eliminated)
- [ ] Security review completed successfully (SQL injection protection maintained)
- [ ] Rollback plan tested and verified (backward compatibility preserved)
- [ ] Monitoring and alerting configured for query performance
- [ ] Documentation complete and accurate (enhanced behavior documented)

## Dependencies and Parallel Work

### Parallelizable Tasks:
- Tasks 6-10 (Tool layer migrations) can be worked on in parallel by different developers
- Tasks 11-13 (Testing) can begin as soon as respective tools are completed
- Tasks 14-16 (Quality assurance) can run in parallel with testing

### Critical Path:
1. **Database foundation (Tasks 1-5)** must be completed first
2. **Tool migrations (Tasks 6-10)** depend on database layer completion
3. **Final validation (Tasks 17-19)** depends on all previous tasks

### Risk Mitigation:
- Implement feature flags to enable/disable enhanced features
- Maintain backward compatibility throughout development
- Create comprehensive rollback procedures
- Perform incremental testing and validation

## Success Metrics

### Performance Metrics:
- Query execution time: < 100ms for typical filtered queries
- Memory usage reduction: ≥ 90% for filtered queries
- Data transfer reduction: ≥ 90% for filtered queries

### Functionality Metrics:
- 100% backward compatibility with existing parameters
- 100% database-level filtering (11x over-fetching eliminated)
- Consistent enhanced behavior across all 5 MCP tools
- Enhanced `name` parameter working correctly (case-insensitive, wildcards, slug fallback)

### Quality Metrics:
- 0 code quality warnings or errors
- 100% test coverage for new functionality
- 0 security vulnerabilities
- Complete documentation for new features
