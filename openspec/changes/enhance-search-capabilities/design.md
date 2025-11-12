# Search Enhancement Architecture Design

## Overview

This document outlines the technical architecture for enhancing search capabilities by fixing parameter bugs, implementing proper API filter operators, and adding unified search functionality.

## Current Architecture Issues

### Identified Bugs

1. **School Filtering Bug** (open5e_v2.py:58-60):
   ```python
   # Note: school parameter is not supported server-side by Open5e v2 API,
   # so we filter client-side below
   ```
   **Reality**: `school__key` and `school__name` ARE supported server-side

2. **Name Filtering Inefficiency**: All tools fetch large datasets then filter client-side when APIs support server-side partial matching

3. **No Filter Operators**: Only using exact equality when `__gte`, `__lte`, `__in`, `__icontains` available

### Current vs Desired Flow

**Current (Inefficient)**:
```
Tool → Repository → API (minimal filters) → Fetch 100s of records →
Client-side filter by name → Client-side filter by school → Return 5 matches
```

**Desired (Efficient)**:
```
Tool → Repository → API (rich filters: name__icontains, school__key, level__gte) →
Fetch 5 matching records → Return 5 matches
```

## Proposed Architecture

### Phase 1: Fix API Client Filter Usage

#### Open5e V2 Client Enhancements

**Current Implementation**:
```python
async def get_spells(self, level: int | None = None, school: str | None = None, **kwargs):
    params = {}
    if level is not None:
        params["level"] = level
    # school filtered client-side (BUG!)

    result = await self.make_request("/spells/", params=params)
    spells = [Spell.model_validate(s) for s in result.get("results", [])]

    if school:  # Client-side filtering (INEFFICIENT!)
        spells = [s for s in spells if s.school.lower() == school.lower()]

    return spells
```

**Fixed Implementation**:
```python
async def get_spells(
    self,
    name: str | None = None,
    level: int | None = None,
    level_min: int | None = None,
    level_max: int | None = None,
    school: str | None = None,
    **kwargs
) -> list[Spell]:
    """Get spells with proper server-side filtering."""
    params = {}

    # Server-side partial name matching
    if name:
        params["name__icontains"] = name  # Case-insensitive contains

    # Level filtering with range support
    if level is not None:
        params["level"] = level
    if level_min is not None:
        params["level__gte"] = level_min
    if level_max is not None:
        params["level__lte"] = level_max

    # FIX: School filtering server-side!
    if school:
        params["school__key"] = school  # Server-side filtering

    # Add any additional parameters
    params.update(kwargs)

    result = await self.make_request("/spells/", params=params)
    spell_dicts = result.get("results", []) if isinstance(result, dict) else result

    # NO client-side filtering needed!
    return [Spell.model_validate(s) for s in spell_dicts]
```

#### D&D 5e API Client

**Leverage Built-in Partial Matching**:
```python
async def get_spells(self, name: str | None = None, level: int | None = None, **kwargs):
    """D&D API has built-in partial name matching."""
    params = {}

    if name:
        params["name"] = name  # Built-in case-insensitive partial match

    if level is not None:
        params["level"] = level

    params.update(kwargs)

    # API handles partial matching natively
    result = await self.make_request("/spells/", params=params)
    # No client-side filtering needed!
    return [Spell.model_validate(s) for s in result.get("results", [])]
```

### Phase 2: Unified Search Implementation

#### New Unified Search Client

