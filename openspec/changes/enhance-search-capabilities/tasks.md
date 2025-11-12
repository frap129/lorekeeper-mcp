# Search Enhancement Implementation Tasks

## Phase 1: Fix Bugs and Server-Side Filtering

### 1.1 Fix Open5e School Filtering Bug
- [ ] **Task**: Remove client-side school filtering and use `school__key` parameter in Open5e v2 API requests
- [ ] **Validation**: School filtering works without client-side code, verify in API logs
- [ ] **Test**: `test_school_server_side_filtering`, `test_no_client_side_filtering`
- **Dependencies**: None
- **Estimated Time**: 1 hour

### 1.2 Implement Name Partial Matching
- [ ] **Task**: Replace client-side name filtering with `name__icontains` for Open5e v2
- [ ] **Validation**: Partial name searches work server-side, reduce data transfer
- [ ] **Test**: `test_name_icontains_usage`, `test_partial_name_match`
- **Dependencies**: None
- **Estimated Time**: 1 hour

### 1.3 Add Range Filter Operators
- [ ] **Task**: Implement `level__gte`, `level__lte`, `challenge_rating_decimal__gte/lte`, `cost__gte/lte` support
- [ ] **Validation**: Range queries use server-side filtering
- [ ] **Test**: `test_level_range_filtering`, `test_cr_range_filtering`, `test_cost_range_filtering`
- **Dependencies**: None
- **Estimated Time**: 2 hours

### 1.4 Implement Equipment Boolean Filters
- [ ] **Task**: Add support for `is_magic_item`, `is_finesse`, `is_light`, `is_versatile` server-side filtering
- [ ] **Validation**: Boolean filters work server-side for equipment queries
- [ ] **Test**: `test_boolean_equipment_filters`, `test_finesse_weapons`
- **Dependencies**: 1.3
- **Estimated Time**: 2 hours

### 1.5 Update Repository Parameter Mapping
- [ ] **Task**: Implement `_map_to_api_params()` method to convert repository filters to API-specific operators
- [ ] **Validation**: Repository correctly maps parameters for both Open5e and D&D APIs
- [ ] **Test**: `test_repository_parameter_mapping`, `test_open5e_operator_mapping`, `test_dnd5e_parameter_mapping`
- **Dependencies**: 1.1, 1.2, 1.3, 1.4
- **Estimated Time**: 3 hours

### 1.6 Remove Client-Side Filtering
- [ ] **Task**: Remove all client-side name and school filtering from tools (spell, creature, equipment lookups)
- [ ] **Validation**: No client-side filtering code remains, all filtering server-side
- [ ] **Test**: Code review, grep for client-side filter patterns
- **Dependencies**: 1.5
- **Estimated Time**: 2 hours

### 1.7 Performance Validation
- [ ] **Task**: Measure data transfer and response time improvements for filtered queries
- [ ] **Validation**: 50%+ reduction in response time, 80%+ reduction in data transfer for filtered queries
- [ ] **Test**: `test_performance_metrics`, benchmark tests with/without filters
- **Dependencies**: 1.6
- **Estimated Time**: 2 hours

## Phase 2: Unified Search Implementation

### 2.1 Verify Unified Search Endpoint
- [ ] **Task**: Manually test `/v2/search/` endpoint with `query`, `fuzzy`, `vector` parameters to confirm documented behavior
- [ ] **Validation**: Fuzzy matching handles typos, vector search returns semantic matches
- [ ] **Test**: Manual curl/httpx testing, document actual API responses
- **Dependencies**: None
- **Estimated Time**: 2 hours

### 2.2 Implement Unified Search Client Method
- [ ] **Task**: Add `unified_search()` method to Open5eV2Client supporting query, fuzzy, vector, object_model parameters
- [ ] **Validation**: Method correctly calls `/v2/search/` with proper parameters
- [ ] **Test**: `test_unified_search_method`, `test_fuzzy_parameter`, `test_vector_parameter`, `test_object_model_filter`
- **Dependencies**: 2.1
- **Estimated Time**: 3 hours

### 2.3 Create search_dnd_content MCP Tool
- [ ] **Task**: Implement new `search_dnd_content()` tool that exposes unified search with fuzzy and semantic options
- [ ] **Validation**: Tool returns cross-entity results, handles content_types filtering
- [ ] **Test**: `test_search_dnd_content_tool`, `test_cross_entity_search`, `test_content_type_filtering`
- **Dependencies**: 2.2
- **Estimated Time**: 3 hours

### 2.4 Test Fuzzy Matching
- [ ] **Task**: Verify fuzzy search handles common typos ("firbal" → "Fireball", "cury wounds" → "Cure Wounds")
- [ ] **Validation**: At least 5 typo patterns return correct results
- [ ] **Test**: `test_fuzzy_typo_tolerance`, `test_common_misspellings`
- **Dependencies**: 2.3
- **Estimated Time**: 2 hours

### 2.5 Test Semantic Search
- [ ] **Task**: Verify semantic search returns conceptually related results ("healing magic" → cure wounds, healing word, etc.)
- [ ] **Validation**: Semantic queries return relevant results even without exact text matches
- [ ] **Test**: `test_semantic_concept_search`, `test_related_content_discovery`
- **Dependencies**: 2.3
- **Estimated Time**: 2 hours

