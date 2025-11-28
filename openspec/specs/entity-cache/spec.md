# entity-cache Specification

## Purpose
Defines the entity-based caching layer that stores D&D entities in type-specific SQLite tables with slug as primary key. Supports filtered queries, bulk operations, document metadata storage, infinite TTL for valid data, schema migrations, and import statistics tracking. Provides the persistence layer for all API and OrcBrew data.
## Requirements
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

### Requirement: Batch Import Support
The cache SHALL efficiently handle large batch imports of entities with transaction support.

#### Scenario: Import 1000 entities in single transaction
**Given** 1000 normalized entities ready for import
**When** calling `bulk_cache_entities()` with the entity list
**Then** all 1000 entities are inserted in a single transaction
**And** the operation completes in < 5 seconds
**And** either all entities are committed or none (atomic)

#### Scenario: Rollback on batch import error
**Given** 500 entities where entity #300 has invalid data
**When** calling `bulk_cache_entities()`
**Then** the transaction is rolled back
**And** no entities from the batch are committed
**And** the error includes the problematic entity's slug

---

### Requirement: Import Statistics Tracking
The cache SHALL provide statistics about imported data for reporting and verification.

#### Scenario: Track successful import count
**Given** a batch import of 500 entities
**When** the import completes successfully
**Then** `bulk_cache_entities()` returns `500`
**And** all 500 entities are queryable in the cache

#### Scenario: Report partial import counts
**Given** a batch where 480 entities succeed and 20 fail validation
**When** the import completes
**Then** the function returns `480`
**And** logs warnings for the 20 failed entities
**And** the 480 successful entities are in the cache

---

### Requirement: Duplicate Handling for Imports
The cache SHALL handle duplicate slugs during import using an "upsert" strategy (insert or update).

#### Scenario: Import entity with new slug
**Given** an entity with slug "new-spell" not in cache
**When** the entity is imported
**Then** a new record is created with `created_at` and `updated_at` set to current time

#### Scenario: Import entity with existing slug
**Given** an entity with slug "fireball" already exists in cache
**When** the same slug is imported with new data
**Then** the existing record is updated
**And** `updated_at` is set to current time
**And** `created_at` remains unchanged
**And** the old data is replaced with new data

#### Scenario: Import preserves API data priority
**Given** an entity with slug "fireball" from "open5e" API exists
**When** importing the same slug from "orcbrew" source
**Then** the cache retains the "open5e" version by default
**And** logs "Skipping import: API data takes priority over OrcBrew for slug 'fireball'"
**Unless** the `--force` flag is used

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

### Requirement: Import Performance Optimization
The cache SHALL optimize bulk imports using SQLite best practices.

#### Scenario: Use WAL mode for concurrent access
**Given** the database is initialized
**When** checking the journal mode
**Then** the database uses "WAL" (Write-Ahead Logging) mode
**And** allows concurrent reads during writes

#### Scenario: Batch inserts use prepared statements
**Given** importing 1000 entities
**When** the cache executes the insert
**Then** a single prepared statement is reused for all inserts
**And** executemany() is used instead of individual execute() calls

---

### Requirement: Import Metadata Tracking
The cache SHALL optionally track metadata about import operations for auditing.

**Note**: This is a future enhancement mentioned for completeness but not required in initial implementation.

#### Scenario: Track import timestamp (future)
**Given** an entity is imported from OrcBrew
**When** the entity is stored
**Then** the entity includes `imported_at` timestamp
**And** `import_source_file` field with the original .orcbrew filename

### Requirement: Store Normalized Document Metadata
The cache MUST store normalized document metadata alongside each cached entity so that repositories and tools can filter by document.

#### Scenario: Cache spell with document metadata
- **GIVEN** a spell entity with slug `"fireball"` and normalized document metadata (`document_key="srd-5e"`, `document_name="System Reference Document"`)
- **WHEN** the entity is cached using `bulk_cache_entities([spell], "spells")`
- **THEN** the spell is stored in the `spells` table with document metadata persisted in dedicated columns or a structured field
- **AND** subsequent calls to `get_cached_entity("spells", "fireball")` return the spell data including the same document metadata

#### Scenario: Cache OrcBrew entity with book metadata
- **GIVEN** an OrcBrew-derived entity with a top-level book heading `"Homebrew Grimoire"`
- **WHEN** the entity is normalized and cached
- **THEN** the cache stores `document_name="Homebrew Grimoire"` and a stable `document_key` derived from that name
- **AND** repositories can use this document metadata to filter OrcBrew content by book

### Requirement: Query Entities by Document Metadata
The cache MUST support filtering cached entities by document metadata through its query interface.

