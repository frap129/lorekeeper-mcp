"""Tests for Dnd5eApiClient."""

from collections.abc import AsyncGenerator

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon


@pytest.fixture
async def dnd5e_client(test_db) -> AsyncGenerator[Dnd5eApiClient, None]:
    """Create Dnd5eApiClient for testing."""
    client = Dnd5eApiClient(max_retries=0)
    yield client
    await client.close()


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
    """Test network error handling."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        side_effect=httpx.RequestError("Network unavailable")
    )

    # Should raise NetworkError since caching is handled by repositories
    with pytest.raises(NetworkError):
        await dnd5e_client.get_rules()


@respx.mock
async def test_get_backgrounds_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching backgrounds."""
    respx.get("https://www.dnd5eapi.co/api/2014/backgrounds/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "acolyte",
                        "name": "Acolyte",
                        "desc": "You have spent your life in service to a temple...",
                    },
                    {
                        "index": "soldier",
                        "name": "Soldier",
                        "desc": "War has been your life...",
                    },
                ]
            },
        )
    )

    backgrounds = await dnd5e_client.get_backgrounds_dnd5e()

    assert len(backgrounds) == 2
    assert backgrounds[0]["name"] == "Acolyte"
    assert backgrounds[0]["slug"] == "acolyte"
    assert backgrounds[1]["name"] == "Soldier"


@respx.mock
async def test_get_classes_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching classes."""
    respx.get("https://www.dnd5eapi.co/api/2014/classes/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "barbarian",
                        "name": "Barbarian",
                        "hit_die": 12,
                    },
                    {
                        "index": "wizard",
                        "name": "Wizard",
                        "hit_die": 6,
                    },
                ]
            },
        )
    )

    classes = await dnd5e_client.get_classes_dnd5e()

    assert len(classes) == 2
    assert classes[0]["name"] == "Barbarian"
    assert classes[0]["slug"] == "barbarian"


@respx.mock
async def test_get_subclasses(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching subclasses."""
    respx.get("https://www.dnd5eapi.co/api/2014/subclasses/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "berserker",
                        "name": "Berserker",
                        "class": {"index": "barbarian", "name": "Barbarian"},
                    },
                    {
                        "index": "champion",
                        "name": "Champion",
                        "class": {"index": "fighter", "name": "Fighter"},
                    },
                ]
            },
        )
    )

    subclasses = await dnd5e_client.get_subclasses()

    assert len(subclasses) == 2
    assert subclasses[0]["name"] == "Berserker"
    assert subclasses[0]["slug"] == "berserker"


@respx.mock
async def test_get_races_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching races."""
    respx.get("https://www.dnd5eapi.co/api/2014/races/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "human",
                        "name": "Human",
                        "speed": 30,
                    },
                    {
                        "index": "elf",
                        "name": "Elf",
                        "speed": 30,
                    },
                ]
            },
        )
    )

    races = await dnd5e_client.get_races_dnd5e()

    assert len(races) == 2
    assert races[0]["name"] == "Human"
    assert races[0]["slug"] == "human"


@respx.mock
async def test_get_subraces(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching subraces."""
    respx.get("https://www.dnd5eapi.co/api/2014/subraces/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "high-elf",
                        "name": "High Elf",
                        "race": {"index": "elf", "name": "Elf"},
                    },
                    {
                        "index": "forest-gnome",
                        "name": "Forest Gnome",
                        "race": {"index": "gnome", "name": "Gnome"},
                    },
                ]
            },
        )
    )

    subraces = await dnd5e_client.get_subraces()

    assert len(subraces) == 2
    assert subraces[0]["name"] == "High Elf"
    assert subraces[0]["slug"] == "high-elf"


@respx.mock
async def test_get_feats_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching feats."""
    respx.get("https://www.dnd5eapi.co/api/2014/feats/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "alert",
                        "name": "Alert",
                        "desc": "Always vigilant...",
                    },
                    {
                        "index": "athlete",
                        "name": "Athlete",
                        "desc": "You have undergone extensive physical training...",
                    },
                ]
            },
        )
    )

    feats = await dnd5e_client.get_feats_dnd5e()

    assert len(feats) == 2
    assert feats[0]["name"] == "Alert"
    assert feats[0]["slug"] == "alert"


@respx.mock
async def test_get_traits(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching traits."""
    respx.get("https://www.dnd5eapi.co/api/2014/traits/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "darkvision",
                        "name": "Darkvision",
                        "desc": "You can see in dim light...",
                    },
                    {
                        "index": "dwarf-resilience",
                        "name": "Dwarf Resilience",
                        "desc": "You have resistance to poison damage...",
                    },
                ]
            },
        )
    )

    traits = await dnd5e_client.get_traits()

    assert len(traits) == 2
    assert traits[0]["name"] == "Darkvision"
    assert traits[0]["slug"] == "darkvision"


