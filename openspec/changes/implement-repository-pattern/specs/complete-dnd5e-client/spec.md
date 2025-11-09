# complete-dnd5e-client Specification

## Purpose
Complete the D&D 5e API client by implementing all available endpoints from the official API, providing comprehensive coverage for character options, equipment, spells, and monsters.

## ADDED Requirements

### Requirement: D&D 5e API Character Options Endpoints
The system SHALL provide client methods for character creation endpoints including backgrounds, classes, subclasses, races, subraces, and feats.

#### Scenario: Fetch backgrounds from D&D 5e API
When a user needs background data, the client should fetch from `/api/2014/backgrounds/`.

**Acceptance Criteria:**
- `get_backgrounds_dnd5e()` method supports name/index filtering
- Returns background features, proficiencies, and equipment
- Parses personality traits and ideals
- Uses entity cache with 7-day TTL
- Distinct method name from Open5e v2 client

#### Scenario: Fetch classes from D&D 5e API
When a user needs class data, the client should fetch from `/api/2014/classes/`.

**Acceptance Criteria:**
- `get_classes_dnd5e()` method supports name/index filtering (distinct from Open5e clients)
- Returns hit dice, proficiencies, and equipment choices
- Includes class feature references
- Uses entity cache with 7-day TTL

#### Scenario: Fetch subclasses
When a user needs subclass information, the client should fetch from `/api/2014/subclasses/`.

**Acceptance Criteria:**
- `get_subclasses()` method supports class and name filtering
- Returns subclass features and progression
- Includes parent class reference
- Uses entity cache with 7-day TTL

#### Scenario: Fetch races from D&D 5e API
When a user needs race data, the client should fetch from `/api/2014/races/`.

**Acceptance Criteria:**
- `get_races_dnd5e()` method supports name/index filtering (distinct from Open5e v1 client)
- Returns ability bonuses, traits, and proficiencies
- Includes size and speed information
- Uses entity cache with 7-day TTL

#### Scenario: Fetch subraces
When a user needs subrace information, the client should fetch from `/api/2014/subraces/`.

**Acceptance Criteria:**
- `get_subraces()` method supports race and name filtering
- Returns subrace traits and ability score increases
- Includes parent race reference
- Uses entity cache with 7-day TTL

#### Scenario: Fetch feats from D&D 5e API
When a user needs feat data, the client should fetch from `/api/2014/feats/`.

**Acceptance Criteria:**
- `get_feats_dnd5e()` method supports name filtering (distinct from Open5e v2 client)
- Returns prerequisites and benefits
- Parses ability score increases
- Uses entity cache with 7-day TTL

#### Scenario: Fetch racial traits
When a user needs specific trait details, the client should fetch from `/api/2014/traits/`.

**Acceptance Criteria:**
- `get_traits()` method supports race filtering
- Returns trait descriptions and mechanics
- Includes prerequisites and choices
- Uses entity cache with 7-day TTL

### Requirement: D&D 5e API Equipment Endpoints
The system SHALL provide client methods for equipment, equipment categories, and magic items.

#### Scenario: Fetch equipment from D&D 5e API
When a user needs general equipment data, the client should fetch from `/api/2014/equipment/`.

**Acceptance Criteria:**
- `get_equipment()` method supports name and category filtering
- Returns cost, weight, and properties
- Handles weapons, armor, gear, and tools
- Uses entity cache with 7-day TTL

#### Scenario: Fetch equipment categories
When browsing equipment taxonomy, the client should fetch from `/api/2014/equipment-categories/`.

**Acceptance Criteria:**
- `get_equipment_categories()` method returns category hierarchy
- Includes category descriptions and member lists
- Uses extended cache TTL (30 days - reference data)

#### Scenario: Fetch magic items from D&D 5e API
When a user needs magic item data, the client should fetch from `/api/2014/magic-items/`.

**Acceptance Criteria:**
- `get_magic_items_dnd5e()` method supports name and rarity filtering (distinct from Open5e v1)
- Returns attunement requirements and effects
- Parses item descriptions and lore
- Uses entity cache with 7-day TTL

### Requirement: D&D 5e API Spells and Magic Endpoints
The system SHALL provide client methods for spells and spell details.

#### Scenario: Fetch spells from D&D 5e API
When a user needs spell data, the client should fetch from `/api/2014/spells/`.

**Acceptance Criteria:**
- `get_spells_dnd5e()` method supports level, school, and class filtering (distinct from Open5e v2 client)
- Returns components, duration, and range
- Parses damage, healing, and conditions
- Includes higher level effects
- Uses entity cache with 7-day TTL

### Requirement: D&D 5e API Monster Endpoints
The system SHALL provide client methods for monster stat blocks.

#### Scenario: Fetch monsters from D&D 5e API
When a user needs monster data, the client should fetch from `/api/2014/monsters/`.

**Acceptance Criteria:**
- `get_monsters_dnd5e()` method supports CR, type, and name filtering (distinct from Open5e clients)
- Returns complete stat blocks with abilities
- Parses actions, reactions, and legendary actions
- Returns Monster model instances (compatible with Open5e clients)
- Uses entity cache with 7-day TTL

### Requirement: D&D 5e API Conditions Endpoint
The system SHALL provide client method for game conditions.

#### Scenario: Fetch conditions from D&D 5e API
When a user needs condition mechanics, the client should fetch from `/api/2014/conditions/`.

**Acceptance Criteria:**
- `get_conditions_dnd5e()` method supports name filtering (distinct from Open5e v2 client)
- Returns condition descriptions and effects
- Parses mechanical impacts
- Uses entity cache with 7-day TTL

### Requirement: D&D 5e API Features Endpoint
The system SHALL provide client method for class and race features.

#### Scenario: Fetch features from D&D 5e API
When a user needs feature details, the client should fetch from `/api/2014/features/`.

**Acceptance Criteria:**
- `get_features()` method supports class, level, and name filtering
- Returns feature descriptions and mechanics
- Includes prerequisites and choices
- Parses feature references and cross-links
- Uses entity cache with 7-day TTL
