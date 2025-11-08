# spell-school-filtering Specification

## Purpose
TBD - created by archiving change fix-open5e-api-issues. Update Purpose after archive.
## Requirements
### Requirement: Client-Side School Filtering
The `get_spells` method in `Open5eV2Client` SHALL implement client-side filtering for the `school` parameter when the Open5e v2 API doesn't support server-side filtering.

**Rationale**: The Open5e v2 API does not support filtering spells by school parameter on the server side. However, the LoreKeeper tool interface advertises this capability, so client-side filtering must be implemented to maintain expected functionality.

**Scope**: `src/lorekeeper_mcp/api_clients/open5e_v2.py` - `get_spells` method

**Related Capabilities**:
- Impacts: `spell-lookup` tool's school filtering functionality
- Depends on: None (standalone implementation)
- Related: Caching system for performance optimization

#### Scenario: Verify client-side school filtering works correctly
- **Given**: School filtering is implemented in the client
- **When**: A spell lookup is called with school="evocation"
- **Then**: Only evocation spells are returned in the results

### Requirement: School Parameter Detection and Handling
The `get_spells` method SHALL detect when a `school` parameter is provided and implement appropriate filtering logic.

**Implementation Pattern**:
```python
async def get_spells(
    self,
    level: int | None = None,
    school: str | None = None,
    **kwargs: Any,
) -> list[Spell]:
    # Build API parameters (exclude unsupported school parameter)
    api_params = {k: v for k, v in kwargs.items() if k != "school"}
    if level is not None:
        api_params["level"] = level

    # Fetch all spells with supported parameters
    result = await self.make_request(
        "/spells/",
        use_entity_cache=True,
        entity_type="spells",
        params=api_params,
    )

    # Extract spell dictionaries
    spell_dicts: list[dict[str, Any]] = (
        result if isinstance(result, list) else result.get("results", [])
    )

    # Convert to Spell objects
    spells = [Spell.model_validate(spell) for spell in spell_dicts]

    # Apply client-side school filtering if requested
    if school:
        spells = [spell for spell in spells if spell.school.lower() == school.lower()]

    return spells
```

**File**: `src/lorekeeper_mcp/api_clients/open5e_v2.py`

#### Scenario: Filter spells by "evocation" school
- **Given**: User calls `lookup_spell(school="evocation")`
- **When**: `get_spells(school="evocation")` is called
- **Then**: Method makes API request without `school` parameter
- **And**: Client filters results to only include spells with `school="evocation"`
- **And**: Returned list contains only evocation spells

#### Scenario: Combine school filtering with level filtering
- **Given**: User calls `lookup_spell(level=3, school="evocation")`
- **When**: `get_spells(level=3, school="evocation")` is called
- **Then**: Method makes API request with `level=3` parameter only
- **And**: Client filters results to include only 3rd-level evocation spells
- **And**: Returned list contains only 3rd-level evocation spells

#### Scenario: No school filtering requested
- **Given**: User calls `lookup_spell(level=2)` without school
- **When**: `get_spells(level=2)` is called
- **Then**: Method makes API request with `level=2` parameter
- **And**: No client-side filtering is applied
- **And**: All 2nd-level spells are returned

### Requirement: School Parameter Normalization
School filtering SHALL be case-insensitive and handle common variations in school naming.

**Rationale**: Ensures consistent filtering behavior regardless of input case and handles potential variations in how schools might be stored in the data.

#### Scenario: Case-insensitive school filtering
- **Given**: User calls `lookup_spell(school="EVOCATION")` (uppercase)
- **When**: `get_spells(school="EVOCATION")` is called
- **Then**: Method matches spells regardless of case in school field
- **And**: Same results as `lookup_spell(school="evocation")`

#### Scenario: Mixed case school filtering
- **Given**: User calls `lookup_spell(school="EvOcAtIoN")` (mixed case)
- **When**: `get_spells(school="EvOcAtIoN")` is called
- **Then**: Method correctly matches all evocation spells
- **And**: Filtering works regardless of input case

### Requirement: Performance Optimization with Caching
Client-side school filtering SHALL leverage existing caching mechanisms to minimize performance impact.

**Implementation Considerations**:
- Use existing entity cache for spell data
- Consider caching filtered results for common school filters
- Maintain existing cache TTL and invalidation behavior