```python
class Open5eV2Client(BaseHttpClient):
    async def unified_search(
        self,
        query: str,
        object_model: str | None = None,
        enable_fuzzy: bool = True,
        enable_semantic: bool = True,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Use Open5e unified search endpoint with fuzzy and semantic capabilities.

        Args:
            query: Search term
            object_model: Filter to specific type ("Spell", "Creature", "Item", etc.)
            enable_fuzzy: Enable typo-tolerant fuzzy matching
            enable_semantic: Enable concept-based semantic/vector search
            limit: Maximum results

        Returns:
            List of search results with mixed content types
        """
        params = {
            "query": query,  # Correct parameter name for /v2/search/
            "fuzzy": enable_fuzzy,
            "vector": enable_semantic,
        }

        if object_model:
            params["object_model"] = object_model  # e.g., "Spell"

        # Use unified search endpoint
        result = await self.make_request("/v2/search/", params=params)

        # Extract results (format depends on search type)
        if isinstance(result, list):
            results = result
        elif isinstance(result, dict):
            results = result.get("results", [])
        else:
            results = []

        return results[:limit]
```

#### New MCP Tool

```python
async def search_dnd_content(
    query: str,
    content_types: list[str] | None = None,
    enable_fuzzy: bool = True,
    enable_semantic: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search across all D&D content with advanced fuzzy and semantic matching.

    This tool uses Open5e's unified search endpoint to find content across multiple
    types (spells, creatures, items, etc.) with typo tolerance and conceptual matching.
    Perfect for exploratory searches like "find anything related to fire" or when
    you're not sure of exact spelling.

    Examples:
        # Cross-entity search
        search_dnd_content(query="dragon")  # Finds dragon creatures, dragon-themed spells, etc.

        # Typo-tolerant search
        search_dnd_content(query="firbal")  # Finds "Fireball" despite typo

        # Concept-based search
        search_dnd_content(query="healing magic")  # Finds Cure Wounds, Healing Word, etc.

        # Type-filtered search
        search_dnd_content(query="fire", content_types=["Spell"])  # Only fire spells

    Args:
        query: Search term (handles typos and concepts automatically)
        content_types: Limit to specific types: ["Spell", "Creature", "Item", "Background", "Feat"]
                      Default None searches all content types
        enable_fuzzy: Enable fuzzy matching for typo tolerance (default True)
        enable_semantic: Enable semantic/vector search for conceptual matching (default True)
        limit: Maximum number of results to return (default 20)

    Returns:
        List of content dictionaries with varied structure based on content type.
        Each result includes a 'type' or 'model' field indicating content type.
    """
    client = Open5eV2Client()

    if content_types:
        # Multiple searches, one per content type
        all_results = []
        per_type_limit = limit // len(content_types)

        for content_type in content_types:
            results = await client.unified_search(
                query=query,
                object_model=content_type,
                enable_fuzzy=enable_fuzzy,
                enable_semantic=enable_semantic,
                limit=per_type_limit,
            )
            all_results.extend(results)

        return all_results[:limit]
    else:
        # Single unified search across all types
        return await client.unified_search(
            query=query,
            enable_fuzzy=enable_fuzzy,
            enable_semantic=enable_semantic,
            limit=limit,
        )
```

### Phase 3: Tool Enhancements (Optional)

#### Enhanced Spell Lookup (Backward Compatible)

```python
async def lookup_spell(
    # Existing parameters (unchanged)
    name: str | None = None,
    level: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    casting_time: str | None = None,

    # NEW: Range parameters (optional, backward compatible)
    level_min: int | None = None,
    level_max: int | None = None,

    # NEW: Additional filters available in API (optional)
    damage_type: str | None = None,

    limit: int = 20,
) -> list[dict[str, Any]]:
    """Enhanced spell lookup with range and additional filters."""
    repository = _get_repository()

    params = {}
    if name:
        params["name"] = name  # Repository maps to name__icontains
    if level is not None:
        params["level"] = level
    if level_min is not None:
        params["level_min"] = level_min  # Repository maps to level__gte
    if level_max is not None:
        params["level_max"] = level_max  # Repository maps to level__lte
    if school:
        params["school"] = school  # Repository maps to school__key
    if concentration is not None:
        params["concentration"] = concentration
    if ritual is not None:
        params["ritual"] = ritual
    if casting_time:
        params["casting_time"] = casting_time
    if damage_type:
        params["damage_type"] = damage_type

    spells = await repository.search(limit=limit, **params)

    # Client-side class_key filtering (not available in API)
    if class_key:
        spells = [s for s in spells if class_key.lower() in [c.lower() for c in s.classes]]

    return [s.model_dump() for s in spells[:limit]]
```

