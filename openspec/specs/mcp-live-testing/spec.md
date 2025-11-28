# mcp-live-testing Specification

## Purpose
Defines the live API testing infrastructure for validating MCP tools against real Open5e endpoints. Includes test isolation, rate limiting, performance validation, cache behavior verification, and comprehensive scenarios for all five lookup tools (spell, creature, equipment, character option, rule).
## Requirements
### Requirement: Live Test Infrastructure
The testing framework SHALL provide infrastructure for executing tests against live Open5e and D&D 5e APIs with proper isolation, rate limiting, and performance tracking.

#### Scenario: Live tests are marked and skippable
- **GIVEN** the test suite contains live API tests
- **WHEN** a developer runs `pytest -m "not live"`
- **THEN** all live tests SHALL be skipped
- **AND** unit tests with mocks SHALL execute normally

#### Scenario: Live tests can be run selectively
- **GIVEN** the test suite contains both unit and live tests
- **WHEN** a developer runs `pytest -m live`
- **THEN** only live API tests SHALL execute
- **AND** unit tests SHALL be skipped

#### Scenario: Rate limiting prevents API throttling
- **GIVEN** multiple live tests execute in sequence
- **WHEN** tests make API calls to the same endpoint
- **THEN** the framework SHALL enforce minimum delay between calls
- **AND** no API rate limit errors SHALL occur

#### Scenario: Test database is isolated from production
- **GIVEN** a live test is executing
- **WHEN** the test writes to the cache
- **THEN** a temporary test database SHALL be used
- **AND** production cache SHALL NOT be affected

### Requirement: Spell Lookup Live Validation
The live test suite SHALL validate lookup_spell functionality against real API data including successful queries, filtering, edge cases, cache behavior, and error handling.

#### Scenario: Basic spell lookup by name succeeds
- **GIVEN** a well-known spell exists in the API
- **WHEN** lookup_spell is called with name="Magic Missile"
- **THEN** at least one result SHALL be returned
- **AND** the first result SHALL have name matching "Magic Missile"
- **AND** required fields (level, school, description) SHALL be present

#### Scenario: Spell not found returns empty results
- **GIVEN** a non-existent spell name
- **WHEN** lookup_spell is called with name="NonexistentSpell12345"
- **THEN** an empty list SHALL be returned
- **AND** no exception SHALL be raised

#### Scenario: Spell filtering by level works correctly
- **GIVEN** the API contains cantrips
- **WHEN** lookup_spell is called with level=0
- **THEN** all returned spells SHALL have level equal to 0
- **AND** at least 5 results SHALL be available

#### Scenario: Spell filtering by school works correctly
- **GIVEN** the API contains evocation spells
- **WHEN** lookup_spell is called with school="evocation"
- **THEN** all returned spells SHALL have school equal to "Evocation"
- **AND** at least 3 results SHALL be available

#### Scenario: Combined spell filters work correctly
- **GIVEN** the API contains wizard concentration spells
- **WHEN** lookup_spell is called with class_key="wizard" and concentration=True
- **THEN** all results SHALL be concentration spells
- **AND** all results SHALL be available to wizards
- **AND** at least 5 results SHALL be available

#### Scenario: Spell lookup caches results
- **GIVEN** lookup_spell has not been called for a specific query
- **WHEN** the same query is executed twice in succession
- **THEN** the second call SHALL use cached data
- **AND** the second call SHALL complete in under 50ms

#### Scenario: Spell limit parameter is respected
- **GIVEN** the API contains many spells
- **WHEN** lookup_spell is called with limit=5
- **THEN** exactly 5 or fewer results SHALL be returned

#### Scenario: Invalid spell parameters are handled gracefully
- **GIVEN** an invalid parameter value
- **WHEN** lookup_spell is called with an invalid school name
- **THEN** an empty list SHALL be returned OR an appropriate error SHALL be raised
- **AND** the system SHALL NOT crash

### Requirement: Creature Lookup Live Validation
The live test suite SHALL validate lookup_creature functionality against real API data including CR filtering, type filtering, and size filtering.

#### Scenario: Basic creature lookup by name succeeds
- **GIVEN** a well-known creature exists in the API
- **WHEN** lookup_creature is called with name="Goblin"
- **THEN** at least one result SHALL be returned
- **AND** the result SHALL have name matching "Goblin"
- **AND** required fields (challenge_rating, type, hit_points) SHALL be present

#### Scenario: Creature filtering by CR works correctly
- **GIVEN** the API contains CR 1 creatures
- **WHEN** lookup_creature is called with cr=1
- **THEN** all returned creatures SHALL have challenge_rating equal to "1"
- **AND** at least 3 results SHALL be available

