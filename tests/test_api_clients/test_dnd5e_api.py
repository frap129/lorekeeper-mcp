"""Tests for Dnd5eApiClient."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient


@pytest.fixture
async def dnd5e_client(test_db) -> Dnd5eApiClient:
    """Create Dnd5eApiClient for testing."""
    client = Dnd5eApiClient()
    yield client
    await client.close()


async def test_client_initialization(dnd5e_client: Dnd5eApiClient) -> None:
    """Test client initializes with correct configuration."""
    assert dnd5e_client.base_url == "https://www.dnd5eapi.co/api/2014"
    assert dnd5e_client.source_api == "dnd5e_api"
    assert dnd5e_client.cache_ttl == 604800  # 7 days default


@respx.mock
async def test_get_rules_all(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching all rules."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "adventuring",
                        "name": "Adventuring",
                        "url": "/api/2014/rules/adventuring",
                    },
                    {
                        "index": "combat",
                        "name": "Combat",
                        "url": "/api/2014/rules/combat",
                    },
                ]
            },
        )
    )

    rules = await dnd5e_client.get_rules()

    assert len(rules) == 2
    assert rules[0]["name"] == "Adventuring"
    assert rules[1]["name"] == "Combat"


@respx.mock
async def test_get_rules_by_section(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching rules by section."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/adventuring").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "adventuring",
                "name": "Adventuring",
                "desc": "Delving into dungeons...",
                "subsections": [
                    {"index": "time", "name": "Time", "url": "/api/2014/rule-sections/time"}
                ],
            },
        )
    )

    rules = await dnd5e_client.get_rules(section="adventuring")

    assert len(rules) == 1
    assert rules[0]["name"] == "Adventuring"
    assert rules[0]["desc"] == "Delving into dungeons..."


@respx.mock
async def test_get_rule_sections_all(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching all rule sections."""
    respx.get("https://www.dnd5eapi.co/api/2014/rule-sections/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "grappling",
                        "name": "Grappling",
                        "url": "/api/2014/rule-sections/grappling",
                    },
                    {
                        "index": "opportunity-attacks",
                        "name": "Opportunity Attacks",
                        "url": "/api/2014/rule-sections/opportunity-attacks",
                    },
                ]
            },
        )
    )

    sections = await dnd5e_client.get_rule_sections()

    assert len(sections) == 2
    assert sections[0]["name"] == "Grappling"


@respx.mock
async def test_get_rule_sections_by_name(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching specific rule section."""
    respx.get("https://www.dnd5eapi.co/api/2014/rule-sections/grappling").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "grappling",
                "name": "Grappling",
                "desc": "When you want to grab a creature...",
            },
        )
    )

    sections = await dnd5e_client.get_rule_sections(name="grappling")

    assert len(sections) == 1
    assert sections[0]["name"] == "Grappling"
    assert sections[0]["desc"] == "When you want to grab a creature..."


@respx.mock
async def test_get_damage_types(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching damage types."""
    respx.get("https://www.dnd5eapi.co/api/2014/damage-types/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "fire", "name": "Fire", "url": "/api/2014/damage-types/fire"},
                    {"index": "cold", "name": "Cold", "url": "/api/2014/damage-types/cold"},
                ]
            },
        )
    )

    damage_types = await dnd5e_client.get_damage_types()

    assert len(damage_types) == 2
    assert damage_types[0]["name"] == "Fire"


@respx.mock
async def test_get_weapon_properties(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching weapon properties."""
    respx.get("https://www.dnd5eapi.co/api/2014/weapon-properties/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "finesse",
                        "name": "Finesse",
                        "url": "/api/2014/weapon-properties/finesse",
                    },
                    {
                        "index": "versatile",
                        "name": "Versatile",
                        "url": "/api/2014/weapon-properties/versatile",
                    },
                ]
            },
        )
    )

    properties = await dnd5e_client.get_weapon_properties()

    assert len(properties) == 2
    assert properties[0]["name"] == "Finesse"


@respx.mock
async def test_get_skills(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching skills."""
    respx.get("https://www.dnd5eapi.co/api/2014/skills/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "acrobatics",
                        "name": "Acrobatics",
                        "url": "/api/2014/skills/acrobatics",
                    },
                    {"index": "stealth", "name": "Stealth", "url": "/api/2014/skills/stealth"},
                ]
            },
        )
    )

    skills = await dnd5e_client.get_skills()

    assert len(skills) == 2
    assert skills[0]["name"] == "Acrobatics"


@respx.mock
async def test_get_ability_scores(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching ability scores."""
    respx.get("https://www.dnd5eapi.co/api/2014/ability-scores/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "str", "name": "STR", "url": "/api/2014/ability-scores/str"},
                    {"index": "dex", "name": "DEX", "url": "/api/2014/ability-scores/dex"},
                ]
            },
        )
    )

    ability_scores = await dnd5e_client.get_ability_scores()

    assert len(ability_scores) == 2
    assert ability_scores[0]["name"] == "STR"
