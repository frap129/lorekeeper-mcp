# Design Document: Repository Pattern Implementation

## Architecture Overview

### Current Architecture
```
┌─────────────┐
│ MCP Tools   │ (spell_lookup, creature_lookup, etc.)
└──────┬──────┘
       │ Direct instantiation & calls
       ▼
┌─────────────────┐
│  API Clients    │ (Open5eV1Client, Open5eV2Client, Dnd5eApiClient)
└──────┬──────────┘
       │ Embedded cache logic
       ▼
┌─────────────────┐
│ Cache (SQLite)  │
└─────────────────┘
```

**Problems**:
- Tools tightly coupled to specific client implementations
- Caching logic mixed with HTTP client logic in BaseHttpClient
- Missing methods for many available API endpoints
- Difficult to unit test tools (requires HTTP mocking)
- Hard to swap data sources or caching strategies

### Proposed Architecture
```
┌─────────────┐
│ MCP Tools   │ (spell_lookup, creature_lookup, etc.)
└──────┬──────┘
       │ Uses abstract interfaces
       ▼
┌─────────────────────────┐
│   Repository Layer      │ (SpellRepository, MonsterRepository, etc.)
│   - Abstract interfaces │
│   - Concrete impls      │
└──────┬───────────┬──────┘
       │           │
       ▼           ▼
┌──────────┐  ┌────────┐
│ Cache    │  │ API    │
│ (SQLite) │  │Clients │
└──────────┘  └────────┘
```

**Benefits**:
- Tools depend on abstract repository interfaces
- Repository implementations handle caching strategy
- API clients focus solely on HTTP communication
- Easy to unit test with repository mocks
- Flexible to add new data sources

## Component Design

### 1. Complete API Client Coverage

#### Open5e v1 Client
**Currently Implemented**: `get_monsters()`, `get_classes()`, `get_races()`

**Missing Endpoints**:
- `/magicitems/` - Magic items (v1 version)
- `/planes/` - Planes of existence
- `/sections/` - Rule sections and lore
- `/spelllist/` - Spell lists by class
- `/manifest/` - API manifest/metadata

#### Open5e v2 Client
**Currently Implemented**: `get_spells()`, `get_weapons()`, `get_armor()`, `get_backgrounds()`, `get_feats()`, `get_conditions()`

**Missing Endpoints**:
- `/items/` - General items
- `/itemsets/` - Item collections
- `/itemcategories/` - Item category taxonomy
- `/species/` - Character species (races)
- `/creatures/` - Monsters (v2 version)
- `/creaturetypes/` - Creature type taxonomy
- `/creaturesets/` - Creature collections
- `/damagetypes/` - Damage types reference
- `/languages/` - Languages reference
- `/alignments/` - Alignments reference
- `/spellschools/` - Spell school reference
- `/classes/` - Character classes (v2)
- `/sizes/` - Size categories
- `/itemrarities/` - Item rarity reference
- `/environments/` - Environment types
- `/abilities/` - Ability scores reference
- `/skills/` - Skills reference
- `/rules/` - Game rules
- `/rulesets/` - Rule collections
- `/images/` - Image assets
- `/weaponproperties/` - Weapon properties reference
- `/services/` - Services/hirelings
- `/documents/` - Source documents
- `/licenses/` - License information
- `/publishers/` - Publisher information
- `/gamesystems/` - Game system metadata

#### D&D 5e API Client
**Currently Implemented**: `get_rules()`, `get_rule_sections()`, `get_damage_types()`, `get_weapon_properties()`, `get_skills()`, `get_ability_scores()`, `get_magic_schools()`, `get_languages()`, `get_proficiencies()`, `get_alignments()`

**Missing Endpoints**:
- `/backgrounds/` - Character backgrounds
- `/classes/` - Character classes
- `/conditions/` - Game conditions
- `/equipment/` - Equipment items
- `/equipment-categories/` - Equipment categories
- `/feats/` - Character feats
- `/features/` - Class features
- `/magic-items/` - Magic items
- `/monsters/` - Monster stat blocks
- `/races/` - Character races
- `/spells/` - Spell details
- `/subclasses/` - Character subclasses
- `/subraces/` - Character subraces
- `/traits/` - Racial traits

### 2. Repository Pattern Design

#### Repository Interface (Protocol/ABC)
```python
from typing import Protocol, TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar('T')

class Repository(Protocol, Generic[T]):
    """Base repository interface for data access."""

    async def get_by_id(self, id: str) -> T | None:
        """Get single entity by ID."""
        ...

    async def get_all(self, **filters) -> list[T]:
        """Get all entities matching filters."""
        ...

    async def search(self, query: str, **filters) -> list[T]:
        """Search entities by query and filters."""
        ...
```

#### Concrete Repository Implementations
Each entity type gets a dedicated repository:

- `SpellRepository` - Spell data access
- `MonsterRepository` - Monster/creature data access
- `EquipmentRepository` - Weapons, armor, items
- `CharacterOptionRepository` - Classes, races, backgrounds, feats
- `RuleRepository` - Rules, conditions, reference data

