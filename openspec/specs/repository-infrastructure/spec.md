# repository-infrastructure Specification

## Purpose
TBD - created by archiving change implement-repository-pattern. Update Purpose after archive.
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

#### Scenario: SQLite cache implements protocol
When using SQLite as cache backend, it should implement the cache protocol.

**Acceptance Criteria:**
- `SQLiteCache` class implements `CacheProtocol`
- Wraps existing `query_cached_entities()` and `bulk_cache_entities()` functions
- Maintains backward compatibility with existing cache functions
- Handles entity type mapping and filtering
- Located in `src/lorekeeper_mcp/cache/sqlite.py`

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

### Requirement: Monster Repository Implementation
The system SHALL provide a monster repository that aggregates data from Open5e v1, Open5e v2, and D&D 5e API clients.

#### Scenario: Fetch monsters with multi-source support
When a tool needs monster data, the repository should be able to fetch from multiple API sources.

**Acceptance Criteria:**
- `MonsterRepository` class implements repository pattern
- Constructor accepts multiple clients: `Open5eV1Client`, optional `Open5eV2Client`, optional `Dnd5eApiClient`
- Constructor accepts `CacheProtocol` dependency
- `get_all(**filters)` tries v1 client first (primary source)
- Filters support: challenge_rating, type, size, name (search)
- Returns `list[Monster]` using Pydantic models
- Caches results from API fetch
- Located in `src/lorekeeper_mcp/repositories/monster.py`

#### Scenario: Search monsters by name with CR filtering
When searching for specific monsters, the repository should combine search and filters efficiently.

**Acceptance Criteria:**
- `search(name: str, **filters)` method supports combined filtering
- Uses v1 API's native search parameter when available
- Fallback to client-side filtering if needed
- Returns `list[Monster]` models

### Requirement: Equipment Repository Implementation
The system SHALL provide an equipment repository that aggregates weapons, armor, and general items.

#### Scenario: Fetch equipment from multiple sources
When a tool needs equipment data, the repository should aggregate from relevant endpoints.

**Acceptance Criteria:**
- `EquipmentRepository` class implements repository pattern
- Constructor accepts `Open5eV2Client`, optional `Dnd5eApiClient`, and `CacheProtocol`
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
When a tool needs character options, the repository should aggregate from v1, v2, and dnd5e APIs.

**Acceptance Criteria:**
- `CharacterOptionRepository` class implements repository pattern
- Constructor accepts all three clients and `CacheProtocol`
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

#### Scenario: Fetch rules from D&D 5e API
When a tool needs rule data, the repository should fetch from the official API with caching.

**Acceptance Criteria:**
- `RuleRepository` class implements repository pattern
- Constructor accepts `Dnd5eApiClient`, optional `Open5eV2Client`, and `CacheProtocol`
- `get_all(rule_type: str, **filters)` fetches based on rule type
- Rule types: "rule", "rule_section", "condition", "damage_type", "weapon_property", etc.
- Uses D&D 5e API as primary source for rules
- Uses Open5e v2 as fallback for conditions
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
- `create_monster_repository()` creates configured MonsterRepository
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
