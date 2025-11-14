## ADDED Requirements

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
