# enhanced-search Specification Delta

## ADDED Requirements

### Requirement: Local Semantic Search with Milvus Lite

The system SHALL provide semantic/vector search capabilities using Milvus Lite as an embedded vector database, enabling natural language similarity queries without requiring external services.

#### Scenario: Semantic search for spells by description
**Given** the cache contains spells "Fireball", "Fire Shield", "Ice Storm"
**When** a semantic search is performed with query "protect from fire damage"
**Then** "Fire Shield" is ranked higher than "Ice Storm"
**And** results are ordered by semantic similarity score descending
**And** no external services are required (fully local)

#### Scenario: Semantic search combined with structured filters
**Given** the cache contains spells at various levels and schools
**When** a semantic search is performed with query "fire damage" and filters level=3, school="Evocation"
**Then** only level 3 Evocation spells are searched
**And** results are ranked by semantic similarity within the filtered set
**And** structured filters are applied before vector search for efficiency

#### Scenario: Semantic search for creatures by concept
**Given** the cache contains creatures "Ancient Red Dragon", "Fire Elemental", "Ice Devil"
**When** a semantic search is performed with query "fire breathing monster"
**Then** "Ancient Red Dragon" and "Fire Elemental" rank higher than "Ice Devil"
**And** results capture semantic meaning beyond keyword matching

#### Scenario: Semantic search fallback on empty query
**Given** the cache contains entities
**When** a semantic search is performed with an empty query string
**Then** the system falls back to structured retrieval
**And** returns entities without semantic ranking
**And** any provided filters are still applied

### Requirement: Embedding Generation for Search

The system SHALL automatically generate vector embeddings for searchable content using a local embedding model.

#### Scenario: Automatic embedding on entity storage
**Given** a spell entity with name "Fireball" and description "A bright streak flashes..."
**When** the entity is stored in the cache
**Then** searchable text is extracted from name, description, and relevant fields
**And** a 384-dimensional embedding vector is generated using all-MiniLM-L6-v2
**And** both the entity data and embedding are stored together

#### Scenario: Lazy loading of embedding model
**Given** a newly initialized cache
**When** no store or semantic search operations have been performed
**Then** the embedding model is not loaded into memory
**When** the first semantic operation is performed
**Then** the model (~80MB) is downloaded if not cached locally
**And** the model is loaded and reused for subsequent operations

#### Scenario: Entity-type-specific text extraction
**Given** entities of different types (spells, creatures, equipment)
**When** generating embeddings for each entity type
**Then** spell embeddings include name, description, and higher_level text
**And** creature embeddings include name, description, type, and ability names
**And** equipment embeddings include name, description, and properties
**And** irrelevant mechanical data (pure numbers) is excluded from embedding text

### Requirement: Hybrid Search Strategy

The system SHALL support hybrid search combining vector similarity with structured filters for optimal search results.

#### Scenario: Hybrid search with document filter
**Given** the cache contains spells from documents "srd-5e" and "tce"
**When** a semantic search is performed with query "healing magic" and document filter "srd-5e"
**Then** only spells from "srd-5e" are included in the vector search
**And** semantic ranking is applied within the document-filtered set
**And** results from "tce" are excluded regardless of semantic similarity

#### Scenario: Hybrid search performance
**Given** a cache with ~10,000 entities
**When** performing hybrid search with filters and semantic query
**Then** query completes in < 100ms
**And** structured filters reduce the search space before vector similarity
**And** results have reasonable recall (>80% of relevant items in top 20)

#### Scenario: Pure structured search without semantics
**Given** the cache supports semantic search
**When** a query is performed without a semantic query parameter
**Then** the system performs structured filtering only
**And** no embedding generation or vector search occurs
**And** behavior is identical to pre-Milvus implementation (backward compatible)

#### Scenario: Similarity score in results
**Given** a semantic search is performed
**When** results are returned
**Then** each result includes a `similarity_score` field (0.0 to 1.0)
**And** results are ordered by similarity_score descending
**And** higher scores indicate greater semantic similarity

#### Scenario: Query text normalization
**Given** a semantic search query with extra whitespace or punctuation
**When** generating the query embedding
**Then** the query text is normalized (trimmed, lowercased)
**And** embedding quality is consistent regardless of query formatting

## MODIFIED Requirements

### Requirement: Document-Based Search Filtering

The unified search functionality SHALL support filtering search results by source document, now leveraging Milvus Lite's native filtering capabilities.

#### Scenario: Filter search results by single document
- **GIVEN** the search index contains content from multiple documents
- **WHEN** a search is performed with document filter for a single document
- **THEN** only results from that document are included in search results
- **AND** results from other documents are excluded
- **AND** search relevance scoring is unaffected by document filtering
- **AND** filtering is performed at the database level using Milvus filter expressions

#### Scenario: Filter search results by multiple documents
- **GIVEN** the search index contains content from multiple documents
- **WHEN** a search is performed with document filter for multiple documents
- **THEN** results from all specified documents are included
- **AND** results from other documents are excluded
- **AND** results maintain relevance order across all included documents
- **AND** Milvus IN clause is used for efficient multi-document filtering

#### Scenario: Semantic search with document filter
- **GIVEN** the cache contains entities from multiple documents
- **WHEN** a semantic search is performed with query "fire magic" and documents=["srd-5e"]
- **THEN** vector similarity search is combined with document filter
- **AND** only entities from "srd-5e" with high semantic similarity are returned
- **AND** filtering and ranking occur in a single Milvus query

### Requirement: Document Filter Performance Optimization

Document filtering SHALL be optimized to minimize performance impact on search operations, leveraging Milvus Lite's native filtering.

#### Scenario: Database-level document filtering
- **GIVEN** search results need to be filtered by document
- **WHEN** filtering is applied
- **THEN** document filter is applied at the Milvus query level
- **AND** filter expression uses indexed document field
- **AND** no post-filtering is required (filtering occurs during vector search)
- **AND** filtering completes in <50ms for typical result sets

#### Scenario: Early termination for empty document list
- **GIVEN** a search is requested with an empty document_keys list
- **WHEN** the search function receives document_keys=[]
- **THEN** an empty result list is returned immediately
- **AND** no Milvus query is executed (short-circuit optimization)
