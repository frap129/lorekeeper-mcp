# D&D 5e SRD API - Complete Endpoint and Filter Reference

## Overview

This document provides a comprehensive reference for all endpoints, routes, filters, and features available in the D&D 5e SRD API. The API provides access to Dungeons & Dragons 5th Edition System Reference Document data in both REST and GraphQL formats.

## Base URL Structure

- **REST API**: `/api/{version}/{resource}`
- **GraphQL**: `/graphql/{version}`
- **Images**: `/api/images/*`
- **Documentation**: `/docs`

## API Versions

- **2014**: Original D&D 5e SRD (full feature set - 25 resource types)
- **2024**: Updated D&D 5e SRD (limited resources - 13 resource types)
- **Deprecated**: `/graphql` (defaults to 2014)

---

## REST API Endpoints

### 2014 API Version (`/api/2014/`)

#### Core Resources (Simple List/Show Pattern)

| Resource             | List Endpoint               | Show Endpoint                      | Description                                               |
| -------------------- | --------------------------- | ---------------------------------- | --------------------------------------------------------- |
| Ability Scores       | `GET /ability-scores`       | `GET /ability-scores/:index`       | Six core ability scores (STR, DEX, CON, INT, WIS, CHA)    |
| Alignments           | `GET /alignments`           | `GET /alignments/:index`           | Character alignments (Lawful Good, Chaotic Neutral, etc.) |
| Conditions           | `GET /conditions`           | `GET /conditions/:index`           | Status conditions (Blinded, Charmed, Deafened, etc.)      |
| Damage Types         | `GET /damage-types`         | `GET /damage-types/:index`         | Damage types (Fire, Cold, Lightning, etc.)                |
| Equipment Categories | `GET /equipment-categories` | `GET /equipment-categories/:index` | Equipment category classifications                        |
| Equipment            | `GET /equipment`            | `GET /equipment/:index`            | All equipment items (weapons, armor, tools, etc.)         |
| Feats                | `GET /feats`                | `GET /feats/:index`                | Character feats                                           |
| Features             | `GET /features`             | `GET /features/:index`             | Class and race features                                   |
| Languages            | `GET /languages`            | `GET /languages/:index`            | Available languages                                       |
| Magic Schools        | `GET /magic-schools`        | `GET /magic-schools/:index`        | Magic schools of spellcasting                             |
| Magic Items          | `GET /magic-items`          | `GET /magic-items/:index`          | Magic items                                               |
| Monsters             | `GET /monsters`             | `GET /monsters/:index`             | Monster stat blocks                                       |
| Proficiencies        | `GET /proficiencies`        | `GET /proficiencies/:index`        | Skill, weapon, armor, tool proficiencies                  |
| Races                | `GET /races`                | `GET /races/:index`                | Character races                                           |
| Rule Sections        | `GET /rule-sections`        | `GET /rule-sections/:index`        | Individual rule sections                                  |
| Rules                | `GET /rules`                | `GET /rules/:index`                | Rule collections and sub-sections                         |
| Skills               | `GET /skills`               | `GET /skills/:index`               | Character skills                                          |
| Subclasses           | `GET /subclasses`           | `GET /subclasses/:index`           | Class subclasses                                          |
| Subraces             | `GET /subraces`             | `GET /subraces/:index`             | Race subraces                                             |
| Traits               | `GET /traits`               | `GET /traits/:index`               | Racial and class traits                                   |
| Weapon Properties    | `GET /weapon-properties`    | `GET /weapon-properties/:index`    | Weapon properties (Finesse, Heavy, etc.)                  |

#### Complex Resources (Additional Endpoints)

**Classes** (`/api/2014/classes/`):

