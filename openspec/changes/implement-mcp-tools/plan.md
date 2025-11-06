# MCP Tools Implementation Plan

**Goal:** Implement five MCP tools to expose D&D 5e lookup functionality through FastMCP server

**Architecture:** Each tool is a decorated async function that accepts typed parameters, calls the appropriate API client(s), and returns structured data. FastMCP handles parameter validation and MCP protocol serialization. All API calls automatically leverage the existing SQLite cache layer.

**Tech Stack:** FastMCP, httpx (via existing clients), SQLite cache, pytest with pytest-asyncio

---

## Task 1: Create Tool Module Foundation

**Files:**
- Modify: `src/lorekeeper_mcp/tools/__init__.py:1-1`
- Create: `tests/test_tools/__init__.py`
- Create: `tests/test_tools/conftest.py`

### Step 1: Write failing import test

**File:** `tests/test_tools/test_module.py`

```python
"""Test tool module structure."""
import pytest


def test_tools_module_exists():
    """Verify tools module can be imported."""
    from lorekeeper_mcp import tools
    assert tools is not None


def test_tools_init_exports():
    """Verify __init__ exports all tool functions."""
    from lorekeeper_mcp.tools import (
        lookup_spell,
        lookup_creature,
        lookup_character_option,
        lookup_equipment,
        lookup_rule,
    )
    assert callable(lookup_spell)
    assert callable(lookup_creature)
    assert callable(lookup_character_option)
    assert callable(lookup_equipment)
    assert callable(lookup_rule)
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_tools/test_module.py::test_tools_init_exports -v`

Expected: `ImportError: cannot import name 'lookup_spell'`

### Step 3: Create tool module structure

**File:** `src/lorekeeper_mcp/tools/__init__.py`

```python
"""MCP tools for D&D 5e data lookup."""
from lorekeeper_mcp.tools.spell_lookup import lookup_spell
from lorekeeper_mcp.tools.creature_lookup import lookup_creature
from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option
from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment
from lorekeeper_mcp.tools.rule_lookup import lookup_rule

__all__ = [
    "lookup_spell",
    "lookup_creature",
    "lookup_character_option",
    "lookup_equipment",
    "lookup_rule",
]
```

**File:** `tests/test_tools/__init__.py`

```python
"""Tests for MCP tools."""
```

**File:** `tests/test_tools/conftest.py`

```python
"""Fixtures for tool tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_spell_response():
    """Mock Open5e v2 spell response."""
    return {
        "count": 1,
        "results": [
            {
                "name": "Fireball",
                "level": 3,
                "school": "evocation",
                "casting_time": "1 action",
                "range": "150 feet",
                "components": "V,S,M",
                "material": "a tiny ball of bat guano and sulfur",
                "duration": "Instantaneous",
                "concentration": False,
                "ritual": False,
                "desc": "A bright streak flashes...",
                "higher_level": "When you cast this spell...",
                "document__slug": "srd",
            }
        ],
    }


@pytest.fixture
def mock_creature_response():
    """Mock Open5e v1 monster response."""
    return {
        "count": 1,
        "results": [
            {
                "name": "Ancient Red Dragon",
                "size": "Gargantuan",
                "type": "dragon",
                "alignment": "chaotic evil",
                "armor_class": 22,
                "hit_points": 546,
                "hit_dice": "28d20+252",
                "speed": {"walk": 40, "climb": 40, "fly": 80},
                "strength": 30,
                "dexterity": 10,
                "constitution": 29,
                "intelligence": 18,
                "wisdom": 15,
                "charisma": 23,
                "challenge_rating": "24",
                "document__slug": "srd",
            }
        ],
    }


@pytest.fixture
def mock_open5e_v1_client(mock_creature_response):
    """Mock Open5eV1Client."""
    client = MagicMock()
    client.get_monsters = AsyncMock(return_value=mock_creature_response)
    client.get_classes = AsyncMock(return_value={"count": 0, "results": []})
    client.get_races = AsyncMock(return_value={"count": 0, "results": []})
    return client


@pytest.fixture
def mock_open5e_v2_client(mock_spell_response):
    """Mock Open5eV2Client."""
    client = MagicMock()
    client.get_spells = AsyncMock(return_value=mock_spell_response)
    client.get_backgrounds = AsyncMock(return_value={"count": 0, "results": []})
    client.get_feats = AsyncMock(return_value={"count": 0, "results": []})
    client.get_weapons = AsyncMock(return_value={"count": 0, "results": []})
    client.get_armor = AsyncMock(return_value={"count": 0, "results": []})
    client.get_conditions = AsyncMock(return_value={"count": 0, "results": []})
    return client


@pytest.fixture
def mock_dnd5e_client():
    """Mock Dnd5eApiClient."""
    client = MagicMock()
    client.get_rules = AsyncMock(return_value={"count": 0, "results": []})
    client.get_damage_types = AsyncMock(return_value={"count": 0, "results": []})
    client.get_weapon_properties = AsyncMock(return_value={"count": 0, "results": []})
    client.get_skills = AsyncMock(return_value={"count": 0, "results": []})
    client.get_ability_scores = AsyncMock(return_value={"count": 0, "results": []})
    client.get_magic_schools = AsyncMock(return_value={"count": 0, "results": []})
    client.get_languages = AsyncMock(return_value={"count": 0, "results": []})
    client.get_proficiencies = AsyncMock(return_value={"count": 0, "results": []})
    client.get_alignments = AsyncMock(return_value={"count": 0, "results": []})
    return client
```

