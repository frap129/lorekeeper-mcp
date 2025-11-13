# Open5e API Endpoints and Filters Summary

This document provides a comprehensive overview of all available endpoints and their filtering capabilities in the Open5e API server.

## API Versioning

The API provides two main versions:
- **API v1**: Legacy endpoints (depreciating)
- **API v2**: Current structured endpoints (recommended)
- **Search**: Unified search across all content

## API Documentation

- **Swagger UI**: `/schema/swagger-ui/`
- **ReDoc**: `/schema/redoc/`
- **OpenAPI Schema**: `/schema/`

---

## Creatures vs Monsters Terminology

### Open5e API Version Differences

**Open5e v1**: Used `/monsters/` endpoint (deprecated)
**Open5e v2**: Uses `/creatures/` endpoint (current)

### Key Changes
- **Endpoint**: `/v1/monsters/` → `/v2/creatures/`
- **Challenge Rating**: `cr` (string) → `challenge_rating_decimal` (float)
- **Filtering**: Basic filters → Advanced filter operators (`__gte`, `__lte`, etc.)

### LoreKeeper MCP Implementation
- **Database Table**: `creatures` (not `monsters`)
- **Repository**: `MonsterRepository` (name kept for compatibility)
- **API Client**: `Open5eV2Client.get_creatures()`
- **Parameter Mapping**: Repository handles v1→v2 parameter conversion

### Migration Notes
- Both terms refer to the same entity type (D&D monsters/creatures)
- v2 provides better filtering and more structured data
- LoreKeeper MCP automatically handles the terminology differences
- Existing code using `MonsterRepository` requires no changes

---

## API V2 Endpoints (Current)

### Core Content Endpoints

#### `/v2/spells/`
- **Description**: List and retrieve spells
- **Filters**:
  - `key`, `name` (exact, contains, icontains)
  - `document__key`, `document__gamesystem__key`
  - `classes__key`, `classes__name`
  - `level` (exact, range, gt, gte, lt, lte)
  - `range` (exact, range, gt, gte, lt, lte)
  - `school__key`, `school__name`
  - `duration`, `concentration`, `verbal`, `somatic`, `material`, `material_consumed`
  - `casting_time`

#### `/v2/creatures/`
- **Description**: List and retrieve creatures/monsters
- **Note**: Open5e v2 uses "creatures" terminology (v1 used "monsters")
- **Filters**:
  - `key`, `name` (exact, icontains)
  - `document__key`, `document__gamesystem__key`
  - `size`, `category`, `subcategory`, `type`
  - `challenge_rating_decimal` (exact, lt, lte, gt, gte)
  - `armor_class` (exact, lt, lte, gt, gte)
  - Ability scores: `ability_score_strength`, `ability_score_dexterity`, etc.
  - Saving throws: `saving_throw_strength`, `saving_throw_dexterity`, etc. (isnull)
  - Skills: `skill_bonus_acrobatics`, `skill_bonus_animal_handling`, etc. (isnull)
  - `passive_perception` (exact, lt, lte, gt, gte)

#### `/v2/items/`
- **Description**: List and retrieve items (weapons, armor, magic items)
- **Filters**:
  - `key`, `name` (exact, icontains)
  - `desc`, `cost`, `weight`
  - `cost`, `weight` (exact, range, gt, gte, lt, lte)
  - `rarity` (exact, in)
  - `requires_attunement`, `category`
  - `document__key`, `document__gamesystem__key`
  - Boolean filters:
    - `is_magic_item` - Magic items only
    - `is_weapon` - Weapons only
    - `is_armor` - Armor only
    - `is_light`, `is_versatile`, `is_thrown`, `is_finesse`, `is_two_handed`

#### `/v2/weapons/`
- **Description**: Dedicated weapons endpoint
- **Filters**:
  - `key`, `name`, `document__key`, `document__gamesystem__key`
  - `damage_dice`
  - Boolean weapon properties: `is_light`, `is_versatile`, `is_thrown`, `is_finesse`, `is_two_handed`

#### `/v2/armor/`
- **Description**: Dedicated armor endpoint
- **Filters**:
  - `key`, `name`, `document__key`, `document__gamesystem__key`
  - `grants_stealth_disadvantage`
  - `strength_score_required` (exact, lt, lte, gt, gte)
  - `ac_base` (exact, lt, lte, gt, gte)
  - `ac_add_dexmod`, `ac_cap_dexmod`

### Character Creation Endpoints

#### `/v2/backgrounds/`
- **Description**: Character backgrounds
- **Filters**: Standard key/name/document filters

#### `/v2/feats/`
- **Description**: Character feats
- **Filters**: Standard key/name/document filters

#### `/v2/species/`
- **Description**: Character species (races)
- **Filters**: Standard key/name/document filters

#### `/v2/classes/`
- **Description**: Character classes
- **Filters**: Standard key/name/document filters

### Reference Data Endpoints

#### `/v2/abilities/`
- **Description**: Ability scores (STR, DEX, CON, INT, WIS, CHA)
- **Filters**: Standard key/name/document filters

#### `/v2/skills/`
- **Description**: Skills (Acrobatics, Athletics, etc.)
- **Filters**: Standard key/name/document filters

#### `/v2/sizes/`
- **Description**: Creature sizes (Tiny, Small, Medium, etc.)
- **Filters**: Standard key/name/document filters

#### `/v2/alignments/`
- **Description**: Character alignments
- **Filters**: Standard key/name/document filters