#### Scenario: Creature filtering by CR range works correctly
- **GIVEN** the API contains creatures of various CRs
- **WHEN** lookup_creature is called with cr_min=5 and cr_max=10
- **THEN** all returned creatures SHALL have CR between 5 and 10 inclusive
- **AND** at least 5 results SHALL be available

#### Scenario: Creature filtering by type works correctly
- **GIVEN** the API contains beast creatures
- **WHEN** lookup_creature is called with type="beast"
- **THEN** all returned creatures SHALL have type equal to "beast"
- **AND** at least 5 results SHALL be available

#### Scenario: Creature filtering by size works correctly
- **GIVEN** the API contains Large creatures
- **WHEN** lookup_creature is called with size="Large"
- **THEN** all returned creatures SHALL have size equal to "Large"
- **AND** at least 3 results SHALL be available

#### Scenario: Creature lookup caches results
- **GIVEN** lookup_creature has not been called for a specific query
- **WHEN** the same query is executed twice in succession
- **THEN** the second call SHALL use cached data
- **AND** the second call SHALL complete in under 50ms

### Requirement: Equipment Lookup Live Validation
The live test suite SHALL validate lookup_equipment functionality for weapons, armor, magic items, and general equipment.

#### Scenario: Weapon lookup by name succeeds
- **GIVEN** a well-known weapon exists in the API
- **WHEN** lookup_equipment is called with type="weapon" and name="Longsword"
- **THEN** at least one result SHALL be returned
- **AND** the result SHALL contain weapon properties (damage_dice, damage_type)

#### Scenario: Armor lookup succeeds
- **GIVEN** the API contains armor items
- **WHEN** lookup_equipment is called with type="armor"
- **THEN** at least 5 armor items SHALL be returned
- **AND** each result SHALL contain armor_class information

#### Scenario: Magic item lookup with rarity filter works
- **GIVEN** the API contains rare magic items
- **WHEN** lookup_equipment is called with type="magic-item" and rarity="rare"
- **THEN** all returned items SHALL have rarity equal to "rare"
- **AND** at least 3 results SHALL be available

#### Scenario: Equipment type "all" searches across categories
- **GIVEN** the API contains various equipment types
- **WHEN** lookup_equipment is called with type="all" and name="sword"
- **THEN** results MAY include weapons, magic items, or other equipment
- **AND** all results SHALL have "sword" in the name

#### Scenario: Equipment lookup caches results
- **GIVEN** lookup_equipment has not been called for a specific query
- **WHEN** the same query is executed twice in succession
- **THEN** the second call SHALL use cached data
- **AND** the second call SHALL complete in under 50ms

### Requirement: Character Option Lookup Live Validation
The live test suite SHALL validate lookup_character_option functionality for classes, races, backgrounds, and feats.

#### Scenario: Class lookup succeeds
- **GIVEN** the API contains D&D classes
- **WHEN** lookup_character_option is called with type="class"
- **THEN** at least 12 classes SHALL be returned
- **AND** results SHALL include "Wizard", "Fighter", and "Cleric"

#### Scenario: Race lookup succeeds
- **GIVEN** the API contains D&D races
- **WHEN** lookup_character_option is called with type="race"
- **THEN** at least 9 races SHALL be returned
- **AND** results SHALL include "Human", "Elf", and "Dwarf"

#### Scenario: Background lookup succeeds
- **GIVEN** the API contains D&D backgrounds
- **WHEN** lookup_character_option is called with type="background"
- **THEN** at least 10 backgrounds SHALL be returned

#### Scenario: Feat lookup succeeds
- **GIVEN** the API contains D&D feats
- **WHEN** lookup_character_option is called with type="feat"
- **THEN** at least 20 feats SHALL be returned

#### Scenario: Character option name filtering works
- **GIVEN** the API contains classes
- **WHEN** lookup_character_option is called with type="class" and name="wiz"
- **THEN** at least one result matching "Wizard" SHALL be returned

#### Scenario: Character option lookup caches results
- **GIVEN** lookup_character_option has not been called for a specific query
- **WHEN** the same query is executed twice in succession
- **THEN** the second call SHALL use cached data
- **AND** the second call SHALL complete in under 50ms

### Requirement: Rule Lookup Live Validation
The live test suite SHALL validate lookup_rule functionality for conditions, damage types, skills, ability scores, and magic schools.

#### Scenario: Condition lookup succeeds
- **GIVEN** the API contains D&D conditions
- **WHEN** lookup_rule is called with rule_type="condition"
- **THEN** at least 10 conditions SHALL be returned
- **AND** results SHALL include "Prone", "Grappled", "Blinded"

#### Scenario: Damage type lookup succeeds
- **GIVEN** the API contains D&D damage types
- **WHEN** lookup_rule is called with rule_type="damage-type"
- **THEN** at least 10 damage types SHALL be returned
- **AND** results SHALL include "Fire", "Cold", "Slashing"