| Endpoint                                     | Description                                  |
| -------------------------------------------- | -------------------------------------------- |
| `GET /classes`                               | List all character classes                   |
| `GET /classes/:index`                        | Get specific class details                   |
| `GET /classes/:index/subclasses`             | Get subclasses available to this class       |
| `GET /classes/:index/starting-equipment`     | Get starting equipment for class             |
| `GET /classes/:index/spellcasting`           | Get spellcasting information for class       |
| `GET /classes/:index/spells`                 | Get spells available to class                |
| `GET /classes/:index/features`               | Get features for class                       |
| `GET /classes/:index/proficiencies`          | Get proficiencies for class                  |
| `GET /classes/:index/multi-classing`         | Get multi-classing requirements and benefits |
| `GET /classes/:index/levels`                 | Get all levels for class                     |
| `GET /classes/:index/levels/:level`          | Get specific level details                   |
| `GET /classes/:index/levels/:level/features` | Get features for specific level              |
| `GET /classes/:index/levels/:level/spells`   | Get spell slots for specific level           |

**Backgrounds** (`/api/2014/backgrounds/`):

| Endpoint                  | Description                     |
| ------------------------- | ------------------------------- |
| `GET /backgrounds`        | List all character backgrounds  |
| `GET /backgrounds/:index` | Get specific background details |

**Spells** (`/api/2014/spells/`):

| Endpoint             | Description                |
| -------------------- | -------------------------- |
| `GET /spells`        | List all spells            |
| `GET /spells/:index` | Get specific spell details |

### 2024 API Version (`/api/2024/`)

The 2024 version provides a reduced subset of resources with simple list/show endpoints only:

| Resource                  | List Endpoint                    | Show Endpoint                           |
| ------------------------- | -------------------------------- | --------------------------------------- |
| Ability Scores            | `GET /ability-scores`            | `GET /ability-scores/:index`            |
| Alignments                | `GET /alignments`                | `GET /alignments/:index`                |
| Conditions                | `GET /conditions`                | `GET /conditions/:index`                |
| Damage Types              | `GET /damage-types`              | `GET /damage-types/:index`              |
| Equipment Categories      | `GET /equipment-categories`      | `GET /equipment-categories/:index`      |
| Equipment                 | `GET /equipment`                 | `GET /equipment/:index`                 |
| Languages                 | `GET /languages`                 | `GET /languages/:index`                 |
| Magic Schools             | `GET /magic-schools`             | `GET /magic-schools/:index`             |
| Skills                    | `GET /skills`                    | `GET /skills/:index`                    |
| Weapon Mastery Properties | `GET /weapon-mastery-properties` | `GET /weapon-mastery-properties/:index` |
| Weapon Properties         | `GET /weapon-properties`         | `GET /weapon-properties/:index`         |

### Image Endpoints

| Endpoint                 | Description                   |
| ------------------------ | ----------------------------- |
| `GET /api/images/*splat` | Serve static images and icons |

---

## Query Parameters and Filters

### Universal Filters (Available on all list endpoints)

| Parameter | Type   | Description                          | Example                                             |
| --------- | ------ | ------------------------------------ | --------------------------------------------------- |
| `name`    | string | Case-insensitive partial name search | `?name=fire` matches "Fire Ball", "Fire Resistance" |

### Resource-Specific Filters (2014 API only)

#### Spells

| Parameter | Type             | Description               | Example                                            |
| --------- | ---------------- | ------------------------- | -------------------------------------------------- |
| `level`   | string\|string[] | Filter by spell level(s)  | `?level=1`, `?level=1,2,3`, `?level[]=1&level[]=2` |
| `school`  | string\|string[] | Filter by magic school(s) | `?school=evocation`, `?school=evocation,illusion`  |

#### Classes

| Parameter  | Type   | Description                     | Example                   |
| ---------- | ------ | ------------------------------- | ------------------------- |
| `subclass` | string | Filter class levels by subclass | `?subclass=battle-master` |

#### Monsters

| Parameter          | Type             | Description                | Example                                          |
| ------------------ | ---------------- | -------------------------- | ------------------------------------------------ |
| `challenge_rating` | string\|string[] | Filter by challenge rating | `?challenge_rating=1`, `?challenge_rating=1,2,3` |

---

## GraphQL Endpoints

### 2014 GraphQL (`/graphql/2014/`)

The 2014 GraphQL endpoint provides access to all 25 resource types with advanced filtering capabilities.

**Available Queries:**

