"""Integration tests for MCP tools with real repositories and database cache.

These tests verify:
1. Tools work with real repositories (not mocks)
2. All 5 tools function correctly
3. Database cache persists data
4. Tool registration and schemas are valid
"""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.sqlite import SQLiteCache
from lorekeeper_mcp.repositories.factory import RepositoryFactory
from lorekeeper_mcp.server import mcp
from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option
from lorekeeper_mcp.tools.creature_lookup import lookup_creature
from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment
from lorekeeper_mcp.tools.rule_lookup import lookup_rule
from lorekeeper_mcp.tools.spell_lookup import lookup_spell

# ============================================================================
# Tool Registration and Validation Tests
# ============================================================================


@pytest.mark.integration
def test_all_tools_registered():
    """Verify all 5 tools are registered with FastMCP."""
    tools = mcp._tool_manager._tools
    tool_names = set(tools.keys())

    expected_tools = {
        "lookup_spell",
        "lookup_creature",
        "lookup_character_option",
        "lookup_equipment",
        "lookup_rule",
    }

    assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"


@pytest.mark.integration
def test_tool_schemas_valid():
    """Verify tool schemas are properly defined."""
    tools = mcp._tool_manager._tools

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
    assert "rule_type" in rule_tool.parameters["required"]


# ============================================================================
# Spell Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@respx.mock
async def test_spell_lookup_basic(test_db):
    """Test basic spell lookup with real repository."""
    # Mock the API response
    spell_response = {
        "results": [
            {
                "name": "Fireball",
                "slug": "fireball",
                "level": 3,
                "school": "Evocation",
                "casting_time": "1 action",
                "range": "150 feet",
                "components": "V, S, M",
                "material": "a tiny ball of bat guano and sulfur",
                "duration": "Instantaneous",
                "concentration": False,
                "ritual": False,
                "desc": "A bright streak flashes from pointing...",
                "document_url": "https://example.com/fireball",
            }
        ]
    }

    respx.get("https://api.open5e.com/v2/spells/?").mock(
        return_value=httpx.Response(200, json=spell_response)
    )

    # Use default repository (not mocked)
    result = await lookup_spell(name="fireball")
    # Verify result structure
    assert isinstance(result, list)
    if len(result) > 0:
        assert "name" in result[0]
        assert "level" in result[0]


@pytest.mark.integration
@respx.mock
async def test_spell_lookup_by_level(test_db):
    """Test spell lookup filtered by level."""
    spell_response = {
        "results": [
            {
                "name": "Magic Missile",
                "slug": "magic-missile",
                "level": 1,
                "school": "Evocation",
                "casting_time": "1 action",
                "range": "120 feet",
                "components": "V, S",
                "material": None,
                "duration": "Instantaneous",
                "concentration": False,
                "ritual": False,
                "desc": "You hurl magical energy...",
                "document_url": "https://example.com/magic-missile",
            }
        ]
    }

    respx.get("https://api.open5e.com/v2/spells/?").mock(
        return_value=httpx.Response(200, json=spell_response)
    )

    # Test that tool can be called with level filter
    result = await lookup_spell(level=1)
    assert isinstance(result, list)


# ============================================================================
# Creature Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@respx.mock
async def test_creature_lookup_basic(test_db):
    """Test basic creature lookup with real repository."""
    monster_response = {
        "results": [
            {
                "name": "Ancient Red Dragon",
                "slug": "ancient-red-dragon",
                "desc": "A massive red dragon...",
                "size": "Gargantuan",
                "type": "dragon",
                "alignment": "chaotic evil",
                "armor_class": 22,
                "hit_points": 546,
                "hit_dice": "28d20+252",
                "strength": 30,
                "dexterity": 10,
                "constitution": 29,
                "intelligence": 18,
                "wisdom": 15,
                "charisma": 23,
                "challenge_rating": "24",
                "speed": {"walk": 40, "climb": 40, "fly": 80},
                "document_url": "https://example.com/dragon",
            }
        ]
    }

    respx.get("https://api.open5e.com/v1/monsters/?").mock(
        return_value=httpx.Response(200, json=monster_response)
    )

    # Test basic creature lookup
    result = await lookup_creature(name="dragon")
    assert isinstance(result, list)
    if len(result) > 0:
        assert "name" in result[0]
        assert "hit_points" in result[0]