### Step 4: Run test to verify new failure

Run: `pytest tests/test_tools/test_module.py::test_tools_init_exports -v`

Expected: `ModuleNotFoundError: No module named 'lorekeeper_mcp.tools.spell_lookup'`

### Step 5: Create stub tool files

**File:** `src/lorekeeper_mcp/tools/spell_lookup.py`

```python
"""Spell lookup tool."""


async def lookup_spell():
    """Placeholder for spell lookup."""
    pass
```

**File:** `src/lorekeeper_mcp/tools/creature_lookup.py`

```python
"""Creature lookup tool."""


async def lookup_creature():
    """Placeholder for creature lookup."""
    pass
```

**File:** `src/lorekeeper_mcp/tools/character_option_lookup.py`

```python
"""Character option lookup tool."""


async def lookup_character_option():
    """Placeholder for character option lookup."""
    pass
```

**File:** `src/lorekeeper_mcp/tools/equipment_lookup.py`

```python
"""Equipment lookup tool."""


async def lookup_equipment():
    """Placeholder for equipment lookup."""
    pass
```

**File:** `src/lorekeeper_mcp/tools/rule_lookup.py`

```python
"""Rule lookup tool."""


async def lookup_rule():
    """Placeholder for rule lookup."""
    pass
```

### Step 6: Run test to verify it passes

Run: `pytest tests/test_tools/test_module.py -v`

Expected: Both tests PASS

### Step 7: Commit module structure

Run: `git add src/lorekeeper_mcp/tools/ tests/test_tools/ && git commit -m "feat(tools): create tool module structure with stubs"`

Expected: Clean commit with 8 files added

---

## Task 2: Implement `lookup_spell` Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py:1-6`
- Create: `tests/test_tools/test_spell_lookup.py`

### Step 1: Write failing test for spell lookup

**File:** `tests/test_tools/test_spell_lookup.py`

```python
"""Tests for spell lookup tool."""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_lookup_spell_by_name(mock_open5e_v2_client, mock_spell_response):
    """Test looking up spell by exact name."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_spell(name="Fireball")

    assert len(result) == 1
    assert result[0]["name"] == "Fireball"
    assert result[0]["level"] == 3
    assert result[0]["school"] == "evocation"
    mock_open5e_v2_client.get_spells.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_spell_with_filters(mock_open5e_v2_client):
    """Test spell lookup with multiple filters."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        await lookup_spell(
            level=3,
            school="evocation",
            concentration=False,
            limit=10,
        )

    call_kwargs = mock_open5e_v2_client.get_spells.call_args[1]
    assert call_kwargs["level"] == 3
    assert call_kwargs["school"] == "evocation"
    assert call_kwargs["concentration"] is False
    assert call_kwargs["limit"] == 10


@pytest.mark.asyncio
async def test_lookup_spell_empty_results(mock_open5e_v2_client):
    """Test spell lookup with no results."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell

    mock_open5e_v2_client.get_spells.return_value = {"count": 0, "results": []}

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_spell(name="NonexistentSpell")

    assert result == []


@pytest.mark.asyncio
async def test_lookup_spell_api_error(mock_open5e_v2_client):
    """Test spell lookup handles API errors gracefully."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell
    from lorekeeper_mcp.api_clients.exceptions import APIError

    mock_open5e_v2_client.get_spells.side_effect = APIError("API unavailable")

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        with pytest.raises(APIError, match="API unavailable"):
            await lookup_spell(name="Fireball")
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_tools/test_spell_lookup.py::test_lookup_spell_by_name -v`

Expected: Test fails with assertion or attribute errors

### Step 3: Implement spell lookup tool

**File:** `src/lorekeeper_mcp/tools/spell_lookup.py`

```python
"""Spell lookup tool."""
from typing import Any, Optional
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


async def lookup_spell(
    name: Optional[str] = None,
    level: Optional[int] = None,
    school: Optional[str] = None,
    class_key: Optional[str] = None,
    concentration: Optional[bool] = None,
    ritual: Optional[bool] = None,
    casting_time: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up D&D 5e spells using Open5e v2 API.

    Args:
        name: Spell name or partial name search
        level: Spell level (0-9, where 0 is cantrips)
        school: Magic school (abjuration, conjuration, etc.)
        class_key: Filter by class (wizard, cleric, etc.)
        concentration: Filter for concentration spells
        ritual: Filter for ritual spells
        casting_time: Casting time filter (e.g., "1 action")
        limit: Maximum number of results (default 20)

    Returns:
        List of spell dictionaries with full spell data

    Raises:
        APIError: If the API request fails
    """
    client = Open5eV2Client()

    # Build query parameters
    params = {"limit": limit}
    if name is not None:
        params["name"] = name
    if level is not None:
        params["level"] = level
    if school is not None:
        params["school"] = school
    if class_key is not None:
        params["class_key"] = class_key
    if concentration is not None:
        params["concentration"] = concentration
    if ritual is not None:
        params["ritual"] = ritual
    if casting_time is not None:
        params["casting_time"] = casting_time

    response = await client.get_spells(**params)
    return response.get("results", [])
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_tools/test_spell_lookup.py -v`

Expected: All 4 tests PASS

### Step 5: Commit spell lookup implementation

