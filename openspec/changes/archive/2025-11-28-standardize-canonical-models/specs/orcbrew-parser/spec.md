# orcbrew-parser Specification Delta

## MODIFIED Requirements

### Requirement: Entity Normalization

The parser SHALL normalize extracted entities to a consistent format compatible with the cache schema by validating through canonical Pydantic models.

#### Scenario: Normalize entity with OrcBrew field names
**Given** an entity with fields `:key`, `:name`, `:option-pack`, `:description`
**When** the parser normalizes the entity
**Then** the normalized entity has fields:
- `slug` (from `:key`)
- `name` (from `:name`)
- `source` (from `:option-pack`)
- `desc` (from `:description`)
- `data` (full original entity as dict)

#### Scenario: Generate slug when :key is missing
**Given** an entity with `:name` but no `:key`
**When** the parser normalizes the entity
**Then** the parser generates a slug from the name (lowercase, hyphenated)
**And** logs "Generated slug '<slug>' for entity '<name>'"

#### Scenario: Handle entity with source_api marker
**Given** a normalized entity
**When** the parser finalizes the entity
**Then** the entity includes `source_api: "orcbrew"` to distinguish from API data

#### Scenario: Validate through OrcBrew Pydantic models
**Given** an OrcBrew spell entity with fields `:name`, `:level`, `:school`, `:description`
**When** the parser normalizes the entity
**Then** the entity is validated through `OrcBrewSpell` Pydantic model
**And** field types are validated (level is int, school is string)
**And** invalid entities raise `ValidationError` with details

#### Scenario: Extract all fields, not just indexed ones
**Given** an OrcBrew spell with fields `:name`, `:level`, `:school`, `:description`, `:concentration`, `:ritual`, `:components`
**When** the parser normalizes the entity
**Then** ALL fields are extracted to top-level (not just indexed fields)
**And** the normalized entity includes `concentration`, `ritual`, `components`
**And** `data` dict still contains full original entity for reference

---

### Requirement: Indexed Field Extraction

The parser SHALL extract indexed fields from entity data for entity types that define indexed fields in the cache schema, using canonical model field names.

#### Scenario: Extract indexed fields for spells
**Given** a spell entity with `:level 3`, `:school "evocation"`, `:concentration false`
**When** the parser extracts indexed fields
**Then** the normalized entity includes:
- `level: 3` (integer)
- `school: "evocation"` (string)
- `concentration: false` (boolean)

#### Scenario: Extract indexed fields for monsters/creatures
**Given** a monster entity with `:challenge 5`, `:type :aberration`, `:size :large`
**When** the parser extracts indexed fields
**Then** the normalized entity includes:
- `challenge_rating: "5"` (string, normalized from `:challenge`)
- `challenge_rating_decimal: 5.0` (float, computed)
- `type: "aberration"` (string)
- `size: "large"` (string)

#### Scenario: Handle fractional challenge ratings
**Given** a monster entity with `:challenge 0.25` or `:challenge "1/4"`
**When** the parser extracts indexed fields
**Then** `challenge_rating: "1/4"` (string representation)
**And** `challenge_rating_decimal: 0.25` (float for filtering)

#### Scenario: Handle missing indexed fields
**Given** a spell entity missing the `:level` field
**When** the parser extracts indexed fields
**Then** the parser does not include `level` in indexed fields
**And** logs "Warning: Missing indexed field 'level' for spell '<name>'"
**And** continues with import (field remains in data JSON)

---

## ADDED Requirements

### Requirement: Model-Based Validation

The parser SHALL validate all normalized entities through OrcBrew-specific Pydantic models before returning them.

#### Scenario: Reject entity with invalid field type
**Given** an OrcBrew spell with `:level "three"` (string instead of int)
**When** the parser attempts to normalize the entity
**Then** the parser raises `ValidationError`
**And** the error message includes "level: Input should be a valid integer"
**And** logs "Validation failed for spell '<name>': level must be integer"

#### Scenario: Accept entity with missing optional fields
**Given** an OrcBrew spell missing `:casting_time`, `:range`, `:duration`
**When** the parser normalizes the entity
**Then** validation succeeds (fields are optional in OrcBrew models)
**And** missing fields are set to `None` in normalized entity

#### Scenario: Convert kebab-case to snake_case
**Given** an OrcBrew entity with fields `:damage-type`, `:armor-class`, `:requires-attunement`
**When** the parser normalizes the entity
**Then** fields are converted to snake_case: `damage_type`, `armor_class`, `requires_attunement`
**And** the canonical model field names are used consistently
