# Fix Test Failures - Design Document

## Overview

This document details the technical approach for fixing 9 test failures by correcting API parameter mapping, adding error handling, and updating test mocks.

## Architecture

### Current State

```
Tool Layer (creature_lookup.py, spell_lookup.py, character_option_lookup.py)
    ↓ passes parameters (e.g., type="Beast", class_key="wizard")
Repository Layer (monster.py, spell.py, character_option.py)
    ↓ maps to API parameters (_map_to_api_params)
API Client Layer (open5e_v2.py)
    ↓ makes HTTP request with wrong parameters
Open5e v2 API
    ↓ returns 400 error or empty results
```

### Desired State

```
Tool Layer (creature_lookup.py, spell_lookup.py, character_option_lookup.py)
    ↓ passes parameters (same as before - no changes needed)
Repository Layer (monster.py, spell.py, character_option.py)
    ↓ correctly maps to API parameters with __key suffixes and lowercase
API Client Layer (open5e_v2.py)
    ↓ makes HTTP request with correct parameters
    ↓ handles 400 errors gracefully
Open5e v2 API
    ↓ returns valid results
```

## Component Changes

### 1. Monster Repository (`src/lorekeeper_mcp/repositories/monster.py`)

**Current `_map_to_api_params` mapping:**
```python
# Pass through exact matches and API-specific parameters
for key in ["type", "size", "challenge_rating", "name__icontains"]:
    if key in filters:
        params[key] = filters[key]
```

**New mapping:**
```python
# Map type and size to __key variants with lowercase
if "type" in filters:
    params["type__key"] = filters["type"].lower()
if "size" in filters:
    params["size__key"] = filters["size"].lower()

# Map exact CR to challenge_rating_decimal
if "cr" in filters:
    params["challenge_rating_decimal"] = float(filters["cr"])

# Keep existing range operators
if "cr_min" in filters:
    params["challenge_rating_decimal__gte"] = filters["cr_min"]
if "cr_max" in filters:
    params["challenge_rating_decimal__lte"] = filters["cr_max"]

# Keep other mappings
if "armor_class_min" in filters:
    params["armor_class__gte"] = filters["armor_class_min"]
if "hit_points_min" in filters:
    params["hit_points__gte"] = filters["hit_points_min"]
if "name" in filters:
    params["name__icontains"] = filters["name"]
```

**Rationale**: The Open5e v2 API uses Django REST framework filtering which requires:
- Relationship lookups with `__key` suffix (e.g., `type__key`, `size__key`)
- Lowercase values for key-based lookups
- Decimal representation for challenge ratings

### 2. Spell Repository (`src/lorekeeper_mcp/repositories/spell.py`)

**Current mapping:**
```python
elif isinstance(self.client, Open5eV2Client):
    # Map to Open5e v2 filter operators
    if "level_min" in filters and "level_max" in filters:
        params["level__gte"] = filters["level_min"]
        params["level__lte"] = filters["level_max"]
    elif "level" in filters:
        params["level"] = filters["level"]
    # Pass through other filters
    for key in ["school", "name", "name__icontains", "damage_type"]:
        if key in filters:
            params[key] = filters[key]
```

**New mapping:**
```python
elif isinstance(self.client, Open5eV2Client):
    # Map to Open5e v2 filter operators
    if "level_min" in filters and "level_max" in filters:
        params["level__gte"] = filters["level_min"]
        params["level__lte"] = filters["level_max"]
    elif "level" in filters:
        params["level"] = filters["level"]

    # Map class_key to classes__key (plural)
    if "class_key" in filters:
        params["classes__key"] = filters["class_key"].lower()

    # Map school to school__key
    if "school" in filters:
        params["school__key"] = filters["school"].lower()

    # Map name to name__icontains
    if "name" in filters:
        params["name__icontains"] = filters["name"]

    # Pass through other filters
    for key in ["name__icontains", "damage_type", "concentration"]:
        if key in filters:
            params[key] = filters[key]
```

**Rationale**: Similar to creature filtering, spell filters need proper relationship lookups:
- `class_key` → `classes__key` (plural because spells can have multiple classes)
- `school` → `school__key` (relationship lookup)
- `concentration` passed through as boolean

### 3. Base API Client (`src/lorekeeper_mcp/api_clients/base.py`)

**Current error handling:**
```python
async def make_request(self, endpoint: str, method: str = "GET", **kwargs: Any) -> Any:
    # ... request logic ...
    if response.status_code >= 400:
        raise ApiError(f"API error: {response.status_code}")
```

**New error handling:**
```python
async def make_request(self, endpoint: str, method: str = "GET", **kwargs: Any) -> Any:
    # ... request logic ...
    if response.status_code >= 400:
        # For 400 errors (validation), check if it's a filter validation issue
        if response.status_code == 400:
            try:
                error_data = response.json()
                # Log the validation error for debugging
                logger.warning(
                    f"API validation error for {endpoint}: {error_data}"
                )
                # Return empty result set for filter validation errors
                return {"results": [], "count": 0}
            except Exception:
                pass

        # For other errors, raise as before
        raise ApiError(f"API error: {response.status_code}")
```

**Rationale**: Invalid filter values (like "InvalidType123") should not crash the application. Instead:
1. Log the validation error for debugging
2. Return an empty result set
3. Allow the application to continue normally

This matches user expectations - an invalid search should return no results, not crash.

### 4. Character Option Repository (`src/lorekeeper_mcp/repositories/character_option.py`)

