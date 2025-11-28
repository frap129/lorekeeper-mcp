# entity-cache Specification Delta

## ADDED Requirements

### Requirement: Milvus Lite Backend Implementation

The cache MUST support Milvus Lite as an embedded vector database backend, providing semantic search capabilities while maintaining all existing structured filtering.

#### Scenario: Initialize Milvus Lite cache
**Given** a configuration specifying Milvus Lite backend
**When** the cache is initialized with `MilvusCache(db_path="~/.lorekeeper/milvus.db")`
**Then** a single database file is created at the specified path
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

The CacheProtocol MUST be extended to optionally support semantic search while maintaining backward compatibility.

#### Scenario: Protocol backward compatibility
**Given** an existing cache implementation (SQLiteCache)
**When** the protocol is checked
**Then** `get_entities` and `store_entities` remain required methods
**And** `semantic_search` is an optional method
**And** SQLiteCache raises NotImplementedError for `semantic_search`

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

The cache layer MUST provide a factory function to create the appropriate cache backend based on configuration.

#### Scenario: Create Milvus cache via factory
**Given** configuration `LOREKEEPER_CACHE_BACKEND=milvus`
**When** calling `create_cache()`
**Then** a MilvusCache instance is returned
**And** the cache is configured with settings from environment

#### Scenario: Create SQLite cache via factory (legacy)
**Given** configuration `LOREKEEPER_CACHE_BACKEND=sqlite`
**When** calling `create_cache()`
**Then** a SQLiteCache instance is returned
**And** semantic_search raises NotImplementedError

#### Scenario: Default to Milvus backend
**Given** no `LOREKEEPER_CACHE_BACKEND` environment variable
**When** calling `create_cache()`
**Then** a MilvusCache instance is returned by default
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

## MODIFIED Requirements

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

## REMOVED Requirements

None - all existing requirements are preserved with modifications.
