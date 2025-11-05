# Implementation Tasks

## Phase 1: Foundation Infrastructure

### 1.1 Base HTTP Client Implementation
- [ ] Create `BaseHttpClient` class in `src/lorekeeper_mcp/api_clients/base.py` (async)
- [ ] Implement async HTTP request method with retry logic and exponential backoff (1s → 2s → 4s → 8s → 16s → 32s max)
- [ ] Add timeout configuration (default: 30s) and rate limiting
- [ ] Integrate with async SQLite cache (`cache.db.get_cached()`, `cache.db.set_cached()`)
- [ ] Create custom exception classes in `src/lorekeeper_mcp/api_clients/exceptions.py` (ApiClientError, NetworkError, ApiError, ParseError, CacheError)
- [ ] Add async request/response logging with appropriate log levels
- [ ] Create async unit tests for base client functionality using pytest-asyncio

### 1.2 Response Model Infrastructure
- [ ] Create directory `src/lorekeeper_mcp/api_clients/models/`
- [ ] Create Pydantic base model in `models/base.py` for common fields (name, description, url, etc.)
- [ ] Create specific models: `models/spell.py`, `models/monster.py`, `models/weapon.py`, `models/armor.py`, `models/character.py` (Class, Race, Background, Feat), `models/rule.py` (Rule, RuleSection)
- [ ] Add data validation and serialization methods to each model
- [ ] Implement field normalization utilities for API version differences
- [ ] Create unit tests for response models with validation scenarios

### 1.3 Client Factory Setup
- [ ] Create `ClientFactory` class in `src/lorekeeper_mcp/api_clients/factory.py`
- [ ] Implement factory methods for each API client type
- [ ] Add configuration management for client instances
- [ ] Integrate dependency injection for cache and logging
- [ ] Create unit tests for factory functionality

## Phase 2: Open5e v1 API Client

