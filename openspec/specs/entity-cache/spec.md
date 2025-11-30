# entity-cache Specification

## Purpose
Defines the entity-based caching layer that stores D&D entities in type-specific Milvus collections with slug as primary key. Supports semantic/vector search, filtered queries, bulk operations, document metadata storage, infinite TTL for valid data, and import statistics tracking. Provides the persistence layer for all API and OrcBrew data using Milvus Lite as the embedded vector database.
## Requirements
### Requirement: Store entities in type-specific tables

The cache MUST store D&D entities in separate collections per entity type (spells, creatures, weapons, armor, classes, races, backgrounds, feats, conditions, rules, rule_sections) with the entity slug as primary key. Note: `creatures` is the canonical collection name (not `monsters`).

#### Scenario: Store and retrieve spell by slug
**Given** a spell entity with slug "fireball"
**When** the entity is cached using `bulk_cache_entities([spell], "spells")` or `store_entities([spell], "spells")`
**Then** the spell is stored in the `spells` collection with slug as primary key
**And** an embedding vector is generated from spell text
**And** calling `get_cached_entity("spells", "fireball")` returns the full spell data

#### Scenario: Store creature with indexed fields
**Given** a creature entity with slug "goblin", type "humanoid", and CR "1/4"
**When** the entity is cached
**Then** the creature is stored in the `creatures` collection
**And** indexed fields (type, size, challenge_rating) are extracted for filtering
**And** an embedding vector is generated from creature text
**And** the complete creature data is stored with dynamic fields

### Requirement: Query entities with filters

The cache MUST support filtering cached entities by indexed fields specific to each entity type, both with and without semantic search.

#### Scenario: Filter spells by level and school (structured only)
**Given** multiple spells cached with various levels and schools
**When** calling `get_entities("spells", level=3, school="Evocation")`
**Then** only spells matching level=3 AND school="Evocation" are returned
**And** no semantic ranking is applied
**And** results are returned in storage order

#### Scenario: Filter with semantic ranking
**Given** multiple spells cached with various levels
**When** calling `semantic_search("spells", "damage spell", level=3)`
**Then** only level=3 spells are included
**And** results are ranked by semantic similarity to "damage spell"
**And** structured filter is applied before vector search

### Requirement: Infinite TTL for valid entities

The cache MUST NOT expire valid entity data. Entities remain cached indefinitely until explicitly updated or deleted.

#### Scenario: Retrieve entity cached weeks ago

**Given** a spell cached 30 days ago
**When** calling `get_cached_entity("spells", "fireball")`
**Then** the spell data is returned without expiration check
**And** the data matches the originally cached spell

#### Scenario: Update entity preserves creation time

**Given** a creature cached 10 days ago
**When** the same creature is cached again with updated data
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

**Given** 100 spells, 50 creatures, and 30 weapons cached
**When** calling `get_entity_count("spells")`
**Then** the function returns 100
**And** `get_entity_count("creatures")` returns 50
**And** `get_entity_count("weapons")` returns 30

#### Scenario: Get comprehensive cache statistics

**Given** a populated cache with various entity types
**When** calling `get_cache_stats()`
**Then** a dictionary is returned containing:
- Total entity counts per type
- Database file size in bytes
- Collection counts
- Embedding dimension and index type

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
The cache SHALL optimize bulk imports using Milvus best practices.

#### Scenario: Batch inserts for efficiency
**Given** importing 1000 entities
**When** the cache executes the insert
**Then** entities are batched into groups for insertion
**And** a single transaction covers all inserts in a batch
**And** embedding generation is parallelized where possible

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

### Requirement: Milvus Lite Backend Implementation

The cache MUST support Milvus Lite as an embedded vector database backend, providing semantic search capabilities while maintaining all existing structured filtering.

#### Scenario: Initialize Milvus Lite cache
**Given** a configuration specifying Milvus Lite backend
**When** the cache is initialized with default configuration
**Then** a single database file is created at the XDG path (`$XDG_DATA_HOME/lorekeeper/milvus.db` or `~/.local/share/lorekeeper/milvus.db`)
**And** collections are automatically created for each entity type
**And** IVF_FLAT index with COSINE similarity is configured
**And** no external services are required

#### Scenario: Store entity with automatic embedding generation
**Given** a spell entity with name "Fireball" and description "A bright streak flashes..."
**When** the entity is stored using `store_entities([spell], "spells")`
**Then** searchable text is extracted from name and description fields
**And** a 384-dimensional embedding vector is generated using all-MiniLM-L6-v2
**And** the entity is stored with both scalar fields and embedding vector
**And** the entity is searchable via both structured and semantic queries

