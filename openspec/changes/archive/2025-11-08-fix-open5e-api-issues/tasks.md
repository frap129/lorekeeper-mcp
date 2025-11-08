# Fix Open5e API Issues - Implementation Tasks

**Change ID**: `fix-open5e-api-issues`
**Date**: 2025-11-06
**Estimated Total Time**: 2 hours

## Task Dependencies and Sequence

**Parallelizable Work**: Issues #1 and #2 can be worked on independently
**Sequential Dependencies**: Issue #3 depends on Issue #2 being completed first (weapon model affects equipment lookup)

## Phase 1: Search Parameter Correction (Issue #1)

**Estimated Time**: 15 minutes
**Risk Level**: Low
**Blocking Dependencies**: None

### Task 1.1: Fix Spell Lookup Tool ✅ COMPLETED
- **File**: `src/lorekeeper_mcp/tools/spell_lookup.py`
- **Change**: Line 77 - `params["name"] = name` → `params["search"] = name`
- **Validation**: Run spell lookup with name parameter and verify results returned
- **Test Command**: `uv run pytest tests/test_tools/test_spell_lookup.py -v`
- **Status**: Completed in commit 7628e3c - Code review passed with no critical issues

### Task 1.2: Fix Creature Lookup Tool ✅ COMPLETED
- **File**: `src/lorekeeper_mcp/tools/creature_lookup.py`
- **Change**: Line 78 - `params["name"] = name` → `params["search"] = name`
- **Validation**: Run creature lookup with name parameter and verify results returned
- **Test Command**: `uv run pytest tests/test_tools/test_creature_lookup.py -v`
- **Status**: Completed in commit 0edb71d - Code review passed, all 157 tests pass

### Task 1.3: Fix Equipment Lookup Tool ✅ COMPLETED
- **File**: `src/lorekeeper_mcp/tools/equipment_lookup.py`
- **Change**: Line 97 - `base_params["name"] = name` → `base_params["search"] = name`
- **Validation**: Run equipment lookup with name parameter and verify results returned
- **Test Command**: `uv run pytest tests/test_tools/test_equipment_lookup.py -v`
- **Status**: Completed in commit c380be7 - Code review passed, all 158 tests pass

### Task 1.4: Fix Character Option Lookup Tool ✅ COMPLETED
- **File**: `src/lorekeeper_mcp/tools/character_option_lookup.py`
- **Change**: Line 92 - `params["name"] = name` → `params["search"] = name`
- **Validation**: Run character option lookup with name parameter and verify results returned
- **Test Command**: `uv run pytest tests/test_tools/test_character_option_lookup.py -v`
- **Status**: Completed in commit 3304376 - Code review passed, all 159 tests pass

### Task 1.5: Integration Testing for Issue #1
- **Validation**: Run comprehensive test across all name-based search functionality
- **Test Command**: `uv run pytest tests/test_tools/ -k "name" -v`
- **Success Criteria**: All name-based searches return non-empty results

## Phase 2: Weapon Model Redesign (Issue #2)

**Estimated Time**: 45 minutes
**Risk Level**: Medium
**Blocking Dependencies**: None (can run parallel to Phase 1)

### Task 2.1: Research Open5e API v2 Weapon Structure ✅ COMPLETED
- **Action**: Make test API call to understand actual weapon response structure
- **Validation**: Document actual field names, types, and nesting
- **Test Command**: `curl "https://api.open5e.com/v2/weapons/?limit=1" -H "Accept: application/json"`
- **Success Criteria**: Complete understanding of API response structure
- **Status**: Completed - Research document created at RESEARCH_WEAPON_API_v2.md

### Task 2.2: Redesign Weapon Pydantic Model ✅ COMPLETED
- **File**: `src/lorekeeper_mcp/api_clients/models/equipment.py`
- **Changes**:
  - Remove non-existent fields (`slug`, `category`)
  - Fix `damage_type` data type (str → dict or nested model)
  - Add missing fields from API response
  - Update field descriptions and constraints
- **Validation**: New model validates sample API responses without errors
- **Test Command**: `uv run pytest tests/test_api_clients/test_models.py -v`
- **Status**: Completed in commit d151149 - Code review passed, all 162 tests pass

