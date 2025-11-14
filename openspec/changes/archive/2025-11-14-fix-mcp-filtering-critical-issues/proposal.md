# Fix MCP Tool Filtering Critical Issues

## Summary

This change addresses four critical issues discovered in the MCP tool filtering architecture that severely impact user experience, performance, and data consistency across all 5 MCP tools (`lookup_spell`, `lookup_rule`, `lookup_creature`, `lookup_equipment`, `lookup_character_option`).

**Priority:** URGENT - Affects core functionality and system performance
**Impact:** All MCP tools and their users
**Type:** Performance + Usability + Architecture fixes

## Issues Addressed

### 🚨 Issue #1: Case-Sensitive Database Filtering
- **Problem:** Database uses exact case-sensitive matching, causing searches to fail based on capitalization
- **Impact:** `lookup_spell(name="fireball")` fails while `lookup_spell(name="Fireball")` works
- **Affected Tools:** `lookup_spell`, `lookup_rule`

### 🚨 Issue #2: No Slug Field Searching
- **Problem:** None of the tools search the `slug` field for exact matches regardless of case
- **Impact:** Users miss exact matches that exist in cache
- **Affected Tools:** All 5 MCP tools

### 🚨 Issue #3: Client-Side Filtering Performance Bug
- **Problem:** 3 tools fetch 11x data from database and filter client-side instead of using efficient database filtering
- **Impact:** 11x higher network/CPU/memory usage for affected tools
- **Affected Tools:** `lookup_creature`, `lookup_equipment`, `lookup_character_option`

### 🚨 Issue #4: Inconsistent Filtering Architecture
- **Problem:** Each tool implements filtering differently, creating unpredictable user experience
- **Impact:** Users cannot rely on consistent behavior across tools
- **Affected Tools:** All 5 MCP tools

## Root Cause Analysis

The core issue is in the `query_cached_entities()` function in `src/lorekeeper_mcp/cache/db.py` which only supports exact, case-sensitive matching:

```python
for field, value in filters.items():
    where_clauses.append(f"{field} = ?")  # Only exact, case-sensitive match
```

## Proposed Solution

### 1. Enhanced Database Layer with Fallback (Priority: CRITICAL)
**Target:** `src/lorekeeper_mcp/cache/db.py`
- Change `name` parameter from case-sensitive to case-insensitive filtering (`LOWER(name) = LOWER(?)`)
- Add automatic slug field fallback when name search fails
- Add partial matching when wildcards detected in `name` parameter
- NO SCHEMA CHANGES - use existing name/slug fields
- NO NEW PARAMETERS - enhance existing `name` behavior only

### 2. Eliminate Client-Side Filtering (Priority: CRITICAL)
**Targets:** 3 tool files with client-side filtering
- Remove the 11x over-fetching bug immediately
- Convert to efficient database filtering only
- Maintain exact existing parameter interface

### 3. Smart Fallback Chain (Priority: HIGH)
Enhance existing `name` parameter with intelligent behavior:
- Default: case-insensitive exact matching
- Fallback: automatic slug search if name match fails
- Partial matching: detected via wildcard characters in `name` parameter
- NO NEW PARAMETERS - single enhanced interface

## Expected Outcomes

### User Experience Improvements
✅ **Consistent Behavior:** All tools work the same way regardless of capitalization
✅ **Better Matches:** Slug field searching finds exact matches faster
✅ **Partial Matching:** Users can search for fragments ("fire" finds "Fireball")

### Performance Improvements
✅ **Efficient Queries:** All filtering happens at database level
✅ **Reduced Memory:** No more fetching 11x unnecessary data
✅ **Faster Response Times:** Database indexes fully utilized

### Code Quality Improvements
✅ **Architecture Consistency:** All tools use same filtering pattern
✅ **Maintainability:** Single database layer handles all filtering logic
✅ **Security:** Proper SQL parameter binding throughout

## Technical Approach

### Database Layer Enhancement
The enhanced `query_cached_entities()` will support:
1. **Case-insensitive exact matching:** `LOWER(name) = LOWER(?)`
2. **Case-insensitive partial matching:** `LOWER(name) LIKE LOWER(?)`
3. **Slug exact matching:** `slug = ?`
4. **Combined fallback logic:** Try name match first, then slug match
5. **Proper SQL parameter binding** for security

### Tool Layer Migration
1. **Remove client-side filtering** from 3 affected tools
2. **Add enhanced search parameters** to all tools
3. **Standardize filtering logic** across all tools
4. **Maintain backward compatibility** with existing parameters

### Testing Strategy
1. **Unit tests** for enhanced database filtering
2. **Integration tests** for each tool's new functionality
3. **Performance tests** to verify efficiency gains
4. **Backward compatibility tests** to ensure existing behavior preserved

## Dependencies

- ✅ **No conflicts** with previous repository cleanup work
- ✅ **Builds on** clean tool interfaces established
- ✅ **Maintains** context injection pattern for testing

## Success Criteria

1. **All tools** support case-insensitive name searching
2. **All tools** support slug field searching
3. **All tools** perform filtering at database level (no client-side filtering)
4. **Backward compatibility** maintained for existing parameters
5. **Performance improvement** verified (no more 11x data over-fetching)
6. **Consistent user experience** across all tools
7. **Comprehensive test coverage** for new functionality

## Related Specifications

This change will update the following OpenSpec specifications:
- **mcp-tools**: Add enhanced search parameter requirements
- **entity-cache**: Add advanced filtering requirements
- **database-setup**: Add case-insensitive index requirements

New specifications will be created for:
- **enhanced-search**: Comprehensive filtering capabilities
- **performance-optimization**: Database-level filtering requirements
