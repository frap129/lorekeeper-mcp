# Fix Open5e API Issues - Change Proposal

**Change ID**: `fix-open5e-api-issues`
**Date**: 2025-11-06
**Status**: Draft

## Summary

This change resolves three critical issues with the Open5e API integration that prevent proper functionality of multiple MCP tools. The issues affect name-based searches, weapon model validation, and spell filtering capabilities.

## Problem Statement

All LoreKeeper MCP tools that interface with the Open5e API (both v1 and v2) are experiencing functional failures:

1. **Broken Name Searches**: All name-based searches return zero results due to incorrect parameter usage
2. **Weapon Model Validation Errors**: Equipment lookup fails due to mismatched Pydantic models
3. **Non-Functional Spell Filtering**: School-based spell filtering is completely ineffective

These issues impact the core functionality of the LoreKeeper MCP server, preventing users from effectively searching for D&D 5e content.

## Proposed Solution

## Why
The Open5e API integration issues prevent core LoreKeeper functionality from working properly. Users cannot search for spells, creatures, equipment, or character options by name, and the equipment lookup tool fails with validation errors. These are critical bugs that impact the primary value proposition of the MCP server. The proposed changes address the root causes identified in DIAGNOSIS.md through minimal, targeted fixes that restore expected functionality while maintaining compatibility with the existing codebase.

### Issue #1: Correct Search Parameter Usage
**Scope**: All Open5e API tools that perform name-based searches
**Files**:
- `src/lorekeeper_mcp/tools/spell_lookup.py`
- `src/lorekeeper_mcp/tools/creature_lookup.py`
- `src/lorekeeper_mcp/tools/equipment_lookup.py`
- `src/lorekeeper_mcp/tools/character_option_lookup.py`

**Change**: Replace `params["name"] = name` with `params["search"] = name` in all affected tools.

### Issue #2: Fix Weapon Pydantic Model
**Scope**: Equipment model validation
**File**: `src/lorekeeper_mcp/api_clients/models/equipment.py`

**Change**: Rewrite the `Weapon` class to accurately reflect the Open5e API v2 response structure, including:
- Remove non-existent fields (`slug`, `category`)
- Correct data types (e.g., `damage_type` as nested object)
- Align required fields with API response

### Issue #3: Implement Client-Side School Filtering
**Scope**: Spell lookup functionality
**File**: `src/lorekeeper_mcp/api_clients/open5e_v2.py`

**Change**: Modify the `get_spells` method to perform client-side filtering when `school` parameter is provided, since the Open5e v2 API doesn't support this filter.

## Impact Analysis

### User-Facing Benefits
- **Restored Search Functionality**: Users can successfully search for spells, creatures, equipment, and character options by name
- **Working Equipment Lookup**: Weapon and armor searches will no longer fail with validation errors
- **Effective Spell Filtering**: Spell school filtering will return properly filtered results

### Technical Impact
- **API Compatibility**: Ensures all Open5e API interactions work as expected
- **Data Validation**: Models accurately reflect API responses, preventing runtime errors
- **Feature Completeness**: All advertised filtering capabilities will function correctly

### Risk Assessment
- **Low Risk**: Changes are minimal and targeted to specific API integration issues
- **Backwards Compatible**: No breaking changes to public tool interfaces
- **Testable**: Each fix can be independently validated

## Success Criteria

1. **Name-based searches return results**: All tools that accept `name` parameter return non-empty results when valid names are provided
2. **Equipment lookup works without errors**: Weapon and armor searches complete without Pydantic validation errors
3. **Spell school filtering works**: Filtering spells by `school` returns only spells from the specified school
4. **All existing functionality preserved**: No regression in features that currently work

## Dependencies

- No external dependencies required
- Changes are isolated to API client and tool implementation layers
- No database schema changes needed

## Validation Plan

- Unit tests for each fixed tool
- Integration tests to verify API compatibility
- End-to-end tests for complete user workflows
- Validation against Open5e API documentation

## Timeline Estimate

- **Issue #1 (Search Parameter)**: 15 minutes - simple find/replace across 4 files
- **Issue #2 (Weapon Model)**: 45 minutes - requires API research and model redesign
- **Issue #3 (Spell Filtering)**: 30 minutes - implement client-side filtering logic
- **Testing & Validation**: 30 minutes - comprehensive testing of all changes

**Total Estimated Time**: 2 hours
