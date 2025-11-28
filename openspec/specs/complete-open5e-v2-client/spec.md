# complete-open5e-v2-client Specification

## Purpose
Defines the complete Open5e v2 API client implementation for fetching D&D 5e content from the modern v2 endpoints. The v2 client provides access to spells, weapons, armor, backgrounds, feats, conditions, creatures, items, character options, rules, and reference data from the Open5e API using the enhanced v2 API structure with richer data and additional filtering capabilities.

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

### Requirement: Client-Side School Filtering
The `get_spells` method in `Open5eV2Client` SHALL implement client-side filtering for the `school` parameter when the Open5e v2 API doesn't support server-side filtering.

**Rationale**: The Open5e v2 API does not support filtering spells by school parameter on the server side. However, the LoreKeeper tool interface advertises this capability, so client-side filtering must be implemented to maintain expected functionality.

**Acceptance Criteria:**
- Method makes API request without `school` parameter
- Client filters results to only include spells with matching school
- School filtering is case-insensitive
- Returns empty list for non-existent schools (no exceptions)
- School filtering works with all other filter parameters (level, concentration, etc.)
- Multiple calls with same school filter leverage cached data

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

### Requirement: Weapon Model Field Structure
The `Weapon` model SHALL accurately reflect the actual structure and field types returned by the Open5e API v2 weapons endpoint.

**Rationale**: The model must match the actual API response structure to prevent Pydantic validation errors when parsing weapon data.

**Acceptance Criteria:**
- Model includes only fields present in API responses (name, damage_dice, damage_type, weight, cost)
- Handles both dict and list[dict] damage_type formats
- Optional fields include: properties, range_normal, range_long, versatile_dice, weapon_range, throw_range
- Non-existent fields (like `category`) are not included in the model
- All sample weapon responses from Open5e API v2 validate successfully

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

### Requirement: Open5e v2 Items and Equipment Endpoints
The system SHALL provide client methods for item-related endpoints including general items, item sets, and item categories.

#### Scenario: Fetch general items from v2 API
When a user needs non-weapon/non-armor item data, the client should fetch from the `/v2/items/` endpoint.

**Acceptance Criteria:**
- `get_items()` method supports name, category, and rarity filtering
- Parses item properties, costs, and weights
- Returns structured item data distinct from weapons and armor
- Handles pagination for large result sets
- Uses entity cache with 7-day TTL