#### Scenario: Lazy loading of embedding model
**Given** a newly initialized MilvusCache
**When** no store or semantic search operations have been performed
**Then** the embedding model is not loaded into memory
**When** the first `store_entities` or `semantic_search` call is made
**Then** the embedding model (~80MB) is downloaded if not cached
**And** the model is loaded into memory
**And** subsequent calls reuse the loaded model

### Requirement: Semantic Search Method

The cache MUST provide a `semantic_search` method that finds entities based on natural language similarity queries.

#### Scenario: Basic semantic search
**Given** the cache contains spells "Fireball", "Fire Shield", "Ice Storm"
**When** calling `semantic_search("spells", "protect from fire")`
**Then** "Fire Shield" is ranked higher than "Ice Storm"
**And** results are ordered by similarity score descending
**And** each result includes the similarity score

#### Scenario: Semantic search with filters
**Given** the cache contains spells at various levels
**When** calling `semantic_search("spells", "fire damage", level=3, limit=5)`
**Then** only level 3 spells are searched
**And** results are ranked by semantic similarity to "fire damage"
**And** at most 5 results are returned

#### Scenario: Semantic search with document filter
**Given** the cache contains spells from "srd-5e" and "tce" documents
**When** calling `semantic_search("spells", "healing magic", document="srd-5e")`
**Then** only spells from "srd-5e" are included in results
**And** semantic ranking is applied within the filtered set

#### Scenario: Empty semantic query fallback
**Given** the cache contains entities
**When** calling `semantic_search("spells", "")` with empty query
**Then** the method falls back to structured retrieval
**And** returns entities without semantic ranking
**And** filters are still applied if provided

### Requirement: Collection Schema Per Entity Type

The cache MUST maintain separate Milvus collections with entity-type-specific schemas.

#### Scenario: Spells collection schema
**Given** a spells collection
**Then** the collection includes indexed scalar fields: `level`, `school`, `concentration`, `ritual`
**And** the collection includes embedding field with dimension 384
**And** the collection includes primary key field `slug`
**And** dynamic fields are enabled for full entity storage

#### Scenario: Creatures collection schema
**Given** a creatures collection
**Then** the collection includes indexed scalar fields: `challenge_rating`, `type`, `size`
**And** the collection includes embedding field with dimension 384
**And** filters can be applied to `challenge_rating` as string comparison

#### Scenario: Equipment collection schema
**Given** an equipment collection
**Then** the collection includes indexed scalar fields: `item_type`, `rarity`
**And** the collection supports filtering by equipment category

### Requirement: Embedding Text Extraction

The cache MUST extract entity-type-specific text for embedding generation.

#### Scenario: Spell text extraction
**Given** a spell entity with name, desc, and higher_level fields
**When** generating embedding text
**Then** text includes name, desc, and higher_level concatenated
**And** empty/None fields are skipped
**And** resulting text is suitable for semantic search

#### Scenario: Creature text extraction
**Given** a creature entity with name, desc, type, actions, and special_abilities
**When** generating embedding text
**Then** text includes name, desc, type
**And** action names are included (not full action descriptions)
**And** special ability names are included
**And** resulting text captures creature identity for semantic matching

#### Scenario: Minimal text fallback
**Given** an entity with only name field populated
**When** generating embedding text
**Then** text includes only the name
**And** embedding is still generated (no error)
**And** a warning is logged about minimal semantic content

### Requirement: Index Configuration for Search Quality

The cache MUST configure Milvus indexes for optimal semantic search performance.

#### Scenario: IVF_FLAT index configuration
**Given** a new collection is created
**Then** IVF_FLAT index is created with nlist=128
**And** COSINE metric type is configured
**And** search uses nprobe=16 for balanced recall/speed

#### Scenario: Search latency target
**Given** a collection with ~10,000 entities
**When** performing semantic search with filters
**Then** query completes in < 100ms
**And** results have reasonable recall (>80% of relevant items in top 20)

### Requirement: Cache Protocol Semantic Search Extension

The CacheProtocol SHALL define the interface for cache implementations with full semantic search support.

#### Scenario: MilvusCache implements full protocol
**Given** a MilvusCache instance
**When** checking protocol compliance
**Then** `get_entities`, `store_entities`, and `semantic_search` are all implemented
**And** all methods are async

