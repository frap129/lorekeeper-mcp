# enhance-search-capabilities Change Proposal

## Summary

Enhance search capabilities in LoreKeeper MCP by fixing parameter bugs, implementing proper server-side filtering with API filter operators, and adding a new unified search tool that exposes fuzzy and semantic search capabilities.

## Problem Statement

The current search implementation has significant issues and missed opportunities:

1. **Bug: Client-Side School Filtering**: Code incorrectly performs client-side school filtering despite `school__key` being available server-side in Open5e v2 API
2. **Bug: Inefficient Name Filtering**: All tools fetch large datasets then filter by name client-side, when APIs support server-side partial matching
3. **Missing Filter Operators**: Open5e v2 supports rich Django-style operators (`__icontains`, `__gte`, `__lte`, `__in`) that aren't being used
4. **No Advanced Search**: Open5e's `/v2/search/` endpoint with fuzzy and semantic capabilities is completely unused
5. **Poor Performance**: Excessive client-side filtering increases data transfer and processing time

## API Capabilities Available

### Open5e v2 API Features

**Individual Endpoints** (`/v2/spells/`, `/v2/creatures/`, `/v2/items/`):
- **Filter Operators**: `name__icontains`, `name__exact`, `field__gte`, `field__lte`, `field__in`
- **Spell Filtering**: `level`, `level__gte`, `level__lte`, `school__key`, `school__name`, `concentration`, `ritual`, `casting_time`, `damage_type`
- **Creature Filtering**: `challenge_rating_decimal`, `challenge_rating_decimal__gte/lte`, `size`, `type`, `armor_class__gte/lte`, `ability_score_*__gte/lte`
- **Equipment Filtering**: `cost__gte/lte`, `weight__gte/lte`, `rarity`, `is_magic_item`, `is_weapon`, `is_armor`, `is_finesse`, `is_light`, `is_versatile`

**Unified Search Endpoint** (`/v2/search/`):
- **Parameter**: `query` (required search term)
- **Fuzzy Matching**: `fuzzy=true` enables typo-tolerant search
- **Semantic Search**: `vector=true` enables concept-based search
- **Type Filtering**: `object_model=Spell` limits to specific content types
- **Default Behavior**: Exact search with fuzzy fallback if no results
- **Combined Mode**: Can enable fuzzy + vector simultaneously

### D&D 5e API Features

- **Partial Name Matching**: `name` parameter has built-in case-insensitive partial matching
- **Multi-Value Filters**: `level=1,2,3` or `challenge_rating=1,2,3` (comma-separated)
- **Spell Filtering**: `level`, `school` with array support
- **Monster Filtering**: `challenge_rating` with array support

### Current Implementation Gaps

1. **School Filtering Bug**: Fetches all spells then filters client-side when `school__key` works server-side
2. **Name Filtering Inefficiency**: Client-side name matching when `name__icontains` available (Open5e) and built-in partial matching (D&D API)
3. **No Filter Operators**: Using only exact equality when range operators (`__gte`, `__lte`) and contains operators available
4. **Missing Unified Search**: `/v2/search/` endpoint with fuzzy + semantic capabilities completely unused
5. **No Boolean Filters**: Equipment properties like `is_finesse`, `is_light`, `is_magic_item` not exposed

## Proposed Solution

### Three-Phase Approach

#### Phase 1: Fix Bugs and Add Server-Side Filtering (Critical)
- Fix school filtering to use `school__key` server-side
- Replace client-side name filtering with proper API parameters
- Implement filter operators for range queries (`__gte`, `__lte`)
- Add server-side boolean filtering for equipment properties

#### Phase 2: Add Unified Search Tool (High Value)
- Create new `search_dnd_content()` MCP tool
- Expose `/v2/search/` endpoint with fuzzy and semantic capabilities
- Enable cross-entity searches
- Allow typo-tolerant and concept-based queries

#### Phase 3: Enhance Existing Tools (Optional)
- Add range parameters (`level_min`/`level_max`, `cost_min`/`cost_max`)
- Add commonly useful filters from APIs
- All enhancements backward compatible (optional parameters)

## Technical Approach

### 1. Backend Fixes (No Tool Signature Changes)

**Fix API Client Parameter Usage**:
- Open5e v2: Use `name__icontains` for partial matching, `school__key` for school filtering
- D&D 5e: Rely on built-in partial name matching
- Map repository parameters to API-specific filter operators

**Example**:
```python
# BEFORE (client-side filtering)
spells = await client.get_spells(level=3)
if school:
    spells = [s for s in spells if s.school.lower() == school.lower()]

# AFTER (server-side filtering)
spells = await client.get_spells(level=3, school__key=school)
```

### 2. New Unified Search Tool

Add new MCP tool that doesn't replace existing tools:

```python
async def search_dnd_content(
    query: str,
    content_types: list[str] | None = None,  # ["Spell", "Creature", "Item"]
    enable_fuzzy: bool = True,
    enable_semantic: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search across all D&D content with fuzzy and semantic matching."""
```

### 3. Backward Compatible Tool Enhancements

Optionally add useful parameters without breaking changes:
- `level_min`/`level_max` for spell searches
- `cost_min`/`cost_max`, `weight_max` for equipment
- `armor_class_min`, `hit_points_min` for creatures
- Boolean filters: `is_finesse`, `is_light`, `is_magic_item`

## Benefits

1. **Bug Fixes**: School filtering works correctly, eliminating known issues
2. **Performance**: Server-side filtering reduces data transfer by 50-90% for filtered queries
3. **New Capabilities**: Fuzzy and semantic search enable typo tolerance and conceptual queries
4. **Backward Compatible**: Existing tool calls continue to work unchanged
5. **API-Native**: Leverages battle-tested API features instead of custom client-side logic
6. **Maintainability**: Less custom filtering code, more reliance on API-provided features

## Success Criteria

- [ ] School filtering works server-side without client-side filtering
- [ ] Name searches use server-side partial matching
- [ ] New unified search tool handles typos (e.g., "firbal" → "Fireball")
- [ ] Semantic search returns conceptually related results
- [ ] All existing test cases pass without modification
- [ ] Performance improves for filtered queries (measure data transfer reduction)

## Change ID

`enhance-search-capabilities`