Run: `git add src/lorekeeper_mcp/tools/spell_lookup.py tests/test_tools/test_spell_lookup.py && git commit -m "feat(tools): implement lookup_spell with filters and error handling"`

Expected: Clean commit

---

## Task 3: Implement `lookup_creature` Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py:1-6`
- Create: `tests/test_tools/test_creature_lookup.py`

### Step 1: Write failing test for creature lookup

**File:** `tests/test_tools/test_creature_lookup.py`

```python
"""Tests for creature lookup tool."""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_lookup_creature_by_name(mock_open5e_v1_client, mock_creature_response):
    """Test looking up creature by exact name."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_creature(name="Ancient Red Dragon")

    assert len(result) == 1
    assert result[0]["name"] == "Ancient Red Dragon"
    assert result[0]["challenge_rating"] == "24"
    mock_open5e_v1_client.get_monsters.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_creature_by_cr_and_type(mock_open5e_v1_client):
    """Test creature lookup with CR and type filters."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        await lookup_creature(cr=5, type="undead", limit=15)

    call_kwargs = mock_open5e_v1_client.get_monsters.call_args[1]
    assert call_kwargs["cr"] == 5
    assert call_kwargs["type"] == "undead"
    assert call_kwargs["limit"] == 15


@pytest.mark.asyncio
async def test_lookup_creature_fractional_cr(mock_open5e_v1_client):
    """Test creature lookup with fractional CR."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        await lookup_creature(cr=0.25)

    call_kwargs = mock_open5e_v1_client.get_monsters.call_args[1]
    assert call_kwargs["cr"] == 0.25


@pytest.mark.asyncio
async def test_lookup_creature_cr_range(mock_open5e_v1_client):
    """Test creature lookup with CR range."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        await lookup_creature(cr_min=1, cr_max=3)

    call_kwargs = mock_open5e_v1_client.get_monsters.call_args[1]
    assert call_kwargs["cr_min"] == 1
    assert call_kwargs["cr_max"] == 3


@pytest.mark.asyncio
async def test_lookup_creature_empty_results(mock_open5e_v1_client):
    """Test creature lookup with no results."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    mock_open5e_v1_client.get_monsters.return_value = {"count": 0, "results": []}

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_creature(name="Nonexistent")

    assert result == []
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_tools/test_creature_lookup.py::test_lookup_creature_by_name -v`

Expected: Test fails

### Step 3: Implement creature lookup tool

**File:** `src/lorekeeper_mcp/tools/creature_lookup.py`

```python
"""Creature lookup tool."""
from typing import Any, Optional
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client


async def lookup_creature(
    name: Optional[str] = None,
    cr: Optional[float] = None,
    cr_min: Optional[float] = None,
    cr_max: Optional[float] = None,
    type: Optional[str] = None,
    size: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up D&D 5e creatures/monsters using Open5e v1 API.

    Args:
        name: Creature name or partial name search
        cr: Exact challenge rating (supports 0.125, 0.25, 0.5, 1-30)
        cr_min: Minimum CR for range searches
        cr_max: Maximum CR for range searches
        type: Creature type (aberration, beast, dragon, undead, etc.)
        size: Size category (Tiny, Small, Medium, Large, Huge, Gargantuan)
        limit: Maximum number of results (default 20)

    Returns:
        List of creature stat block dictionaries

    Raises:
        APIError: If the API request fails
    """
    client = Open5eV1Client()

    # Build query parameters
    params = {"limit": limit}
    if name is not None:
        params["name"] = name
    if cr is not None:
        params["cr"] = cr
    if cr_min is not None:
        params["cr_min"] = cr_min
    if cr_max is not None:
        params["cr_max"] = cr_max
    if type is not None:
        params["type"] = type
    if size is not None:
        params["size"] = size

    response = await client.get_monsters(**params)
    return response.get("results", [])
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_tools/test_creature_lookup.py -v`

Expected: All 5 tests PASS

### Step 5: Commit creature lookup implementation

Run: `git add src/lorekeeper_mcp/tools/creature_lookup.py tests/test_tools/test_creature_lookup.py && git commit -m "feat(tools): implement lookup_creature with CR filtering"`

Expected: Clean commit

---

## Task 4: Implement `lookup_character_option` Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/character_option_lookup.py:1-6`
- Create: `tests/test_tools/test_character_option_lookup.py`

### Step 1: Write failing test for character option lookup

**File:** `tests/test_tools/test_character_option_lookup.py`

```python
"""Tests for character option lookup tool."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_lookup_class(mock_open5e_v1_client):
    """Test looking up a class."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    mock_open5e_v1_client.get_classes.return_value = {
        "count": 1,
        "results": [{"name": "Paladin", "hit_dice": "1d10"}],
    }

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_character_option(type="class", name="Paladin")

    assert len(result) == 1
    assert result[0]["name"] == "Paladin"
    mock_open5e_v1_client.get_classes.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_race(mock_open5e_v1_client):
    """Test looking up a race."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    mock_open5e_v1_client.get_races.return_value = {
        "count": 1,
        "results": [{"name": "Elf", "speed": 30}],
    }

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_character_option(type="race", name="Elf")

    assert len(result) == 1
    assert result[0]["name"] == "Elf"
    mock_open5e_v1_client.get_races.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_background(mock_open5e_v2_client):
    """Test looking up a background."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    mock_open5e_v2_client.get_backgrounds.return_value = {
        "count": 1,
        "results": [{"name": "Acolyte"}],
    }

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_character_option(type="background", name="Acolyte")

    assert len(result) == 1
    assert result[0]["name"] == "Acolyte"
    mock_open5e_v2_client.get_backgrounds.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_feat(mock_open5e_v2_client):
    """Test looking up a feat."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    mock_open5e_v2_client.get_feats.return_value = {
        "count": 1,
        "results": [{"name": "Sharpshooter"}],
    }

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_character_option(type="feat", name="Sharpshooter")

    assert len(result) == 1
    assert result[0]["name"] == "Sharpshooter"
    mock_open5e_v2_client.get_feats.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_invalid_type():
    """Test invalid type parameter raises ValueError."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    with pytest.raises(ValueError, match="Invalid type"):
        await lookup_character_option(type="invalid-type")
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_tools/test_character_option_lookup.py::test_lookup_class -v`

