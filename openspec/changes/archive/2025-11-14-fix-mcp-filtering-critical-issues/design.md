# Database Layer Enhancement Design

## Overview

This design document outlines the architectural changes needed to fix the critical filtering issues in the MCP tools. The core enhancement is to the `query_cached_entities()` function in `src/lorekeeper_mcp/cache/db.py`, which will be extended to support case-insensitive matching, slug field searching, and efficient database-level filtering.

## Current Architecture Limitations

### Existing `query_cached_entities()` Function
```python
async def query_cached_entities(
    self,
    entity_type: str,
    filters: dict[str, Any] | None = None,
    limit: int | None = None,
    offset: int | None = None
) -> list[dict[str, Any]]:
    # ...
    for field, value in filters.items():
        where_clauses.append(f"{field} = ?")  # ❌ Only exact, case-sensitive match
        params.append(value)
```

**Problems:**
1. Only supports exact, case-sensitive matching
2. No slug field search capability
3. No partial matching support
4. Forces tools to implement client-side filtering

## Enhanced Architecture Design

### 1. Enhanced Name Parameter with Automatic Fallback

The existing `name` parameter will be enhanced with two key improvements:

1. **Case-Insensitive Default**: Change from case-sensitive to case-insensitive matching
2. **Automatic Slug Fallback**: If name search fails, automatically try slug search

```python
async def query_cached_entities(
    self,
    entity_type: str,
    filters: dict[str, Any] | None = None,
    limit: int | None = None,
    offset: int | None = None
) -> list[dict[str, Any]]:

    # First attempt: Enhanced name search
    name_results = await self._search_by_name(filters, limit, offset)

    # Fallback: Try slug search if name search returns empty
    if not name_results and filters and "name" in filters:
        slug_results = await self._search_by_slug(filters["name"], limit, offset)
        return slug_results

    return name_results

async def _search_by_name(self, filters, limit, offset):
    """Enhanced case-insensitive name search."""
    where_clauses = []
    params = []

    if filters and "name" in filters:
        # Detect wildcard patterns for partial matching
        name_value = filters["name"]
        if "*" in name_value or "%" in name_value:
            processed = name_value.replace("*", "%")
            where_clauses.append("LOWER(name) LIKE LOWER(?)")
            params.append(processed)
        else:
            # Default to case-insensitive exact matching
            where_clauses.append("LOWER(name) = LOWER(?)")
            params.append(name_value)

    # Build and execute enhanced query
    # ... rest of implementation

async def _search_by_slug(self, name_value, limit, offset):
    """Fallback slug search."""
    where_clauses = ["slug = ?"]
    params = [name_value]

    # Build and execute slug query
    # ... rest of implementation
```

### 2. Enhanced `query_cached_entities()` Implementation

```python
async def query_cached_entities(
    self,
    entity_type: str,
    filters: dict[str, Any] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    fallback_slug: bool = True  # Auto-try slug if name match fails
) -> list[dict[str, Any]]:

    where_clauses = []
    params = []

    if filters:
        for field, value in filters.items():
            if field == "name" and isinstance(value, str):
                # Enhanced name filtering with smart detection
                sql_pattern, processed_value = determine_name_matching_mode(value)
                where_clauses.append(sql_pattern)
                params.append(processed_value)
            else:
                # Legacy exact match for all other fields
                where_clauses.append(f"{field} = ?")
                params.append(value)

    # Build and execute query
    where_sql = ""
    if where_clauses:
        where_sql = " WHERE " + " AND ".join(where_clauses)

    limit_sql = ""
    if limit is not None:
        limit_sql = f" LIMIT {limit}"

    offset_sql = ""
    if offset is not None:
        offset_sql = f" OFFSET {offset}"

    sql = f"""
        SELECT data FROM {entity_type}
        {where_sql}
        ORDER BY name
        {limit_sql}{offset_sql}
    """

    cursor = await self.execute_query(sql, params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        try:
            data = json.loads(row["data"])
            results.append(data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in cache for {entity_type}")
            continue

    # Note: Automatic slug fallback is handled at the higher level
    # in the main query_cached_entities function to avoid recursion

    return results
```

### 3. Database Index Enhancements

To support efficient case-insensitive queries, we'll add new indexes:

```python
# In cache setup
CREATE INDEX IF NOT EXISTS idx_spells_name_lower ON spells(LOWER(name));
CREATE INDEX IF NOT EXISTS idx_creatures_name_lower ON creatures(LOWER(name));
CREATE INDEX IF NOT EXISTS idx_equipment_name_lower ON equipment(LOWER(name));
CREATE INDEX IF NOT EXISTS idx_character_options_name_lower ON character_options(LOWER(name));
CREATE INDEX IF NOT EXISTS idx_rules_name_lower ON rules(LOWER(name));

# Slug indexes (should already exist as PRIMARY KEY)
-- slug is already PRIMARY KEY, no additional index needed
```

### 4. Tool Layer Standardization

All tools will use the same enhanced `name` parameter with automatic fallback:

```python
# Base tool class for consistent filtering
class BaseLookupTool:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def build_filters(
        self,
        name: str | None = None,
        **other_filters
    ) -> dict[str, Any]:
        """Build filter dictionary with enhanced name parameter."""
        filters = {}

        if name is not None:
            # Enhanced name parameter - database layer handles detection
            filters["name"] = name

        # Add other filters as exact matches
        for key, value in other_filters.items():
            if value is not None:
                filters[key] = value

        return filters
```

## Migration Strategy

### Phase 1: Database Layer Enhancement
1. Implement enhanced `query_cached_entities()` function
2. Add new database indexes for case-insensitive queries
3. Maintain backward compatibility with existing filters
4. Add comprehensive unit tests for new functionality

### Phase 2: Tool Layer Migration
1. Update `lookup_spell` and `lookup_rule` to use enhanced case-insensitive filtering
2. Migrate `lookup_creature`, `lookup_equipment`, `lookup_character_option` from client-side to database-side filtering
3. Enable enhanced name parameter behavior in all tools (no new parameters)
4. Update tool tests to verify enhanced functionality with existing parameters

### Phase 3: Performance Optimization
1. Verify database-level filtering is working (no 11x over-fetching)
2. Test query performance with new indexes
3. Validate memory usage reduction
4. Benchmark before/after performance

## Security Considerations

### SQL Injection Prevention
- All user input must use parameterized queries
- The enhanced function maintains proper SQL parameter binding
- No string concatenation of user input in SQL queries

```python
# ✅ Safe - uses parameter binding
where_clauses.append("LOWER(name) = LOWER(?)")
params.append(user_input)

# ❌ Dangerous - never do this
# where_clauses.append(f"LOWER(name) = LOWER('{user_input}')")
```

### Input Validation
- Validate filter parameter types
- Limit maximum length of search strings
- Sanitize special characters in LIKE queries

## Performance Impact

### Index Benefits
- **Case-insensitive queries:** `O(log n)` instead of `O(n)` full table scans
- **Slug queries:** Already optimized via PRIMARY KEY
- **Partial matches:** Efficient with `LOWER(column) LIKE LOWER(?)` and indexes

### Memory Benefits
- **Eliminate 11x over-fetching:** Client-side filtering removed
- **Reduced result set processing:** Database returns only needed data
- **Lower memory footprint:** No temporary client-side filtering lists

### Network Benefits
- **Smaller query results:** Database filtering reduces data transfer
- **Fewer round trips:** Single query instead of multiple client-side operations

## Testing Strategy

### Unit Tests
1. **Enhanced filtering modes:** Test all new filter types
2. **Backward compatibility:** Ensure existing filters still work
3. **Fallback logic:** Test name→slug fallback behavior
4. **SQL injection protection:** Verify parameter binding

### Integration Tests
1. **Tool functionality:** Test each tool with new parameters
2. **Performance:** Verify reduced data fetching
3. **Edge cases:** Empty results, special characters, SQL attempts

### Performance Tests
1. **Query performance:** Before/after database query timing
2. **Memory usage:** Compare client-side vs database-side filtering
3. **Concurrent access:** Multiple simultaneous filtering requests

## Rollback Plan

If issues arise, the enhanced function supports graceful degradation:

1. **Backward Compatibility:** Legacy exact-match filters still work
2. **Feature Flag:** Can disable enhanced features via configuration
3. **Index Removal:** New indexes can be dropped without affecting core functionality
4. **Simplified Rollback:** Revert to original implementation if needed

## Future Extensibility

The enhanced architecture supports future additions:

1. **New match modes:** Easy to add new comparison types
2. **Multi-field search:** Can combine multiple enhanced filters
3. **Full-text search:** Framework ready for FTS integration
4. **Custom functions:** Can add database-specific search functions

This design provides a robust, secure, and performant solution to the critical filtering issues while maintaining backward compatibility and enabling future enhancements.
