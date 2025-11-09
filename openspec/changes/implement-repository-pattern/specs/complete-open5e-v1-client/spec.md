# complete-open5e-v1-client Specification

## Purpose
Complete the Open5e v1 API client by implementing all available endpoints, providing full coverage of the v1 API for monsters, classes, races, magic items, planes, sections, and spell lists.

## MODIFIED Requirements

### Requirement: Open5e v1 Comprehensive Endpoint Coverage
The system SHALL provide client methods for all Open5e v1 API endpoints beyond the currently implemented monsters, classes, and races.

#### Scenario: Fetch magic items from Open5e v1
When a user needs magic item data, the client should fetch from the `/v1/magicitems/` endpoint with filtering capabilities.

**Acceptance Criteria:**
- `get_magic_items()` method supports name, type, rarity, and requires_attunement filtering
- Parses item properties, effects, and requirements
- Returns structured magic item data with consistent field names
- Handles pagination for large result sets (700+ items)
- Uses entity cache with 7-day TTL

#### Scenario: Fetch planes of existence
When a user needs planar lore and mechanics, the client should fetch from the `/v1/planes/` endpoint.

**Acceptance Criteria:**
- `get_planes()` method supports name filtering
- Parses plane descriptions and properties
- Returns structured plane data
- Uses entity cache with 7-day TTL

#### Scenario: Fetch rule sections and lore
When a user needs detailed rule text and lore sections, the client should fetch from the `/v1/sections/` endpoint.

**Acceptance Criteria:**
- `get_sections()` method supports name and parent filtering
- Handles hierarchical section structure
- Returns section content with proper nesting
- Supports filtering by document source
- Uses entity cache with 7-day TTL

#### Scenario: Fetch spell lists by class
When determining which spells are available to a class, the client should fetch from the `/v1/spelllist/` endpoint.

**Acceptance Criteria:**
- `get_spell_list()` method supports class filtering
- Returns list of spell slugs/references for each class
- Handles multi-class spell list queries
- Uses entity cache with extended TTL (30 days - reference data)

#### Scenario: Fetch API manifest
When introspecting available API resources, the client should fetch from the `/v1/manifest/` endpoint.

**Acceptance Criteria:**
- `get_manifest()` method returns API metadata
- Lists available endpoints and versions
- Caches manifest with extended TTL (30 days)
- Provides document source information

## MODIFIED Requirements

### Requirement: Open5e v1 Client Response Normalization
The system SHALL normalize Open5e v1 API responses to use consistent 'slug' field naming, already partially implemented in `_extract_entities()`.

#### Scenario: Normalize v1 'index' to 'slug'
When Open5e v1 returns entities with 'slug' field (unlike D&D 5e API which uses 'index'), ensure consistent extraction.

**Acceptance Criteria:**
- All v1 endpoints return entities with 'slug' field
- No 'index' to 'slug' normalization needed (v1 already uses 'slug')
- Validation that paginated responses extract from 'results' array
- Single entity responses wrapped in list format
- Filter out entities without required 'slug' field