Expected: Test fails

### Step 3: Implement character option lookup tool

**File:** `src/lorekeeper_mcp/tools/character_option_lookup.py`

```python
"""Character option lookup tool."""
from typing import Any, Optional, Literal
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


OptionType = Literal["class", "race", "background", "feat"]


async def lookup_character_option(
    type: OptionType,
    name: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up character creation and advancement options.

    Args:
        type: Option type (class, race, background, feat) - REQUIRED
        name: Name or partial name search
        limit: Maximum number of results (default 20)

    Returns:
        List of option dictionaries (structure varies by type)

    Raises:
        ValueError: If type is not valid
        APIError: If the API request fails
    """
    valid_types = {"class", "race", "background", "feat"}
    if type not in valid_types:
        raise ValueError(
            f"Invalid type '{type}'. Must be one of: {', '.join(valid_types)}"
        )

    params = {"limit": limit}
    if name is not None:
        params["name"] = name

    # Route to appropriate client and endpoint
    if type == "class":
        client = Open5eV1Client()
        response = await client.get_classes(**params)
    elif type == "race":
        client = Open5eV1Client()
        response = await client.get_races(**params)
    elif type == "background":
        client = Open5eV2Client()
        response = await client.get_backgrounds(**params)
    elif type == "feat":
        client = Open5eV2Client()
        response = await client.get_feats(**params)

    return response.get("results", [])
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_tools/test_character_option_lookup.py -v`

Expected: All 5 tests PASS

### Step 5: Commit character option lookup implementation

Run: `git add src/lorekeeper_mcp/tools/character_option_lookup.py tests/test_tools/test_character_option_lookup.py && git commit -m "feat(tools): implement lookup_character_option with type routing"`

Expected: Clean commit

---

## Task 5: Implement `lookup_equipment` Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py:1-6`
- Create: `tests/test_tools/test_equipment_lookup.py`

### Step 1: Write failing test for equipment lookup

**File:** `tests/test_tools/test_equipment_lookup.py`

```python
"""Tests for equipment lookup tool."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_lookup_weapon(mock_open5e_v2_client):
    """Test looking up a weapon."""
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    mock_open5e_v2_client.get_weapons.return_value = {
        "count": 1,
        "results": [{"name": "Longsword", "damage_dice": "1d8"}],
    }

    with patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_equipment(type="weapon", name="Longsword")

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"
    mock_open5e_v2_client.get_weapons.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_armor(mock_open5e_v2_client):
    """Test looking up armor."""
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    mock_open5e_v2_client.get_armor.return_value = {
        "count": 1,
        "results": [{"name": "Chain Mail", "ac_base": 16}],
    }

    with patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_equipment(type="armor", name="Chain Mail")

    assert len(result) == 1
    assert result[0]["name"] == "Chain Mail"
    mock_open5e_v2_client.get_armor.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_simple_weapons(mock_open5e_v2_client):
    """Test filtering for simple weapons."""
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    mock_open5e_v2_client.get_weapons.return_value = {
        "count": 2,
        "results": [
            {"name": "Club", "is_simple": True},
            {"name": "Dagger", "is_simple": True},
        ],
    }

    with patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_equipment(type="weapon", is_simple=True)

    call_kwargs = mock_open5e_v2_client.get_weapons.call_args[1]
    assert call_kwargs["is_simple"] is True


@pytest.mark.asyncio
async def test_lookup_all_equipment_types(mock_open5e_v1_client, mock_open5e_v2_client):
    """Test looking up all equipment types."""
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    mock_open5e_v2_client.get_weapons.return_value = {
        "count": 1,
        "results": [{"name": "Chain Whip", "type": "weapon"}],
    }
    mock_open5e_v2_client.get_armor.return_value = {
        "count": 1,
        "results": [{"name": "Chain Mail", "type": "armor"}],
    }
    mock_open5e_v1_client.get_magic_items.return_value = {
        "count": 1,
        "results": [{"name": "Chain of Binding", "type": "magic-item"}],
    }

    with patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ), patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_equipment(type="all", name="chain")

    # Should merge results from all three endpoints
    assert len(result) == 3
    names = {r["name"] for r in result}
    assert "Chain Whip" in names
    assert "Chain Mail" in names
    assert "Chain of Binding" in names
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_tools/test_equipment_lookup.py::test_lookup_weapon -v`

Expected: Test fails

### Step 3: Implement equipment lookup tool

**File:** `src/lorekeeper_mcp/tools/equipment_lookup.py`