### 2.1 Core Open5e v1 Client
- [ ] Create `Open5eV1Client` class in `src/lorekeeper_mcp/api_clients/open5e_v1.py` inheriting from `BaseHttpClient`
- [ ] Implement base URL configuration (https://api.open5e.com/v1/) and endpoint mapping
- [ ] Add async pagination handling for large result sets (3,207+ monsters, 1,618+ items)
- [ ] Create async unit tests for client initialization and configuration

### 2.2 Monsters API Implementation
- [ ] Implement async `get_monsters()` method with filtering (name, CR, type, size)
- [ ] Add CR range search support (cr_min, cr_max) for challenge rating queries
- [ ] Parse monster stat blocks and abilities using Monster Pydantic model
- [ ] Handle monster actions, traits, legendary actions, and lair actions
- [ ] Create async unit tests for monsters API with various filter combinations and mocked responses

### 2.3 Classes API Implementation
- [ ] Implement async `get_classes()` method with name filtering
- [ ] Parse class features and progression tables using Class Pydantic model
- [ ] Handle subclasses and archetypes (12+ classes with multiple subclasses each)
- [ ] Extract proficiencies and spellcasting information
- [ ] Create async unit tests for classes API with mocked responses

### 2.4 Races API Implementation
- [ ] Implement async `get_races()` method with name filtering
- [ ] Parse racial traits and ability score increases using Race Pydantic model
- [ ] Handle subraces and racial features (20+ races with subraces)
- [ ] Extract speed, languages, and special abilities
- [ ] Create async unit tests for races API with mocked responses

### 2.5 Magic Items API Implementation
- [ ] Implement async `get_magic_items()` method with name and rarity filtering
- [ ] Parse item descriptions and effects using MagicItem Pydantic model
- [ ] Handle attunement requirements and item types (1,618+ items)
- [ ] Extract mechanical properties and flavor text
- [ ] Create async unit tests for magic items API with mocked responses

## Phase 3: Open5e v2 API Client

### 3.1 Core Open5e v2 Client
- [ ] Create `Open5eV2Client` class in `src/lorekeeper_mcp/api_clients/open5e_v2.py` inheriting from `BaseHttpClient`
- [ ] Implement base URL configuration (https://api.open5e.com/v2/) and endpoint mapping
- [ ] Add support for v2-specific response structures (document references, gamesystem metadata)
- [ ] Create async unit tests for client initialization and configuration

### 3.2 Spells API Implementation
- [ ] Implement async `get_spells()` method with comprehensive filtering (name, level, school, class_key, concentration, ritual, casting_time)
- [ ] Add support for 8 magic schools, 10+ casting time types, boolean filters
- [ ] Parse spell components, material costs, and material_consumed flag using Spell Pydantic model
- [ ] Handle higher level effects, casting_options array, and v2-specific fields
- [ ] Extract damage_roll, damage_types array, saving_throw_ability information
- [ ] Create async unit tests for spells API with complex filter scenarios (1,774+ spells) and mocked responses

### 3.3 Weapons API Implementation
- [ ] Implement async `get_weapons()` method with filtering (name, damage_dice, is_simple, is_finesse, is_versatile, etc.)
- [ ] Parse weapon properties array and mastery features using Weapon Pydantic model (75 weapons)
- [ ] Handle damage_type references, range/long_range, and distance_unit fields
- [ ] Distinguish simple vs martial weapons with is_simple boolean
- [ ] Create async unit tests for weapons API with mocked responses

### 3.4 Armor API Implementation
- [ ] Implement async `get_armor()` method with name and category filtering (light/medium/heavy/shield)
- [ ] Parse AC values (ac_base, ac_add_dexmod, ac_cap_dexmod) and ac_display using Armor Pydantic model (25 armor pieces)
- [ ] Handle strength_score_required and grants_stealth_disadvantage flags
- [ ] Process shields and armor types consistently
- [ ] Create async unit tests for armor API with mocked responses

### 3.5 Character Options APIs
- [ ] Implement async `get_backgrounds()` method with name filtering (54 backgrounds)
- [ ] Implement async `get_feats()` method with name and type filtering (91 feats)
- [ ] Parse background benefits array and feat benefits/prerequisite using Background and Feat Pydantic models
- [ ] Handle skill proficiencies, tool proficiencies, and equipment grants
- [ ] Create async unit tests for backgrounds and feats APIs with mocked responses

### 3.6 Conditions API Implementation
- [ ] Implement async `get_conditions()` method with name filtering (21 conditions)
- [ ] Parse condition descriptions array and mechanical effects using Condition Pydantic model
- [ ] Handle condition interactions and removal criteria (gamesystem-specific)
- [ ] Create async unit tests for conditions API with mocked responses

## Phase 4: D&D 5e API Client

### 4.1 Core D&D 5e Client
- [ ] Create `Dnd5eApiClient` class in `src/lorekeeper_mcp/api_clients/dnd5e_api.py` inheriting from `BaseHttpClient`
- [ ] Implement base URL configuration (https://www.dnd5eapi.co/api/2014/) and API version handling
- [ ] Add support for automatic redirects from /api/ to /api/2014/ endpoints
- [ ] Create async unit tests for client initialization and version handling

### 4.2 Rules API Implementation
- [ ] Implement async `get_rules()` method with section filtering (adventuring, combat, equipment, spellcasting, using-ability-scores, appendix)
- [ ] Parse rule categories, subsections array, and desc using Rule Pydantic model (6 rule categories)
- [ ] Handle rule hierarchies and cross-references via URL fields
- [ ] Implement async `get_rule_sections()` for detailed rule information (33 rule sections)
- [ ] Create async unit tests for rules API with mocked responses

### 4.3 Reference Data APIs
- [ ] Implement async reference data methods: `get_damage_types()` (13 types), `get_weapon_properties()` (11 properties), `get_skills()` (18 skills), `get_ability_scores()` (6 scores), `get_magic_schools()` (8 schools), `get_languages()` (16 languages), `get_proficiencies()` (117 proficiencies), `get_alignments()` (9 alignments)
- [ ] Add extended caching with 30-day TTL (2,592,000 seconds) for reference data
- [ ] Parse reference descriptions and mechanical information using Reference Pydantic model
- [ ] Handle cross-references between reference types via index/url fields
- [ ] Create async unit tests for all reference data APIs with mocked responses

## Phase 5: Integration and Testing

### 5.1 Mock Infrastructure
- [ ] Create `tests/fixtures/` directory with JSON mock response files
- [ ] Add mock responses for each endpoint (spell.json, monster.json, etc.)
- [ ] Configure `respx` mock routes for httpx in test fixtures
- [ ] Create shared test fixtures for common scenarios (cache hits/misses, network errors, API errors)
- [ ] Add fixture for testing pagination (large result sets)

### 5.2 Integration Testing
- [ ] Create async integration tests for all API clients using respx mocks
- [ ] Test cache integration across all clients (cache hit, cache miss, cache expiry)
- [ ] Verify error handling and retry logic with simulated network failures
- [ ] Test client factory and configuration dependency injection
- [ ] Add async performance tests for concurrent API requests

### 5.3 End-to-End Testing
- [ ] Create async end-to-end tests simulating real MCP tool usage patterns
- [ ] Test complex search scenarios across multiple APIs (e.g., spell + class lookup)
- [ ] Verify data consistency between API versions (v1 vs v2 response normalization)
- [ ] Test offline capability with pre-populated cached data
- [ ] Add async load testing for concurrent requests (10+ simultaneous)

### 5.4 Documentation and Examples
- [ ] Add comprehensive docstrings to all public async methods (Args, Returns, Raises)
- [ ] Create async usage examples for each API client in `examples/` directory
- [ ] Document configuration options (timeouts, retry limits, cache TTLs) and error handling
- [ ] Add troubleshooting guide for common issues (rate limits, timeouts, parse errors)
- [ ] Create async/await best practices guide for API client usage

## Phase 6: Validation and Deployment

### 6.1 Code Quality
- [ ] Run `uv format` on all new code
- [ ] Run `ruff` linting and fix all issues
- [ ] Ensure test coverage exceeds 90%
- [ ] Add type hints to all public interfaces
- [ ] Review and optimize performance bottlenecks

### 6.2 Final Validation
- [ ] Validate all requirements are met
- [ ] Test against real API endpoints
- [ ] Verify cache behavior and TTL settings
- [ ] Test error scenarios and recovery
- [ ] Validate integration with existing codebase

### 6.3 Deployment Preparation
- [ ] Update `__init__.py` files with proper exports
- [ ] Add API clients to project dependencies if needed
- [ ] Update documentation with new capabilities
- [ ] Prepare changelog and release notes
- [ ] Final code review and approval

## Dependencies and Parallel Work

### Parallelizable Tasks:
- Base client implementation can be done in parallel with response model creation
- Different API clients can be implemented simultaneously once base infrastructure is ready
- Unit tests can be written in parallel with implementation

### Critical Path Dependencies:
- Phase 1 (Foundation) must be completed before other phases
- Each API client depends on the base client being functional
- Integration testing depends on all API clients being implemented
- Final validation depends on all previous phases being complete

### Estimated Timeline:
- Phase 1: 3-4 days
- Phase 2: 4-5 days
- Phase 3: 5-6 days
- Phase 4: 3-4 days
- Phase 5: 3-4 days
- Phase 6: 2-3 days

**Total Estimated Time: 20-26 days**