**Current `_search_feats` method:**
```python
async def _search_feats(self, **filters: Any) -> list[dict[str, Any]]:
    # Extract limit parameter (not a cache filter field)
    limit = filters.pop("limit", None)

    # Try cache first
    cached = await self.cache.get_entities("feats", **filters)
    if cached:
        return cached[:limit] if limit else cached

    # Fetch from API
    feats: list[dict[str, Any]] = await self.client.get_feats(limit=limit, **filters)

    if feats:
        await self.cache.store_entities(feats, "feats")

    return feats
```

**Changes needed:**
```python
async def _search_feats(self, **filters: Any) -> list[dict[str, Any]]:
    # Extract limit parameter (not a cache filter field)
    limit = filters.pop("limit", None)

    # Default to higher limit for feats to get comprehensive results
    api_limit = limit if limit else 100

    # Try cache first
    cached = await self.cache.get_entities("feats", **filters)
    if cached:
        return cached[:limit] if limit else cached

    # Fetch from API with proper limit
    feats: list[dict[str, Any]] = await self.client.get_feats(limit=api_limit, **filters)

    if feats:
        await self.cache.store_entities(feats, "feats")

    return feats[:limit] if limit else feats
```

**Rationale**: The Open5e v2 API returns only 5 results by default. For feats (91 total), we need to explicitly request more. Using a default of 100 ensures comprehensive results while respecting user-specified limits.

### 5. Integration Test Mocks (`tests/test_tools/test_integration.py`)

**Current mocks:**
```python
respx.get("https://api.open5e.com/v1/monsters/?").mock(...)
```

**New mocks needed:**
```python
# Mock v2 creatures endpoint with various parameter combinations
respx.get("https://api.open5e.com/v2/creatures/?limit=220").mock(...)
respx.get("https://api.open5e.com/v2/creatures/?limit=20&challenge_rating_decimal=21.0").mock(...)
```

**Rationale**: Tests must mock the actual endpoints being called. Since the repository now uses v2 by default, mocks must match v2 endpoint structure.

## Data Flow Examples

### Example 1: Creature Type Filter

**Input:**
```python
await lookup_creature(type="Beast", limit=10)
```

**Flow:**
1. Tool receives `type="Beast"`, `limit=10`
2. Tool calls `repository.search(type="Beast", limit=10)`
3. Repository's `_map_to_api_params` transforms:
   - `type="Beast"` → `type__key="beast"` (lowercase)
4. API client receives `type__key="beast"`, `limit=10`
5. API request: `GET /v2/creatures/?type__key=beast&limit=10`
6. API returns list of beast creatures
7. Results flow back through repository → tool → user

**Before fix:** API returned 400 error (`type` is not valid)
**After fix:** API returns valid beast creatures

### Example 2: Spell Class Filter

**Input:**
```python
await lookup_spell(class_key="wizard", concentration=True, limit=10)
```

**Flow:**
1. Tool receives `class_key="wizard"`, `concentration=True`, `limit=10`
2. Tool calls `repository.search(class_key="wizard", concentration=True, limit=10)`
3. Repository's `_map_to_api_params` transforms:
   - `class_key="wizard"` → `classes__key="wizard"` (plural)
   - `concentration=True` → `concentration=True` (pass through)
4. API client receives `classes__key="wizard"`, `concentration=True`, `limit=10`
5. API request: `GET /v2/spells/?classes__key=wizard&concentration=true&limit=10`
6. API returns list of wizard concentration spells
7. Results flow back

**Before fix:** Returned 0 results (`class_key` doesn't exist in API)
**After fix:** Returns wizard concentration spells

### Example 3: Invalid Type Error Handling

**Input:**
```python
await lookup_creature(type="InvalidType123")
```

**Flow:**
1. Tool receives `type="InvalidType123"`
2. Repository transforms: `type__key="invalidtype123"`
3. API request: `GET /v2/creatures/?type__key=invalidtype123`
4. API returns 400 with validation error
5. Base client catches 400, logs warning, returns `{"results": [], "count": 0}`
6. Repository receives empty results
7. Tool returns empty list `[]`

**Before fix:** Raised `ApiError` and crashed
**After fix:** Returns empty list gracefully

## Testing Strategy

### Unit Tests
- Test `_map_to_api_params` in isolation with various input combinations
- Verify correct parameter transformations
- Test lowercase conversion
- Test CR exact and range parameters

### Integration Tests
- Update mocks to use v2 endpoints
- Verify tool → repository → API client flow
- Test error handling paths

### Live Tests
- Run against real Open5e v2 API
- Verify all 9 previously failing tests now pass
- Confirm no regressions in other tests

## Rollback Plan

If issues arise:
1. Revert parameter mapping changes in repositories
2. Restore original error handling in base.py
3. Roll back test mock changes
4. All changes are isolated to specific methods, making rollback safe

## Performance Considerations

**Negligible Impact**: Parameter mapping adds minimal overhead (string manipulation and dictionary operations). Error handling only activates on errors, not normal flow.

**Improved Efficiency**: Correct API parameters mean:
- Fewer empty result sets from the API
- Less unnecessary data transfer
- Better cache hit rates

## Security Considerations

**Input Validation**: Lowercase conversion happens after user input, preventing injection attempts through case manipulation.

**Error Information Disclosure**: 400 errors are logged but not exposed to users beyond "no results found" behavior.

## Migration Notes

**No Breaking Changes**: All changes are internal to the repository layer. Tools and external APIs remain unchanged.

**Backward Compatibility**: Existing cached data remains valid. New queries will use corrected parameters.
