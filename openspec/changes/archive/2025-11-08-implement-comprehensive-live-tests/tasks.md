# Implementation Tasks: Comprehensive Live MCP Tests

## 1. Infrastructure Setup

### Task 1.1: Configure pytest markers
- [ ] Add `live` marker to `[tool.pytest.ini_options]` in `pyproject.toml`
- [ ] Add `slow` marker for tests >1s
- [ ] Update marker descriptions
- **Validation**: Run `pytest --markers` and verify markers are listed
- **Estimated effort**: 5 minutes

### Task 1.2: Create live test fixtures
- [ ] Add `live_db` fixture to `tests/conftest.py` for test database with optional reset
- [ ] Add `rate_limiter` fixture to enforce delays between API calls
- [ ] Add `cache_stats` fixture to track cache hit/miss rates
- [ ] Add `clear_cache` fixture to reset cache before tests
- **Dependencies**: Task 1.1
- **Validation**: Import fixtures in test file without errors
- **Estimated effort**: 30 minutes

### Task 1.3: Create test file skeleton
- [ ] Create `tests/test_tools/test_live_mcp.py` with module docstring
- [ ] Import all required dependencies (pytest, tools, fixtures)
- [ ] Add file-level documentation about live testing
- [ ] Create empty test classes for each tool (5 classes)
- **Dependencies**: Task 1.2
- **Validation**: File imports successfully, `pytest --collect-only -m live` shows no tests yet
- **Estimated effort**: 10 minutes

## 2. Spell Lookup Live Tests

### Task 2.1: Implement basic spell lookup tests
- [ ] `test_spell_by_name_found` - Verify "Magic Missile" lookup
- [ ] `test_spell_by_name_not_found` - Verify non-existent spell returns empty
- [ ] `test_spell_basic_fields_present` - Verify response schema
- **Dependencies**: Task 1.3
- **Validation**: `pytest -m live tests/test_tools/test_live_mcp.py::TestLiveSpellLookup -v`
- **Estimated effort**: 20 minutes

### Task 2.2: Implement spell filtering tests
- [ ] `test_spell_filter_by_level` - Verify level=0 returns cantrips
- [ ] `test_spell_filter_by_school` - Verify school="evocation" filtering
- [ ] `test_spell_filter_combined` - Verify class_key + concentration filtering
- [ ] `test_spell_limit_respected` - Verify limit parameter works
- **Dependencies**: Task 2.1
- **Validation**: All spell filtering tests pass
- **Estimated effort**: 25 minutes

### Task 2.3: Implement spell cache tests
- [ ] `test_spell_cache_miss_then_hit` - Verify cache behavior on duplicate queries
- [ ] `test_spell_cache_performance` - Verify cached queries <50ms
- [ ] `test_spell_different_queries_different_cache` - Verify cache isolation
- **Dependencies**: Task 2.2, requires `cache_stats` fixture
- **Validation**: Cache tests pass, verify hit/miss counts
- **Estimated effort**: 20 minutes

### Task 2.4: Implement spell error handling tests
- [ ] `test_spell_invalid_school` - Verify graceful handling of invalid school
- [ ] `test_spell_invalid_limit` - Verify handling of negative/zero limit
- [ ] `test_spell_empty_results` - Verify handling of queries with no matches
- **Dependencies**: Task 2.3
- **Validation**: Error tests pass, no crashes occur
- **Estimated effort**: 15 minutes

## 3. Creature Lookup Live Tests

### Task 3.1: Implement basic creature lookup tests
- [ ] `test_creature_by_name_found` - Verify "Goblin" lookup
- [ ] `test_creature_by_name_not_found` - Verify non-existent creature returns empty
- [ ] `test_creature_basic_fields_present` - Verify response schema (CR, type, HP)
- **Dependencies**: Task 1.3
- **Validation**: Basic creature tests pass
- **Estimated effort**: 20 minutes

### Task 3.2: Implement creature filtering tests
- [ ] `test_creature_filter_by_cr` - Verify cr=1 filtering
- [ ] `test_creature_filter_by_cr_range` - Verify cr_min/cr_max filtering
- [ ] `test_creature_filter_by_type` - Verify type="beast" filtering
- [ ] `test_creature_filter_by_size` - Verify size="Large" filtering
- **Dependencies**: Task 3.1
- **Validation**: All creature filtering tests pass
- **Estimated effort**: 25 minutes