**Implementation Strategy**:
```python
class SpellRepository:
    """Repository for spell data access."""

    def __init__(
        self,
        client: Open5eV2Client,
        cache: CacheProtocol,
    ):
        self._client = client
        self._cache = cache

    async def get_all(self, **filters) -> list[Spell]:
        """Get all spells with optional filters."""
        # 1. Try cache first
        cached = await self._cache.get_spells(**filters)
        if cached:
            return cached

        # 2. Fetch from API
        spells = await self._client.get_spells(**filters)

        # 3. Update cache
        await self._cache.store_spells(spells)

        return spells

    async def search(self, name: str, **filters) -> list[Spell]:
        """Search spells by name."""
        # Use client-side filtering for now
        all_spells = await self.get_all(**filters)
        return [s for s in all_spells if name.lower() in s.name.lower()]
```

### 3. Cache Abstraction

Extract caching logic from `BaseHttpClient` into dedicated cache layer:

```python
class CacheProtocol(Protocol):
    """Protocol for cache implementations."""

    async def get_entities(
        self,
        entity_type: str,
        **filters
    ) -> list[dict[str, Any]]:
        ...

    async def store_entities(
        self,
        entities: list[dict[str, Any]],
        entity_type: str,
    ) -> None:
        ...
```

**Implementation**:
```python
class SQLiteCache:
    """SQLite-based cache implementation."""

    async def get_entities(
        self,
        entity_type: str,
        **filters
    ) -> list[dict[str, Any]]:
        return await query_cached_entities(entity_type, **filters)

    async def store_entities(
        self,
        entities: list[dict[str, Any]],
        entity_type: str,
    ) -> None:
        await bulk_cache_entities(entities, entity_type)
```

### 4. Migration Strategy

**Phase 1: Complete API Clients** (Can be done in parallel)
- Implement all missing Open5e v1 endpoints
- Implement all missing Open5e v2 endpoints
- Implement all missing D&D 5e API endpoints
- Add comprehensive tests for each new endpoint

**Phase 2: Create Repository Layer**
- Define repository interfaces/protocols
- Extract cache logic from BaseHttpClient
- Implement concrete repositories for each entity type
- Add repository unit tests with mocks

**Phase 3: Migrate Tools**
- Refactor one tool at a time to use repositories
- Update tool tests to use repository mocks
- Ensure backward compatibility
- Validate performance with caching

**Phase 4: Cleanup**
- Remove legacy caching code from BaseHttpClient
- Update documentation
- Add examples of repository usage

## Data Flow Examples

### Example: Spell Lookup with Repository

**Before (Current)**:
```python
# In spell_lookup.py tool
client = Open5eV2Client()  # Direct instantiation
spells = await client.get_spells(level=3)  # Cache handled inside
```

**After (With Repository)**:
```python
# In spell_lookup.py tool
spell_repo = get_spell_repository()  # Dependency injection
spells = await spell_repo.get_all(level=3)  # Cache handled by repo
```

**Unit Test Before**:
```python
# Must mock HTTP client
@respx.mock
async def test_spell_lookup():
    respx.get("https://api.open5e.com/v2/spells/").mock(...)
    result = await lookup_spell(level=3)
```

**Unit Test After**:
```python
# Mock repository interface
async def test_spell_lookup():
    mock_repo = Mock(SpellRepository)
    mock_repo.get_all.return_value = [test_spell]
    result = await lookup_spell(level=3, repo=mock_repo)
```

## Performance Considerations

### Caching Strategy
- Repository layer checks cache before API calls
- Cache-aside pattern: load from cache, fetch on miss, update cache
- TTL-based expiration remains unchanged (7 days for most data)
- Reference data uses extended TTL (30 days)

### Additional Abstraction Overhead
- Repository adds one function call layer (~microseconds)
- Cache queries remain parallelized (no change)
- Background refresh strategy preserved
- Overall performance impact: negligible (<1ms per request)

## Testing Strategy

### API Client Tests
- Unit tests for each endpoint method
- Mock HTTP responses with `respx`
- Test error handling and retry logic
- Validate response parsing and model creation

### Repository Tests
- Unit tests with mocked clients and cache
- Integration tests with real cache (SQLite)
- Test cache hit/miss scenarios
- Validate filter composition

### Tool Tests
- Unit tests with mocked repositories (fast)
- Integration tests with real repositories (slower)
- End-to-end tests with live APIs (optional)

## Open Questions

1. **Repository Factory**: Should we use a factory pattern or dependency injection container?
   - **Recommendation**: Start with simple factory, migrate to DI if needed

2. **Cache Invalidation**: Should repositories handle cache invalidation explicitly?
   - **Recommendation**: Keep TTL-based for now, add explicit invalidation if needed

3. **Multi-Source Repositories**: Should a single repository query multiple APIs?
   - **Recommendation**: Yes - repository can aggregate from v1/v2/dnd5e APIs

4. **Async Context Managers**: Should repositories implement `async with` pattern?
   - **Recommendation**: Yes for client lifecycle management

## Success Metrics

- **Coverage**: 100% of available API endpoints implemented
- **Test Coverage**: >90% coverage for repositories and clients
- **Performance**: No degradation compared to current implementation
- **Tool Migration**: All 5 MCP tools successfully migrated
- **Documentation**: Complete repository usage guide with examples