## Repository Layer Updates

### Parameter Mapping

```python
class SpellRepository(Repository[Spell]):
    def _map_to_api_params(self, **filters) -> dict[str, Any]:
        """Map repository parameters to API-specific filter operators."""
        params = {}

        if isinstance(self.client, Open5eV2Client):
            # Map to Open5e filter operators
            if "name" in filters:
                params["name__icontains"] = filters["name"]
            if "school" in filters:
                params["school__key"] = filters["school"]
            if "level_min" in filters:
                params["level__gte"] = filters["level_min"]
            if "level_max" in filters:
                params["level__lte"] = filters["level_max"]
            # Pass through exact matches
            for key in ["level", "concentration", "ritual", "casting_time"]:
                if key in filters:
                    params[key] = filters[key]

        elif isinstance(self.client, Dnd5eApiClient):
            # D&D API uses name directly (built-in partial match)
            if "name" in filters:
                params["name"] = filters["name"]
            # Handle multi-value level ranges
            if "level_min" in filters and "level_max" in filters:
                # Convert range to comma-separated list
                levels = list(range(filters["level_min"], filters["level_max"] + 1))
                params["level"] = ",".join(map(str, levels))
            elif "level" in filters:
                params["level"] = filters["level"]
            # Pass through other filters
            for key in ["school"]:
                if key in filters:
                    params[key] = filters[key]

        return params
```

## Performance Impact

### Expected Improvements

**Before (School Filter Example)**:
- API call: Fetch all ~500 spells
- Transfer: ~500KB JSON
- Client-side filter to 8 evocation spells
- **Total time**: ~800ms

**After (School Filter Example)**:
- API call: Fetch 8 evocation spells with `school__key=evocation`
- Transfer: ~8KB JSON
- No client-side filtering
- **Total time**: ~150ms

**Performance gain**: 80% reduction in latency, 98% reduction in data transfer

## Testing Strategy

### Unit Tests

```python
# Test filter operator usage
async def test_spell_school_server_side_filtering():
    """Verify school filtering uses server-side parameters."""
    client = Open5eV2Client()
    with respx.mock:
        route = respx.get("https://api.open5e.com/v2/spells/").mock(
            return_value={"results": []}
        )

        await client.get_spells(school="evocation")

        # Assert server-side parameter used
        assert "school__key" in route.calls.last.request.url.params
        assert route.calls.last.request.url.params["school__key"] == "evocation"

# Test unified search
async def test_unified_search_fuzzy_semantic():
    """Verify unified search uses correct parameters."""
    client = Open5eV2Client()
    with respx.mock:
        route = respx.get("https://api.open5e.com/v2/search/").mock(
            return_value={"results": []}
        )

        await client.unified_search(query="fire", enable_fuzzy=True, enable_semantic=True)

        # Assert correct endpoint and parameters
        assert route.calls.last.request.url.path == "/v2/search/"
        assert route.calls.last.request.url.params["query"] == "fire"
        assert route.calls.last.request.url.params["fuzzy"] == "true"
        assert route.calls.last.request.url.params["vector"] == "true"
```

### Integration Tests

- Test actual API responses with `school__key` parameter
- Verify unified search returns results for typos
- Confirm semantic search finds conceptually related content
- Validate performance improvements (measure response times)

## Backward Compatibility

- Existing tool signatures remain unchanged for Phase 1
- New `search_dnd_content` tool is additive (doesn't replace anything)
- Phase 3 enhancements add optional parameters only
- All existing test cases pass without modification

## Migration Path

1. **Phase 1**: Deploy bug fixes (transparent to users)
2. **Phase 2**: Add new unified search tool (users can start using it)
3. **Phase 3**: Optionally enhance existing tools (users gradually adopt new parameters)

No breaking changes at any phase.