@pytest.mark.integration
@respx.mock
async def test_creature_lookup_by_cr(test_db):
    """Test creature lookup filtered by challenge rating."""
    monster_response = {
        "results": [
            {
                "name": "Lich",
                "slug": "lich",
                "desc": "A lich is an undead wizard...",
                "size": "Medium",
                "type": "undead",
                "alignment": "any evil",
                "armor_class": 17,
                "hit_points": 135,
                "hit_dice": "10d8+40",
                "strength": 11,
                "dexterity": 16,
                "constitution": 16,
                "intelligence": 20,
                "wisdom": 14,
                "charisma": 16,
                "challenge_rating": "21",
                "speed": {"walk": 0, "fly": 0},
                "document_url": "https://example.com/lich",
            }
        ]
    }

    respx.get("https://api.open5e.com/v1/monsters/?").mock(
        return_value=httpx.Response(200, json=monster_response)
    )

    # Test that tool can be called with CR filter
    result = await lookup_creature(cr=21.0)
    assert isinstance(result, list)


# ============================================================================
# Equipment Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@respx.mock
async def test_equipment_lookup_weapons(test_db):
    """Test equipment lookup for weapons."""
    # Step 1: Mock category endpoint returning list of weapons
    category_response = {
        "equipment": [
            {"index": "longsword", "name": "Longsword"},
        ]
    }
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/weapon").mock(
        return_value=httpx.Response(200, json=category_response)
    )

    # Step 2: Mock individual weapon endpoint returning full details
    weapon_detail = {
        "index": "longsword",
        "name": "Longsword",
        "equipment_category": {"index": "melee-weapons"},
        "weapon_category": "melee weapons",
        "weapon_range": "Melee",
        "category_range": "Melee",
        "damage": {"damage_dice": "1d8", "damage_type": {"index": "slashing"}},
        "two_handed_damage": {"damage_dice": "1d10", "damage_type": {"index": "slashing"}},
        "range": {"normal": 5, "long": None},
        "weight": 3.0,
        "properties": [{"index": "versatile"}],
        "cost": {"quantity": 1, "unit": "gp"},
        "url": "https://example.com/longsword",
    }
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/longsword").mock(
        return_value=httpx.Response(200, json=weapon_detail)
    )

    result = await lookup_equipment(name="longsword", type="weapon")
    assert isinstance(result, list)


@pytest.mark.integration
@respx.mock
async def test_equipment_lookup_armor(test_db):
    """Test equipment lookup for armor."""
    # Step 1: Mock category endpoint returning list of armor
    category_response = {
        "equipment": [
            {"index": "plate", "name": "Plate"},
        ]
    }
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/armor").mock(
        return_value=httpx.Response(200, json=category_response)
    )

    # Step 2: Mock individual armor endpoint returning full details
    armor_detail = {
        "index": "plate",
        "name": "Plate",
        "equipment_category": {"index": "armor"},
        "armor_category": "heavy armor",
        "armor_class": {"base": 18},
        "str_minimum": 15,
        "stealth_disadvantage": True,
        "weight": 65.0,
        "cost": {"quantity": 1500, "unit": "gp"},
        "url": "https://example.com/plate",
    }
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/plate").mock(
        return_value=httpx.Response(200, json=armor_detail)
    )

    result = await lookup_equipment(name="plate", type="armor")
    assert isinstance(result, list)


