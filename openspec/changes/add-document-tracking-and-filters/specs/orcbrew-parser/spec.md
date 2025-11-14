## ADDED Requirements

### Requirement: Treat OrcBrew Book as Document
The parser SHALL treat the highest-level OrcBrew book heading as the source document for all entities contained within that book.

#### Scenario: Normalize OrcBrew book heading into document metadata
- **GIVEN** a .orcbrew file with a top-level book name such as `"Book Name"`
- **WHEN** the parser reads and normalizes entities from that book
- **THEN** each normalized entity includes `document_name="Book Name"` and a stable `document_key` derived from that name (for example, a lowercased, hyphenated slug)
- **AND** the parser preserves the existing `source` / `source_api` markers to distinguish OrcBrew data from API-derived entities

### Requirement: Expose OrcBrew Document Metadata to Cache
The parser SHALL expose OrcBrew document metadata in a form that can be stored in the entity cache.

#### Scenario: Pass OrcBrew document metadata into normalized entity structure
- **GIVEN** an OrcBrew entity that has been parsed and normalized
- **WHEN** the parser returns the normalized entity to the caller that writes into the cache
- **THEN** the normalized structure includes document metadata fields (`document_key`, `document_name`, `document_source="orcbrew"`)
- **AND** these fields are preserved when entities are stored in the cache and later used by repositories and tools for document-based filtering
