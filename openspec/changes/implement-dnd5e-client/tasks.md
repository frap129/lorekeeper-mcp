# Implementation Tasks

## 1. Core D&D 5e Client Implementation

### 1.1 Create Dnd5eApiClient Class
- [ ] Create `src/lorekeeper_mcp/api_clients/dnd5e_api.py` file
- [ ] Implement `Dnd5eApiClient` class inheriting from `BaseHttpClient`
- [ ] Configure base URL (https://www.dnd5eapi.co/api/2014/)
- [ ] Set up API version handling with automatic redirect support
- [ ] Configure extended cache TTL (30 days = 2,592,000 seconds) for reference data
- [ ] Add source_api identifier as "dnd5e_api"

### 1.2 Factory Method
- [ ] Add `create_dnd5e_api()` static method to `ClientFactory` class in `factory.py`
- [ ] Import `Dnd5eApiClient` in factory module
- [ ] Configure factory method with appropriate defaults (base_url, cache_ttl)
- [ ] Add docstring with Args, Returns, and usage example

### 1.3 Package Exports
- [ ] Import `Dnd5eApiClient` in `api_clients/__init__.py`
- [ ] Add `Dnd5eApiClient` to `__all__` list
- [ ] Verify imports work correctly

## 2. Rules API Implementation

### 2.1 Get Rules Method
- [ ] Implement `get_rules()` async method with section filtering
- [ ] Support fetching from `/rules/` endpoint (6 rule categories)
- [ ] Add section parameter for filtering (adventuring, combat, equipment, spellcasting, using-ability-scores, appendix)
- [ ] Parse rule categories and subsections array
- [ ] Handle rule hierarchies and cross-references via URL fields
- [ ] Use entity cache for rules data
- [ ] Add comprehensive docstring with Args, Returns, Raises

### 2.2 Get Rule Sections Method
- [ ] Implement `get_rule_sections()` async method
- [ ] Support fetching from `/rule-sections/` endpoint (33 rule sections)
- [ ] Add name filtering capability
- [ ] Parse detailed rule mechanics and descriptions
- [ ] Handle nested rule structures and references
- [ ] Use entity cache for rule sections
- [ ] Add comprehensive docstring with Args, Returns, Raises

## 3. Reference Data API Implementation

### 3.1 Damage Types
- [ ] Implement `get_damage_types()` async method
- [ ] Fetch from `/damage-types/` endpoint (13 types)
- [ ] Use extended cache TTL (30 days)
- [ ] Parse descriptions and mechanical information
- [ ] Add comprehensive docstring

### 3.2 Weapon Properties
- [ ] Implement `get_weapon_properties()` async method
- [ ] Fetch from `/weapon-properties/` endpoint (11 properties)
- [ ] Use extended cache TTL (30 days)
- [ ] Parse property descriptions and mechanics
- [ ] Add comprehensive docstring

### 3.3 Skills
- [ ] Implement `get_skills()` async method
- [ ] Fetch from `/skills/` endpoint (18 skills)
- [ ] Use extended cache TTL (30 days)
- [ ] Parse skill descriptions and ability associations
- [ ] Add comprehensive docstring

### 3.4 Ability Scores
- [ ] Implement `get_ability_scores()` async method
- [ ] Fetch from `/ability-scores/` endpoint (6 scores)
- [ ] Use extended cache TTL (30 days)
- [ ] Parse ability score explanations
- [ ] Add comprehensive docstring

### 3.5 Magic Schools
- [ ] Implement `get_magic_schools()` async method
- [ ] Fetch from `/magic-schools/` endpoint (8 schools)
- [ ] Use extended cache TTL (30 days)
- [ ] Parse magic school descriptions
- [ ] Add comprehensive docstring

### 3.6 Languages
- [ ] Implement `get_languages()` async method
- [ ] Fetch from `/languages/` endpoint (16 languages)
- [ ] Use extended cache TTL (30 days)
- [ ] Parse language types and examples
- [ ] Add comprehensive docstring

### 3.7 Proficiencies
- [ ] Implement `get_proficiencies()` async method
- [ ] Fetch from `/proficiencies/` endpoint (117 proficiencies)
- [ ] Use extended cache TTL (30 days)
- [ ] Parse proficiency categories
- [ ] Add comprehensive docstring

### 3.8 Alignments
- [ ] Implement `get_alignments()` async method
- [ ] Fetch from `/alignments/` endpoint (9 alignments)
- [ ] Use extended cache TTL (30 days)
- [ ] Parse alignment descriptions
- [ ] Add comprehensive docstring

## 4. Unit Testing

### 4.1 Test Infrastructure
- [ ] Create `tests/test_api_clients/test_dnd5e_api.py` file
- [ ] Set up pytest-asyncio fixtures for Dnd5eApiClient
- [ ] Create mock response fixtures for all endpoints
- [ ] Configure respx mocks for httpx requests

### 4.2 Client Initialization Tests
- [ ] Test client initialization with default parameters
- [ ] Test base URL configuration
- [ ] Test API version handling
- [ ] Test redirect handling
- [ ] Test cache TTL configuration

### 4.3 Rules API Tests
- [ ] Test `get_rules()` with section filtering
- [ ] Test `get_rules()` without filtering (all rules)
- [ ] Test `get_rule_sections()` with name filtering
- [ ] Test `get_rule_sections()` without filtering
- [ ] Test rule hierarchy parsing
- [ ] Test cross-reference handling

### 4.4 Reference Data Tests
- [ ] Test `get_damage_types()` with mocked response
- [ ] Test `get_weapon_properties()` with mocked response
- [ ] Test `get_skills()` with mocked response
- [ ] Test `get_ability_scores()` with mocked response
- [ ] Test `get_magic_schools()` with mocked response
- [ ] Test `get_languages()` with mocked response
- [ ] Test `get_proficiencies()` with mocked response
- [ ] Test `get_alignments()` with mocked response

### 4.5 Cache Integration Tests
- [ ] Test entity cache integration for rules
- [ ] Test entity cache integration for rule sections
- [ ] Test extended TTL for reference data
- [ ] Test cache hit scenarios
- [ ] Test cache miss scenarios
- [ ] Test offline fallback behavior

### 4.6 Error Handling Tests
- [ ] Test network error handling
- [ ] Test API error responses (400, 404, 500)
- [ ] Test timeout handling
- [ ] Test retry logic
- [ ] Test parse error handling

### 4.7 Factory Tests
- [ ] Test `ClientFactory.create_dnd5e_api()` method
- [ ] Test factory configuration
- [ ] Test dependency injection
- [ ] Verify created client has correct configuration

## 5. Code Quality and Validation

### 5.1 Code Formatting
- [ ] Run `uv format` on all new code
- [ ] Run `ruff` linting and fix all issues
- [ ] Add type hints to all public methods
- [ ] Ensure docstrings follow project conventions

### 5.2 Test Coverage
- [ ] Verify test coverage exceeds 90%
- [ ] Run pytest with coverage reporting
- [ ] Add additional tests for any uncovered code paths

### 5.3 Integration Verification
- [ ] Test client against real D&D 5e API endpoints (manual verification)
- [ ] Verify cache behavior matches expectations
- [ ] Test error scenarios with actual API
- [ ] Validate response parsing with real data

### 5.4 OpenSpec Validation
- [ ] Run `openspec validate implement-dnd5e-client --strict`
- [ ] Resolve any validation errors
- [ ] Verify all requirements are addressed

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
