# api-parameter-usage Specification

## Summary

Fix API parameter usage bugs and implement proper filter operators across all Open5e and D&D 5e API clients to enable server-side filtering and eliminate inefficient client-side filtering.

## Background

Current implementation has critical bugs where server-side filtering is available but not used, resulting in unnecessary client-side filtering and poor performance. The Open5e v2 API supports Django-style filter operators (`__icontains`, `__gte`, `__lte`) that are completely unused.

## Requirements

## ADDED Requirements

### Requirement: Use filter operators for Open5e v2 endpoints

Open5e v2 API clients SHALL use proper Django-style filter operators (`name__icontains`, `school__key`, `level__gte`, etc.) for server-side filtering on individual endpoints.

**Rationale**: Open5e v2 uses Django REST framework filter operators. Using `name__icontains` provides case-insensitive partial matching server-side. Currently, the code fetches all records and filters client-side, which is inefficient.

#### Scenario: Server-side partial name matching
- **Given**: User searches for spells with name="fire"
- **When**: Open5e v2 client makes API request
- **Then**: Request includes `?name__icontains=fire` parameter
- **And**: API returns only spells containing "fire" in name
- **And**: No client-side filtering is needed

#### Scenario: Server-side school filtering
- **Given**: User searches for evocation spells
- **When**: Open5e v2 client makes API request
- **Then**: Request includes `?school__key=evocation` parameter
- **And**: API returns only evocation spells server-side
- **And**: No client-side school filtering is performed

### Requirement: Fix school filtering bug in Open5e v2 client

The Open5e v2 client SHALL use `school__key` parameter for server-side school filtering instead of client-side filtering.

**Rationale**: Code currently has a comment "school parameter is not supported server-side" which is incorrect. The API supports `school__key` and `school__name` filters.

#### Scenario: Remove client-side school filtering
- **Given**: open5e_v2.py get_spells method
- **When**: School parameter is provided
- **Then**: Client uses `school__key` parameter in API request
- **And**: No client-side filtering code exists
- **And**: Performance improves by ~80% for school-filtered queries

### Requirement: Implement range filter operators

API clients SHALL use range operators (`__gte`, `__lte`, `__gt`, `__lt`) for numeric field filtering where available.

**Rationale**: Open5e v2 supports range operators for numeric fields like level, challenge rating, cost, weight, etc. These enable efficient server-side range queries.

#### Scenario: Spell level range filtering
- **Given**: User searches for spells level 2-4
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?level__gte=2&level__lte=4`
- **And**: API returns only spells within range
- **And**: No client-side filtering needed

#### Scenario: Challenge rating range filtering
- **Given**: User searches for creatures CR 1-3
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?challenge_rating_decimal__gte=1&challenge_rating_decimal__lte=3`
- **And**: API returns only creatures within CR range
- **And**: Server-side filtering eliminates client-side work

### Requirement: Utilize D&D 5e API built-in partial matching

The D&D 5e API client SHALL rely on the API's built-in case-insensitive partial name matching.

**Rationale**: The D&D 5e API `name` parameter already provides partial matching. No client-side filtering is needed.

#### Scenario: Partial name search in D&D API
- **Given**: User searches for spells with name="fire"
- **When**: D&D 5e API request includes `?name=fire`
- **Then**: API returns "Fireball", "Fire Bolt", "Fire Shield", etc.
- **And**: Partial matching works out of the box
- **And**: No additional client-side filtering needed

### Requirement: Utilize Open5e unified search endpoint

The search system SHALL use the `/v2/search/` endpoint with `query`, `fuzzy`, and `vector` parameters for advanced cross-entity searches.

**Rationale**: The `/v2/search/` endpoint provides unified search across all content types with built-in fuzzy and semantic search capabilities.

#### Scenario: Unified search with fuzzy and semantic matching
- **Given**: User performs advanced search for "firbal" (typo)
- **When**: Request is made to `/v2/search/?query=firbal&fuzzy=true&vector=true`
- **Then**: API returns "Fireball" spell via fuzzy matching
- **And**: May include semantically related fire spells via vector search
- **And**: Results are deduplicated and ranked by relevance

#### Scenario: Cross-entity search
- **Given**: User searches for "dragon" without specifying entity type
- **When**: Unified search is used with `/v2/search/?query=dragon&fuzzy=true&vector=true`
- **Then**: Results include dragon creatures, dragon-themed spells, dragon-related items
- **And**: Results span multiple content types
- **And**: All results relevant to "dragon"