#### Scenario: Fetch item sets and collections
When a user needs grouped items (e.g., artisan's tools, gaming sets), the client should fetch from `/v2/itemsets/`.

**Acceptance Criteria:**
- `get_item_sets()` method supports name filtering
- Returns collections of related items
- Includes set membership and relationships
- Uses entity cache with 7-day TTL

#### Scenario: Fetch item categories
When browsing item taxonomy, the client should fetch from `/v2/itemcategories/`.

**Acceptance Criteria:**
- `get_item_categories()` method returns category hierarchy
- Supports filtering by parent category
- Returns category descriptions and member counts
- Uses extended cache TTL (30 days - reference data)

### Requirement: Open5e v2 Creature Endpoints
The system SHALL provide client methods for v2 creature endpoints which offer enhanced data compared to v1.

#### Scenario: Fetch creatures from v2 API
When a user needs enhanced creature data with v2 improvements, the client should fetch from `/v2/creatures/`.

**Acceptance Criteria:**
- `get_creatures()` method supports CR, type, size, and environment filtering
- Returns Monster model instances (compatible with v1)
- Includes enhanced v2 fields (gamesystem, publisher, permalinks)
- Handles pagination for 1000+ creatures
- Uses entity cache with 7-day TTL

#### Scenario: Fetch creature types taxonomy
When browsing creature categories, the client should fetch from `/v2/creaturetypes/`.

**Acceptance Criteria:**
- `get_creature_types()` method returns type taxonomy
- Includes type descriptions and example creatures
- Uses extended cache TTL (30 days - reference data)

#### Scenario: Fetch creature sets
When accessing grouped creatures (e.g., published bestiaries), the client should fetch from `/v2/creaturesets/`.

**Acceptance Criteria:**
- `get_creature_sets()` method supports filtering by document
- Returns creature collection metadata
- Includes set membership information
- Uses entity cache with 7-day TTL

### Requirement: Open5e v2 Reference Data Endpoints
The system SHALL provide client methods for reference data including damage types, languages, alignments, schools, sizes, rarities, environments, abilities, and skills.

#### Scenario: Fetch reference data collections
When a user needs reference lookup tables, the client should fetch from reference endpoints.

**Acceptance Criteria:**
- `get_damage_types_v2()` method fetches damage type reference (distinct from dnd5e client)
- `get_languages_v2()` method fetches language reference (distinct from dnd5e client)
- `get_alignments_v2()` method fetches alignment reference
- `get_spell_schools_v2()` method fetches school reference
- `get_sizes()` method fetches size category reference
- `get_item_rarities()` method fetches rarity reference
- `get_environments()` method fetches environment types
- `get_abilities()` method fetches ability score reference
- `get_skills_v2()` method fetches skill reference (distinct from dnd5e client)
- All reference methods use extended cache TTL (30 days)
- All methods use entity cache

### Requirement: Open5e v2 Character Options Endpoints
The system SHALL provide client methods for v2 character creation endpoints including species and classes.

#### Scenario: Fetch species (races) from v2 API
When a user needs character species data with v2 enhancements, the client should fetch from `/v2/species/`.

**Acceptance Criteria:**
- `get_species()` method supports name and document filtering
- Returns species data with traits and abilities
- Includes v2 enhancements (subraces, variants)
- Uses entity cache with 7-day TTL

#### Scenario: Fetch classes from v2 API
When a user needs class data with v2 enhancements, the client should fetch from `/v2/classes/`.

**Acceptance Criteria:**
- `get_classes_v2()` method supports name filtering (distinct from v1 method)
- Returns class features, proficiencies, and progression
- Includes subclass information
- Uses entity cache with 7-day TTL

### Requirement: Open5e v2 Rules and Metadata Endpoints
The system SHALL provide client methods for rules, rulesets, documents, licenses, publishers, and game system metadata.

#### Scenario: Fetch game rules from v2 API
When a user needs rules data, the client should fetch from `/v2/rules/`.

**Acceptance Criteria:**
- `get_rules_v2()` method supports name and ruleset filtering (distinct from dnd5e client)
- Returns rule descriptions and mechanics
- Includes cross-references to related rules
- Uses entity cache with 7-day TTL

#### Scenario: Fetch rulesets and collections
When browsing rule collections, the client should fetch from `/v2/rulesets/`.

**Acceptance Criteria:**
- `get_rulesets()` method returns ruleset collections
- Includes ruleset metadata and membership
- Uses extended cache TTL (30 days - reference data)

#### Scenario: Fetch source documents
When checking source material, the client should fetch from `/v2/documents/`.

**Acceptance Criteria:**
- `get_documents()` method returns document metadata
- Includes publisher, license, and version information
- Uses extended cache TTL (30 days - reference data)

#### Scenario: Fetch license and publisher information
When checking licensing and attribution, the client should fetch from `/v2/licenses/` and `/v2/publishers/`.

**Acceptance Criteria:**
- `get_licenses()` method returns license details
- `get_publishers()` method returns publisher information
- Both use extended cache TTL (30 days - reference data)

#### Scenario: Fetch game system metadata
When checking API version and game system info, the client should fetch from `/v2/gamesystems/`.

**Acceptance Criteria:**
- `get_game_systems()` method returns system metadata
- Includes version and compatibility information
- Uses extended cache TTL (30 days - reference data)

### Requirement: Open5e v2 Additional Content Endpoints
The system SHALL provide client methods for images, weapon properties, and services.

#### Scenario: Fetch image assets
When accessing artwork and visual assets, the client should fetch from `/v2/images/`.

**Acceptance Criteria:**
- `get_images()` method supports filtering by related entity
- Returns image URLs and metadata
- Includes attribution and license information
- Uses entity cache with 7-day TTL

#### Scenario: Fetch weapon properties reference
When looking up weapon property definitions, the client should fetch from `/v2/weaponproperties/`.

**Acceptance Criteria:**
- `get_weapon_properties_v2()` method returns property definitions (distinct from dnd5e client)
- Includes mechanical effects and descriptions
- Uses extended cache TTL (30 days - reference data)

#### Scenario: Fetch services and hirelings
When looking up available services, the client should fetch from `/v2/services/`.

**Acceptance Criteria:**
- `get_services()` method supports name and cost filtering
- Returns service descriptions and costs
- Uses entity cache with 7-day TTL

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