```python
"""Equipment lookup tool."""
from typing import Any, Optional, Literal
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


EquipmentType = Literal["weapon", "armor", "magic-item", "all"]


async def lookup_equipment(
    type: EquipmentType = "all",
    name: Optional[str] = None,
    rarity: Optional[str] = None,
    damage_dice: Optional[str] = None,
    is_simple: Optional[bool] = None,
    requires_attunement: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up weapons, armor, and magic items.

    Args:
        type: Equipment type (weapon, armor, magic-item, all)
        name: Item name or partial name search
        rarity: Magic item rarity (common, uncommon, rare, very rare, legendary, artifact)
        damage_dice: Weapon damage dice filter (e.g., "1d8", "2d6")
        is_simple: Filter for simple weapons only
        requires_attunement: Attunement requirement filter
        limit: Maximum number of results per type (default 20)

    Returns:
        List of equipment dictionaries (structure varies by type)

    Raises:
        APIError: If the API request fails
    """
    results = []

    # Build base params
    base_params = {"limit": limit}
    if name is not None:
        base_params["name"] = name

    # Query weapons
    if type in ("weapon", "all"):
        v2_client = Open5eV2Client()
        weapon_params = base_params.copy()
        if damage_dice is not None:
            weapon_params["damage_dice"] = damage_dice
        if is_simple is not None:
            weapon_params["is_simple"] = is_simple

        weapon_response = await v2_client.get_weapons(**weapon_params)
        results.extend(weapon_response.get("results", []))

    # Query armor
    if type in ("armor", "all"):
        v2_client = Open5eV2Client()
        armor_response = await v2_client.get_armor(**base_params)
        results.extend(armor_response.get("results", []))

    # Query magic items
    if type in ("magic-item", "all"):
        v1_client = Open5eV1Client()
        magic_params = base_params.copy()
        if rarity is not None:
            magic_params["rarity"] = rarity
        if requires_attunement is not None:
            magic_params["requires_attunement"] = requires_attunement

        magic_response = await v1_client.get_magic_items(**magic_params)
        results.extend(magic_response.get("results", []))

    # Apply overall limit if querying multiple types
    if type == "all" and len(results) > limit:
        results = results[:limit]

    return results
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_tools/test_equipment_lookup.py -v`

Expected: All 4 tests PASS

### Step 5: Commit equipment lookup implementation

Run: `git add src/lorekeeper_mcp/tools/equipment_lookup.py tests/test_tools/test_equipment_lookup.py && git commit -m "feat(tools): implement lookup_equipment with multi-type support"`

Expected: Clean commit

---

## Task 6: Implement `lookup_rule` Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/rule_lookup.py:1-6`
- Create: `tests/test_tools/test_rule_lookup.py`

### Step 1: Write failing test for rule lookup

**File:** `tests/test_tools/test_rule_lookup.py`

```python
"""Tests for rule lookup tool."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_lookup_condition(mock_open5e_v2_client):
    """Test looking up a condition."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_open5e_v2_client.get_conditions.return_value = {
        "count": 1,
        "results": [{"name": "Grappled", "desc": "A grappled creature's speed..."}],
    }

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_rule(type="condition", name="Grappled")

    assert len(result) == 1
    assert result[0]["name"] == "Grappled"
    mock_open5e_v2_client.get_conditions.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_damage_type(mock_dnd5e_client):
    """Test looking up a damage type."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_dnd5e_client.get_damage_types.return_value = {
        "count": 1,
        "results": [{"name": "Radiant", "desc": "Radiant damage..."}],
    }

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Dnd5eApiClient",
        return_value=mock_dnd5e_client,
    ):
        result = await lookup_rule(type="damage-type", name="Radiant")

    assert len(result) == 1
    assert result[0]["name"] == "Radiant"
    mock_dnd5e_client.get_damage_types.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_skill(mock_dnd5e_client):
    """Test looking up a skill."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_dnd5e_client.get_skills.return_value = {
        "count": 1,
        "results": [{"name": "Stealth", "ability_score": "dexterity"}],
    }

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Dnd5eApiClient",
        return_value=mock_dnd5e_client,
    ):
        result = await lookup_rule(type="skill", name="Stealth")

    assert len(result) == 1
    mock_dnd5e_client.get_skills.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_rules_with_section(mock_dnd5e_client):
    """Test looking up rules with section filter."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_dnd5e_client.get_rules.return_value = {
        "count": 1,
        "results": [{"name": "Combat", "desc": "Combat rules..."}],
    }

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Dnd5eApiClient",
        return_value=mock_dnd5e_client,
    ):
        result = await lookup_rule(type="rule", section="combat")

    call_kwargs = mock_dnd5e_client.get_rules.call_args[1]
    assert call_kwargs["section"] == "combat"


@pytest.mark.asyncio
async def test_lookup_all_reference_types(mock_dnd5e_client):
    """Test all valid reference types."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_response = {"count": 0, "results": []}

    # Configure all mock methods
    mock_dnd5e_client.get_weapon_properties.return_value = mock_response
    mock_dnd5e_client.get_ability_scores.return_value = mock_response
    mock_dnd5e_client.get_magic_schools.return_value = mock_response
    mock_dnd5e_client.get_languages.return_value = mock_response
    mock_dnd5e_client.get_proficiencies.return_value = mock_response
    mock_dnd5e_client.get_alignments.return_value = mock_response

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Dnd5eApiClient",
        return_value=mock_dnd5e_client,
    ):
        # Test each type
        await lookup_rule(type="weapon-property")
        await lookup_rule(type="ability-score")
        await lookup_rule(type="magic-school")
        await lookup_rule(type="language")
        await lookup_rule(type="proficiency")
        await lookup_rule(type="alignment")

    # Verify all were called
    mock_dnd5e_client.get_weapon_properties.assert_awaited_once()
    mock_dnd5e_client.get_ability_scores.assert_awaited_once()
    mock_dnd5e_client.get_magic_schools.assert_awaited_once()
    mock_dnd5e_client.get_languages.assert_awaited_once()
    mock_dnd5e_client.get_proficiencies.assert_awaited_once()
    mock_dnd5e_client.get_alignments.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_invalid_rule_type():
    """Test invalid rule type raises ValueError."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    with pytest.raises(ValueError, match="Invalid type"):
        await lookup_rule(type="invalid-rule-type")
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_tools/test_rule_lookup.py::test_lookup_condition -v`

