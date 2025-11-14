# Spec Delta: Entity Cache (Modified)

## ADDED Requirements

### Requirement: Source API Tracking
The cache schema SHALL track the source API for each cached entity to distinguish between different data sources.

**Modification**: Add `source_api` field support for "orcbrew" source in addition to existing API sources.

#### Scenario: Store entity from OrcBrew import
**Given** an entity imported from a .orcbrew file
**And** the entity has `source_api: "orcbrew"`
**When** the entity is stored in the cache
**Then** the `source_api` field is set to "orcbrew"
**And** the entity is distinguishable from API-fetched entities

#### Scenario: Query entities by source
**Given** the cache contains entities from multiple sources (open5e, dnd5e, orcbrew)
**When** querying entities with filter `source_api="orcbrew"`
**Then** the cache returns only OrcBrew-imported entities

#### Scenario: Update entity maintains source
**Given** an entity with `source_api: "orcbrew"` exists in cache
**When** the same entity slug is imported again
**Then** the `source_api` field remains "orcbrew"
**And** the updated_at timestamp is updated

---

## ADDED Requirements

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
The cache SHALL validate imported entities before storing them.

#### Scenario: Reject entity missing required fields
**Given** an entity missing the `slug` field
**When** attempting to store the entity
**Then** the cache raises `ValueError` with message "Entity missing required field 'slug'"
**And** the entity is not stored

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