### Task 3.3: Implement creature cache tests
- [ ] `test_creature_cache_behavior` - Verify cache hit/miss behavior
- [ ] `test_creature_cache_performance` - Verify cached queries <50ms
- **Dependencies**: Task 3.2
- **Validation**: Cache tests pass
- **Estimated effort**: 15 minutes

### Task 3.4: Implement creature error handling tests
- [ ] `test_creature_invalid_cr` - Verify handling of invalid CR values
- [ ] `test_creature_invalid_type` - Verify handling of invalid type
- [ ] `test_creature_empty_results` - Verify handling of no matches
- **Dependencies**: Task 3.3
- **Validation**: Error tests pass
- **Estimated effort**: 15 minutes

## 4. Equipment Lookup Live Tests

### Task 4.1: Implement basic equipment lookup tests
- [ ] `test_equipment_weapon_lookup` - Verify "Longsword" lookup with weapon properties
- [ ] `test_equipment_armor_lookup` - Verify armor lookup with AC properties
- [ ] `test_equipment_basic_fields_present` - Verify response schema
- **Dependencies**: Task 1.3
- **Validation**: Basic equipment tests pass
- **Estimated effort**: 20 minutes

### Task 4.2: Implement equipment filtering tests
- [ ] `test_equipment_magic_item_rarity` - Verify rarity filtering
- [ ] `test_equipment_type_all` - Verify type="all" searches across categories
- [ ] `test_equipment_name_filter` - Verify name filtering works
- **Dependencies**: Task 4.1
- **Validation**: All equipment filtering tests pass
- **Estimated effort**: 20 minutes

### Task 4.3: Implement equipment cache and error tests
- [ ] `test_equipment_cache_behavior` - Verify cache hit/miss
- [ ] `test_equipment_invalid_type` - Verify handling of invalid type
- [ ] `test_equipment_empty_results` - Verify handling of no matches
- **Dependencies**: Task 4.2
- **Validation**: Cache and error tests pass
- **Estimated effort**: 15 minutes

## 5. Character Option Lookup Live Tests

### Task 5.1: Implement basic character option lookup tests
- [ ] `test_character_option_class_lookup` - Verify class lookup returns 12+ classes
- [ ] `test_character_option_race_lookup` - Verify race lookup returns 9+ races
- [ ] `test_character_option_background_lookup` - Verify background lookup
- [ ] `test_character_option_feat_lookup` - Verify feat lookup returns 20+ feats
- **Dependencies**: Task 1.3
- **Validation**: Basic character option tests pass
- **Estimated effort**: 25 minutes

### Task 5.2: Implement character option filtering tests
- [ ] `test_character_option_name_filter` - Verify name filtering works
- [ ] `test_character_option_limit_respected` - Verify limit parameter
- **Dependencies**: Task 5.1
- **Validation**: Filtering tests pass
- **Estimated effort**: 15 minutes

### Task 5.3: Implement character option cache and error tests
- [ ] `test_character_option_cache_behavior` - Verify cache hit/miss
- [ ] `test_character_option_invalid_type` - Verify handling of invalid type
- [ ] `test_character_option_empty_results` - Verify handling of no matches
- **Dependencies**: Task 5.2
- **Validation**: Cache and error tests pass
- **Estimated effort**: 15 minutes

## 6. Rule Lookup Live Tests

### Task 6.1: Implement basic rule lookup tests
- [ ] `test_rule_condition_lookup` - Verify condition lookup returns 10+ conditions
- [ ] `test_rule_damage_type_lookup` - Verify damage type lookup returns 10+ types
- [ ] `test_rule_skill_lookup` - Verify skill lookup returns exactly 18 skills
- [ ] `test_rule_ability_score_lookup` - Verify ability score lookup returns exactly 6
- [ ] `test_rule_magic_school_lookup` - Verify magic school lookup returns exactly 8
- **Dependencies**: Task 1.3
- **Validation**: Basic rule tests pass with correct counts
- **Estimated effort**: 30 minutes

### Task 6.2: Implement rule filtering tests
- [ ] `test_rule_name_filter` - Verify name filtering works for conditions
- [ ] `test_rule_limit_respected` - Verify limit parameter
- **Dependencies**: Task 6.1
- **Validation**: Filtering tests pass
- **Estimated effort**: 15 minutes