#### Scenario: Skill lookup succeeds
- **GIVEN** the API contains D&D skills
- **WHEN** lookup_rule is called with rule_type="skill"
- **THEN** exactly 18 skills SHALL be returned
- **AND** results SHALL include "Perception", "Stealth", "Athletics"

#### Scenario: Ability score lookup succeeds
- **GIVEN** the API contains D&D ability scores
- **WHEN** lookup_rule is called with rule_type="ability-score"
- **THEN** exactly 6 ability scores SHALL be returned
- **AND** results SHALL include "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"

#### Scenario: Magic school lookup succeeds
- **GIVEN** the API contains D&D magic schools
- **WHEN** lookup_rule is called with rule_type="magic-school"
- **THEN** exactly 8 magic schools SHALL be returned
- **AND** results SHALL include "Evocation", "Abjuration", "Conjuration"

#### Scenario: Rule name filtering works
- **GIVEN** the API contains conditions
- **WHEN** lookup_rule is called with rule_type="condition" and name="grappl"
- **THEN** at least one result matching "Grappled" SHALL be returned

#### Scenario: Rule lookup caches results
- **GIVEN** lookup_rule has not been called for a specific query
- **WHEN** the same query is executed twice in succession
- **THEN** the second call SHALL use cached data
- **AND** the second call SHALL complete in under 50ms

### Requirement: Cache Behavior Validation
The live test suite SHALL validate that caching works correctly with live API data including cache hits, misses, and TTL enforcement.

#### Scenario: Cache miss triggers API call
- **GIVEN** the cache does not contain data for a query
- **WHEN** a tool function is called
- **THEN** an API request SHALL be made
- **AND** the response SHALL be stored in the cache
- **AND** the response time SHALL be consistent with API latency (>100ms)

#### Scenario: Cache hit avoids API call
- **GIVEN** the cache contains fresh data for a query
- **WHEN** the same tool function is called again
- **THEN** no API request SHALL be made
- **AND** data SHALL be retrieved from cache
- **AND** the response time SHALL be under 50ms

#### Scenario: Different queries use different cache entries
- **GIVEN** multiple different queries are executed
- **WHEN** each query is executed twice
- **THEN** each unique query SHALL have its own cache entry
- **AND** repeated queries SHALL hit their respective caches

### Requirement: Performance Validation
The live test suite SHALL validate that tool functions meet performance targets with live APIs and caching.

#### Scenario: Uncached API call completes within time limit
- **GIVEN** the cache is empty
- **WHEN** any tool function is called
- **THEN** the call SHALL complete within 3 seconds
- **AND** results SHALL be returned

#### Scenario: Cached lookup is fast
- **GIVEN** data is cached
- **WHEN** the same query is repeated
- **THEN** the call SHALL complete within 50ms
- **AND** correct results SHALL be returned

#### Scenario: Parallel requests are handled correctly
- **GIVEN** multiple different queries
- **WHEN** all queries are executed concurrently
- **THEN** all queries SHALL complete successfully
- **AND** total time SHALL be less than sequential execution

### Requirement: Error Handling Validation
The live test suite SHALL validate that tool functions handle errors gracefully including network issues, invalid parameters, and empty results.

#### Scenario: Invalid parameter type is handled gracefully
- **GIVEN** a tool function expects a string parameter
- **WHEN** called with an invalid type (e.g., very large negative number for limit)
- **THEN** the function SHALL either return empty results OR raise appropriate exception
- **AND** the system SHALL NOT crash

#### Scenario: Empty results are handled gracefully
- **GIVEN** a query matches no data
- **WHEN** a tool function is called
- **THEN** an empty list SHALL be returned
- **AND** no exception SHALL be raised

#### Scenario: Network timeout is handled (optional)
- **GIVEN** a simulated network timeout condition
- **WHEN** a tool function is called
- **THEN** the function SHALL retry OR raise a network error
- **AND** the system SHALL recover gracefully

### Requirement: Test Documentation
The project SHALL provide clear documentation for running and maintaining live tests.

#### Scenario: Developer can run live tests
- **GIVEN** a developer wants to validate against live APIs
- **WHEN** they read the testing documentation
- **THEN** instructions for running live tests SHALL be provided
- **AND** expected behavior SHALL be documented
- **AND** troubleshooting tips SHALL be included

#### Scenario: Developer can skip live tests
- **GIVEN** a developer wants to run only fast unit tests
- **WHEN** they read the testing documentation
- **THEN** instructions for skipping live tests SHALL be provided
- **AND** the pytest command SHALL be documented

#### Scenario: Test failures are interpretable
- **GIVEN** a live test fails
- **WHEN** a developer reviews the failure
- **THEN** the error message SHALL clearly indicate the failure reason
- **AND** guidance for resolution SHALL be provided (if applicable)
