# entity-cache Specification Delta

## MODIFIED Requirements

### Requirement: Store entities in type-specific tables

The cache MUST store D&D entities in separate tables per entity type (spells, creatures, weapons, armor, classes, races, backgrounds, feats, conditions, rules, rule_sections) with the entity slug as primary key. Note: `creatures` is the canonical table name (not `monsters`).

#### Scenario: Store and retrieve spell by slug

**Given** a spell entity with slug "fireball"
**When** the entity is cached using `bulk_cache_entities([spell], "spells")`
**Then** the spell is stored in the `spells` table with slug as primary key
**And** calling `get_cached_entity("spells", "fireball")` returns the full spell data

#### Scenario: Store creature with indexed fields

**Given** a creature entity with slug "goblin", type "humanoid", and CR "1/4"
**When** the entity is cached
**Then** the creature is stored in the `creatures` table
**And** indexed fields (type, size, challenge_rating) are extracted for filtering
**And** the complete creature data is stored as JSON blob

#### Scenario: Retrieve multiple entities by type

**Given** three spells cached in the spells table
**When** calling `query_cached_entities("spells")`
**Then** all three spells are returned as dictionaries

#### Scenario: Support both creatures and monsters table names

**Given** code querying for "monsters" entity type
**When** calling `query_cached_entities("monsters")`
**Then** the cache transparently queries the `creatures` table
**And** returns results as if querying "creatures"
**And** logs a deprecation warning "Use 'creatures' instead of 'monsters'"

---

### Requirement: Validation During Import

The cache SHALL validate imported entities before storing them, accepting both canonical Pydantic models and dictionaries.

#### Scenario: Reject entity missing required fields
**Given** an entity missing the `slug` field
**When** attempting to store the entity
**Then** the cache raises `ValueError` with message "Entity missing required field 'slug'"
**And** the entity is not stored

#### Scenario: Accept Pydantic model directly
**Given** a `Creature` Pydantic model instance
**When** calling `bulk_cache_entities([creature], "creatures")`
**Then** the cache accepts the model
**And** calls `model_dump()` to serialize for storage
**And** stores the entity successfully

#### Scenario: Accept dictionary with canonical field names
**Given** a dictionary with canonical field names (slug, name, desc, etc.)
**When** calling `bulk_cache_entities([entity_dict], "spells")`
**Then** the cache stores the dictionary as-is
**And** does not require Pydantic validation (already validated by caller)

#### Scenario: Validate indexed field types
**Given** a spell entity with `level: "three"` (string instead of int)
**When** attempting to store the entity
**Then** the cache logs a warning "Invalid type for indexed field 'level', expected int"
**And** stores the entity without the indexed field (but includes it in JSON data)

---

## ADDED Requirements

### Requirement: Canonical Model Serialization

The cache SHALL serialize canonical Pydantic models to JSON using `model_dump()` with consistent settings.

#### Scenario: Serialize creature model preserving all fields
**Given** a `Creature` model with all fields populated
**When** the cache serializes for storage
**Then** `model_dump(mode="json", exclude_none=False)` is used
**And** all fields including `None` values are preserved
**And** nested objects are serialized to JSON-compatible types

#### Scenario: Serialize OrcBrew model with missing fields
**Given** an `OrcBrewSpell` model with many `None` fields
**When** the cache serializes for storage
**Then** `None` values are preserved (not excluded)
**And** the full structure is recoverable on retrieval

#### Scenario: Deserialize to Pydantic model on retrieval
**Given** a cached spell entity
**When** calling `get_cached_entity("spells", "fireball", as_model=True)`
**Then** the cache returns a `Spell` Pydantic model instance
**And** the model is validated on construction
**And** default value is `as_model=False` for backward compatibility
