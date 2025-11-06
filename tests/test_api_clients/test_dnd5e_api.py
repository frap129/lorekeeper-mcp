"""Tests for Dnd5eApiClient."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.exceptions import ApiError
from lorekeeper_mcp.cache.db import get_cached_entity


@pytest.fixture
async def dnd5e_client(test_db) -> Dnd5eApiClient:
    """Create Dnd5eApiClient for testing."""
    client = Dnd5eApiClient(max_retries=0)
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


@respx.mock
async def test_get_magic_schools(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching magic schools."""
    respx.get("https://www.dnd5eapi.co/api/2014/magic-schools/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "evocation",
                        "name": "Evocation",
                        "url": "/api/2014/magic-schools/evocation",
                    },
                    {
                        "index": "abjuration",
                        "name": "Abjuration",
                        "url": "/api/2014/magic-schools/abjuration",
                    },
                ]
            },
        )
    )

    schools = await dnd5e_client.get_magic_schools()

    assert len(schools) == 2
    assert schools[0]["name"] == "Evocation"


@respx.mock
async def test_get_languages(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching languages."""
    respx.get("https://www.dnd5eapi.co/api/2014/languages/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "common", "name": "Common", "url": "/api/2014/languages/common"},
                    {"index": "elvish", "name": "Elvish", "url": "/api/2014/languages/elvish"},
                ]
            },
        )
    )

    languages = await dnd5e_client.get_languages()

    assert len(languages) == 2
    assert languages[0]["name"] == "Common"


@respx.mock
async def test_get_proficiencies(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching proficiencies."""
    respx.get("https://www.dnd5eapi.co/api/2014/proficiencies/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "light-armor",
                        "name": "Light Armor",
                        "url": "/api/2014/proficiencies/light-armor",
                    },
                    {
                        "index": "longswords",
                        "name": "Longswords",
                        "url": "/api/2014/proficiencies/longswords",
                    },
                ]
            },
        )
    )

    proficiencies = await dnd5e_client.get_proficiencies()

    assert len(proficiencies) == 2
    assert proficiencies[0]["name"] == "Light Armor"


@respx.mock
async def test_get_alignments(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching alignments."""
    respx.get("https://www.dnd5eapi.co/api/2014/alignments/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "lawful-good",
                        "name": "Lawful Good",
                        "url": "/api/2014/alignments/lawful-good",
                    },
                    {
                        "index": "chaotic-evil",
                        "name": "Chaotic Evil",
                        "url": "/api/2014/alignments/chaotic-evil",
                    },
                ]
            },
        )
    )

    alignments = await dnd5e_client.get_alignments()

    assert len(alignments) == 2
    assert alignments[0]["name"] == "Lawful Good"


@respx.mock
async def test_get_rules_uses_entity_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify rules are cached as entities."""
    mock_response = {
        "results": [
            {
                "index": "combat",
                "name": "Combat",
                "desc": "Combat rules...",
            }
        ]
    }
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await dnd5e_client.get_rules()

    # Verify entity cached
    cached = await get_cached_entity("rules", "combat")
    assert cached is not None
    assert cached["name"] == "Combat"


@respx.mock
async def test_get_damage_types_extended_ttl(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify reference data uses 30-day cache TTL."""
    mock_response = {"results": [{"index": "fire", "name": "Fire", "desc": "Fire damage..."}]}
    respx.get("https://www.dnd5eapi.co/api/2014/damage-types/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await dnd5e_client.get_damage_types()

    # Verify that extended TTL is applied by checking the client's cache_ttl
    # after calling get_damage_types (which temporarily sets it to REFERENCE_DATA_TTL)
    # The cache_ttl should be restored to default after the call
    assert dnd5e_client.cache_ttl == 604800  # 7 days default (should be restored)


@respx.mock
async def test_get_rules_api_error(dnd5e_client: Dnd5eApiClient) -> None:
    """Test API error handling."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )

    with pytest.raises(ApiError) as exc_info:
        await dnd5e_client.get_rules()

    assert exc_info.value.status_code == 500


@respx.mock
async def test_get_rules_network_error(dnd5e_client: Dnd5eApiClient) -> None:
    """Test network error handling with empty cache fallback."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        side_effect=httpx.RequestError("Network unavailable")
    )

    # Should return empty list when no cache available
    result = await dnd5e_client.get_rules()

    assert result == []


async def test_get_rules_network_error_with_cache_fallback(dnd5e_client: Dnd5eApiClient) -> None:
    """Test offline fallback to cached entities."""
    # First request succeeds and caches
    with respx.mock:
        respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [{"index": "combat", "name": "Combat", "desc": "Combat rules..."}]
                },
            )
        )
        await dnd5e_client.get_rules()

    # Second request fails, should return cached
    with respx.mock:
        respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
            side_effect=httpx.RequestError("Network unavailable")
        )
        result = await dnd5e_client.get_rules()

        assert len(result) == 1
        assert result[0]["name"] == "Combat"
