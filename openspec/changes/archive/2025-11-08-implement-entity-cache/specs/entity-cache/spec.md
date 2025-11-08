# Entity Cache Capability

## ADDED Requirements

### Requirement: Store entities in type-specific tables

The cache MUST store D&D entities in separate tables per entity type (spells, monsters, weapons, armor, classes, races, backgrounds, feats, conditions, rules, rule_sections) with the entity slug as primary key.

#### Scenario: Store and retrieve spell by slug

**Given** a spell entity with slug "fireball"
**When** the entity is cached using `bulk_cache_entities([spell], "spells")`
**Then** the spell is stored in the `spells` table with slug as primary key
**And** calling `get_cached_entity("spells", "fireball")` returns the full spell data

#### Scenario: Store monster with indexed fields

**Given** a monster entity with slug "goblin", type "humanoid", and CR "1/4"
**When** the entity is cached
**Then** the monster is stored in the `monsters` table
**And** indexed fields (type, size, challenge_rating) are extracted for filtering
**And** the complete monster data is stored as JSON blob

#### Scenario: Retrieve multiple entities by type

**Given** three spells cached in the spells table
**When** calling `query_cached_entities("spells")`
**Then** all three spells are returned as dictionaries

### Requirement: Query entities with filters

The cache MUST support filtering cached entities by indexed fields specific to each entity type.

#### Scenario: Filter spells by level and school

**Given** multiple spells cached with various levels and schools
**When** calling `query_cached_entities("spells", level=3, school="Evocation")`
**Then** only spells matching level=3 AND school="Evocation" are returned

#### Scenario: Filter monsters by challenge rating

**Given** multiple monsters cached with various CRs
**When** calling `query_cached_entities("monsters", challenge_rating="5")`
**Then** only monsters with CR=5 are returned

#### Scenario: Query with no matches returns empty list

**Given** a cache with several entities
**When** querying with filters that match no entities
**Then** an empty list is returned (not None or error)

### Requirement: Infinite TTL for valid entities

The cache MUST NOT expire valid entity data. Entities remain cached indefinitely until explicitly updated or deleted.

#### Scenario: Retrieve entity cached weeks ago

**Given** a spell cached 30 days ago
**When** calling `get_cached_entity("spells", "fireball")`
**Then** the spell data is returned without expiration check
**And** the data matches the originally cached spell

#### Scenario: Update entity preserves creation time

**Given** a monster cached 10 days ago
**When** the same monster is cached again with updated data
**Then** `created_at` timestamp remains unchanged
**And** `updated_at` timestamp reflects the new cache time
**And** the data blob contains the updated information

### Requirement: Bulk cache operations for performance

The cache MUST support bulk insertion of multiple entities in a single transaction for efficiency.

#### Scenario: Bulk cache spell list from API

**Given** a list of 50 spells from an API response
**When** calling `bulk_cache_entities(spells, "spells")`
**Then** all 50 spells are inserted/updated in a single transaction
**And** the function returns the count of entities processed
**And** all operations succeed or roll back together

#### Scenario: Bulk insert handles duplicates

**Given** 20 new spells and 10 already-cached spells
**When** bulk caching all 30 spells
**Then** new spells are inserted
**And** existing spells are updated with new data
**And** no duplicate slug errors occur

### Requirement: Cache statistics for observability

The cache MUST track and report statistics on cache usage, entity counts, and health metrics.

#### Scenario: Get entity count per type

**Given** 100 spells, 50 monsters, and 30 weapons cached
**When** calling `get_entity_count("spells")`
**Then** the function returns 100
**And** `get_entity_count("monsters")` returns 50
**And** `get_entity_count("weapons")` returns 30

#### Scenario: Get comprehensive cache statistics

**Given** a populated cache with various entity types
**When** calling `get_cache_stats()`
**Then** a dictionary is returned containing:
- Total entity counts per type
- Database file size in bytes
- Table counts
- Schema version

### Requirement: Schema migration support

The cache MUST provide migration utilities to transition from the old URL-based cache to the new entity-based schema.

#### Scenario: Initialize new entity cache tables

**Given** an empty or non-existent database
**When** calling `init_entity_cache()`
**Then** all entity tables are created with correct schemas
**And** all indexes are created on filtered fields
**And** WAL mode is enabled for concurrent access

#### Scenario: Drop old cache table safely

**Given** a database with the old `api_cache` table
**When** calling `migrate_cache_schema()`
**Then** the old `api_cache` table is dropped
**And** new entity tables are created
**And** no data corruption occurs
