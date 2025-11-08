# open5e-v2-client Specification

## Purpose
TBD - created by archiving change build-api-clients. Update Purpose after archive.
## Requirements
### Requirement: Open5e v2 Spells API Client
The system SHALL provide an Open5e v2 client method to fetch spell data from the `/v2/spells/` endpoint with comprehensive filtering capabilities for the `lookup_spell` tool.

#### Scenario:
When a user searches for spells using the `lookup_spell` tool, the Open5e v2 client should fetch spell data from the `/v2/spells/` endpoint with comprehensive filtering capabilities.

**Acceptance Criteria:**
- `get_spells()` method supports name, level, school, class, concentration, ritual, casting_time filtering
- Handles pagination for large result sets (1774+ spells available)
- Parses spell components, material costs, and damage information
- Extracts higher level effects and casting options
- Returns structured spell data with consistent field names
- Supports exact match and partial name searches

### Requirement: Open5e v2 Weapons API Client
The system SHALL provide an Open5e v2 client method to fetch weapon data from the `/v2/weapons/` endpoint with filtering capabilities for the `lookup_equipment` tool.

#### Scenario:
When a user searches for weapons using the `lookup_equipment` tool, the Open5e v2 client should fetch weapon data from `/v2/weapons/` endpoint.

**Acceptance Criteria:**
- `get_weapons()` method supports name, damage_dice, and property filtering
- Parses weapon properties (light, versatile, thrown, finesse, two-handed)
- Extracts damage types and range information
- Distinguishes between simple and martial weapons
- Returns structured weapon data with property details
- Handles mastery properties and special abilities

### Requirement: Open5e v2 Armor API Client
The system SHALL provide an Open5e v2 client method to fetch armor data from the `/v2/armor/` endpoint with filtering capabilities for the `lookup_equipment` tool.

#### Scenario:
When a user searches for armor using the `lookup_equipment` tool, the Open5e v2 client should fetch armor data from `/v2/armor/` endpoint.

**Acceptance Criteria:**
- `get_armor()` method supports name filtering
- Parses armor class values and type categories
- Extracts strength requirements and stealth penalties
- Returns structured armor data with weight and cost information
- Handles shields and armor categories consistently

### Requirement: Open5e v2 Backgrounds API Client
The system SHALL provide an Open5e v2 client method to fetch background data from the `/v2/backgrounds/` endpoint with filtering capabilities for the `lookup_character_option` tool.

#### Scenario:
When a user searches for character backgrounds using the `lookup_character_option` tool, the Open5e v2 client should fetch background data from `/v2/backgrounds/` endpoint.

**Acceptance Criteria:**
- `get_backgrounds()` method supports name filtering
- Fetches skill proficiencies, tool proficiencies, and languages
- Parses equipment packages and special features
- Returns structured background data with suggested characteristics
- Handles background variations and custom options

### Requirement: Open5e v2 Feats API Client
The system SHALL provide an Open5e v2 client method to fetch feat data from the `/v2/feats/` endpoint with filtering capabilities for the `lookup_character_option` tool.

#### Scenario:
When a user searches for feats using the `lookup_character_option` tool, the Open5e v2 client should fetch feat data from `/v2/feats/` endpoint.

**Acceptance Criteria:**
- `get_feats()` method supports name filtering
- Parses feat prerequisites and benefits
- Extracts feat types and ability score requirements
- Returns structured feat data with detailed descriptions
- Handles complex feat interactions and prerequisites

### Requirement: Open5e v2 Conditions API Client
The system SHALL provide an Open5e v2 client method to fetch condition data from the `/v2/conditions/` endpoint with filtering capabilities for the `lookup_rule` tool.

#### Scenario:
When a user searches for conditions using the `lookup_rule` tool, the Open5e v2 client should fetch condition data from `/v2/conditions/` endpoint.

**Acceptance Criteria:**
- `get_conditions()` method supports name filtering
- Parses condition descriptions and mechanical effects
- Returns structured condition data with game impact
- Handles condition interactions and removal criteria

### Requirement: Open5e v2 Client Factory
The system SHALL provide a factory method to create properly configured Open5e v2 client instances with dependency injection support.

#### Scenario:
When the application needs to create an Open5e v2 client instance, it should use a factory that provides proper configuration and dependency injection.

**Acceptance Criteria:**
- `ClientFactory.create_open5e_v2()` method exists
- Configures base URL, timeouts, and retry logic
- Injects cache dependency
- Returns fully configured client instance
- Supports custom configuration when needed

### Requirement: Advanced Search Capabilities
The system SHALL provide advanced search capabilities that leverage Open5e v2's sophisticated filtering options while maintaining a simple interface.

#### Scenario: Multi-criteria spell search
When a user searches for spells with multiple criteria (e.g., 3rd level evocation wizard spells requiring concentration), the client must support combining multiple filters efficiently.

**Acceptance Criteria:**
- Supports multiple simultaneous filters (level + school + class + concentration + ritual)
- Handles complex search queries efficiently with query parameter combination
- Provides relevance ranking for partial name matches (fuzzy search)
- Supports exact match mode when name matches exactly
- Returns search metadata (total count from API, pagination next/previous URLs)

### Requirement: Response Data Normalization
The system SHALL normalize Open5e v2 API response data to match standardized response models used across all API clients.

#### Scenario: v2 response structure normalization
When Open5e v2 returns data with document metadata and nested references different from v1, the client must normalize to standardized Pydantic models for tool consistency.

**Acceptance Criteria:**
- Maps v2 document structure (document.name, document.key, document.publisher) to consistent format
- Handles new fields introduced in v2 (casting_options array, mastery properties for weapons)
- Normalizes nested object references (school.name, damage_type.name) to simple strings or structured objects
- Preserves enhanced v2 data (gamesystem, permalink, publisher) while maintaining compatibility
- Provides clear field mapping documentation for v1 vs v2 differences
