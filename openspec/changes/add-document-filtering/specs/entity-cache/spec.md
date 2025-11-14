# Entity Cache Specification - Document Filtering Delta

## ADDED Requirements

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

## MODIFIED Requirements

None - all changes are additive.

## REMOVED Requirements

None - no functionality is being removed.
