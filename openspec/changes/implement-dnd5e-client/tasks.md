# Implementation Tasks

## 1. Core D&D 5e Client Implementation

### 1.1 Create Dnd5eApiClient Class
- [x] Create `src/lorekeeper_mcp/api_clients/dnd5e_api.py` file
- [x] Implement `Dnd5eApiClient` class inheriting from `BaseHttpClient`
- [x] Configure base URL (https://www.dnd5eapi.co/api/2014/)
- [x] Set up API version handling with automatic redirect support
- [x] Configure extended cache TTL (30 days = 2,592,000 seconds) for reference data
- [x] Add source_api identifier as "dnd5e_api"

### 1.2 Factory Method
- [x] Add `create_dnd5e_api()` static method to `ClientFactory` class in `factory.py`
- [x] Import `Dnd5eApiClient` in factory module
- [x] Configure factory method with appropriate defaults (base_url, cache_ttl)
- [x] Add docstring with Args, Returns, and usage example

### 1.3 Package Exports
- [x] Import `Dnd5eApiClient` in `api_clients/__init__.py`
- [x] Add `Dnd5eApiClient` to `__all__` list
- [x] Verify imports work correctly

## 2. Rules API Implementation

### 2.1 Get Rules Method
- [x] Implement `get_rules()` async method with section filtering
- [x] Support fetching from `/rules/` endpoint (6 rule categories)
- [x] Add section parameter for filtering (adventuring, combat, equipment, spellcasting, using-ability-scores, appendix)
- [x] Parse rule categories and subsections array
- [x] Handle rule hierarchies and cross-references via URL fields
- [x] Use entity cache for rules data
- [x] Add comprehensive docstring with Args, Returns, Raises

### 2.2 Get Rule Sections Method
- [x] Implement `get_rule_sections()` async method
- [x] Support fetching from `/rule-sections/` endpoint (33 rule sections)
- [x] Add name filtering capability
- [x] Parse detailed rule mechanics and descriptions
- [x] Handle nested rule structures and references
- [x] Use entity cache for rule sections
- [x] Add comprehensive docstring with Args, Returns, Raises

## 3. Reference Data API Implementation

### 3.1 Damage Types
- [x] Implement `get_damage_types()` async method
- [x] Fetch from `/damage-types/` endpoint (13 types)
- [x] Use extended cache TTL (30 days)
- [x] Parse descriptions and mechanical information
- [x] Add comprehensive docstring

### 3.2 Weapon Properties
- [x] Implement `get_weapon_properties()` async method
- [x] Fetch from `/weapon-properties/` endpoint (11 properties)
- [x] Use extended cache TTL (30 days)
- [x] Parse property descriptions and mechanics
- [x] Add comprehensive docstring

### 3.3 Skills
- [x] Implement `get_skills()` async method
- [x] Fetch from `/skills/` endpoint (18 skills)
- [x] Use extended cache TTL (30 days)
- [x] Parse skill descriptions and ability associations
- [x] Add comprehensive docstring

### 3.4 Ability Scores
- [x] Implement `get_ability_scores()` async method
- [x] Fetch from `/ability-scores/` endpoint (6 scores)
- [x] Use extended cache TTL (30 days)
- [x] Parse ability score explanations
- [x] Add comprehensive docstring

### 3.5 Magic Schools
- [x] Implement `get_magic_schools()` async method
- [x] Fetch from `/magic-schools/` endpoint (8 schools)
- [x] Use extended cache TTL (30 days)
- [x] Parse magic school descriptions
- [x] Add comprehensive docstring

### 3.6 Languages
- [x] Implement `get_languages()` async method
- [x] Fetch from `/languages/` endpoint (16 languages)
- [x] Use extended cache TTL (30 days)
- [x] Parse language types and examples
- [x] Add comprehensive docstring

### 3.7 Proficiencies
- [x] Implement `get_proficiencies()` async method
- [x] Fetch from `/proficiencies/` endpoint (117 proficiencies)
- [x] Use extended cache TTL (30 days)
- [x] Parse proficiency categories
- [x] Add comprehensive docstring

### 3.8 Alignments
- [x] Implement `get_alignments()` async method
- [x] Fetch from `/alignments/` endpoint (9 alignments)
- [x] Use extended cache TTL (30 days)
- [x] Parse alignment descriptions
- [x] Add comprehensive docstring

## 4. Unit Testing

### 4.1 Test Infrastructure
- [x] Create `tests/test_api_clients/test_dnd5e_api.py` file
- [x] Set up pytest-asyncio fixtures for Dnd5eApiClient
- [x] Create mock response fixtures for all endpoints
- [x] Configure respx mocks for httpx requests

### 4.2 Client Initialization Tests
- [x] Test client initialization with default parameters
- [x] Test base URL configuration
- [x] Test API version handling
- [x] Test redirect handling
- [x] Test cache TTL configuration

### 4.3 Rules API Tests
- [x] Test `get_rules()` with section filtering
- [x] Test `get_rules()` without filtering (all rules)
- [x] Test `get_rule_sections()` with name filtering
- [x] Test `get_rule_sections()` without filtering
- [x] Test rule hierarchy parsing
- [x] Test cross-reference handling

### 4.4 Reference Data Tests
- [x] Test `get_damage_types()` with mocked response
- [x] Test `get_weapon_properties()` with mocked response
- [x] Test `get_skills()` with mocked response
- [x] Test `get_ability_scores()` with mocked response
- [x] Test `get_magic_schools()` with mocked response
- [x] Test `get_languages()` with mocked response
- [x] Test `get_proficiencies()` with mocked response
- [x] Test `get_alignments()` with mocked response

### 4.5 Cache Integration Tests
- [x] Test entity cache integration for rules
- [x] Test entity cache integration for rule sections
- [x] Test extended TTL for reference data
- [x] Test cache hit scenarios
- [x] Test cache miss scenarios
- [x] Test offline fallback behavior

### 4.6 Error Handling Tests
- [x] Test network error handling
- [x] Test API error responses (400, 404, 500)
- [x] Test timeout handling
- [x] Test retry logic
- [x] Test parse error handling

### 4.7 Factory Tests
- [x] Test `ClientFactory.create_dnd5e_api()` method
- [x] Test factory configuration
- [x] Test dependency injection
- [x] Verify created client has correct configuration

## 5. Code Quality and Validation

### 5.1 Code Formatting
- [x] Run `uv format` on all new code
- [x] Run `ruff` linting and fix all issues
- [x] Add type hints to all public methods
- [x] Ensure docstrings follow project conventions

### 5.2 Test Coverage
- [x] Verify test coverage exceeds 90%
- [x] Run pytest with coverage reporting
- [x] Add additional tests for any uncovered code paths

### 5.3 Integration Verification
- [x] Test client against real D&D 5e API endpoints (manual verification)
- [x] Verify cache behavior matches expectations
- [x] Test error scenarios with actual API
- [x] Validate response parsing with real data

### 5.4 OpenSpec Validation
- [x] Run `openspec validate implement-dnd5e-client --strict`
- [x] Resolve any validation errors
- [x] Verify all requirements are addressed

## Dependencies and Parallel Work

### Parallelizable Tasks:
- Reference data methods (3.1-3.8) can be implemented in parallel
- Unit tests (4.3-4.4) can be written concurrently
- Different test categories (4.3-4.7) can be written simultaneously

### Critical Path Dependencies:
- 1.1 (Core Client) must be completed before 2.x and 3.x
- 1.2 (Factory) depends on 1.1 being complete
- 1.3 (Exports) depends on 1.1 being complete
- All testing (4.x) depends on implementation (1.x, 2.x, 3.x) being complete
- Code quality (5.x) depends on all implementation and tests being complete

### Estimated Timeline:
- Phase 1 (Core): 1-2 days
- Phase 2 (Rules): 1 day
- Phase 3 (Reference): 2-3 days
- Phase 4 (Testing): 2-3 days
- Phase 5 (Validation): 1 day

**Total Estimated Time: 7-10 days**