Expected: Test fails

### Step 3: Implement rule lookup tool

**File:** `src/lorekeeper_mcp/tools/rule_lookup.py`

```python
"""Rule lookup tool."""
from typing import Any, Optional, Literal
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient


RuleType = Literal[
    "rule",
    "condition",
    "damage-type",
    "weapon-property",
    "skill",
    "ability-score",
    "magic-school",
    "language",
    "proficiency",
    "alignment",
]


async def lookup_rule(
    type: RuleType,
    name: Optional[str] = None,
    section: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up game rules, conditions, and reference information.

    Args:
        type: Rule type (rule, condition, damage-type, etc.) - REQUIRED
        name: Name or partial name search
        section: For rules - section name (combat, spellcasting, etc.)
        limit: Maximum number of results (default 20)

    Returns:
        List of rule/reference dictionaries

    Raises:
        ValueError: If type is not valid
        APIError: If the API request fails
    """
    valid_types = {
        "rule",
        "condition",
        "damage-type",
        "weapon-property",
        "skill",
        "ability-score",
        "magic-school",
        "language",
        "proficiency",
        "alignment",
    }
    if type not in valid_types:
        raise ValueError(
            f"Invalid type '{type}'. Must be one of: {', '.join(sorted(valid_types))}"
        )

    params = {"limit": limit}
    if name is not None:
        params["name"] = name

    # Route to appropriate client and endpoint
    if type == "condition":
        client = Open5eV2Client()
        response = await client.get_conditions(**params)
    else:
        # All other types use D&D 5e API
        client = Dnd5eApiClient()

        # Add section parameter for rules
        if type == "rule" and section is not None:
            params["section"] = section

        # Call appropriate method
        if type == "rule":
            response = await client.get_rules(**params)
        elif type == "damage-type":
            response = await client.get_damage_types(**params)
        elif type == "weapon-property":
            response = await client.get_weapon_properties(**params)
        elif type == "skill":
            response = await client.get_skills(**params)
        elif type == "ability-score":
            response = await client.get_ability_scores(**params)
        elif type == "magic-school":
            response = await client.get_magic_schools(**params)
        elif type == "language":
            response = await client.get_languages(**params)
        elif type == "proficiency":
            response = await client.get_proficiencies(**params)
        elif type == "alignment":
            response = await client.get_alignments(**params)

    return response.get("results", [])
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_tools/test_rule_lookup.py -v`

Expected: All 6 tests PASS

### Step 5: Commit rule lookup implementation

Run: `git add src/lorekeeper_mcp/tools/rule_lookup.py tests/test_tools/test_rule_lookup.py && git commit -m "feat(tools): implement lookup_rule with 10 reference types"`

Expected: Clean commit

---

## Task 7: Register Tools with FastMCP Server

**Files:**
- Modify: `src/lorekeeper_mcp/server.py` (import and register tools)
- Create: `tests/test_tools/test_integration.py`

### Step 1: Write failing test for tool registration

**File:** `tests/test_tools/test_integration.py`

```python
"""Integration tests for MCP tool registration."""
import pytest


def test_all_tools_registered():
    """Verify all 5 tools are registered with FastMCP."""
    from lorekeeper_mcp.server import mcp

    tool_names = {t.name for t in mcp.list_tools()}
    expected_tools = {
        "lookup_spell",
        "lookup_creature",
        "lookup_character_option",
        "lookup_equipment",
        "lookup_rule",
    }

    assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"


def test_tool_schemas_valid():
    """Verify tool schemas are properly defined."""
    from lorekeeper_mcp.server import mcp

    tools = {t.name: t for t in mcp.list_tools()}

    # Check lookup_spell schema
    spell_tool = tools.get("lookup_spell")
    assert spell_tool is not None
    assert "name" in spell_tool.parameters["properties"]
    assert "level" in spell_tool.parameters["properties"]
    assert "limit" in spell_tool.parameters["properties"]

    # Check lookup_creature schema
    creature_tool = tools.get("lookup_creature")
    assert creature_tool is not None
    assert "cr" in creature_tool.parameters["properties"]

    # Check lookup_character_option schema
    char_tool = tools.get("lookup_character_option")
    assert char_tool is not None
    assert "type" in char_tool.parameters["required"]

    # Check lookup_equipment schema
    equip_tool = tools.get("lookup_equipment")
    assert equip_tool is not None

    # Check lookup_rule schema
    rule_tool = tools.get("lookup_rule")
    assert rule_tool is not None
    assert "type" in rule_tool.parameters["required"]
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_tools/test_integration.py::test_all_tools_registered -v`