#### `/v2/conditions/`
- **Description**: Status conditions (Blinded, Charmed, etc.)
- **Filters**: Standard key/name/document filters

#### `/v2/damagetypes/`
- **Description**: Damage types (Fire, Cold, etc.)
- **Filters**: Standard key/name/document filters

#### `/v2/languages/`
- **Description**: Languages
- **Filters**: Standard key/name/document filters

#### `/v2/environments/`
- **Description**: Creature environments
- **Filters**: Standard key/name/document filters

### Specialized Endpoints

#### `/v2/rules/`
- **Description**: Game rules
- **Filters**: Standard key/name/document filters

#### `/v2/rulesets/`
- **Description**: Rule collections
- **Filters**: Standard key/name/document filters

#### `/v2/images/`
- **Description**: Image references
- **Filters**: Standard key/name/document filters

#### `/v2/services/`
- **Description**: Services (tavern, inn, etc.)
- **Filters**: Standard key/name/document filters

### Collections and Categories

#### `/v2/itemcategories/`
- **Description**: Item categories
- **Filters**: Standard key/name/document filters

#### `/v2/itemsets/`
- **Description**: Item collections/sets
- **Filters**: Standard key/name/document filters

#### `/v2/itemrarities/`
- **Description**: Item rarity levels
- **Filters**: None (list all)

#### `/v2/creaturesets/`
- **Description**: Creature collections/sets
- **Filters**: Standard key/name/document filters

#### `/v2/creaturetypes/`
- **Description**: Creature types
- **Filters**: Standard key/name/document filters

#### `/v2/spellschools/`
- **Description**: Magical schools
- **Filters**: Standard key/name/document filters

#### `/v2/weaponproperties/`
- **Description**: Weapon properties
- **Filters**: Standard key/name/document filters

### Metadata Endpoints

#### `/v2/documents/`
- **Description**: Source documents and books
- **Filters**: All fields (JSON-compatible)

#### `/v2/licenses/`
- **Description**: Content licenses
- **Filters**: All fields

#### `/v2/publishers/`
- **Description**: Content publishers
- **Filters**: All fields

#### `/v2/gamesystems/`
- **Description**: Game systems (D&D 5e, etc.)
- **Filters**: None (list all)

### Utility Endpoints

#### `/v2/enums/`
- **Description**: Available enumeration values
- **Method**: GET
- **Returns**: JSON of all enum options

---

## API V1 Endpoints (Legacy)

### Character Content
- `/spells/` - Spells with v1 format
- `/monsters/` - **Deprecated** - Use `/v2/creatures/` instead
- `/backgrounds/` - Backgrounds
- `/feats/` - Feats
- `/races/` - Races
- `/classes/` - Classes and archetypes
- `/conditions/` - Conditions

### Equipment
- `/magicitems/` - Magic items
- `/weapons/` - Weapons
- `/armor/` - Armor

### Reference
- `/spelllist/` - Spell lists
- `/planes/` - Planes of existence
- `/sections/` - Document sections
- `/documents/` - Source documents

### Utilities
- `/manifest/` - Data manifests for version checking
- `/version/` - API and data version information

### Common V1 Filters
All v1 endpoints support these common filters:
- `slug` (in, iexact, exact)
- `name` (iexact, exact, icontains)
- `desc` (iexact, exact, in, icontains)
- `document__slug` (iexact, exact, in)

Plus endpoint-specific filters for fields like:
- Spells: `level`, `school`, `casting_time`, `duration`, `components`, `concentration`
- Monsters: `cr`, `hit_points`, `armor_class`, `type`, `size`
- Items: `type`, `rarity`, `requires_attunement`

---

## Search Endpoint

### `/v2/search/`
- **Description**: Unified search across all Open5e content
- **Method**: GET
- **Parameters**:
  - `query` (required): Search term
  - `fuzzy` (bool): Enable fuzzy matching for typos (default: false)
  - `vector` (bool): Enable semantic similarity search (default: false)
  - `strict` (bool): Only return explicitly requested search types (default: false)
  - `object_model`: Filter to specific content type (Spell, Creature, Item, etc.)
  - `document_pk`: Filter to specific document
  - `schema`: API schema version (v1 or v2, default: v2)

### Search Behavior
- **Default mode**: Exact search with fuzzy fallback if no results
- **Strict mode**: Only return explicitly requested search types
- **Combined mode**: Multiple search types can be enabled together
- **Priority order**: Exact → Fuzzy → Vector (results merged and deduplicated)

---

## Universal Filter Operators

### Standard Filter Types
- `exact` - Exact match
- `iexact` - Case-insensitive exact match
- `contains` - Contains substring
- `icontains` - Case-insensitive contains
- `in` - In list of values
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal
- `range` - Within range
- `isnull` - Is null/empty

### Common Patterns
- Document filtering: `document__key`, `document__gamesystem__key`
- Name filtering: `name__icontains` for partial matches
- Numeric ranges: `field__gte`, `field__lte`
- Lists: `field__in=value1,value2,value3`

---

## Authentication

- Public API endpoints (no authentication required)
- Admin interface available at `/admin/` (DEBUG mode only)

## Response Format

All endpoints return JSON with standard structure:
- List endpoints return arrays of objects
- Detail endpoints return single objects
- Search includes metadata about match types
- Pagination support for large result sets

## Version Information

Current version information available at:
- `/version/` - Returns hash versions of API and data
- API supports both v1 and v2 simultaneously
- v2 is the recommended format for new development