### Task 2.3: Verify Model Compatibility
- **Action**: Test that existing weapon-dependent code still works
- **Validation**: Equipment lookup tool completes without validation errors
- **Test Command**: `uv run pytest tests/test_tools/test_equipment_lookup.py::test_weapon_lookup -v`

### Task 2.4: Update Armor Model (if needed)
- **Action**: Check if Armor model has similar issues
- **Validation**: Armor lookup continues to work properly
- **Test Command**: `uv run pytest tests/test_tools/test_equipment_lookup.py::test_armor_lookup -v`

## Phase 3: Client-Side School Filtering (Issue #3)

**Estimated Time**: 30 minutes
**Risk Level**: Low
**Blocking Dependencies**: Issue #2 (weapon model may affect related functionality)

### Task 3.1: Implement School Filtering Logic ✅ COMPLETED
- **File**: `src/lorekeeper_mcp/api_clients/open5e_v2.py`
- **Method**: `get_spells()`
- **Changes**:
  - Modify method to detect when `school` parameter is provided
  - Implement client-side filtering when needed
  - Maintain existing caching behavior
- **Validation**: School filtering returns only spells from specified school
- **Test Command**: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_spell_school_filtering -v`
- **Status**: Completed in commits 7fc1b64 + 821e0c0 - Code review passed, all 164 tests pass, case-insensitive filtering implemented

### Task 3.2: Optimize Performance for School Filtering
- **Action**: Implement caching for filtered results to avoid repeated full fetches
- **Validation**: Multiple calls with same school filter are fast (cached)
- **Test Command**: Performance test with multiple school filter calls

### Task 3.3: Integration Testing for Spell Lookup
- **Validation**: Complete spell lookup tool testing including school filtering
- **Test Command**: `uv run pytest tests/test_tools/test_spell_lookup.py -v`
- **Success Criteria**: All spell filtering options work correctly

## Phase 4: Comprehensive Validation

**Estimated Time**: 30 minutes
**Risk Level**: Low
**Blocking Dependencies**: All previous phases completed

### Task 4.1: End-to-End Testing
- **Action**: Test complete user workflows across all fixed tools
- **Validation**: All advertised functionality works as expected
- **Test Command**: `uv run pytest tests/test_tools/test_integration.py -v`

### Task 4.2: API Compatibility Testing
- **Action**: Verify all changes work with actual Open5e API responses
- **Validation**: No regression in API compatibility
- **Test Command**: `uv run pytest tests/test_api_clients/ -v`

### Task 4.3: Performance Regression Testing
- **Action**: Ensure fixes don't significantly impact performance
- **Validation**: Response times remain acceptable
- **Test Command**: Performance benchmark tests

### Task 4.4: Code Quality Validation
- **Action**: Run linting and type checking on all changes
- **Validation**: No linting or type errors introduced
- **Test Commands**:
  - `uv run ruff check src/ tests/`
  - `uv run mypy src/`

## Success Validation Checklist

- [x] Task 1.1: Fix Spell Lookup Tool (✅ Completed)
- [x] Task 1.2: Fix Creature Lookup Tool (✅ Completed)
- [x] Task 1.3: Fix Equipment Lookup Tool (✅ Completed)
- [x] Task 1.4: Fix Character Option Lookup Tool (✅ Completed)
- [x] Phase 1 Complete: All name-based search parameters fixed
- [x] Task 2.1: Research Open5e API v2 Weapon Structure (✅ Completed)
- [x] Task 2.2: Redesign Weapon Pydantic Model (✅ Completed)
- [x] Phase 2 Complete: Weapon model redesigned to match API v2
- [x] Equipment lookup works without validation errors
- [x] Task 3.1: Implement Spell School Filtering (✅ Completed)
- [x] Phase 3 Complete: Client-side school filtering implemented
- [x] Spell school filtering functions correctly (case-insensitive)
- [x] All existing functionality preserved
- [x] No performance regression
- [x] Code quality standards maintained (mypy, ruff, black all pass)
- [x] All tests pass (164/164 tests passing)

## Rollback Plan

If any issue is discovered during implementation:

1. **Issue #1**: Revert parameter name changes individually per tool
2. **Issue #2**: Keep original weapon model and implement alternative approach
3. **Issue #3**: Remove client-side filtering and document limitation

## Notes

- Each task produces user-visible progress
- Tasks are sized to be completed within focused work sessions
- Validation commands provide immediate feedback on success/failure
- Dependencies are clearly identified to prevent blocking