Expected: Test fails - tools not registered

### Step 3: Register tools in server.py

**File:** `src/lorekeeper_mcp/server.py`

Find the line where `mcp = FastMCP("LoreKeeper")` is defined, and add tool imports and registrations after it:

```python
# Import tools
from lorekeeper_mcp.tools import (
    lookup_spell,
    lookup_creature,
    lookup_character_option,
    lookup_equipment,
    lookup_rule,
)

# Register tools with FastMCP
mcp.tool()(lookup_spell)
mcp.tool()(lookup_creature)
mcp.tool()(lookup_character_option)
mcp.tool()(lookup_equipment)
mcp.tool()(lookup_rule)
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_tools/test_integration.py -v`

Expected: Both tests PASS

### Step 5: Commit tool registration

Run: `git add src/lorekeeper_mcp/server.py tests/test_tools/test_integration.py && git commit -m "feat(tools): register all 5 tools with FastMCP server"`

Expected: Clean commit

---

## Task 8: Add Tool Descriptions for MCP

**Files:**
- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py:6-35`
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py:6-35`
- Modify: `src/lorekeeper_mcp/tools/character_option_lookup.py:6-25`
- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py:6-35`
- Modify: `src/lorekeeper_mcp/tools/rule_lookup.py:6-35`

### Step 1: Add FastMCP decorators to spell_lookup

**File:** `src/lorekeeper_mcp/tools/spell_lookup.py`

Update the function signature to include the decorator:

```python
"""Spell lookup tool."""
from typing import Any, Optional
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


