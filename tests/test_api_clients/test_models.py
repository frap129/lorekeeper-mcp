"""Tests for Pydantic response models."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.api_clients.models.base import BaseModel
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon
from lorekeeper_mcp.api_clients.models.monster import Monster
from lorekeeper_mcp.api_clients.models.spell import Spell


def test_base_model_required_fields() -> None:
    """Test that BaseModel validates required fields."""
    model = BaseModel(name="Test Item", slug="test-item")
    assert model.name == "Test Item"
    assert model.slug == "test-item"


def test_base_model_optional_fields() -> None:
    """Test that BaseModel handles optional fields."""
    model = BaseModel(
        name="Test Item",
        slug="test-item",
        desc="Test description",
        document_url="https://example.com",
    )
    assert model.desc == "Test description"
    assert model.document_url == "https://example.com"


def test_base_model_missing_required_field() -> None:
    """Test that BaseModel raises error for missing required fields."""
    with pytest.raises(ValidationError):
        BaseModel(name="Test")  # Missing slug


def test_base_model_to_dict() -> None:
    """Test model serialization to dict."""
    model = BaseModel(name="Test", slug="test", desc="Description")
    data = model.model_dump()

    assert data["name"] == "Test"
    assert data["slug"] == "test"
    assert data["desc"] == "Description"


def test_spell_model_minimal() -> None:
    """Test Spell model with minimal required fields."""
    spell = Spell(
        name="Fireball",
        slug="fireball",
        level=3,
        school="Evocation",
        casting_time="1 action",
        range="150 feet",
        components="V, S, M",
        duration="Instantaneous",
    )

    assert spell.name == "Fireball"
    assert spell.level == 3
    assert spell.school == "Evocation"


def test_spell_model_full() -> None:
    """Test Spell model with all fields."""
    spell = Spell(
        name="Fireball",
        slug="fireball",
        level=3,
        school="Evocation",
        casting_time="1 action",
        range="150 feet",
        components="V, S, M",
        duration="Instantaneous",
        desc="A bright streak flashes...",
        higher_level="When you cast this spell using a spell slot of 4th level or higher...",
        concentration=False,
        ritual=False,
        material="A tiny ball of bat guano and sulfur",
        damage_type=["fire"],
    )

    assert spell.concentration is False
    assert spell.ritual is False
    assert spell.material == "A tiny ball of bat guano and sulfur"
    assert spell.damage_type == ["fire"]


def test_spell_cantrip() -> None:
    """Test Spell model with cantrip (level 0)."""
    spell = Spell(
        name="Fire Bolt",
        slug="fire-bolt",
        level=0,
        school="Evocation",
        casting_time="1 action",
        range="120 feet",
        components="V, S",
        duration="Instantaneous",
    )

    assert spell.level == 0
    assert spell.name == "Fire Bolt"


def test_monster_model_minimal() -> None:
    """Test Monster model with minimal fields."""
    monster = Monster(
        name="Goblin",
        slug="goblin",
        size="Small",
        type="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        challenge_rating="1/4",
    )

    assert monster.name == "Goblin"
    assert monster.size == "Small"
    assert monster.armor_class == 15
    assert monster.challenge_rating == "1/4"


def test_monster_model_with_stats() -> None:
    """Test Monster model with ability scores."""
    monster = Monster(
        name="Goblin",
        slug="goblin",
        size="Small",
        type="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        challenge_rating="1/4",
        strength=8,
        dexterity=14,
        constitution=10,
        intelligence=10,
        wisdom=8,
        charisma=8,
    )

    assert monster.strength == 8
    assert monster.dexterity == 14


def test_monster_model_invalid_stats() -> None:
    """Test Monster model validation for invalid ability scores and stats."""
    # Test ability score below 1
    with pytest.raises(ValidationError):
        Monster(
            name="Invalid Monster",
            slug="invalid",
            size="Medium",
            type="humanoid",
            alignment="neutral",
            armor_class=10,
            hit_points=10,
            hit_dice="2d6",
            challenge_rating="1/2",
            strength=0,  # Invalid: must be >= 1
        )

    # Test ability score above 30
    with pytest.raises(ValidationError):
        Monster(
            name="Invalid Monster",
            slug="invalid",
            size="Medium",
            type="humanoid",
            alignment="neutral",
            armor_class=10,
            hit_points=10,
            hit_dice="2d6",
            challenge_rating="1/2",
            dexterity=31,  # Invalid: must be <= 30
        )

    # Test negative armor_class
    with pytest.raises(ValidationError):
        Monster(
            name="Invalid Monster",
            slug="invalid",
            size="Medium",
            type="humanoid",
            alignment="neutral",
            armor_class=-1,  # Invalid: must be >= 0
            hit_points=10,
            hit_dice="2d6",
            challenge_rating="1/2",
        )

    # Test negative hit_points
    with pytest.raises(ValidationError):
        Monster(
            name="Invalid Monster",
            slug="invalid",
            size="Medium",
            type="humanoid",
            alignment="neutral",
            armor_class=10,
            hit_points=-5,  # Invalid: must be >= 0
            hit_dice="2d6",
            challenge_rating="1/2",
        )


def test_armor_model() -> None:
    """Test Armor model."""
    armor = Armor(
        name="Chain Mail",
        slug="chain-mail",
        category="Heavy",
        base_ac=16,
        cost="75 gp",
        weight=55.0,
        stealth_disadvantage=True,
    )

    assert armor.name == "Chain Mail"
    assert armor.category == "Heavy"
    assert armor.base_ac == 16
    assert armor.stealth_disadvantage is True


def test_weapon_model_real_api_dagger() -> None:
    """Test Weapon model with real Open5e API v2 dagger response."""
    # Real data from Open5e API v2 - Dagger
    weapon_data = {
        "name": "Dagger",
        "slug": "dagger",
        "key": "srd-2024_dagger",
        "damage_dice": "1d4",
        "damage_type": {
            "name": "Piercing",
            "key": "piercing",
            "url": "https://api.open5e.com/v2/damagetypes/piercing/",
        },
        "properties": [
            {
                "property": {
                    "name": "Finesse",
                    "type": None,
                    "url": "/v2/weaponproperties/srd-2024_finesse-wp/",
                },
                "detail": None,
            },
            {
                "property": {
                    "name": "Light",
                    "type": None,
                    "url": "/v2/weaponproperties/srd-2024_light-wp/",
                },
                "detail": None,
            },
        ],
        "range": 20.0,
        "long_range": 60.0,
        "distance_unit": "feet",
        "is_simple": True,
        "is_improvised": False,
    }

    weapon = Weapon(**weapon_data)

    assert weapon.name == "Dagger"
    assert weapon.key == "srd-2024_dagger"
    assert weapon.damage_dice == "1d4"
    assert weapon.damage_type.name == "Piercing"
    assert weapon.damage_type.key == "piercing"
    assert weapon.is_simple is True
    assert weapon.is_improvised is False
    assert weapon.range == 20.0
    assert weapon.long_range == 60.0
    assert weapon.distance_unit == "feet"
    assert len(weapon.properties) == 2
    assert weapon.properties[0].property.name == "Finesse"


def test_weapon_model_greatsword() -> None:
    """Test Weapon model with martial melee weapon (greatsword)."""
    weapon_data = {
        "name": "Greatsword",
        "slug": "greatsword",
        "key": "srd-2024_greatsword",
        "damage_dice": "2d6",
        "damage_type": {
            "name": "Slashing",
            "key": "slashing",
            "url": "https://api.open5e.com/v2/damagetypes/slashing/",
        },
        "properties": [
            {
                "property": {
                    "name": "Heavy",
                    "type": None,
                    "url": "/v2/weaponproperties/srd-2024_heavy-wp/",
                },
                "detail": None,
            },
            {
                "property": {
                    "name": "Two-Handed",
                    "type": None,
                    "url": "/v2/weaponproperties/srd-2024_two-handed-wp/",
                },
                "detail": None,
            },
        ],
        "range": 0.0,
        "long_range": 0.0,
        "distance_unit": "feet",
        "is_simple": False,
        "is_improvised": False,
    }

    weapon = Weapon(**weapon_data)

    assert weapon.name == "Greatsword"
    assert weapon.key == "srd-2024_greatsword"
    assert weapon.damage_dice == "2d6"
    assert weapon.damage_type.name == "Slashing"
    assert weapon.is_simple is False
    assert weapon.range == 0.0
    assert weapon.long_range == 0.0
    assert len(weapon.properties) == 2


def test_weapon_with_versatile_property() -> None:
    """Test Weapon with Versatile property containing detail."""
    weapon_data = {
        "name": "Longsword",
        "slug": "longsword",
        "key": "srd-2024_longsword",
        "damage_dice": "1d8",
        "damage_type": {
            "name": "Slashing",
            "key": "slashing",
            "url": "https://api.open5e.com/v2/damagetypes/slashing/",
        },
        "properties": [
            {
                "property": {
                    "name": "Versatile",
                    "type": None,
                    "url": "/v2/weaponproperties/srd-2024_versatile-wp/",
                },
                "detail": "1d10",
            }
        ],
        "range": 0.0,
        "long_range": 0.0,
        "distance_unit": "feet",
        "is_simple": False,
        "is_improvised": False,
    }

    weapon = Weapon(**weapon_data)

    assert weapon.name == "Longsword"
    assert len(weapon.properties) == 1
    assert weapon.properties[0].property.name == "Versatile"
    assert weapon.properties[0].detail == "1d10"


def test_weapon_with_mastery_property() -> None:
    """Test Weapon with Mastery property (5e 2024 feature)."""
    weapon_data = {
        "name": "Dagger",
        "slug": "dagger",
        "key": "srd-2024_dagger",
        "damage_dice": "1d4",
        "damage_type": {
            "name": "Piercing",
            "key": "piercing",
            "url": "https://api.open5e.com/v2/damagetypes/piercing/",
        },
        "properties": [
            {
                "property": {
                    "name": "Nick",
                    "type": "Mastery",
                    "url": "/v2/weaponproperties/srd-2024_nick-mastery/",
                },
                "detail": None,
            }
        ],
        "range": 0.0,
        "long_range": 0.0,
        "distance_unit": "feet",
        "is_simple": True,
        "is_improvised": False,
    }

    weapon = Weapon(**weapon_data)

    assert weapon.properties[0].property.type == "Mastery"
    assert weapon.properties[0].property.name == "Nick"


def test_weapon_with_empty_properties() -> None:
    """Test Weapon with no properties."""
    weapon_data = {
        "name": "Club",
        "slug": "club",
        "key": "srd-2024_club",
        "damage_dice": "1d4",
        "damage_type": {
            "name": "Bludgeoning",
            "key": "bludgeoning",
            "url": "https://api.open5e.com/v2/damagetypes/bludgeoning/",
        },
        "properties": [],
        "range": 0.0,
        "long_range": 0.0,
        "distance_unit": "feet",
        "is_simple": True,
        "is_improvised": False,
    }

    weapon = Weapon(**weapon_data)

    assert len(weapon.properties) == 0
    assert weapon.name == "Club"