# ============================================================================
# Character Option Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@respx.mock
async def test_character_option_lookup_class(test_db):
    """Test character option lookup for classes."""
    class_response = {
        "results": [
            {
                "index": "barbarian",
                "name": "Barbarian",
                "hit_die": 12,
                "url": "https://example.com/barbarian",
            }
        ]
    }

    respx.get("https://www.dnd5eapi.co/api/2014/classes/?").mock(
        return_value=httpx.Response(200, json=class_response)
    )

    result = await lookup_character_option(type="class", name="barbarian")
    assert isinstance(result, list)


@pytest.mark.integration
@respx.mock
async def test_character_option_lookup_race(test_db):
    """Test character option lookup for races."""
    race_response = {
        "results": [
            {
                "index": "dwarf",
                "name": "Dwarf",
                "ability_bonuses": [{"ability_score": {"index": "con"}, "bonus": 2}],
                "speed": 25,
                "url": "https://example.com/dwarf",
            }
        ]
    }

    respx.get("https://www.dnd5eapi.co/api/2014/races/?").mock(
        return_value=httpx.Response(200, json=race_response)
    )

    result = await lookup_character_option(type="race", name="dwarf")
    assert isinstance(result, list)


@pytest.mark.integration
@respx.mock
async def test_rule_lookup_ability_scores_with_cache(test_db):
    """Test ability score lookup with cache support."""
    ability_response = {
        "results": [
            {
                "index": "str",
                "name": "Strength",
                "full_name": "Strength",
                "desc": ["Strength measures bodily power..."],
                "url": "/api/2014/ability-scores/str",
            },
            {
                "index": "dex",
                "name": "Dexterity",
                "full_name": "Dexterity",
                "desc": ["Dexterity measures agility..."],
                "url": "/api/2014/ability-scores/dex",
            },
        ]
    }

    # Mock the API endpoint - repository filters name client-side
    route = respx.get("https://www.dnd5eapi.co/api/2014/ability-scores/").mock(
        return_value=httpx.Response(200, json=ability_response)
    )

    # First call - should hit API and cache
    result1 = await lookup_rule(rule_type="ability-score", name="Strength")
    assert len(result1) == 1
    assert result1[0]["name"] == "Strength"
    assert route.call_count == 1

    # Second call - should hit cache
    result2 = await lookup_rule(rule_type="ability-score", name="Strength")
    assert len(result2) == 1
    assert result2[0]["name"] == "Strength"
    assert route.call_count == 1  # No additional API call


# ============================================================================
# Database Cache Tests
# ============================================================================
# Rule Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@respx.mock
async def test_rule_lookup_condition(test_db):
    """Test rule lookup for conditions."""
    condition_response = {
        "results": [
            {
                "index": "blinded",
                "name": "Blinded",
                "desc": "A blinded creature can't see...",
                "url": "https://example.com/blinded",
            }
        ]
    }

    respx.get("https://www.dnd5eapi.co/api/2014/conditions/?").mock(
        return_value=httpx.Response(200, json=condition_response)
    )

    result = await lookup_rule(rule_type="condition", name="blinded")
    assert isinstance(result, list)


@pytest.mark.integration
@respx.mock
async def test_rule_lookup_damage_type(test_db):
    """Test rule lookup for damage types."""
    damage_response = {
        "results": [
            {
                "index": "fire",
                "name": "Fire",
                "desc": "Fire damage.",
                "url": "https://example.com/fire",
            }
        ]
    }

    respx.get("https://www.dnd5eapi.co/api/2014/damage-types/?").mock(
        return_value=httpx.Response(200, json=damage_response)
    )

    result = await lookup_rule(rule_type="damage-type", name="fire")
    assert isinstance(result, list)


@pytest.mark.integration
@respx.mock
async def test_rule_lookup_skill(test_db):
    """Test rule lookup for skills."""
    skill_response = {
        "results": [
            {
                "index": "acrobatics",
                "name": "Acrobatics",
                "ability_score": {"index": "dex"},
                "url": "https://example.com/acrobatics",
            }
        ]
    }

    respx.get("https://www.dnd5eapi.co/api/2014/skills/?").mock(
        return_value=httpx.Response(200, json=skill_response)
    )

    result = await lookup_rule(rule_type="skill", name="acrobatics")
    assert isinstance(result, list)


