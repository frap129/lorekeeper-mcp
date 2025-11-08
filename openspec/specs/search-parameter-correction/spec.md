# search-parameter-correction Specification

## Purpose
TBD - created by archiving change fix-open5e-api-issues. Update Purpose after archive.
## Requirements
### Requirement: Search Parameter Standardization
All Open5e API tools SHALL use the correct `search` parameter for name-based text searches instead of the incorrect `name` parameter.

**Rationale**: The Open5e API (both v1 and v2) expects `search` as the query parameter for text-based name searches. The current implementation uses `name`, which causes all name-based searches to return zero results.

**Scope**: All tools that perform name-based searches against Open5e API endpoints

**Related Capabilities**:
- Impacts: `spell-lookup`, `creature-lookup`, `equipment-lookup`, `character-option-lookup`
- Depends on: None (standalone fix)

#### Scenario: Verify search parameter usage across all tools
- **Given**: All Open5e API tools are updated to use `search` parameter
- **When**: Each tool is called with a name search
- **Then**: All API requests use the `search` parameter instead of `name`

### Requirement: Spell Lookup Tool - Parameter Handling
The `lookup_spell` tool SHALL pass name searches using the `search` parameter to the Open5e v2 API.

**Before**:
```python
params["name"] = name
```

**After**:
```python
params["search"] = name
```

**File**: `src/lorekeeper_mcp/tools/spell_lookup.py`
**Line**: 77

#### Scenario: Search for "fireball" spell
- **Given**: User calls `lookup_spell(name="fireball")`
- **When**: Tool makes API request to Open5e v2 `/spells/` endpoint
- **Then**: API request includes `?search=fireball` parameter
- **And**: Response contains fireball-related spells (non-zero result count)

#### Scenario: Search for partial spell names
- **Given**: User calls `lookup_spell(name="magic")`
- **When**: Tool makes API request to Open5e v2 `/spells/` endpoint
- **Then**: API request includes `?search=magic` parameter
- **And**: Response contains spells with "magic" in the name

### Requirement: Creature Lookup Tool - Parameter Handling
The `lookup_creature` tool SHALL pass name searches using the `search` parameter to the Open5e v1 API.

**Before**:
```python
params["name"] = name
```

**After**:
```python
params["search"] = name
```

**File**: `src/lorekeeper_mcp/tools/creature_lookup.py`
**Line**: 78

#### Scenario: Search for "dragon" creatures
- **Given**: User calls `lookup_creature(name="dragon")`
- **When**: Tool makes API request to Open5e v1 `/monsters/` endpoint
- **Then**: API request includes `?search=dragon` parameter
- **And**: Response contains dragon-related creatures (non-zero result count)

#### Scenario: Search with additional filters
- **Given**: User calls `lookup_creature(name="goblin", cr_max=2)`
- **When**: Tool makes API request to Open5e v1 `/monsters/` endpoint
- **Then**: API request includes both `?search=goblin&cr_max=2` parameters
- **And**: Response contains goblin creatures with challenge rating ≤ 2

### Requirement: Equipment Lookup Tool - Parameter Handling
The `lookup_equipment` tool SHALL pass name searches using the `search` parameter to both Open5e v1 and v2 APIs.

**Before**:
```python
base_params["name"] = name
```

**After**:
```python
base_params["search"] = name
```

**File**: `src/lorekeeper_mcp/tools/equipment_lookup.py`
**Line**: 97

#### Scenario: Search for "longsword" equipment
- **Given**: User calls `lookup_equipment(type="weapon", name="longsword")`
- **When**: Tool makes API request to Open5e v2 `/weapons/` endpoint
- **Then**: API request includes `?search=longsword` parameter
- **And**: Response contains longsword-related weapons (non-zero result count)

#### Scenario: Search across all equipment types
- **Given**: User calls `lookup_equipment(type="all", name="chain")`
- **When**: Tool makes API requests to both v1 and v2 endpoints
- **Then**: All API requests include `?search=chain` parameter
- **And**: Response contains chain-related items from all equipment types

### Requirement: Character Option Lookup Tool - Parameter Handling
The `lookup_character_option` tool SHALL pass name searches using the `search` parameter to the appropriate Open5e API.

**Before**:
```python
params["name"] = name
```

**After**:
```python
params["search"] = name
```

**File**: `src/lorekeeper_mcp/tools/character_option_lookup.py`
**Line**: 92

#### Scenario: Search for "wizard" class
- **Given**: User calls `lookup_character_option(type="class", name="wizard")`
- **When**: Tool makes API request to Open5e API for classes
- **Then**: API request includes `?search=wizard` parameter
- **And**: Response contains wizard class information (non-zero result count)

#### Scenario: Search for racial traits
- **Given**: User calls `lookup_character_option(type="race", name="elf")`
- **When**: Tool makes API request to Open5e API for races
- **Then**: API request includes `?search=elf` parameter
- **And**: Response contains elf race information (non-zero result count)

## Validation Criteria

1. **Functional Validation**: All name-based searches return non-zero result counts when valid names are provided
2. **API Compatibility**: All API requests use correct Open5e parameter names
3. **Backward Compatibility**: All existing tool interfaces and behaviors are preserved
4. **No Regressions**: Tools that don't use name parameters continue to work unchanged

## Success Metrics

- 100% of name-based searches return results where expected
- Zero tools use deprecated `name` parameter for Open5e API calls
- All existing filtering and search capabilities continue to function
- API response times remain within acceptable ranges
