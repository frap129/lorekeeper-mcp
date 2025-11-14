# complete-open5e-v2-client Specification

## Purpose
TBD - created by archiving change implement-repository-pattern. Update Purpose after archive.
## Requirements
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