### 2.6 Document Unified Search Tool
- [ ] **Task**: Add comprehensive documentation and examples for new search_dnd_content tool
- [ ] **Validation**: Documentation includes use cases, examples, parameter descriptions
- [ ] **Test**: Documentation review
- **Dependencies**: 2.5
- **Estimated Time**: 1 hour

## Phase 3: Optional Tool Enhancements

### 3.1 Add Spell Range Parameters
- [ ] **Task**: Add optional `level_min`, `level_max`, `damage_type` parameters to lookup_spell
- [ ] **Validation**: New parameters work, existing calls unaffected (backward compatible)
- [ ] **Test**: `test_spell_level_range`, `test_damage_type_filter`, `test_backward_compatibility`
- **Dependencies**: 1.5
- **Estimated Time**: 2 hours

### 3.2 Add Equipment Range Parameters
- [ ] **Task**: Add optional `cost_min`, `cost_max`, `weight_max`, `is_finesse`, `is_light`, `is_magic` to lookup_equipment
- [ ] **Validation**: New filters work correctly, backward compatible
- [ ] **Test**: `test_equipment_cost_range`, `test_weight_filter`, `test_weapon_properties`
- **Dependencies**: 1.4
- **Estimated Time**: 2 hours

### 3.3 Add Creature Range Parameters
- [ ] **Task**: Add optional `armor_class_min`, `hit_points_min` parameters to lookup_creature
- [ ] **Validation**: Range filters work, backward compatible
- [ ] **Test**: `test_creature_ac_filter`, `test_hp_filter`
- **Dependencies**: 1.3
- **Estimated Time**: 2 hours

### 3.4 Update Tool Documentation
- [ ] **Task**: Update docstrings for all enhanced tools with new parameter descriptions and examples
- [ ] **Validation**: All new parameters documented with examples
- [ ] **Test**: Documentation review
- **Dependencies**: 3.1, 3.2, 3.3
- **Estimated Time**: 2 hours

## Parallelizable Work

**Parallel Group A** (Bug Fixes - can run simultaneously):
- 1.1 Fix Open5e School Filtering Bug
- 1.2 Implement Name Partial Matching
- 1.3 Add Range Filter Operators
- 1.4 Implement Equipment Boolean Filters

**Parallel Group B** (After 2.1, can run simultaneously):
- 2.4 Test Fuzzy Matching
- 2.5 Test Semantic Search

**Parallel Group C** (Phase 3 enhancements - can run simultaneously):
- 3.1 Add Spell Range Parameters
- 3.2 Add Equipment Range Parameters
- 3.3 Add Creature Range Parameters

## Success Criteria

### Phase 1 (Must Have - Bug Fixes):
- [ ] School filtering works server-side using `school__key` parameter
- [ ] Name filtering uses `name__icontains` (Open5e) or built-in partial matching (D&D API)
- [ ] No client-side name or school filtering code remains
- [ ] Range operators work for level, CR, cost, weight fields
- [ ] Performance improves: 50%+ latency reduction, 80%+ data transfer reduction

### Phase 2 (Must Have - Unified Search):
- [ ] New `search_dnd_content` tool successfully created
- [ ] Fuzzy search handles typos: "firbal" returns "Fireball"
- [ ] Semantic search finds related content: "healing magic" returns healing spells
- [ ] Cross-entity search works across spells, creatures, items
- [ ] Tool documented with examples and use cases

### Phase 3 (Optional - Enhancements):
- [ ] Range parameters available for common use cases (level, cost, CR)
- [ ] All enhancements backward compatible (no breaking changes)
- [ ] New parameters documented and tested
- [ ] Existing tool functionality unchanged

## Risk Mitigation

### High Risk Areas:

1. **API Parameter Compatibility**
   - **Risk**: Open5e might not support all documented filter operators
   - **Mitigation**: Test each operator manually before implementing (Task 2.1)
   - **Fallback**: Document which operators work, implement only verified ones

2. **Unified Search Behavior**
   - **Risk**: `/v2/search/` might behave differently than documented
   - **Mitigation**: Manual testing in Task 2.1 before building tool
   - **Fallback**: Adjust implementation based on actual behavior

3. **Performance Regressions**
   - **Risk**: Changes might unexpectedly slow down some queries
   - **Mitigation**: Benchmark tests in Task 1.7
   - **Fallback**: Keep metrics, revert if performance degrades

4. **Breaking Changes**
   - **Risk**: Backend changes might break existing tool behavior
   - **Mitigation**: Maintain backward compatibility, run full test suite
   - **Fallback**: All phases can be rolled back independently

## Timeline Estimate

- **Phase 1**: 13 hours (critical bug fixes and performance improvements)
- **Phase 2**: 13 hours (unified search feature)
- **Phase 3**: 8 hours (optional enhancements)
- **Total**: 34 hours for complete implementation

**Minimum Viable**: Phase 1 only (13 hours) fixes critical bugs and improves performance significantly.
