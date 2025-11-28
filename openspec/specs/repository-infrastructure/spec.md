# repository-infrastructure Specification

## Purpose
Defines the repository pattern infrastructure that provides a clean abstraction layer between MCP tools and data sources (API clients and cache). The repository pattern centralizes data access logic, handles cache-aside caching, supports multiple API sources, enables document-based filtering, and allows dependency injection for testing. This includes base protocols, concrete repository implementations, factory methods, and testing infrastructure for tool migration.

## Requirements

### Requirement: Repository Base Protocol
The system SHALL define a base repository protocol (interface) that all concrete repositories implement.

#### Scenario: Define generic repository interface
When creating repository implementations, they should conform to a standard protocol for consistency.

**Acceptance Criteria:**
- `Repository[T]` protocol defined using Python's Protocol and Generic types
- Protocol defines `get_all(**filters) -> list[T]` method
- Protocol defines `search(query: str, **filters) -> list[T]` method
- Protocol optionally defines `get_by_id(id: str) -> T | None` method
- Protocol is covariant in T for flexible typing
- Located in `src/lorekeeper_mcp/repositories/base.py`

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

### Requirement: Spell Repository Implementation
The system SHALL provide a spell repository that aggregates data from Open5e v2 API with caching support.

#### Scenario: Fetch all spells with caching
When a tool needs spell data, the repository should check cache first, then fetch from API, then update cache.

**Acceptance Criteria:**
- `SpellRepository` class implements repository pattern
- Constructor accepts `Open5eV2Client` and `CacheProtocol` dependencies
- `get_all(**filters)` method queries cache first, falls back to API
- Filters support: level, school, class_key, concentration, ritual, casting_time
- Returns `list[Spell]` using Pydantic models
- Automatically updates cache after API fetch
- Located in `src/lorekeeper_mcp/repositories/spell.py`

#### Scenario: Search spells by name
When searching spells, the repository should support client-side name filtering.

**Acceptance Criteria:**
- `search(name: str, **filters)` method combines name search with filters
- Case-insensitive name matching
- Efficient filtering (fetch with filters first, then filter by name)
- Returns `list[Spell]` models

### Requirement: Creature Repository Implementation
The system SHALL provide a creature repository that aggregates data from Open5e v1 and v2 API clients.

#### Scenario: Fetch creatures with multi-source support
When a tool needs creature data, the repository should be able to fetch from multiple API sources.

**Acceptance Criteria:**
- `CreatureRepository` class implements repository pattern
- Constructor accepts multiple clients: `Open5eV1Client`, optional `Open5eV2Client`
- Constructor accepts `CacheProtocol` dependency
- `get_all(**filters)` tries v1 client first (primary source)
- Filters support: challenge_rating, type, size, name (search)
- Returns `list[Creature]` using Pydantic models
- Caches results from API fetch
- Located in `src/lorekeeper_mcp/repositories/creature.py`

#### Scenario: Search creatures by name with CR filtering
When searching for specific creatures, the repository should combine search and filters efficiently.

**Acceptance Criteria:**
- `search(name: str, **filters)` method supports combined filtering
- Uses v1 API's native search parameter when available
- Fallback to client-side filtering if needed
- Returns `list[Creature]` models

### Requirement: Equipment Repository Implementation
The system SHALL provide an equipment repository that aggregates weapons, armor, and general items.

#### Scenario: Fetch equipment from multiple sources
When a tool needs equipment data, the repository should aggregate from relevant endpoints.

**Acceptance Criteria:**
- `EquipmentRepository` class implements repository pattern
- Constructor accepts `Open5eV2Client` and `CacheProtocol`
- `get_all(item_type: str, **filters)` fetches based on item type (weapon, armor, item)
- Item type determines which API endpoint to use (weapons, armor, items/equipment)
- Returns unified equipment list with consistent structure
- Caches results by item type
- Located in `src/lorekeeper_mcp/repositories/equipment.py`

#### Scenario: Search equipment by name and type
When searching equipment, the repository should support type-specific filtering.