#### Scenario: Protocol semantic_search method signature
**Given** the updated CacheProtocol
**When** implementing `semantic_search`
**Then** the method signature is:
```python
async def semantic_search(
    self,
    entity_type: str,
    query: str,
    limit: int = 20,
    document: str | list[str] | None = None,
    **filters: Any,
) -> list[dict[str, Any]]
```
**And** returns entities with `similarity_score` field included
**And** results are ordered by similarity_score descending

### Requirement: EmbeddingService Component

The cache MUST use a dedicated EmbeddingService for all embedding operations with lazy model loading.

#### Scenario: Lazy model loading on first use
**Given** a newly initialized MilvusCache with EmbeddingService
**When** no embedding operations have been performed
**Then** the embedding model is not loaded into memory
**And** memory usage remains minimal (~50MB baseline)
**When** the first `store_entities` or `semantic_search` call is made
**Then** the model is loaded on demand
**And** subsequent calls reuse the loaded model instance

#### Scenario: Batch embedding generation
**Given** a list of 100 entities to store
**When** calling `store_entities(entities, "spells")`
**Then** EmbeddingService generates embeddings in batches (batch_size=32)
**And** batch processing is more efficient than individual encoding
**And** total encoding time is proportional to entity count

#### Scenario: Custom embedding model support
**Given** environment variable `LOREKEEPER_EMBEDDING_MODEL=custom-model-name`
**When** EmbeddingService initializes
**Then** the custom model is loaded instead of default
**And** embedding dimension is detected from model config
**And** schema uses the correct dimension

### Requirement: Cache Factory for Backend Selection

The cache layer SHALL provide a factory function to create MilvusCache instances.

#### Scenario: Create Milvus cache via factory
**Given** calling `create_cache()` with optional db_path parameter
**When** the factory creates a cache instance
**Then** a MilvusCache instance is returned
**And** the cache is configured with settings from environment or defaults

#### Scenario: Default Milvus configuration
**Given** no environment variables are set
**When** calling `create_cache()`
**Then** a MilvusCache instance is returned
**And** uses XDG path (`$XDG_DATA_HOME/lorekeeper/milvus.db` or `~/.local/share/lorekeeper/milvus.db`) by default
**And** semantic search capabilities are available

### Requirement: Error Handling and Graceful Degradation

The cache MUST handle errors gracefully with appropriate fallbacks.

#### Scenario: Embedding generation failure fallback
**Given** embedding model fails to encode a query
**When** `semantic_search` is called
**Then** the system logs a warning about embedding failure
**And** falls back to structured name-based search
**And** returns results without semantic ranking

#### Scenario: Milvus connection error handling
**Given** the Milvus database file is corrupted or locked
**When** any cache operation is attempted
**Then** a CacheError is raised with descriptive message
**And** detailed error is logged for debugging
**And** the caller can handle the error appropriately

#### Scenario: Model download timeout handling
**Given** first-time model download is interrupted
**When** EmbeddingService attempts to load the model
**Then** a clear error message indicates download failure
**And** suggests checking network connectivity
**And** subsequent retries attempt download again

### Requirement: Range Filter Support in Filter Expressions

The cache MUST support range filter parameters (`_min` and `_max` suffixes) and convert them to appropriate comparison operators in Milvus filter expressions.

#### Scenario: Convert level_min to greater-than-or-equal filter
**Given** a filter dictionary with `{"level_min": 4}`
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `level >= 4`
**And** only entities with level 4 or higher match the filter

#### Scenario: Convert level_max to less-than-or-equal filter
**Given** a filter dictionary with `{"level_max": 3}`
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `level <= 3`
**And** only entities with level 3 or lower match the filter

#### Scenario: Combine range filters with semantic search
**Given** a cache containing spells at various levels
**When** calling `semantic_search("spells", "fire damage", level_min=4, level_max=6)`
**Then** the filter expression includes `level >= 4 and level <= 6`
**And** only level 4, 5, or 6 spells are searched
**And** results are ranked by semantic similarity to "fire damage"

#### Scenario: Combine range filter with exact filter
**Given** a filter dictionary with `{"level_min": 3, "school": "evocation"}`
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `level >= 3 and school == "evocation"`
**And** both conditions must be satisfied for a match

#### Scenario: Generic field minimum range support
**Given** a filter dictionary with `{"armor_class_min": 15}` for armor entities
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `armor_class >= 15`
**And** the pattern works for any indexed numeric field with `_min` suffix

#### Scenario: Generic field maximum range support
**Given** a filter dictionary with `{"challenge_rating_max": 5}` for creature entities
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `challenge_rating <= 5`
**And** the pattern works for any indexed numeric field with `_max` suffix