### Task 6.3: Implement rule cache and error tests
- [ ] `test_rule_cache_behavior` - Verify cache hit/miss
- [ ] `test_rule_invalid_type` - Verify handling of invalid rule type
- [ ] `test_rule_empty_results` - Verify handling of no matches
- **Dependencies**: Task 6.2
- **Validation**: Cache and error tests pass
- **Estimated effort**: 15 minutes

## 7. Cross-Cutting Tests

### Task 7.1: Implement performance tests
- [ ] `test_uncached_call_performance` - Verify API calls complete <3s
- [ ] `test_cached_call_performance` - Verify cached calls complete <50ms
- [ ] `test_parallel_requests` - Verify concurrent requests work correctly
- **Dependencies**: Tasks 2.1-6.1
- **Validation**: Performance tests pass, timings within thresholds
- **Estimated effort**: 25 minutes

### Task 7.2: Implement cache validation tests
- [ ] `test_cache_isolation_across_tools` - Verify different tools use different caches
- [ ] `test_cache_key_uniqueness` - Verify different parameters create different cache keys
- **Dependencies**: Tasks 2.1-6.1
- **Validation**: Cache isolation tests pass
- **Estimated effort**: 20 minutes

## 8. Documentation and Cleanup

### Task 8.1: Update testing documentation
- [ ] Add "Live API Testing" section to `docs/testing.md`
- [ ] Document how to run live tests: `pytest -m live`
- [ ] Document how to skip live tests: `pytest -m "not live"`
- [ ] Add troubleshooting guide for common failures
- [ ] Document rate limiting considerations
- [ ] Add section on interpreting live test failures
- **Dependencies**: All test tasks
- **Validation**: Documentation is clear and accurate
- **Estimated effort**: 30 minutes

### Task 8.2: Add CI workflow for manual live tests (optional)
- [ ] Create `.github/workflows/live-tests.yml` (if using GitHub Actions)
- [ ] Configure as manual workflow dispatch
- [ ] Add environment variables for API configuration
- [ ] Document workflow usage in README or CONTRIBUTING
- **Dependencies**: Task 8.1
- **Validation**: Workflow runs successfully when triggered
- **Estimated effort**: 20 minutes (optional)

### Task 8.3: Deprecate old live test script
- [ ] Add deprecation notice to `test_mcp_tools_live.py`
- [ ] Update README/CONTRIBUTING to reference new pytest-based tests
- [ ] Create migration guide for users of old script
- **Dependencies**: Task 8.1
- **Validation**: Users are directed to new test infrastructure
- **Estimated effort**: 15 minutes

### Task 8.4: Run full test suite and validate
- [ ] Run all live tests: `uv run pytest -m live -v`
- [ ] Verify all tests pass against live APIs
- [ ] Check cache behavior is working correctly
- [ ] Verify rate limiting prevents API errors
- [ ] Document any API-specific quirks discovered
- **Dependencies**: All previous tasks
- **Validation**: All live tests pass, zero failures
- **Estimated effort**: 30 minutes

## Summary

**Total estimated effort**: ~7-8 hours

**Parallelizable work**:
- Tasks 2.x, 3.x, 4.x, 5.x, 6.x can be done in any order after infrastructure (Task 1) is complete
- Documentation (Task 8.1) can be written alongside test implementation

**Critical path**:
1. Infrastructure (Task 1) → enables all other work
2. Test implementation (Tasks 2-6) → validates functionality
3. Cross-cutting tests (Task 7) → validates integration
4. Documentation (Task 8) → enables adoption

**Test counts by tool**:
- Spell lookup: ~12 tests
- Creature lookup: ~10 tests
- Equipment lookup: ~8 tests
- Character options: ~9 tests
- Rule lookup: ~10 tests
- Cross-cutting: ~5 tests
- **Total**: ~54 live tests

**Success criteria**:
- [ ] All 50+ live tests pass against live APIs
- [ ] Tests can be skipped with `pytest -m "not live"`
- [ ] Tests can be run selectively with `pytest -m live`
- [ ] Cache behavior is validated with real API data
- [ ] Documentation is complete and clear
- [ ] No API rate limiting issues occur during test runs
