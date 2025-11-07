# Fix Open5e API Issues - Design Document

**Change ID**: `fix-open5e-api-issues`
**Date**: 2025-11-06

## Design Rationale

The proposed changes address three distinct but related API integration issues that stem from mismatches between the LoreKeeper implementation and the Open5e API specifications. Each issue requires a different architectural approach.

## Issue #1: Search Parameter Correction

### Problem Analysis
The Open5e API uses `search` as the query parameter for name-based text searches, but LoreKeeper tools are sending `name`. This fundamental mismatch causes all text searches to return zero results.

### Design Decision
**Approach**: Simple parameter name substitution across all affected tools
**Rationale**:
- Lowest risk approach - direct API specification compliance
- Consistent with other successful API integrations in the codebase
- No architectural changes required

### Implementation Strategy
- **Files**: 4 tool files in `src/lorekeeper_mcp/tools/`
- **Change**: Single line change per file (`params["name"]` → `params["search"]`)
- **Pattern**: Maintain existing parameter handling logic, just change the key name

### Trade-offs
- **Pros**: Minimal code change, low risk, immediate fix
- **Cons**: None identified
- **Alternative Considered**: Custom search implementation (rejected as unnecessary)

## Issue #2: Weapon Model Redesign

### Problem Analysis
The current `Weapon` Pydantic model includes fields that don't exist in the Open5e API v2 response and uses incorrect data types. This causes validation errors when trying to parse API responses.

### Design Decision
**Approach**: Complete model redesign based on actual API response structure
**Rationale**:
- Ensures data integrity and type safety
- Prevents runtime validation errors
- Maintains Pydantic model benefits

### Implementation Strategy
**Data Structure Research**: First, examine actual Open5e API v2 weapon responses to understand the true structure
**Model Redesign**:
- Remove non-existent fields (`slug`, `category`)
- Change `damage_type` from `str` to appropriate nested structure
- Add missing fields that the API actually provides
- Ensure all required API fields are represented

### Trade-offs
- **Pros**: Accurate data modeling, prevents errors, maintains type safety
- **Cons**: Requires research into API structure, potential breaking changes if not careful
- **Alternative Considered**: Dynamic parsing without models (rejected to maintain type safety)

### Model Validation Approach
- Compare current model against actual API responses
- Test with various weapon types to ensure comprehensive coverage
- Validate that all fields used by dependent tools are preserved

## Issue #3: Client-Side Spell Filtering

### Problem Analysis
The Open5e v2 API doesn't support server-side filtering by `school` parameter, but the LoreKeeper tool advertises this capability. Current implementation passes the parameter to the API and gets unfiltered results.

### Design Decision
**Approach**: Implement client-side filtering for unsupported parameters
**Rationale**:
- Preserves advertised tool functionality
- Maintains API compatibility
- Follows progressive enhancement pattern

### Implementation Strategy
**API Request**: Continue making API requests with supported parameters
**Client Processing**:
- When `school` filter is requested, fetch all relevant spells
- Apply filtering in Python code before returning results
- Maintain existing caching behavior

### Filtering Logic Design
```python
# Pseudocode for client-side filtering
if school_filter:
    all_spells = await self.get_spells(level=level, **other_supported_params)
    filtered_spells = [spell for spell in all_spells if spell.school == school_filter]
    return filtered_spells
else:
    return await self.get_spells(**params)
```

### Trade-offs
- **Pros**: Preserves functionality, works with existing API, no breaking changes
- **Cons**: Additional client-side processing, potentially more data transfer
- **Alternative Considered**: API wrapper service (rejected as overly complex)

### Performance Considerations
- Use existing caching layer to minimize repeated full queries
- Consider implementing smart caching for school-filtered results
- Monitor performance impact of additional client-side processing

## Cross-Cutting Concerns

### Error Handling
- Ensure all changes maintain robust error handling
- Validate that existing error cases are preserved
- Add specific error messages for new failure modes

### Testing Strategy
- **Unit Tests**: Test each changed component in isolation
- **Integration Tests**: Verify end-to-end tool functionality
- **API Compatibility**: Ensure changes work with actual Open5e API responses
- **Regression Tests**: Verify no existing functionality is broken

### Documentation Updates
- Update any documentation that references the corrected behavior
- Ensure tool descriptions remain accurate after fixes
- Document any performance implications of client-side filtering

## Validation Approach

### Testing Priority
1. **Issue #1**: Verify name searches work across all affected tools
2. **Issue #2**: Confirm equipment lookup completes without validation errors
3. **Issue #3**: Validate school filtering returns correct subset of spells

### Success Metrics
- All tools return expected results for name-based searches
- Equipment tools handle various weapon types without errors
- Spell school filtering reduces result set appropriately
- No regression in existing working functionality

## Risk Mitigation

### Rolling Deployment Strategy
- Implement changes incrementally, one issue at a time
- Test each fix before proceeding to the next
- Maintain ability to rollback individual fixes if needed

### Monitoring
- Add logging to track API response patterns
- Monitor for validation errors in production
- Track performance metrics for client-side filtering

This design ensures each issue is addressed with the most appropriate technical solution while maintaining system stability and user experience.
