# Fix Open5e API Issues Implementation Plan

**Goal:** Fix three critical API integration issues preventing proper functionality of LoreKeeper MCP tools

**Architecture:** Targeted fixes to API parameter usage, data models, and client-side filtering to restore expected functionality while maintaining backward compatibility

**Tech Stack:** Python, Pydantic models, Open5e API integration, existing MCP tool infrastructure

---

### Task 1: Fix Spell Lookup Search Parameter

**Files:**

- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py:77`
- Test: `tests/test_tools/test_spell_lookup.py`

**Step 1: Write the failing test**

```python
def test_spell_search_parameter():
    """Test that spell lookup uses 'search' parameter instead of 'name'"""
    from unittest.mock import AsyncMock, patch
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell
    from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

    # Mock the API client to verify parameter usage
    with patch('lorekeeper_mcp.api_clients.open5e_v2.Open5eV2Client') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get_spells.return_value = []
        mock_client.return_value = mock_instance

        # Call the spell lookup function
        lookup_spell(name="fireball")

        # Verify the API was called with search parameter, not name
        mock_instance.get_spells.assert_called_once()
        call_args = mock_instance.get_spells.call_args
        assert 'search' in call_args.kwargs
        assert call_args.kwargs['search'] == "fireball"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_spell_search_parameter -v`
Expected: FAIL with "function not defined" or parameter assertion error

**Step 3: Write minimal implementation**

```python
# src/lorekeeper_mcp/tools/spell_lookup.py:77
# Change: params["name"] = name
# To: params["search"] = name
params["search"] = name
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_spell_search_parameter -v`
Expected: PASS

---

### Task 2: Fix Creature Lookup Search Parameter

**Files:**

- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py:78`
- Test: `tests/test_tools/test_creature_lookup.py`

**Step 1: Write the failing test**

```python
def test_creature_search_parameter():
    """Test that creature lookup uses 'search' parameter instead of 'name'"""
    from unittest.mock import AsyncMock, patch
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature
    from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client

    with patch('lorekeeper_mcp.api_clients.open5e_v1.Open5eV1Client') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get_monsters.return_value = []
        mock_client.return_value = mock_instance

        lookup_creature(name="dragon")

        mock_instance.get_monsters.assert_called_once()
        call_args = mock_instance.get_monsters.call_args
        assert 'search' in call_args.kwargs
        assert call_args.kwargs['search'] == "dragon"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py::test_creature_search_parameter -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/lorekeeper_mcp/tools/creature_lookup.py:78
# Change: params["name"] = name
# To: params["search"] = name
params["search"] = name
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py::test_creature_search_parameter -v`
Expected: PASS

---

### Task 3: Fix Equipment Lookup Search Parameter

**Files:**

- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py:97`
- Test: `tests/test_tools/test_equipment_lookup.py`

**Step 1: Write the failing test**

```python
def test_equipment_search_parameter():
    """Test that equipment lookup uses 'search' parameter instead of 'name'"""
    from unittest.mock import AsyncMock, patch
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    with patch('lorekeeper_mcp.api_clients.open5e_v2.Open5eV2Client') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get_weapons.return_value = []
        mock_client.return_value = mock_instance

        lookup_equipment(type="weapon", name="longsword")

        mock_instance.get_weapons.assert_called_once()
        call_args = mock_instance.get_weapons.call_args
        assert 'search' in call_args.kwargs
        assert call_args.kwargs['search'] == "longsword"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py::test_equipment_search_parameter -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/lorekeeper_mcp/tools/equipment_lookup.py:97
# Change: base_params["name"] = name
# To: base_params["search"] = name
base_params["search"] = name
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py::test_equipment_search_parameter -v`
Expected: PASS

---

### Task 4: Fix Character Option Lookup Search Parameter

**Files:**

- Modify: `src/lorekeeper_mcp/tools/character_option_lookup.py:92`
- Test: `tests/test_tools/test_character_option_lookup.py`

**Step 1: Write the failing test**

```python
def test_character_option_search_parameter():
    """Test that character option lookup uses 'search' parameter instead of 'name'"""
    from unittest.mock import AsyncMock, patch
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    with patch('lorekeeper_mcp.api_clients.open5e_v2.Open5eV2Client') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get_classes.return_value = []
        mock_client.return_value = mock_instance

        lookup_character_option(type="class", name="wizard")

        mock_instance.get_classes.assert_called_once()
        call_args = mock_instance.get_classes.call_args
        assert 'search' in call_args.kwargs
        assert call_args.kwargs['search'] == "wizard"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_character_option_lookup.py::test_character_option_search_parameter -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/lorekeeper_mcp/tools/character_option_lookup.py:92
