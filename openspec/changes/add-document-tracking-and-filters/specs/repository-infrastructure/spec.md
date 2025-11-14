## ADDED Requirements

### Requirement: Repository Document Filter Support
Repositories SHALL support optional document-based filtering using normalized document metadata stored in the entity cache.

#### Scenario: Filter spells by document key in repository
- **WHEN** the `SpellRepository` is asked to fetch or search spells with a `document_key` filter
- **THEN** it constrains its query to cached entities whose document metadata matches the specified key
- **AND** combines document filters with existing filters (level, school, class, etc.) at the database level
- **AND** returns an empty list (not an error) if no entities match the combined filters

#### Scenario: SRD-only monster repository filtering
- **WHEN** the `MonsterRepository` is invoked with a filter indicating SRD-only content
- **THEN** it limits results to monsters whose document metadata indicates SRD origin (Open5e SRD documents or D&D 5e SRD)
- **AND** avoids additional upstream API calls when the required entities are already present in the cache
- **AND** continues to respect existing filters such as challenge rating and type

### Requirement: Repository Access to Document Configuration
Repositories SHALL be able to honor global document inclusion/exclusion configuration when constructing queries.

#### Scenario: Apply global document configuration to repository queries
- **WHEN** a repository executes a query without an explicit document filter
- **THEN** it applies any configured `included_documents` / `excluded_documents` rules from settings to constrain results
- **AND** uses normalized `document_key` metadata to enforce these rules at the cache or query layer
- **AND** logs or exposes enough context to debug which documents are being implicitly included or excluded when necessary

## MODIFIED Requirements

### Requirement: Cache Abstraction Protocol
The system SHALL define a cache protocol that repositories use for data persistence, decoupling cache implementation from repository logic.

#### Scenario: Abstract cache operations
When repositories need to cache data, they should use a protocol-based interface independent of SQLite details.

**Acceptance Criteria:**
- `CacheProtocol` defined using Python's Protocol
- Protocol defines `get_entities(entity_type: str, **filters) -> list[dict[str, Any]]` method
- Protocol defines `store_entities(entities: list[dict[str, Any]], entity_type: str) -> None` method
- Protocol defines optional `clear(entity_type: str) -> None` method
- Located in `src/lorekeeper_mcp/cache/protocol.py`
- Cache filters MUST be able to accept document-related filter arguments (for example, `document_key` or equivalent) so repositories can perform document-based filtering without bypassing the cache abstraction
