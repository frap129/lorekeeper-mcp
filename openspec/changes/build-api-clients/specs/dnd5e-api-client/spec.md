# D&D 5e API Client Specification

## ADDED Requirements

### Requirement: D&D 5e Rules API Client
The system SHALL provide a D&D 5e API client method to fetch rule data from the `/2014/rules/` and `/2014/rule-sections/` endpoints for the `lookup_rule` tool.

#### Scenario:
When a user searches for game rules using the `lookup_rule` tool, the D&D 5e API client should fetch rule data from the `/2014/rules/` and `/2014/rule-sections/` endpoints.

**Acceptance Criteria:**
- `get_rules()` method supports section and name filtering
- Fetches rule categories: adventuring, combat, equipment, spellcasting, using-ability-scores, appendix
- Parses rule subsections and detailed mechanics
- Returns structured rule data with hierarchical organization
- Supports browsing rules by section or searching by name

### Requirement: D&D 5e Rule Sections API Client
The system SHALL provide a D&D 5e API client method to fetch detailed rule section data for specific rule mechanics and examples.

#### Scenario:
When a user needs detailed information about specific rule sections (like opportunity attacks or grappled condition mechanics), the client should fetch detailed rule section data.

**Acceptance Criteria:**
- `get_rule_sections()` method supports name filtering
- Fetches detailed rule mechanics and examples
- Parses cross-references to related rules
- Returns structured rule section data with full descriptions
- Handles nested rule structures and references

### Requirement: D&D 5e Reference Data API Client
The system SHALL provide a D&D 5e API client method to fetch reference data from various endpoints for the `lookup_rule` tool.

#### Scenario:
When a user searches for reference information like damage types, weapon properties, skills, or ability scores using the `lookup_rule` tool, the client should fetch reference data from various endpoints.

**Acceptance Criteria:**
- `get_damage_types()` method fetches all damage type descriptions
- `get_weapon_properties()` method fetches weapon property explanations
- `get_skills()` method fetches skill descriptions and ability associations
- `get_ability_scores()` method fetches ability score explanations
- `get_magic_schools()` method fetches magic school descriptions
- `get_languages()` method fetches language types and examples
- `get_proficiencies()` method fetches proficiency categories
- `get_alignments()` method fetches alignment descriptions

### Requirement: D&D 5e API Client Factory
The system SHALL provide a factory method to create properly configured D&D 5e API client instances with dependency injection support.

#### Scenario:
When the application needs to create a D&D 5e API client instance, it should use a factory that provides proper configuration and dependency injection.

**Acceptance Criteria:**
- `ClientFactory.create_dnd5e_api()` method exists
- Configures base URL for 2014 API version
- Handles API redirects and version management
- Injects cache dependency
- Returns fully configured client instance

## ADDED Requirements

### Requirement: API Version Handling
The system SHALL handle D&D 5e API version management transparently, including redirects and version compatibility.

#### Scenario: Versioned endpoint access
When accessing D&D 5e API endpoints that use versioned URLs (/api/2014/), the client must handle version prefixes and redirects transparently without user intervention.

**Acceptance Criteria:**
- Handles automatic redirects from `/api/` to `/api/2014/` using httpx follow_redirects
- Configurable API version parameter (default: "2014") with fallback to latest stable
- Maintains compatibility across API versions if new versions are released
- Provides version information in response metadata or logging
- Handles deprecated endpoints gracefully with clear error messages

### Requirement: Rules Data Integration
The system SHALL integrate D&D 5e API rules data seamlessly with the existing Open5e content ecosystem.

#### Scenario: Cross-API rule references
When D&D 5e API provides rules data (e.g., combat rules) that reference game mechanics also available in Open5e (e.g., conditions), the client must integrate seamlessly with normalized data models.

**Acceptance Criteria:**
- Normalizes rule data to match project Pydantic Rule models
- Cross-references rules with Open5e content where applicable (e.g., conditions)
- Provides consistent error handling across API boundaries (same exception types)
- Supports combined searches across multiple APIs in tool implementations
- Maintains source attribution for rule content (document__title, document__license_url equivalent)

### Requirement: Reference Data Caching Strategy
The system SHALL implement appropriate caching strategies for reference data that changes infrequently but is accessed often.

#### Scenario: Long-lived reference data cache
When accessing static reference data (damage types, skills, ability scores) that never changes, the client must use extended cache TTL to minimize API calls and enable offline capability.

**Acceptance Criteria:**
- Extended TTL for reference data (30 days = 2,592,000 seconds vs 7 days for dynamic content)
- Cache warming on first request for commonly accessed reference data (damage types, skills)
- Efficient cache invalidation using timestamp comparison for reference updates
- Offline capability for essential reference information (all reference data pre-cached)
- Cache size management to prevent unbounded growth (reference data is ~200 items total)
