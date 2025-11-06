# Implementation Tasks: Implement MCP Tools

## Task Sequence

### 1. Create tool module structure
**Description**: Set up the tools module with proper imports and helper utilities.

**Acceptance Criteria**:
- [ ] `src/lorekeeper_mcp/tools/__init__.py` exports all tool functions
- [ ] Helper functions created for common patterns (error handling, response formatting)
- [ ] Type hints and docstrings follow project conventions

**Validation**: `python -c "from lorekeeper_mcp.tools import *"`

**Dependencies**: None

---

### 2. Implement `lookup_spell` tool
**Description**: Implement spell lookup using Open5e v2 API client.

**Acceptance Criteria**:
- [ ] Tool registered with FastMCP using `@mcp.tool()` decorator
- [ ] Accepts all parameters from spec: name, level, school, class_key, concentration, ritual, casting_time, limit
- [ ] Calls `Open5eV2Client.get_spells()` with appropriate filters
- [ ] Returns structured spell data with source attribution
- [ ] Handles errors gracefully (API failures, empty results, invalid parameters)
- [ ] Unit tests cover happy path, error cases, and parameter validation

**Validation**:
```python
# Tool can be invoked
result = await lookup_spell(name="fireball")
assert len(result) > 0
```

**Dependencies**: Task 1

---

### 3. Implement `lookup_creature` tool
**Description**: Implement creature/monster lookup using Open5e v1 API client.

**Acceptance Criteria**:
- [ ] Tool registered with FastMCP
- [ ] Accepts parameters: name, cr, cr_min, cr_max, type, size, limit
- [ ] Calls `Open5eV1Client.get_monsters()` with appropriate filters
- [ ] Returns full stat blocks with source attribution
- [ ] Handles CR decimal values (0.125, 0.25, 0.5) correctly
- [ ] Unit tests cover CR ranges, creature types, and edge cases

**Validation**:
```python
# Test CR filtering
result = await lookup_creature(cr=5, type="undead")
assert all(r["challenge_rating"] == 5 for r in result)
```

**Dependencies**: Task 1

---

### 4. Implement `lookup_character_option` tool
**Description**: Implement character option lookup for classes, races, backgrounds, and feats.

**Acceptance Criteria**:
- [ ] Tool registered with FastMCP
- [ ] Accepts parameters: type (required), name, limit
- [ ] Routes to correct API client based on `type`:
  - `class` → Open5eV1Client.get_classes()
  - `race` → Open5eV1Client.get_races()
  - `background` → Open5eV2Client.get_backgrounds()
  - `feat` → Open5eV2Client.get_feats()
- [ ] Returns appropriate data structure for each type
- [ ] Validates `type` parameter (must be one of: class, race, background, feat)
- [ ] Unit tests cover all four option types and invalid type handling

**Validation**:
```python
# Test each type
classes = await lookup_character_option(type="class", name="paladin")
races = await lookup_character_option(type="race", name="elf")
backgrounds = await lookup_character_option(type="background")
feats = await lookup_character_option(type="feat", name="sharpshooter")
```

**Dependencies**: Task 1

---

### 5. Implement `lookup_equipment` tool
**Description**: Implement equipment lookup for weapons, armor, and magic items.

**Acceptance Criteria**:
- [ ] Tool registered with FastMCP
- [ ] Accepts parameters: type, name, rarity, damage_dice, is_simple, requires_attunement, limit
- [ ] Routes based on `type`:
  - `weapon` → Open5eV2Client.get_weapons()
  - `armor` → Open5eV2Client.get_armor()
  - `magic-item` → (needs implementation - see note)
  - `all` → Query all three endpoints and merge results
- [ ] Filters weapon results by damage_dice, is_simple if provided
- [ ] Filters magic items by rarity, requires_attunement if provided
- [ ] Unit tests cover all equipment types and filters

**Note**: Open5e v1 magic items endpoint may need to be added to Open5eV1Client if not present.

**Validation**:
```python
# Test filtering
weapons = await lookup_equipment(type="weapon", is_simple=True)
magic = await lookup_equipment(type="magic-item", rarity="rare")
```

**Dependencies**: Task 1

---

### 6. Implement `lookup_rule` tool
**Description**: Implement rules and reference lookup using D&D 5e API and Open5e v2.