async def lookup_spell(
    name: Optional[str] = None,
    level: Optional[int] = None,
    school: Optional[str] = None,
    class_key: Optional[str] = None,
    concentration: Optional[bool] = None,
    ritual: Optional[bool] = None,
    casting_time: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up D&D 5e spells using the Open5e v2 API.

    Search for spells by name, filter by level, school, class, and properties.
    Returns full spell descriptions including components, range, duration, and effects.

    Examples:
        - lookup_spell(name="fireball")
        - lookup_spell(level=3, school="evocation")
        - lookup_spell(class_key="wizard", concentration=True, limit=10)

    Args:
        name: Spell name or partial name search
        level: Spell level (0-9, where 0 is cantrips)
        school: Magic school (abjuration, conjuration, divination, enchantment, evocation, illusion, necromancy, transmutation)
        class_key: Filter by class (wizard, cleric, druid, bard, paladin, ranger, sorcerer, warlock)
        concentration: Filter for concentration spells only
        ritual: Filter for ritual spells only
        casting_time: Casting time filter (e.g., "1 action", "1 bonus action", "1 reaction")
        limit: Maximum number of results (default 20)

    Returns:
        List of spell dictionaries with name, level, school, components, casting time,
        range, duration, description, higher level effects, available classes, and source.

    Raises:
        APIError: If the API request fails
    """
    # ... rest of implementation
```

### Step 2: Verify tool description renders in FastMCP

Run: `python -c "from lorekeeper_mcp.server import mcp; spell = [t for t in mcp.list_tools() if t.name == 'lookup_spell'][0]; print(spell.description)"`

Expected: Tool description is printed

### Step 3: Add descriptions to remaining tools

Update `creature_lookup.py`, `character_option_lookup.py`, `equipment_lookup.py`, and `rule_lookup.py` with similar detailed docstrings including examples.

### Step 4: Run all tests to ensure no regressions

Run: `pytest tests/test_tools/ -v`

Expected: All tests PASS

### Step 5: Commit tool descriptions

Run: `git add src/lorekeeper_mcp/tools/*.py && git commit -m "docs(tools): add detailed descriptions and examples for MCP protocol"`

Expected: Clean commit

---

## Task 9: Add Error Handling Tests

**Files:**
- Modify: `tests/test_tools/test_spell_lookup.py` (add network error test)
- Modify: `tests/test_tools/test_creature_lookup.py` (add timeout test)
- Modify: `tests/test_tools/test_equipment_lookup.py` (add malformed response test)

### Step 1: Write failing test for network errors

**File:** `tests/test_tools/test_spell_lookup.py`

Add at the end:

```python
@pytest.mark.asyncio
async def test_lookup_spell_network_error(mock_open5e_v2_client):
    """Test spell lookup handles network errors."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell
    from lorekeeper_mcp.api_clients.exceptions import NetworkError

    mock_open5e_v2_client.get_spells.side_effect = NetworkError("Connection timeout")

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        with pytest.raises(NetworkError, match="Connection timeout"):
            await lookup_spell(name="Fireball")
```

### Step 2: Run test to verify it passes (error bubbles up)

Run: `pytest tests/test_tools/test_spell_lookup.py::test_lookup_spell_network_error -v`

Expected: Test PASS (tools let exceptions bubble up for now)

### Step 3: Add timeout test for creature lookup

**File:** `tests/test_tools/test_creature_lookup.py`

Add:

```python
@pytest.mark.asyncio
async def test_lookup_creature_timeout(mock_open5e_v1_client):
    """Test creature lookup handles timeouts."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature
    from lorekeeper_mcp.api_clients.exceptions import NetworkError

    mock_open5e_v1_client.get_monsters.side_effect = NetworkError("Request timeout")

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        with pytest.raises(NetworkError):
            await lookup_creature(name="Dragon")
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_tools/test_creature_lookup.py::test_lookup_creature_timeout -v`

Expected: Test PASS

### Step 5: Commit error handling tests

Run: `git add tests/test_tools/*.py && git commit -m "test(tools): add error handling tests for network failures"`

Expected: Clean commit

---

## Task 10: Update Documentation

**Files:**
- Modify: `docs/tools.md` (verify examples match implementation)
- Modify: `README.md` (update tool list and usage examples)

### Step 1: Verify docs/tools.md examples are accurate

Read: `cat docs/tools.md`

Manually verify that all examples in the documentation match the actual tool signatures and parameters.

### Step 2: Update README.md with complete tool list

**File:** `README.md`

Update the tools section to list all 5 implemented tools with brief descriptions:

```markdown
## Available Tools

LoreKeeper provides 5 MCP tools for querying D&D 5e game data:

1. **`lookup_spell`** - Search spells by name, level, school, class, and properties
2. **`lookup_creature`** - Find monsters by name, CR, type, and size
3. **`lookup_character_option`** - Get classes, races, backgrounds, and feats
4. **`lookup_equipment`** - Search weapons, armor, and magic items
5. **`lookup_rule`** - Look up game rules, conditions, and reference information

See [docs/tools.md](docs/tools.md) for detailed usage and examples.
```

### Step 3: Run documentation validation

Run: `grep -r "lookup_spell\|lookup_creature\|lookup_character_option\|lookup_equipment\|lookup_rule" docs/ README.md`

Expected: All 5 tools are documented

### Step 4: Run full test suite

Run: `pytest tests/ -v --cov=lorekeeper_mcp.tools --cov-report=term-missing`

Expected: All tests PASS, coverage >90%

### Step 5: Commit documentation updates

Run: `git add README.md docs/tools.md && git commit -m "docs: update tool documentation and README"`

Expected: Clean commit

---

## Task 11: Final Integration Test

**Files:**
- Create: `tests/test_tools/test_end_to_end.py`

### Step 1: Write end-to-end integration test

**File:** `tests/test_tools/test_end_to_end.py`

```python
"""End-to-end integration tests for MCP tools."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_full_spell_lookup_workflow(mock_open5e_v2_client, mock_spell_response):
    """Test complete spell lookup workflow."""
    from lorekeeper_mcp.tools import lookup_spell

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_spell(name="Fireball", level=3, limit=5)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "Fireball"
    assert result[0]["level"] == 3
    assert "desc" in result[0]
    assert "document__slug" in result[0]


@pytest.mark.asyncio
async def test_full_creature_lookup_workflow(mock_open5e_v1_client, mock_creature_response):
    """Test complete creature lookup workflow."""
    from lorekeeper_mcp.tools import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_creature(name="Ancient Red Dragon", cr=24)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["challenge_rating"] == "24"
    assert "hit_points" in result[0]
    assert "strength" in result[0]


@pytest.mark.asyncio
async def test_all_tools_callable():
    """Verify all tools can be imported and called."""
    from lorekeeper_mcp.tools import (
        lookup_spell,
        lookup_creature,
        lookup_character_option,
        lookup_equipment,
        lookup_rule,
    )

    # All should be async callables
    assert callable(lookup_spell)
    assert callable(lookup_creature)
    assert callable(lookup_character_option)
    assert callable(lookup_equipment)
    assert callable(lookup_rule)

    # Verify they're async
    import inspect
    assert inspect.iscoroutinefunction(lookup_spell)
    assert inspect.iscoroutinefunction(lookup_creature)
    assert inspect.iscoroutinefunction(lookup_character_option)
    assert inspect.iscoroutinefunction(lookup_equipment)
    assert inspect.iscoroutinefunction(lookup_rule)
```

### Step 2: Run end-to-end tests

Run: `pytest tests/test_tools/test_end_to_end.py -v`

Expected: All 3 tests PASS

### Step 3: Run full test suite with coverage

Run: `pytest tests/ -v --cov=lorekeeper_mcp --cov-report=term-missing`

Expected: All tests PASS, overall coverage >85%

### Step 4: Run code quality checks

Run: `ruff check src/lorekeeper_mcp/tools/ && ruff format --check src/lorekeeper_mcp/tools/`

Expected: No issues found

### Step 5: Commit end-to-end tests

Run: `git add tests/test_tools/test_end_to_end.py && git commit -m "test(tools): add end-to-end integration tests"`

Expected: Clean commit

---

## Validation Checklist

Before marking this change complete, verify:

- [ ] All 5 tools are implemented and registered with FastMCP
- [ ] All tools have comprehensive unit tests with >90% coverage
- [ ] Integration tests verify tool registration and MCP protocol compatibility
- [ ] All tests pass: `pytest tests/test_tools/ -v`
- [ ] Code quality checks pass: `ruff check src/lorekeeper_mcp/tools/`
- [ ] Documentation is accurate and complete
- [ ] Server starts without errors: `uv run python -m lorekeeper_mcp`
- [ ] All commits are clean and follow conventional commit format

## Summary

This plan implements the 5 core MCP tools in bite-sized, test-driven steps. Each task follows the TDD cycle:
1. Write failing test
2. Run test to verify failure
3. Write minimal implementation
4. Run test to verify pass
5. Commit

Total estimated time: ~3-4 hours for careful, methodical implementation with frequent commits.
