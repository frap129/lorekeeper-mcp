# canonical-models Specification

## Purpose
Defines the canonical Pydantic data models for all D&D entity types (Creature, Spell, Weapon, Armor, MagicItem, CharacterOption, Rule) that provide a unified data layer across all API sources and parsers. Includes slug normalization, description field mapping, relaxed OrcBrew variants, and consistent serialization for cache storage.
## Requirements
### Requirement: Canonical Model Package Structure

The system SHALL provide a dedicated `models/` package containing canonical Pydantic models for all supported D&D entity types.

#### Scenario: Import canonical models from top-level package
- **GIVEN** a developer needs to use entity models
- **WHEN** they import from `lorekeeper_mcp.models`
- **THEN** all canonical models (Creature, Spell, Weapon, Armor, MagicItem) are available
- **AND** the import path is `from lorekeeper_mcp.models import Creature, Spell`

#### Scenario: Models package is independent of API clients
- **GIVEN** the `models/` package exists
- **WHEN** examining its dependencies
- **THEN** it does not import from `api_clients/`
- **AND** it can be used by both API clients and parsers

---

### Requirement: Slug Normalization

All canonical models SHALL normalize the `slug` field from various source field names (`key`, `slug`, or generated from `name`).

#### Scenario: Normalize API key field to slug
- **GIVEN** an entity dict with `{"key": "fireball", "name": "Fireball"}`
- **WHEN** the entity is validated through a canonical model
- **THEN** the model has `slug="fireball"`
- **AND** the original `key` field is not required after validation

#### Scenario: Generate slug from name when missing
- **GIVEN** an entity dict with `{"name": "Magic Missile"}` and no `slug` or `key`
- **WHEN** the entity is validated through a canonical model
- **THEN** the model generates `slug="magic-missile"` (lowercase, hyphenated)
- **AND** special characters like apostrophes are removed

#### Scenario: Preserve explicit slug when provided
- **GIVEN** an entity dict with both `{"slug": "custom-slug", "name": "Different Name"}`
- **WHEN** the entity is validated
- **THEN** the model uses `slug="custom-slug"` as provided
- **AND** does not override with generated value

---

### Requirement: Description Field Normalization

All canonical models SHALL normalize description fields from `description` to `desc`.

#### Scenario: Normalize OrcBrew description field
- **GIVEN** an OrcBrew entity with `{"description": "A powerful spell."}`
- **WHEN** the entity is validated through a canonical model
- **THEN** the model has `desc="A powerful spell."`
- **AND** works whether source uses `description` or `desc`

#### Scenario: Handle missing description
- **GIVEN** an entity without a description field
- **WHEN** the entity is validated
- **THEN** `desc` is set to `None`
- **AND** validation does not fail

---

### Requirement: Creature Model (renamed from Monster)

The system SHALL use `Creature` as the canonical model name for monsters/creatures, aligning with Open5e v2 terminology.

#### Scenario: Create creature from API response
- **GIVEN** an Open5e v2 creature response with nested objects
- **WHEN** validated through the `Creature` model
- **THEN** `size` is extracted as string (from `size.name`)
- **AND** `type` is extracted as string (from `type.name`)
- **AND** `challenge_rating` is string and `challenge_rating_decimal` is float

#### Scenario: Create creature from OrcBrew data
- **GIVEN** an OrcBrew creature with `challenge` field (not `challenge_rating`)
- **WHEN** validated through the `Creature` model
- **THEN** `challenge` is mapped to `challenge_rating`
- **AND** `challenge_rating_decimal` is computed from the value

---

### Requirement: Spell Model with Class List Normalization

The `Spell` model SHALL normalize the `classes` field to a list of lowercase strings regardless of source format.

#### Scenario: Normalize API class objects to strings
- **GIVEN** a spell with `classes: [{"index": "wizard", "name": "Wizard"}]`
- **WHEN** validated through the `Spell` model
- **THEN** `classes` becomes `["wizard"]`
- **AND** all class names are lowercase

#### Scenario: Handle comma-separated class string
- **GIVEN** a spell with `classes: "Wizard, Sorcerer, Warlock"`
- **WHEN** validated through the `Spell` model
- **THEN** `classes` becomes `["wizard", "sorcerer", "warlock"]`

#### Scenario: Preserve empty class list
- **GIVEN** a spell with no classes specified
- **WHEN** validated
- **THEN** `classes` is an empty list `[]`
- **AND** validation does not fail

---

### Requirement: Weapon Model with Simplified Damage Type

The `Weapon` model SHALL provide a `damage_type_name` property for easy access to the damage type string.

#### Scenario: Access damage type as string
- **GIVEN** a weapon with `damage_type: {"name": "Slashing", "key": "slashing"}`
- **WHEN** accessing `weapon.damage_type_name`
- **THEN** returns `"Slashing"`

#### Scenario: Store simplified damage type from OrcBrew
- **GIVEN** an OrcBrew weapon with `damage-type: "piercing"`
- **WHEN** validated through the `Weapon` model
- **THEN** `damage_type` stores the string directly
- **AND** `damage_type_name` returns `"piercing"`

---

### Requirement: OrcBrew Relaxed Models

The system SHALL provide OrcBrew-specific model variants with relaxed field requirements for incomplete data.

#### Scenario: Validate OrcBrew spell with missing fields
- **GIVEN** an OrcBrew spell with only `name`, `level`, `school`, `description`
- **WHEN** validated through `OrcBrewSpell` model
- **THEN** validation succeeds
- **AND** missing fields (`casting_time`, `range`, `duration`) are `None`

#### Scenario: OrcBrew creature without ability scores
- **GIVEN** an OrcBrew creature with `name`, `type`, `size`, `challenge`
- **WHEN** validated through `OrcBrewCreature` model
- **THEN** validation succeeds
- **AND** ability scores default to `None`
- **AND** `hit_points` and `hit_dice` default to `None`

#### Scenario: Convert OrcBrew model to canonical
- **GIVEN** an `OrcBrewSpell` instance
- **WHEN** calling `to_canonical()` method
- **THEN** returns a `Spell` instance with same data
- **AND** missing fields remain `None`