**Acceptance Criteria:**
- `search(name: str, item_type: str, **filters)` method filters by type and name
- Supports filtering weapons by properties (light, finesse, etc.)
- Supports filtering armor by category (light, medium, heavy)
- Returns filtered equipment list

### Requirement: Character Option Repository Implementation
The system SHALL provide a repository for character creation options (classes, races, backgrounds, feats).

#### Scenario: Fetch character options from multiple sources
When a tool needs character options, the repository should aggregate from v1 and v2 APIs.

**Acceptance Criteria:**
- `CharacterOptionRepository` class implements repository pattern
- Constructor accepts all API clients and `CacheProtocol`
- `get_all(option_type: str, **filters)` fetches based on option type
- Option types: "class", "race", "background", "feat", "subclass", "subrace"
- Chooses appropriate API client based on option type and data availability
- Returns unified option list
- Caches results by option type
- Located in `src/lorekeeper_mcp/repositories/character_option.py`

#### Scenario: Search character options
When searching options, the repository should support type-specific searches.

**Acceptance Criteria:**
- `search(name: str, option_type: str, **filters)` filters by type and name
- Case-insensitive name matching
- Returns filtered option list

### Requirement: Rule Repository Implementation
The system SHALL provide a repository for game rules, conditions, and reference data.

#### Scenario: Fetch rules from Open5e API
When a tool needs rule data, the repository should fetch from the API with caching.

**Acceptance Criteria:**
- `RuleRepository` class implements repository pattern
- Constructor accepts `Open5eV2Client` and `CacheProtocol`
- `get_all(rule_type: str, **filters)` fetches based on rule type
- Rule types: "rule", "rule_section", "condition", "damage_type", "weapon_property", etc.
- Uses Open5e v2 as primary source for rules and conditions
- Returns unified rule list
- Caches results with appropriate TTL (30 days for reference data)
- Located in `src/lorekeeper_mcp/repositories/rule.py`

### Requirement: Repository Factory
The system SHALL provide a factory for creating properly configured repository instances with dependency injection.

#### Scenario: Create repositories with default configuration
When the application needs repository instances, use a factory for consistent configuration.

**Acceptance Criteria:**
- `RepositoryFactory` class provides static factory methods
- `create_spell_repository()` creates configured SpellRepository
- `create_creature_repository()` creates configured CreatureRepository
- `create_equipment_repository()` creates configured EquipmentRepository
- `create_character_option_repository()` creates configured CharacterOptionRepository
- `create_rule_repository()` creates configured RuleRepository
- Factory creates and injects client instances
- Factory creates and injects cache instance
- Supports optional client/cache override for testing
- Located in `src/lorekeeper_mcp/repositories/factory.py`

### Requirement: Extract Cache Logic from BaseHttpClient
The system SHALL refactor BaseHttpClient to remove embedded cache logic, delegating caching responsibility to repositories.

#### Scenario: BaseHttpClient focuses on HTTP only
When making API requests, the base client should only handle HTTP concerns, not caching.

**Acceptance Criteria:**
- Remove `use_entity_cache`, `entity_type`, and `cache_filters` parameters from `make_request()`
- Remove `_query_cache_parallel()`, `_extract_entities()`, and `_cache_api_entities()` methods
- Keep `use_cache` parameter for optional legacy URL-based caching
- Remove background refresh logic (moved to repositories if needed)
- Simplify `make_request()` to focus on HTTP retry, error handling, and response parsing
- Update all client subclasses to remove entity cache calls
- Mark as BREAKING CHANGE in migration notes

#### Scenario: Repository handles cache-aside pattern
When repositories fetch data, they should implement cache-aside pattern explicitly.

**Acceptance Criteria:**
- Repositories call cache.get_entities() before API fetch
- Repositories call client methods directly without cache parameters
- Repositories call cache.store_entities() after successful API fetch
- Cache miss triggers API fetch
- Network error uses cached data as fallback
- Clear separation of HTTP and caching concerns

### Requirement: Repository Document Filter Support
Repositories SHALL support optional document-based filtering using normalized document metadata stored in the entity cache.