#### Scenario: Entity-specific unified search
- **Given**: User searches for "fire" limited to spells
- **When**: Request uses `/v2/search/?query=fire&fuzzy=true&vector=true&object_model=Spell`
- **Then**: Results include only spell entities
- **And**: Fuzzy and semantic matching still applied
- **And**: Type filter works with advanced search

### Requirement: Support multi-value filtering

API clients SHALL support comma-separated or array syntax for filters accepting multiple values.

**Rationale**: Both APIs support multi-value parameters which allow efficient filtering by multiple values in a single request.

#### Scenario: Multiple spell levels in D&D API
- **Given**: User searches for spells of levels 1, 2, and 3
- **When**: D&D API request uses `?level=1,2,3`
- **Then**: API returns spells from all specified levels
- **And**: Single API call replaces multiple requests

#### Scenario: Multiple spell schools in Open5e
- **Given**: User searches for evocation and illusion spells
- **When**: Open5e v2 request uses `?school__in=evocation,illusion`
- **Then**: API returns spells from both schools
- **And**: Results are efficiently filtered server-side

## MODIFIED Requirements

### Modified Requirement: Repository parameter mapping

Repository layer SHALL map high-level filter parameters to API-specific filter operators based on the client type.

**Rationale**: Different APIs use different parameter formats. Repository acts as adapter layer, translating generic filters to API-specific syntax.

#### Scenario: Repository maps to Open5e operators
- **Given**: Repository receives `{"name": "fire", "level_min": 2, "level_max": 4, "school": "evocation"}`
- **When**: Using Open5e v2 client
- **Then**: Repository maps to `{"name__icontains": "fire", "level__gte": 2, "level__lte": 4, "school__key": "evocation"}`
- **And**: Parameters are passed to API client
- **And**: Server-side filtering is maximized

#### Scenario: Repository maps to D&D API format
- **Given**: Repository receives `{"name": "fire", "level_min": 2, "level_max": 4}`
- **When**: Using D&D 5e API client
- **Then**: Repository maps to `{"name": "fire", "level": "2,3,4"}`
- **And**: Range converted to comma-separated values
- **And**: API handles filtering natively

## Implementation Notes

### Filter Operator Mapping

| Generic Parameter | Open5e v2 Operator | D&D 5e API Parameter | Notes |
|-------------------|-------------------|----------------------|-------|
| name              | name__icontains   | name                 | Open5e uses operator, D&D has built-in partial match |
| school            | school__key       | school               | Open5e needs __key suffix |
| level_min         | level__gte        | level (comma list)   | D&D uses comma-separated values |
| level_max         | level__lte        | level (comma list)   | D&D uses comma-separated values |
| level             | level             | level                | Exact match in both |
| cr_min            | challenge_rating_decimal__gte | challenge_rating (comma) | Range vs list |
| cr_max            | challenge_rating_decimal__lte | challenge_rating (comma) | Range vs list |

### API Client Updates Required

1. **Open5e V2 Client**:
   - Add `name__icontains` for partial matching
   - Fix `school__key` for school filtering (remove client-side filtering)
   - Add `level__gte`, `level__lte` for range queries
   - Implement `cost__gte`, `cost__lte`, `weight__gte`, `weight__lte`

2. **D&D 5e Client**:
   - Leverage existing partial name matching
   - Support comma-separated multi-value parameters

3. **Unified Search Client**:
   - New `unified_search()` method on Open5eV2Client
   - Parameters: `query`, `fuzzy`, `vector`, `object_model`

### Tool Interface Changes

**No tool signature changes for Phase 1** - All changes are backend-only:
- Existing tool parameters map to new filter operators
- No breaking changes to tool interfaces
- Transparent performance improvements

### Error Handling

- Graceful handling when filter operators not supported
- Clear error messages for invalid parameter combinations
- Fallback to client-side filtering only if API doesn't support feature

### Performance Expectations

**School Filtering Example**:
- Before: Fetch 500 spells (~500KB), filter client-side to 8 results
- After: Fetch 8 spells (~8KB) with `school__key=evocation`
- **Improvement**: 80% latency reduction, 98% data transfer reduction

**Name Filtering Example**:
- Before: Fetch 500 spells, filter client-side for "fire" to 12 results
- After: Fetch 12 spells with `name__icontains=fire`
- **Improvement**: 75% latency reduction, 95% data transfer reduction