#### Scenario: Filter spells by document key in cache query
- **GIVEN** multiple spells cached from different documents
- **WHEN** calling `query_cached_entities("spells", document_key="srd-5e")`
- **THEN** only spells whose document metadata matches `"srd-5e"` are returned
- **AND** the query returns an empty list if no spells match the specified document key

#### Scenario: Filter mixed-origin entities by document source
- **GIVEN** a mix of entities from Open5e, D&D 5e API, and OrcBrew
- **WHEN** calling `query_cached_entities(entity_type, document_source="orcbrew")`
- **THEN** only entities whose document metadata indicates an OrcBrew origin are returned
- **AND** this filter can be combined with other indexed fields (such as level or challenge rating) without client-side filtering

### Requirement: Document Discovery Function
The cache layer SHALL provide a function to query all available documents across all entity types, regardless of source.

#### Scenario: List all cached documents
- **GIVEN** the cache contains entities from Open5e, D&D 5e API, and OrcBrew
- **WHEN** `get_available_documents()` is called with no filters
- **THEN** the function returns a list of all distinct documents across all entity types
- **AND** each document includes name, source_api, and entity count
- **AND** documents are deduplicated across entity types (same document in spells and creatures appears once)

#### Scenario: Filter documents by source API
- **GIVEN** the cache contains documents from multiple sources
- **WHEN** `get_available_documents(source_api="open5e_v2")` is called
- **THEN** only documents with source_api="open5e_v2" are returned
- **AND** documents from other sources (dnd5e_api, orcbrew) are excluded

#### Scenario: Count entities per document
- **GIVEN** a document "srd-5e" has 100 spells and 50 creatures in cache
- **WHEN** `get_available_documents()` returns this document
- **THEN** the document entry includes entity_count=150
- **AND** optionally includes entity_types breakdown: {"spells": 100, "creatures": 50}

#### Scenario: Handle empty cache
- **GIVEN** the cache has no entities
- **WHEN** `get_available_documents()` is called
- **THEN** an empty list is returned
- **AND** no errors are raised

### Requirement: Document Metadata Query Function
The cache layer SHALL provide a function to retrieve cached document metadata.

#### Scenario: Get Open5e document metadata
- **GIVEN** the "documents" entity type contains cached Open5e document metadata
- **WHEN** `get_document_metadata(document_key="srd-5e")` is called
- **THEN** the function returns the full document metadata
- **AND** metadata includes publisher, license, game_system, description

#### Scenario: Handle missing document metadata
- **GIVEN** no metadata exists for document "custom-homebrew"
- **WHEN** `get_document_metadata(document_key="custom-homebrew")` is called
- **THEN** None is returned
- **AND** no errors are raised

### Requirement: Multi-Document Filtering
The cache query function SHALL support filtering by multiple documents using an IN clause.

#### Scenario: Filter by single document as string
- **GIVEN** the cache contains spells from multiple documents
- **WHEN** `query_cached_entities("spells", document="srd-5e")` is called
- **THEN** only spells with document="srd-5e" are returned
- **AND** behavior is identical to current implementation (backward compatible)

#### Scenario: Filter by multiple documents as list
- **GIVEN** the cache contains spells from multiple documents
- **WHEN** `query_cached_entities("spells", document=["srd-5e", "tce", "phb"])` is called
- **THEN** only spells with document in the list are returned
- **AND** results include entities from all three documents
- **AND** SQL query uses IN clause: `WHERE document IN (?, ?, ?)`

#### Scenario: Filter with no document filter
- **GIVEN** the cache contains spells from multiple documents
- **WHEN** `query_cached_entities("spells")` is called with no document parameter
- **THEN** all spells are returned regardless of document
- **AND** behavior is identical to current implementation (backward compatible)

#### Scenario: Filter by empty document list
- **GIVEN** the cache contains spells
- **WHEN** `query_cached_entities("spells", document=[])` is called
- **THEN** an empty list is returned
- **AND** no database query is executed (short-circuit optimization)

### Requirement: Source-Agnostic Document Handling
Document discovery and filtering SHALL work uniformly across all sources without source-specific logic.

#### Scenario: Query documents from multiple sources
- **GIVEN** cache contains:
  - Spells from Open5e with document="srd-5e"
  - Spells from D&D 5e API with document="System Reference Document 5.1"
  - Spells from OrcBrew with document="Homebrew Grimoire"
- **WHEN** `get_available_documents()` is called
- **THEN** all three documents are returned
- **AND** each document indicates its source via source_api field
- **AND** no source-specific code paths are executed

#### Scenario: Filter across sources by document name
- **GIVEN** cache contains creatures from Open5e and OrcBrew both using document name "srd-5e"
- **WHEN** `query_cached_entities("creatures", document="srd-5e")` is called
- **THEN** creatures from both sources are returned
- **AND** filtering uses document field only, ignoring source_api
- **AND** results are not duplicated (same slug returns one entity)

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
