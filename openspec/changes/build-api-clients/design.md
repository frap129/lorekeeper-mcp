# API Client Architecture Design

## Overview

This design outlines the architecture for API clients that will interface with Open5e and D&D 5e APIs to provide unified access to D&D 5e game data for the LoreKeeper MCP server.

## Architectural Decisions

### 1. Base HTTP Client Pattern

**Decision**: Create a base HTTP client class that provides common functionality including:
- HTTP request handling with retry logic
- Rate limiting and backoff strategies
- Response caching integration
- Error handling and logging
- Request/response interceptors

**Rationale**: Avoids code duplication across different API clients and ensures consistent behavior for reliability, caching, and error handling.

### 2. Separate API Client Classes

**Decision**: Create separate client classes for each API service:
- `Open5eV1Client` - for monsters, classes, races, magic items
- `Open5eV2Client` - for spells, weapons, armor, backgrounds, feats, conditions
- `Dnd5eApiClient` - for rules and reference data

**Rationale**: Different API versions have different response formats and endpoint patterns. Separate clients provide clean interfaces and make it easier to handle API-specific quirks.

### 3. Response Model Unification

**Decision**: Create standardized response models for each data type (Spell, Monster, Weapon, etc.) that normalize differences between API versions.

**Rationale**: MCP tools should work with consistent data structures regardless of which API provided the data. This simplifies tool implementation and provides better user experience.

### 4. Cache-Aside Pattern Integration

**Decision**: Integrate with existing SQLite cache using cache-aside pattern:
- Check cache first before making API request
- Store successful responses in cache with TTL
- Return cached data when available
- Handle cache failures gracefully

**Rationale**: Reduces API calls, improves response times, and provides offline capability. Aligns with existing project architecture.

### 5. Error Handling Strategy

**Decision**: Implement hierarchical error handling:
- Network errors -> retry with exponential backoff
- API errors (4xx/5xx) -> log and return user-friendly message
- Parse errors -> log raw response and return structured error
- Cache errors -> continue without caching, don't fail request

**Rationale**: Provides resilience and meaningful error messages for debugging while maintaining service availability.

## Class Structure

```python
# Base client providing common HTTP functionality (all methods async)
class BaseHttpClient:
    async def _make_request()           # HTTP request with retry logic
    async def _get_cached_response()    # Check cache before API call
    async def _cache_response()         # Store response in cache
    async def _handle_errors()          # Error handling and logging

# API-specific clients (all methods async)
class Open5eV1Client(BaseHttpClient):
    async def get_monsters()      # Filter: name, CR, type, size
    async def get_classes()       # Filter: name
    async def get_races()         # Filter: name
    async def get_magic_items()   # Filter: name, rarity

class Open5eV2Client(BaseHttpClient):
    async def get_spells()        # Filter: name, level, school, class, concentration, ritual
    async def get_weapons()       # Filter: name, damage_dice, properties
    async def get_armor()         # Filter: name, category
    async def get_backgrounds()   # Filter: name
    async def get_feats()         # Filter: name, type
    async def get_conditions()    # Filter: name

class Dnd5eApiClient(BaseHttpClient):
    async def get_rules()              # Filter: section, name
    async def get_rule_sections()      # Filter: name
    async def get_damage_types()       # Reference data
    async def get_weapon_properties()  # Reference data
    async def get_skills()             # Reference data
    async def get_ability_scores()     # Reference data
    async def get_magic_schools()      # Reference data
    async def get_languages()          # Reference data
    async def get_proficiencies()      # Reference data
    async def get_alignments()         # Reference data

# Factory for client instantiation with dependency injection
class ClientFactory:
    @staticmethod
    def create_open5e_v1() -> Open5eV1Client

    @staticmethod
    def create_open5e_v2() -> Open5eV2Client

    @staticmethod
    def create_dnd5e_api() -> Dnd5eApiClient
```

## Data Flow

1. MCP tool calls appropriate client method
2. Client checks cache for existing data
3. If cache miss, client makes HTTP request via base class
4. Base client handles retries, rate limiting, errors
5. Response is parsed into standardized model
6. Response is cached for future use
7. Standardized data returned to MCP tool

## Technology Choices

- **HTTP Library**: `httpx` - async support, better performance than requests
- **Async/Await**: All clients use async/await for I/O operations (integrates with existing async cache and FastMCP server)
- **Rate Limiting**: Built-in exponential backoff with jitter (initial: 1s, max: 32s, multiplier: 2x)
- **Error Handling**: Custom exception hierarchy for different error types
  - `ApiClientError` (base)
  - `NetworkError` (retryable - timeouts, connection errors)
  - `ApiError` (non-retryable - 4xx/5xx responses)
  - `ParseError` (malformed JSON/data)
  - `CacheError` (cache failures, non-fatal)
- **Response Parsing**: Pydantic models for validation and serialization
- **Logging**: Structured logging with different levels for debugging

## Cache TTL Strategy

- **Standard game data**: 7 days (604,800 seconds) - spells, monsters, items, classes, races
- **Reference data**: 30 days (2,592,000 seconds) - damage types, skills, weapon properties
- **Error responses**: 5 minutes (300 seconds) - failed API calls to prevent hammering

## Directory Structure

```
src/lorekeeper_mcp/api_clients/
├── __init__.py              # Public API exports
├── base.py                  # BaseHttpClient (async)
├── factory.py               # ClientFactory for DI
├── open5e_v1.py            # Open5eV1Client
├── open5e_v2.py            # Open5eV2Client
├── dnd5e_api.py            # Dnd5eApiClient
├── exceptions.py           # Custom exception classes
└── models/                 # Pydantic response models
    ├── __init__.py
    ├── base.py             # BaseModel, common fields
    ├── spell.py            # Spell model
    ├── monster.py          # Monster model
    ├── weapon.py           # Weapon model
    ├── armor.py            # Armor model
    ├── character.py        # Class, Race, Background, Feat models
    └── rule.py             # Rule, RuleSection, Reference models
```

## Trade-offs Considered

### Single Client vs Multiple Clients
**Trade-off**: Multiple clients increase code complexity vs single client being harder to maintain
**Decision**: Multiple clients for cleaner separation of concerns

### Synchronous vs Asynchronous
**Trade-off**: Async adds complexity vs better performance for I/O bound operations
**Decision**: **Async-first architecture** - Required for integration with existing async infrastructure (aiosqlite cache, FastMCP async lifespan). All client methods will be `async def` to enable concurrent requests and non-blocking I/O.

### Strict vs Lenient Parsing
**Trade-off**: Strict validation catches errors early vs may break on API changes
**Decision**: Lenient parsing with warnings for missing/extra fields

### Factory Pattern vs Direct Instantiation
**Trade-off**: Factory adds indirection vs provides dependency injection
**Decision**: Use factory pattern for consistent client initialization with injected cache, logger, and configuration dependencies

## Future Extensibility

- Easy to add new API endpoints to existing clients
- Simple to add new API providers following the same pattern
- Cache strategy can be enhanced without changing client logic
- Response models can evolve without breaking tool implementations
