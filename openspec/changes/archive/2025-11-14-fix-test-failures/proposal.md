# Fix Test Failures

## Summary

Fix 9 test failures (7 live, 2 integration) affecting creature lookups, spell filtering, feat lookups, and test mocking. These failures stem from incorrect API parameter mapping, missing error handling, and incomplete test mocks.

## Problem Statement

The test suite currently has 9 failing tests:

### Integration Test Failures (2)
1. **test_creature_lookup_basic** - Missing RESPX mock for `/v2/creatures/?limit=220`
2. **test_creature_lookup_by_cr** - Missing RESPX mock for `/v2/creatures/?limit=20&challenge_rating=21.0`

### Live Test Failures (7)
3. **test_spell_filter_combined** - Returns 0 wizard concentration spells (expected >= 5)
4. **test_creature_basic_fields_present** - Returns 0 results when searching for "Goblin"
5. **test_creature_filter_by_cr** - Returns CR 11 instead of CR 1
6. **test_creature_filter_by_type** - API returns 400 error for `type="Beast"`
7. **test_creature_filter_by_size** - API returns 400 error for `size="Large"`
8. **test_creature_invalid_type** - API returns 400 error (should handle gracefully)
9. **test_character_option_feat_lookup** - Returns only 1 feat instead of >= 20

These failures prevent deployment and indicate critical issues with API integration, particularly with the Open5e v2 API which uses different parameter conventions than expected.

## Root Causes

### 1. Incorrect Open5e V2 API Parameter Mapping (Issues #3, #6, #7)

**Root Cause**: The Open5e v2 API uses Django REST framework filter operators with double underscores (e.g., `type__key`, `size__key`, `classes__key`) and expects lowercase values, but our repository code passes direct values (e.g., `type=Beast`).

**Evidence**:
- API returns: `{"type":["Select a valid choice. That choice is not one of the available choices."]}`
- Working API call: `curl "https://api.open5e.com/v2/creatures/?type__key=beast"` ✓
- Failing API call: `curl "https://api.open5e.com/v2/creatures/?type=Beast"` ✗
- Similarly for `size__key`, `classes__key`

**Impact**: All creature type/size filters and spell class filters fail in production.

### 2. Missing Challenge Rating Parameter Name (Issue #5)

**Root Cause**: The Open5e v2 API expects `challenge_rating_decimal` for exact matches, not `challenge_rating`. The repository's `_map_to_api_params` doesn't handle exact CR matches, only range operators (`__gte`, `__lte`).

**Evidence**:
- Repository maps `cr_min` → `challenge_rating_decimal__gte` ✓
- Repository maps `cr_max` → `challenge_rating_decimal__lte` ✓
- Repository doesn't map `cr` → `challenge_rating_decimal` ✗
- Tool passes `cr=1` but API needs `challenge_rating_decimal=1.0`

**Impact**: Exact CR filtering returns wrong creatures (CR 11 instead of CR 1).

### 3. No Error Handling for Invalid API Parameters (Issue #8)

**Root Cause**: When invalid parameters cause a 400 error, the `base.py` `make_request` method raises an `ApiError` instead of returning an empty result set.

**Evidence**:
```python
# src/lorekeeper_mcp/api_clients/base.py:89
if response.status_code >= 400:
    raise ApiError(f"API error: {response.status_code}")
```

**Impact**: Invalid filter values crash the application instead of returning empty results.

### 4. Spell Class Filter Uses Wrong Parameter (Issue #3)

**Root Cause**: The spell lookup tool passes `class_key="wizard"` but the Open5e v2 API expects `classes__key=wizard` (plural, with double underscore).

**Evidence**:
- Tool passes: `class_key="wizard"`
- API expects: `classes__key=wizard`
- Working API call: `curl "https://api.open5e.com/v2/spells/?classes__key=wizard&concentration=true"`

**Impact**: Class-based spell filtering returns 0 results.

### 5. Feat Lookup Not Using Open5e V2 API Properly (Issue #9)

