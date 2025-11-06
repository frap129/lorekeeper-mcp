# D&D 5e API Client Delta Specification

## ADDED Requirements

### Requirement: D&D 5e Rules API Client
The system SHALL provide a D&D 5e API client method to fetch rule data from the `/api/2014/rules/` and `/api/2014/rule-sections/` endpoints for the `lookup_rule` tool.

#### Scenario: Fetch rules by section
When a user searches for game rules using the `lookup_rule` tool, the D&D 5e API client should fetch rule data from the `/api/2014/rules/` endpoint with optional section filtering.

**Acceptance Criteria:**
- `get_rules()` method supports section and name filtering
- Fetches rule categories: adventuring, combat, equipment, spellcasting, using-ability-scores, appendix
- Parses rule subsections and detailed mechanics
- Returns structured rule data with hierarchical organization
- Supports browsing rules by section or searching by name
- Uses entity cache for rules data with standard 7-day TTL

#### Scenario: Fetch detailed rule sections
When a user needs detailed information about specific rule sections (like opportunity attacks or grappled condition mechanics), the client should fetch detailed rule section data from the `/api/2014/rule-sections/` endpoint.

**Acceptance Criteria:**
- `get_rule_sections()` method supports name filtering
- Fetches detailed rule mechanics and examples (33 rule sections)
- Parses cross-references to related rules
- Returns structured rule section data with full descriptions
- Handles nested rule structures and references
- Uses entity cache for rule sections with standard 7-day TTL

### Requirement: D&D 5e Reference Data API Client
The system SHALL provide a D&D 5e API client methods to fetch reference data from various endpoints for the `lookup_rule` tool.

#### Scenario: Fetch reference data types
When a user searches for reference information like damage types, weapon properties, skills, or ability scores using the `lookup_rule` tool, the client should fetch reference data from the appropriate D&D 5e API endpoints.

**Acceptance Criteria:**
- `get_damage_types()` method fetches all damage type descriptions (13 types)
- `get_weapon_properties()` method fetches weapon property explanations (11 properties)
- `get_skills()` method fetches skill descriptions and ability associations (18 skills)
- `get_ability_scores()` method fetches ability score explanations (6 scores)
- `get_magic_schools()` method fetches magic school descriptions (8 schools)
- `get_languages()` method fetches language types and examples (16 languages)
- `get_proficiencies()` method fetches proficiency categories (117 proficiencies)
- `get_alignments()` method fetches alignment descriptions (9 alignments)
- All reference data uses extended cache TTL (30 days = 2,592,000 seconds)
- All methods support entity cache for offline capability

### Requirement: D&D 5e API Client Factory
The system SHALL provide a factory method to create properly configured D&D 5e API client instances with dependency injection support.

#### Scenario: Create D&D 5e API client via factory
When the application needs to create a D&D 5e API client instance, it should use a factory that provides proper configuration and dependency injection.

**Acceptance Criteria:**
- `ClientFactory.create_dnd5e_api()` method exists
- Configures base URL for 2014 API version (https://www.dnd5eapi.co/api/2014/)
- Handles API redirects and version management automatically
- Configures extended cache TTL for reference data
- Injects cache dependency
- Returns fully configured client instance

### Requirement: API Version Handling
The system SHALL handle D&D 5e API version management transparently, including redirects and version compatibility.

#### Scenario: Versioned endpoint access with redirects
When accessing D&D 5e API endpoints that use versioned URLs (`/api/2014/`), the client must handle version prefixes and redirects transparently without user intervention.

**Acceptance Criteria:**
- Handles automatic redirects from `/api/` to `/api/2014/` using httpx follow_redirects
- Base URL includes version prefix (`/api/2014/`) by default
- Maintains compatibility across API versions if new versions are released
- Provides version information in response metadata or logging
- Handles deprecated endpoints gracefully with clear error messages

### Requirement: Reference Data Caching Strategy
The system SHALL implement appropriate caching strategies for reference data that changes infrequently but is accessed often.

#### Scenario: Long-lived reference data cache
When accessing static reference data (damage types, skills, ability scores) that never changes, the client must use extended cache TTL to minimize API calls and enable offline capability.

**Acceptance Criteria:**
- Extended TTL for reference data (30 days = 2,592,000 seconds vs 7 days for dynamic content)
- Standard cache TTL for rules and rule sections (7 days = 604,800 seconds)
- Entity cache integration for all data types
- Efficient cache invalidation using timestamp comparison for reference updates
- Offline capability for essential reference information when cached
- Cache size management to prevent unbounded growth (reference data is ~200 items total)