**Acceptance Criteria**:
- [ ] Tool registered with FastMCP
- [ ] Accepts parameters: type (required), name, section, limit
- [ ] Routes based on `type`:
  - `rule` → Dnd5eApiClient.get_rules()
  - `condition` → Open5eV2Client.get_conditions()
  - `damage-type` → Dnd5eApiClient.get_damage_types()
  - `weapon-property` → Dnd5eApiClient.get_weapon_properties()
  - `skill` → Dnd5eApiClient.get_skills()
  - `ability-score` → Dnd5eApiClient.get_ability_scores()
  - `magic-school` → Dnd5eApiClient.get_magic_schools()
  - `language` → Dnd5eApiClient.get_languages()
  - `proficiency` → Dnd5eApiClient.get_proficiencies()
  - `alignment` → Dnd5eApiClient.get_alignments()
- [ ] Validates `type` parameter against allowed values
- [ ] Uses `section` parameter for rule lookups
- [ ] Unit tests cover all reference types

**Validation**:
```python
# Test different types
conditions = await lookup_rule(type="condition", name="grappled")
rules = await lookup_rule(type="rule", section="combat")
damage = await lookup_rule(type="damage-type", name="radiant")
```

**Dependencies**: Task 1

---

### 7. Register all tools with FastMCP server
**Description**: Import and register tools in server.py so they're available to MCP clients.

**Acceptance Criteria**:
- [ ] All tool functions imported in `server.py`
- [ ] Tools registered before server starts (or use auto-discovery)
- [ ] Server startup confirms tools are available
- [ ] MCP protocol schema includes all 5 tools

**Validation**:
```python
from lorekeeper_mcp.server import mcp
assert len(mcp.tools) >= 5
tool_names = {t.name for t in mcp.tools}
assert "lookup_spell" in tool_names
assert "lookup_creature" in tool_names
assert "lookup_character_option" in tool_names
assert "lookup_equipment" in tool_names
assert "lookup_rule" in tool_names
```

**Dependencies**: Tasks 2, 3, 4, 5, 6

---

### 8. Write comprehensive unit tests
**Description**: Create test files for each tool with comprehensive coverage.

**Acceptance Criteria**:
- [ ] `tests/test_tools/test_spell_lookup.py` created with 90%+ coverage
- [ ] `tests/test_tools/test_creature_lookup.py` created with 90%+ coverage
- [ ] `tests/test_tools/test_character_option_lookup.py` created with 90%+ coverage
- [ ] `tests/test_tools/test_equipment_lookup.py` created with 90%+ coverage
- [ ] `tests/test_tools/test_rule_lookup.py` created with 90%+ coverage
- [ ] Tests use mocked API clients (no real API calls)
- [ ] Tests verify error handling, edge cases, and parameter validation
- [ ] All tests pass with `pytest tests/test_tools/`

**Validation**: `pytest tests/test_tools/ --cov=lorekeeper_mcp.tools --cov-report=term-missing`

**Dependencies**: Tasks 2-6

---

### 9. Integration testing
**Description**: Test tools end-to-end with mocked API responses.

**Acceptance Criteria**:
- [ ] `tests/test_tools/test_integration.py` created
- [ ] Tests verify tool registration with FastMCP
- [ ] Tests verify parameter validation through FastMCP
- [ ] Tests verify response format matches MCP protocol
- [ ] Integration tests use fixtures from `conftest.py`

**Validation**: `pytest tests/test_tools/test_integration.py -v`

**Dependencies**: Task 7, 8

---

### 10. Update documentation
**Description**: Ensure README and documentation reflect implemented tools.

**Acceptance Criteria**:
- [ ] README.md tool descriptions match implementation
- [ ] Code comments and docstrings are complete
- [ ] Type hints are accurate and complete
- [ ] Examples in docs/tools.md can be executed

**Validation**: Manual review of documentation accuracy

**Dependencies**: Tasks 2-7

---

## Implementation Order
Execute tasks sequentially (1 → 10). Tasks 2-6 can be parallelized after Task 1 is complete if needed, but sequential execution is recommended for clarity.

## Testing Strategy
- **Unit tests**: Mock API clients, test tool logic in isolation
- **Integration tests**: Test through FastMCP with mocked HTTP responses
- **Manual testing**: Use MCP client (e.g., Claude Desktop) to verify real-world usage

## Validation Checklist
- [ ] All tasks marked complete
- [ ] All tests passing (`pytest`)
- [ ] Code quality checks passing (`ruff check`, `mypy`)
- [ ] Server starts without errors
- [ ] Tools visible in MCP client
- [ ] Sample queries return expected results