**Root Cause**: The character option repository's `_search_feats` method calls `self.client.get_feats()` which exists in the Open5e v2 client but doesn't pass a `limit` parameter properly, and the test expects >= 20 feats but only gets 1.

**Evidence**:
- Open5e v2 API has 91 feats total
- Test gets only 1 feat
- API call with no limit returns only 5 by default
- Need to pass explicit `limit` parameter or use pagination

**Impact**: Feat lookups are incomplete and unusable.

### 6. Goblin Search Returns Empty (Issue #4)

**Root Cause**: The creature lookup tool uses a multiplier of 11 for name searches (`fetch_limit = limit * 11`) and filters client-side, but the test expects immediate results. The API call may be working but the search parameter or client-side filtering might be failing.

**Evidence**:
- API returns goblins: `curl "https://api.open5e.com/v2/creatures/?name__icontains=goblin"` returns 29 results
- Code uses client-side filtering: `creatures = [creature for creature in creatures if name_lower in creature.name.lower()]`
- Possible issue: API call isn't using `name__icontains` parameter

**Impact**: Name-based creature searches appear broken.

### 7. Missing Test Mocks for V2 Creatures Endpoint (Issues #1, #2)

**Root Cause**: Integration tests mock the v1 API endpoint (`/v1/monsters/`) but the repository now uses Open5e v2 (`/v2/creatures/`) by default.

**Evidence**:
```python
# test_integration.py:231
respx.get("https://api.open5e.com/v1/monsters/?").mock(...)
```

But the code calls:
```python
# repository/monster.py:109
await self.client.get_creatures(limit=limit, **api_params)  # Uses v2 API
```

**Impact**: Integration tests fail with unmocked requests.

## Proposed Solution

### Phase 1: Fix API Parameter Mapping (Critical)
1. Update `MonsterRepository._map_to_api_params()` to map `type` → `type__key` and `size` → `size__key` with lowercase conversion
2. Add mapping for exact `cr` parameter → `challenge_rating_decimal`
3. Update `SpellRepository._map_to_api_params()` to handle `class_key` → `classes__key`
4. Update `Open5eV2Client.get_creatures()` to use `type__key` and `size__key`

### Phase 2: Add Graceful Error Handling
1. Update `base.py` to catch 400 errors for invalid filter values
2. Return empty lists instead of raising exceptions for validation errors
3. Add logging for debugging

### Phase 3: Fix Feat Lookup
1. Ensure `CharacterOptionRepository._search_feats()` passes `limit` correctly
2. Update Open5e v2 client's `get_feats()` to accept and use `limit` parameter
3. Consider defaulting to a higher limit (e.g., 100) for feats

### Phase 4: Fix Integration Test Mocks
1. Update integration tests to mock `/v2/creatures/` endpoints
2. Add mocks for all parameter combinations used in tests

### Phase 5: Fix Goblin Search
1. Verify `MonsterRepository` passes `name__icontains` to API
2. Debug client-side filtering logic

## Success Criteria

1. All 9 tests pass consistently
2. Live API calls work with correct parameter mapping
3. Invalid parameters return empty results instead of errors
4. Feat lookups return full result sets
5. Creature type/size/CR filtering works correctly
6. Spell class filtering works correctly

## Risks & Mitigation

**Risk**: Breaking existing functionality
**Mitigation**: Comprehensive test coverage ensures changes don't regress working features

**Risk**: API parameter changes affect other tools
**Mitigation**: All changes are localized to repository layer; tools remain unchanged

## Alternative Approaches Considered

1. **Switch back to Open5e v1 API**: Rejected - v2 has more features and better data
2. **Client-side filtering only**: Rejected - inefficient and defeats purpose of API filters
3. **Wrapper layer for parameter translation**: Rejected - adds unnecessary complexity

## Dependencies

None - all changes are internal to the existing codebase.

## Timeline Estimate

- Phase 1: 2-3 hours
- Phase 2: 1 hour
- Phase 3: 1 hour
- Phase 4: 1 hour
- Phase 5: 1 hour

**Total**: 6-8 hours