#### Scenario: Filter spells by document key in repository
- **WHEN** the `SpellRepository` is asked to fetch or search spells with a `document_key` filter
- **THEN** it constrains its query to cached entities whose document metadata matches the specified key
- **AND** combines document filters with existing filters (level, school, class, etc.) at the database level
- **AND** returns an empty list (not an error) if no entities match the combined filters

#### Scenario: SRD-only creature repository filtering
- **WHEN** the `CreatureRepository` is invoked with a filter indicating SRD-only content
- **THEN** it limits results to creatures whose document metadata indicates SRD origin (Open5e SRD documents)
- **AND** avoids additional upstream API calls when the required entities are already present in the cache
- **AND** continues to respect existing filters such as challenge rating and type

### Requirement: Repository Access to Document Configuration
Repositories SHALL be able to honor global document inclusion/exclusion configuration when constructing queries.

#### Scenario: Apply global document configuration to repository queries
- **WHEN** a repository executes a query without an explicit document filter
- **THEN** it applies any configured `included_documents` / `excluded_documents` rules from settings to constrain results
- **AND** uses normalized `document_key` metadata to enforce these rules at the cache or query layer
- **AND** logs or exposes enough context to debug which documents are being implicitly included or excluded when necessary

### Requirement: Single API Source Policy
The repository infrastructure SHALL use Open5e API exclusively for all D&D content retrieval.

#### Scenario: Repository factory creates Open5e-only repositories
- **WHEN** RepositoryFactory creates any repository instance
- **THEN** the repository uses Open5e v1/v2 API clients exclusively
- **AND** source filtering is limited to "open5e_v1", "open5e_v2", and "orcbrew" sources

#### Scenario: Source filtering excludes dnd5e_api
- **WHEN** list_documents tool is invoked with source filtering
- **THEN** "dnd5e_api" is not a valid source option
- **AND** only "open5e_v1", "open5e_v2", and "orcbrew" are accepted source values

---

### Requirement: Tool Unit Tests with Repository Mocks
The system SHALL update all tool unit tests to use repository mocks instead of HTTP mocks, improving test speed and clarity.

#### Scenario: Fast unit tests with mocked repositories
When running unit tests for tools, they should mock repositories instead of HTTP clients.

**Acceptance Criteria:**
- Remove `@respx.mock` decorators from unit tests
- Use `unittest.mock.Mock` or `pytest-mock` to create repository mocks
- Mock `get_all()` and `search()` methods with test data
- Tests run without network calls (faster, more reliable)
- Tests focus on tool logic, not HTTP/caching details
- Example pattern: `mock_repo = Mock(spec=SpellRepository); mock_repo.get_all.return_value = [test_spell]; result = await lookup_spell(..., repository=mock_repo)`

### Requirement: Integration Tests with Real Repositories
The system SHALL add integration tests that use real repository implementations with SQLite cache.

#### Scenario: Integration test with real cache
When testing full data flow, use real repositories with test database.

**Acceptance Criteria:**
- New `test_integration.py` test file per tool (may already exist)
- Use temporary SQLite database for integration tests
- Create real repository instances with test clients
- Verify cache-aside pattern works correctly
- Test offline mode (cache fallback when network unavailable)
- Mark as `@pytest.mark.integration` for optional execution

### Requirement: Tool Documentation Updates
The system SHALL update tool docstrings to reflect repository-based implementation.

#### Scenario: Document repository usage in tools
When developers read tool code, they should understand repository pattern is used.

**Acceptance Criteria:**
- Update module docstrings to mention repository pattern
- Document optional `repository` parameter in function docstrings
- Add examples of providing custom repositories
- Update inline comments to reference repositories instead of clients
- Maintain user-facing documentation unchanged (internal refactor)

### Requirement: Backward Compatibility During Migration
The system SHALL ensure backward compatibility by making repository parameters optional with factory defaults.

#### Scenario: Gradual migration without breaking changes
When migrating tools, existing code should continue to work without modifications.

**Acceptance Criteria:**
- All repository parameters default to `None`
- Tools create repositories via factory when not provided
- Existing tool callers require no changes
- Server integration continues to work without modification
- Tests can optionally inject repositories for mocking
- No breaking changes to MCP tool interfaces