@respx.mock
async def test_get_equipment(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching equipment."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "longsword",
                        "name": "Longsword",
                        "equipment_category": {"index": "melee-weapons", "name": "Melee Weapons"},
                    },
                    {
                        "index": "plate-armor",
                        "name": "Plate Armor",
                        "equipment_category": {"index": "armor", "name": "Armor"},
                    },
                ]
            },
        )
    )

    equipment = await dnd5e_client.get_equipment()

    assert len(equipment) == 2
    assert equipment[0]["name"] == "Longsword"
    assert equipment[0]["slug"] == "longsword"


@respx.mock
async def test_get_equipment_categories(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching equipment categories."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "armor",
                        "name": "Armor",
                        "equipment": [{"index": "plate-armor", "name": "Plate Armor"}],
                    },
                    {
                        "index": "melee-weapons",
                        "name": "Melee Weapons",
                        "equipment": [{"index": "longsword", "name": "Longsword"}],
                    },
                ]
            },
        )
    )

    categories = await dnd5e_client.get_equipment_categories()

    assert len(categories) == 2
    assert categories[0]["name"] == "Armor"
    assert categories[0]["slug"] == "armor"


@respx.mock
async def test_get_magic_items_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching magic items."""
    respx.get("https://www.dnd5eapi.co/api/2014/magic-items/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "bag-of-holding",
                        "name": "Bag of Holding",
                        "rarity": "Uncommon",
                    },
                    {
                        "index": "wand-of-fireballs",
                        "name": "Wand of Fireballs",
                        "rarity": "Rare",
                    },
                ]
            },
        )
    )

    items = await dnd5e_client.get_magic_items_dnd5e()

    assert len(items) == 2
    assert items[0]["name"] == "Bag of Holding"
    assert items[0]["slug"] == "bag-of-holding"


@respx.mock
async def test_get_spells_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching spells."""
    respx.get("https://www.dnd5eapi.co/api/2014/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "acid-splash",
                        "name": "Acid Splash",
                        "level": 0,
                        "school": "evocation",
                    },
                    {
                        "index": "magic-missile",
                        "name": "Magic Missile",
                        "level": 1,
                        "school": "evocation",
                    },
                ]
            },
        )
    )

    spells = await dnd5e_client.get_spells_dnd5e()

    assert len(spells) == 2
    assert spells[0]["name"] == "Acid Splash"
    assert spells[0]["slug"] == "acid-splash"


@respx.mock
async def test_get_monsters_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching monsters."""
    respx.get("https://www.dnd5eapi.co/api/2014/monsters/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "aboleth",
                        "name": "Aboleth",
                        "size": "Large",
                        "type": "aberration",
                        "alignment": "lawful evil",
                        "armor_class": 17,
                        "hit_points": 135,
                        "hit_dice": "10d12+70",
                        "challenge_rating": "10",
                    },
                    {
                        "index": "acererak",
                        "name": "Acererak",
                        "size": "Medium",
                        "type": "undead",
                        "alignment": "neutral evil",
                        "armor_class": 20,
                        "hit_points": 165,
                        "hit_dice": "11d8+110",
                        "challenge_rating": "23",
                    },
                ]
            },
        )
    )

    monsters = await dnd5e_client.get_monsters_dnd5e()

    assert len(monsters) == 2
    assert monsters[0]["name"] == "Aboleth"
    assert monsters[0]["slug"] == "aboleth"
    assert monsters[0]["size"] == "Large"
    assert monsters[1]["armor_class"] == 20


@respx.mock
async def test_get_conditions_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching conditions."""
    respx.get("https://www.dnd5eapi.co/api/2014/conditions/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "blinded",
                        "name": "Blinded",
                        "desc": "A blinded creature can't see...",
                    },
                    {
                        "index": "charmed",
                        "name": "Charmed",
                        "desc": "A charmed creature can't attack its charmer...",
                    },
                ]
            },
        )
    )

    conditions = await dnd5e_client.get_conditions_dnd5e()

    assert len(conditions) == 2
    assert conditions[0]["name"] == "Blinded"
    assert conditions[0]["slug"] == "blinded"