- `spells` - List spells with extensive filtering
- `spell(index: String)` - Get single spell by index
- `classes` - List classes with filtering
- `class(index: String)` - Get single class by index
- `monsters` - List monsters
- `monster(index: String)` - Get single monster by index
- Plus all other 2014 resources (ability scores, equipment, backgrounds, feats, etc.)

**Advanced Filtering Parameters (GraphQL):**

**Spells:**

- `name` - String filter
- `level` - Int or Int[] filter
- `school` - String filter
- `class` - String filter
- `subclass` - String filter
- `concentration` - Boolean filter
- `ritual` - Boolean filter
- `attack_type` - String filter
- `casting_time` - String filter
- `area_of_effect` - Filter by type and size
- `damage_type` - String filter
- `dc_type` - String filter
- `range` - String filter

**Classes:**

- `name` - String filter
- `hit_die` - Int filter

**Universal:**

- `order` - Sort order
- `skip` - Pagination offset
- `limit` - Pagination limit

### 2024 GraphQL (`/graphql/2024/`)

The 2024 GraphQL endpoint provides access to the reduced 13 resource set:

**Available Queries:**

- Ability scores, alignments, conditions, damage types
- Equipment, equipment categories, languages
- Magic schools, skills
- Weapon mastery properties, weapon properties

---

## Special Features

### Response Format

- **List endpoints**: Return `{count: number, results: array}` format
- **Single item**: Return full object with all fields
- **Error handling**: JSON error responses with validation details

### Caching

- Redis caching implemented for spells and monsters (2014 version)
- Cache keys based on original request URL
- Improves response times for frequently accessed data

### Rate Limiting

- Configurable rate limiting (default: 50 requests per second)
- Response message: `Rate limit exceeded, try again later`

### CORS Support

- All CORS requests enabled
- GraphQL endpoints include CORS middleware
- Supports cross-origin requests from web applications

### Validation

- Zod schema validation for all path and query parameters
- Detailed error responses for invalid parameters
- Type-safe parameter handling

### Index Fields

- Most resources have an `index` field for URL lookup
- Examples: "wizard", "fire-bolt", "longsword", "acolyte"
- Human-readable, URL-friendly identifiers

---

## Version Differences Summary

### 2014 Version

- **25 resource types** with full data
- Complex class relationships (levels, spells, features, proficiencies, multi-classing)
- Advanced filtering on spells, monsters, and classes
- Complete GraphQL implementation with all resources
- Backgrounds, feats, magic items, monsters, races, rules, subclasses, subraces, traits

### 2024 Version

- **13 resource types** (reduced set)
- Simple list/show pattern only
- No complex relationships or nested data
- Missing: backgrounds, classes, feats, magic items, monsters, races, rules, subclasses, subraces, traits
- Limited GraphQL implementation

---

## Usage Examples

### REST API Examples

```bash
# List all spells
GET /api/2014/spells

# Get fire bolt spell
GET /api/2014/spells/fire-bolt

# Search for spells with "fire" in name
GET /api/2014/spells?name=fire

# Filter 1st level evocation spells
GET /api/2014/spells?level=1&school=evocation

# Get wizard class details
GET /api/2014/classes/wizard

# Get wizard level 3 features
GET /api/2014/classes/wizard/levels/3/features

# List monsters with CR 1-3
GET /api/2014/monsters?challenge_rating=1,2,3
```

### GraphQL Examples

```graphql
# Get 1st level evocation spells
query {
  spells(level: 1, school: "evocation", limit: 10) {
    name
    level
    school {
      name
    }
    casting_time
    range
    components
    duration
    description
  }
}

# Get wizard class with all subclasses
query {
  class(index: "wizard") {
    name
    hit_die
    subclasses {
      name
      subclass_flavor
    }
  }
}
```

---

## Error Handling

The API returns standardized error responses:

```json
{
  "error": "Resource not found",
  "message": "The requested resource could not be found",
  "status": 404
}
```

Common error scenarios:

- Invalid resource index
- Invalid query parameter values
- Rate limit exceeded
- Validation errors for malformed requests

---

_This document covers all available functionality as of the current API version. For the most up-to-date information, refer to the live API documentation at `/docs`._