# Change: params["name"] = name
# To: params["search"] = name
params["search"] = name
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_character_option_lookup.py::test_character_option_search_parameter -v`
Expected: PASS

---

### Task 5: Research Open5e API v2 Weapon Structure

**Files:**

- Research: Open5e v2 weapons API endpoint
- Document: Actual weapon response structure

**Step 1: Test API call to understand weapon response**

```bash
curl "https://api.open5e.com/v2/weapons/?limit=1" -H "Accept: application/json"
```

Expected: JSON response showing actual weapon data structure

**Step 2: Document findings**

Analyze the response to identify:
- Actual field names
- Data types (especially damage_type structure)
- Optional vs required fields
- Any missing fields from current model

---

### Task 6: Redesign Weapon Pydantic Model

**Files:**

- Modify: `src/lorekeeper_mcp/api_clients/models/equipment.py`
- Test: `tests/test_api_clients/test_models.py`

**Step 1: Write failing test for weapon model validation**

```python
def test_weapon_model_with_real_api_data():
    """Test that Weapon model validates against real Open5e API response"""
    from lorekeeper_mcp.api_clients.models.equipment import Weapon

    # Sample weapon data from Open5e v2 API (based on actual API research)
    sample_weapon_data = {
        "name": "Longsword",
        "damage_dice": "1d8",
        "damage_type": {"name": "slashing"},
        "weight": 3.0,
        "cost": "15gp",
        "weapon_range": "Melee"
    }

    # This should not raise validation error
    weapon = Weapon.model_validate(sample_weapon_data)
    assert weapon.name == "Longsword"
    assert weapon.damage_dice == "1d8"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_clients/test_models.py::test_weapon_model_with_real_api_data -v`
Expected: FAIL with validation errors

**Step 3: Write minimal implementation**

```python
# src/lorekeeper_mcp/api_clients/models/equipment.py
# Update Weapon class to match actual API response structure
class Weapon(BaseModel):
    name: str = Field(..., description="Weapon name")
    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: dict | list[dict] = Field(..., description="Damage type information")
    weight: float = Field(..., ge=0, description="Weight in pounds")
    cost: str = Field(..., description="Cost in gold pieces")

    # Optional fields from API response
    properties: list[str] | None = Field(None, description="Weapon properties")
    range_normal: int | None = Field(None, description="Normal range in feet")
    range_long: int | None = Field(None, description="Long range in feet")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")
    weapon_range: str = Field(None, description="Melee or Ranged classification")
    throw_range: dict | None = Field(None, description="Throw range information")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_api_clients/test_models.py::test_weapon_model_with_real_api_data -v`
Expected: PASS

---

### Task 7: Implement Spell School Filtering

**Files:**

- Modify: `src/lorekeeper_mcp/api_clients/open5e_v2.py`
- Test: `tests/test_api_clients/test_open5e_v2.py`

**Step 1: Write failing test for school filtering**

```python
def test_spell_school_filtering():
    """Test that get_spells method filters by school when provided"""
    from unittest.mock import AsyncMock, patch
    from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
    from lorekeeper_mcp.api_clients.models.spell import Spell

    # Mock spell data
    mock_spells = [
        {"name": "Fireball", "school": "evocation", "level": 3},
        {"name": "Magic Missile", "school": "evocation", "level": 1},
        {"name": "Detect Magic", "school": "divination", "level": 1}
    ]

    with patch.object(Open5eV2Client, 'make_request') as mock_request:
        mock_request.return_value = {"results": mock_spells}

        client = Open5eV2Client()
        result = client.get_spells(school="evocation")

        # Should only return evocation spells
        assert len(result) == 2
        assert all(spell.school == "evocation" for spell in result)
        assert spell.name in ["Fireball", "Magic Missile"] for spell in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_spell_school_filtering -v`
Expected: FAIL with school filtering not implemented

**Step 3: Write minimal implementation**

```python
# src/lorekeeper_mcp/api_clients/open5e_v2.py
# Add school filtering to get_spells method
async def get_spells(
    self,
    level: int | None = None,
    school: str | None = None,
    **kwargs: Any,
) -> list[Spell]:
    # Build API parameters (exclude unsupported school parameter)
    api_params = {k: v for k, v in kwargs.items() if k != "school"}
    if level is not None:
        api_params["level"] = level

    # Fetch all spells with supported parameters
    result = await self.make_request(
        "/spells/",
        use_entity_cache=True,
        entity_type="spells",
        params=api_params,
    )

    # Extract spell dictionaries
    spell_dicts: list[dict[str, Any]] = (
        result if isinstance(result, list) else result.get("results", [])
    )

    # Convert to Spell objects
    spells = [Spell.model_validate(spell) for spell in spell_dicts]

    # Apply client-side school filtering if requested
    if school:
        spells = [spell for spell in spells if spell.school.lower() == school.lower()]

    return spells
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_spell_school_filtering -v`
Expected: PASS

---

### Task 8: Integration Testing

**Step 1: Run comprehensive test suite**

Run: `uv run pytest tests/test_tools/ -k "name" -v`
Expected: All name-based search tests pass

**Step 2: Validate all equipment lookups work**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py -v`
Expected: No validation errors

**Step 3: Test spell school filtering end-to-end**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py -v`
Expected: All spell filtering tests pass

**Step 4: Run quality checks**

Run: `uv run ruff check src/ tests/`
Run: `uv run mypy src/`
Expected: No linting or type errors

---

### Task 9: Final Validation

**Step 1: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 2: Verify functionality**

- Test spell lookup with name and school filtering
- Test equipment lookup for weapons and armor
- Test creature lookup with name searches
- Test character option lookup with name searches

**Step 3: Commit changes**

Commit message: "fix: Correct Open5e API integration issues

- Fix search parameters in all lookup tools (name→search)
- Redesign Weapon model to match API response structure
- Implement client-side spell school filtering
- Restore expected functionality for all D&D 5e content searches"