**File**: `src/lorekeeper_mcp/api_clients/open5e_v2.py`

#### Scenario: Multiple calls with same school filter
- **Given**: User makes two consecutive calls `lookup_spell(school="evocation")`
- **When**: Both calls are made within cache TTL period
- **Then**: First call fetches and filters spells
- **And**: Second call uses cached data and applies same filtering
- **And**: Both calls return identical filtered results

#### Scenario: School filter with empty results
- **Given**: User calls `lookup_spell(school="nonexistent")` with invalid school name
- **When**: `get_spells(school="nonexistent")` is called
- **Then**: Method fetches all spells and applies filtering
- **And**: Returns empty list since no spells match the invalid school
- **And**: No errors are thrown for invalid school names

### Requirement: Integration with Spell Lookup Tool
The `lookup_spell` tool SHALL continue to work seamlessly with the client-side filtering implementation.

**Before**: School filtering parameter has no effect - returns all spells

**After**: School filtering returns only spells from the specified school

**File**: `src/lorekeeper_mcp/tools/spell_lookup.py`

#### Scenario: Complete spell lookup with school filtering
- **Given**: User calls `lookup_spell(name="fire", school="evocation", level=3)`
- **When**: Tool processes the request through client-side filtering
- **Then**: API request is made with name and level parameters only
- **And**: Client-side filtering reduces results to evocation spells only
- **And**: Final results contain only 3rd-level evocation spells with "fire" in name

#### Scenario: School filtering preserves other functionality
- **Given**: User calls `lookup_spell(concentration=True, school="divination")`
- **When**: Tool processes the request
- **Then**: All existing filtering (concentration) continues to work
- **And**: School filtering is applied in addition to concentration filtering
- **And**: Results contain only concentration divination spells

### Requirement: API Response Issues
The system SHALL handle API response issues gracefully without affecting the school filtering functionality.
- **Expected Behavior**: Fall back to empty result set if API request fails
- **Error Handling**: Existing error handling mechanisms preserved
- **User Experience**: Appropriate error messages for network/API failures

#### Scenario: Handle complete API failure
- **Given**: User calls `lookup_spell(school="evocation")` and API is completely unreachable
- **When**: `get_spells(school="evocation")` makes the API request
- **Then**: API request fails with NetworkError
- **And**: Method catches the error and returns empty list
- **And**: No exception is propagated to the caller

#### Scenario: Handle partial API response with timeout
- **Given**: User calls `lookup_spell(level=3, school="evocation")` and API times out after partial data
- **When**: `get_spells(level=3, school="evocation")` makes the request
- **Then**: API returns partial spell data before timeout
- **And**: Method applies school filtering to available partial data
- **And**: Returns filtered partial results rather than error

#### Scenario: Preserve error handling for non-school requests
- **Given**: User calls `lookup_spell(level=2)` without school parameter
- **When**: API request fails with NetworkError
- **Then**: Existing error handling mechanisms work unchanged
- **And**: Appropriate error message is returned to user
- **And**: School filtering logic doesn't interfere with normal error flow

## Validation Criteria

1. **Functional Accuracy**: School filtering returns only spells from the specified school
2. **Case Insensitivity**: School filtering works regardless of input case
3. **Combined Filtering**: School filtering works correctly with other filter parameters
4. **Performance**: No significant performance regression for non-school-filtered requests
5. **Backward Compatibility**: All existing spell lookup functionality continues to work

## Success Metrics

- 100% accuracy in school filtering (no false positives/negatives)
- School filtering works with all supported spell schools
- No performance degradation for non-school filtered requests
- Integration with existing caching system works correctly
- All existing spell lookup scenarios continue to function

## Error Handling

### Invalid School Names
- **Expected Behavior**: Return empty list for non-existent schools
- **Error Handling**: No exceptions thrown, graceful degradation
- **User Experience**: Users receive empty results rather than errors

## Performance Considerations

1. **Data Volume**: School filtering processes full spell lists client-side
2. **Caching Strategy**: Leverage existing caching to minimize repeated full fetches
3. **Memory Usage**: Ensure filtering doesn't cause excessive memory consumption
4. **Response Time**: Maintain acceptable response times for school-filtered requests