@respx.mock
async def test_get_features(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching features."""
    respx.get("https://www.dnd5eapi.co/api/2014/features/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "action-surge",
                        "name": "Action Surge",
                        "desc": "On your turn, you can take one additional action...",
                        "class": {"index": "fighter", "name": "Fighter"},
                    },
                    {
                        "index": "bardic-inspiration",
                        "name": "Bardic Inspiration",
                        "desc": "You can inspire others...",
                        "class": {"index": "bard", "name": "Bard"},
                    },
                ]
            },
        )
    )

    features = await dnd5e_client.get_features()

    assert len(features) == 2
    assert features[0]["name"] == "Action Surge"
    assert features[0]["slug"] == "action-surge"


@respx.mock
async def test_get_weapons(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching weapons returns Weapon model instances."""
    # Mock the weapon category endpoint
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/weapon").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "weapon",
                "name": "Weapon",
                "equipment": [
                    {"index": "longsword", "name": "Longsword"},
                    {"index": "shortbow", "name": "Shortbow"},
                ],
            },
        )
    )
    # Mock individual weapon endpoints
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/longsword").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "longsword",
                "name": "Longsword",
                "weapon_category": "Martial",
                "damage": {
                    "damage_dice": "1d8",
                    "damage_type": {"index": "slashing", "name": "Slashing"},
                },
                "properties": [],
                "range": {"normal": 5},
            },
        )
    )
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/shortbow").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "shortbow",
                "name": "Shortbow",
                "weapon_category": "Simple",
                "damage": {
                    "damage_dice": "1d6",
                    "damage_type": {"index": "piercing", "name": "Piercing"},
                },
                "properties": [],
                "range": {"normal": 80, "long": 320},
            },
        )
    )
    weapons = await dnd5e_client.get_weapons()
    assert len(weapons) == 2
    assert isinstance(weapons[0], Weapon)
    assert weapons[0].slug == "longsword"


@respx.mock
async def test_get_armor(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching armor returns Armor model instances."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/armor").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "armor",
                "name": "Armor",
                "equipment": [
                    {"index": "plate-armor", "name": "Plate Armor"},
                    {"index": "leather-armor", "name": "Leather Armor"},
                ],
            },
        )
    )
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/plate-armor").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "plate-armor",
                "name": "Plate Armor",
                "armor_category": "Heavy",
                "armor_class": {"base": 18},
            },
        )
    )
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/leather-armor").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "leather-armor",
                "name": "Leather Armor",
                "armor_category": "Light",
                "armor_class": {"base": 11, "dex_bonus": True},
            },
        )
    )
    armor_items = await dnd5e_client.get_armor()
    assert len(armor_items) == 2
    assert isinstance(armor_items[0], Armor)
    assert armor_items[0].slug == "plate-armor"


@pytest.mark.asyncio
@respx.mock
async def test_get_armor_filters_equipment_correctly() -> None:
    """Test that get_armor() properly fetches armor."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/armor").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "armor",
                "name": "Armor",
                "equipment": [
                    {"index": "padded-armor", "name": "Padded"},
                    {"index": "chain-mail", "name": "Chain Mail"},
                ],
            },
        )
    )
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/padded-armor").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "padded-armor",
                "name": "Padded",
                "armor_category": "Light",
                "armor_class": {"base": 11, "dex_bonus": True},
            },
        )
    )
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/chain-mail").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "chain-mail",
                "name": "Chain Mail",
                "armor_category": "Heavy",
                "armor_class": {"base": 16, "dex_bonus": False},
            },
        )
    )
    client = Dnd5eApiClient()
    armor = await client.get_armor()
    await client.close()
    assert len(armor) == 2
    armor_names = [a.name for a in armor]
    assert "Padded" in armor_names
    assert "Chain Mail" in armor_names


@pytest.mark.asyncio
@respx.mock
async def test_get_weapons_filters_equipment_correctly() -> None:
    """Test that get_weapons() properly fetches weapons."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/weapon").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "weapon",
                "name": "Weapon",
                "equipment": [
                    {"index": "club", "name": "Club"},
                    {"index": "dagger", "name": "Dagger"},
                ],
            },
        )
    )
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/club").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "club",
                "name": "Club",
                "weapon_category": "Simple",
                "damage": {"damage_dice": "1d4", "damage_type": {"index": "bludgeoning"}},
                "range": {"normal": 5},
            },
        )
    )
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/dagger").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "dagger",
                "name": "Dagger",
                "weapon_category": "Simple",
                "damage": {"damage_dice": "1d4", "damage_type": {"index": "piercing"}},
                "range": {"normal": 5, "long": 20},
            },
        )
    )
    client = Dnd5eApiClient()
    weapons = await client.get_weapons()
    await client.close()
    assert len(weapons) == 2
    weapon_names = [w.name for w in weapons]
    assert "Club" in weapon_names
    assert "Dagger" in weapon_names
