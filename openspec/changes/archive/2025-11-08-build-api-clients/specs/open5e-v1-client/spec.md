# Open5e v1 API Client Specification

## ADDED Requirements

### Requirement: Open5e v1 Monsters API Client
The system SHALL provide an Open5e v1 client method to fetch monster data from the `/v1/monsters/` endpoint with filtering capabilities for the `lookup_creature` tool.

#### Scenario:
When a user searches for creatures or monsters using the `lookup_creature` tool, the Open5e v1 client should fetch monster data from the `/v1/monsters/` endpoint with filtering capabilities.

**Acceptance Criteria:**
- `get_monsters()` method supports name, CR, type, size filtering
- Handles pagination for large result sets
- Parses monster stat blocks including abilities, actions, traits
- Supports CR range searches (cr_min, cr_max)
- Returns structured monster data with consistent field names
- Handles missing or malformed monster data gracefully

### Requirement: Open5e v1 Classes API Client
The system SHALL provide an Open5e v1 client method to fetch class data from the `/v1/classes/` endpoint with filtering capabilities for the `lookup_character_option` tool.

#### Scenario:
When a user searches for character class information using the `lookup_character_option` tool, the Open5e v1 client should fetch class data from `/v1/classes/` endpoint.

**Acceptance Criteria:**
- `get_classes()` method supports name filtering
- Fetches class features, subclasses, and progression tables
- Parses class proficiencies and spellcasting information
- Returns structured class data with nested features
- Handles classes without subclasses gracefully

### Requirement: Open5e v1 Races API Client
The system SHALL provide an Open5e v1 client method to fetch race data from the `/v1/races/` endpoint with filtering capabilities for the `lookup_character_option` tool.

#### Scenario:
When a user searches for character race information using the `lookup_character_option` tool, the Open5e v1 client should fetch race data from `/v1/races/` endpoint.

**Acceptance Criteria:**
- `get_races()` method supports name filtering
- Fetches racial traits, ability score increases, and subraces
- Parses speed, languages, and special abilities
- Returns structured race data with nested traits
- Handles races without subraces gracefully

### Requirement: Open5e v1 Magic Items API Client
The system SHALL provide an Open5e v1 client method to fetch magic item data from the `/v1/magicitems/` endpoint with filtering capabilities for the `lookup_equipment` tool.

#### Scenario:
When a user searches for magic items using the `lookup_equipment` tool, the Open5e v1 client should fetch magic item data from `/v1/magicitems/` endpoint.

**Acceptance Criteria:**
- `get_magic_items()` method supports name and rarity filtering
- Fetches item descriptions, effects, and attunement requirements
- Parses item types and properties
- Returns structured magic item data
- Handles items with complex descriptions gracefully

### Requirement: Open5e v1 Client Factory
The system SHALL provide a factory method to create properly configured Open5e v1 client instances with dependency injection support.

#### Scenario:
When the application needs to create an Open5e v1 client instance, it should use a factory that provides proper configuration and dependency injection.

**Acceptance Criteria:**
- `ClientFactory.create_open5e_v1()` method exists
- Configures base URL, timeouts, and retry logic
- Injects cache dependency
- Returns fully configured client instance
- Supports custom configuration when needed

## ADDED Requirements

### Requirement: Response Data Normalization
The system SHALL normalize Open5e v1 API response data to match standardized response models used across all API clients.

#### Scenario: API response normalization
When Open5e v1 returns data with varying field names and structures, the client must normalize to standardized Pydantic models ensuring consistency across API versions.

**Acceptance Criteria:**
- Converts snake_case field names to consistent camelCase or snake_case per project convention
- Handles missing fields with sensible defaults (empty strings, empty arrays, None values)
- Normalizes nested object structures (actions, traits, subclasses) to consistent format
- Preserves all relevant data from API response without data loss
- Provides warnings for unexpected data structures or fields not in model schema