# ============================================================================
# Database Cache Tests
# ============================================================================


@pytest.mark.integration
async def test_cache_persistence(test_db):
    """Test that cache persists data correctly across operations."""
    cache = SQLiteCache(db_path=str(test_db))

    test_spell = {
        "name": "Test Spell",
        "slug": "test-spell",
        "level": 1,
        "school": "abjuration",
        "casting_time": "1 action",
        "range": "Self",
        "components": "V",
        "material": None,
        "duration": "1 minute",
        "concentration": False,
        "ritual": False,
        "desc": "A test spell",
        "document_url": "https://example.com",
        "higher_level": None,
        "damage_type": None,
    }

    # Store entity
    stored = await cache.store_entities([test_spell], "spells")
    assert stored > 0

    # Retrieve entity by indexed field (level)
    retrieved = await cache.get_entities("spells", level=1)
    assert len(retrieved) > 0
    assert retrieved[0]["name"] == "Test Spell"


@pytest.mark.integration
async def test_cache_filtering(test_db):
    """Test cache filtering capabilities."""
    cache = SQLiteCache(db_path=str(test_db))

    spells = [
        {
            "name": "Fireball",
            "slug": "fireball",
            "level": 3,
            "school": "evocation",
            "casting_time": "1 action",
            "range": "150 feet",
            "components": "V, S, M",
            "material": "a tiny ball of bat guano and sulfur",
            "duration": "Instantaneous",
            "concentration": False,
            "ritual": False,
            "desc": "A bright streak flashes...",
            "document_url": "https://example.com",
            "higher_level": None,
            "damage_type": None,
        },
        {
            "name": "Magic Missile",
            "slug": "magic-missile",
            "level": 1,
            "school": "evocation",
            "casting_time": "1 action",
            "range": "120 feet",
            "components": "V, S",
            "material": None,
            "duration": "Instantaneous",
            "concentration": False,
            "ritual": False,
            "desc": "You hurl magical energy...",
            "document_url": "https://example.com",
            "higher_level": None,
            "damage_type": None,
        },
    ]

    # Store spells
    stored = await cache.store_entities(spells, "spells")
    assert stored == 2

    # Filter by level
    level_1_spells = await cache.get_entities("spells", level=1)
    assert len(level_1_spells) > 0
    assert level_1_spells[0]["level"] == 1

    # Filter by school
    evocation_spells = await cache.get_entities("spells", school="evocation")
    assert len(evocation_spells) >= 2


@pytest.mark.integration
async def test_repository_factory_creates_instances():
    """Test that repository factory creates properly configured instances."""
    v1_client = Open5eV1Client()
    v2_client = Open5eV2Client()
    dnd5e_client = Dnd5eApiClient()

    try:
        # Create all repositories
        spell_repo = RepositoryFactory.create_spell_repository(client=v2_client)
        monster_repo = RepositoryFactory.create_monster_repository(client=v1_client)
        equipment_repo = RepositoryFactory.create_equipment_repository(client=dnd5e_client)
        char_opt_repo = RepositoryFactory.create_character_option_repository(client=dnd5e_client)
        rule_repo = RepositoryFactory.create_rule_repository(client=dnd5e_client)

        # Verify all repositories are created
        assert spell_repo is not None
        assert monster_repo is not None
        assert equipment_repo is not None
        assert char_opt_repo is not None
        assert rule_repo is not None

        # Verify repositories have required methods
        assert hasattr(spell_repo, "search")
        assert hasattr(spell_repo, "get_all")
        assert hasattr(monster_repo, "search")
        assert hasattr(equipment_repo, "search")
        assert hasattr(char_opt_repo, "search")
        assert hasattr(rule_repo, "search")
    finally:
        await v1_client.close()
        await v2_client.close()
        await dnd5e_client.close()
