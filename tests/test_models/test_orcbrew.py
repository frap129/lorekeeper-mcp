"""Tests for OrcBrew-specific validation models."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.models.orcbrew import (
    OrcBrewArmor,
    OrcBrewCreature,
    OrcBrewMagicItem,
    OrcBrewSpell,
    OrcBrewWeapon,
)


class TestOrcBrewSpell:
    """Tests for OrcBrewSpell model with relaxed constraints."""

    def test_orcbrew_spell_minimal_fields(self) -> None:
        """Test OrcBrewSpell with minimal fields (missing optional fields)."""
        spell = OrcBrewSpell(
            name="Test Spell",
            slug="test-spell",
            level=1,
            school="Evocation",
        )
        assert spell.name == "Test Spell"
        assert spell.level == 1
        # These are optional in OrcBrew models
        assert spell.casting_time is None
        assert spell.range is None
        assert spell.duration is None

    def test_orcbrew_spell_with_all_fields(self) -> None:
        """Test OrcBrewSpell with all fields populated."""
        spell = OrcBrewSpell(
            name="Fireball",
            slug="fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            concentration=False,
            description="A burst of flame",
        )
        assert spell.casting_time == "1 action"
        assert spell.desc == "A burst of flame"

    def test_orcbrew_spell_normalizes_description(self) -> None:
        """Test that description field is normalized to desc."""
        spell = OrcBrewSpell(
            name="Test",
            slug="test",
            level=1,
            school="Evocation",
            description="Test description",
        )
        assert spell.desc == "Test description"

    def test_orcbrew_spell_invalid_level_still_rejected(self) -> None:
        """Test that invalid level values are still rejected."""
        with pytest.raises(ValidationError):
            OrcBrewSpell(
                name="Invalid",
                slug="invalid",
                level=10,  # Still invalid
                school="Evocation",
            )


class TestOrcBrewCreature:
    """Tests for OrcBrewCreature model with relaxed constraints."""

    def test_orcbrew_creature_minimal_fields(self) -> None:
        """Test OrcBrewCreature with minimal fields."""
        creature = OrcBrewCreature(
            name="Goblin",
            slug="goblin",
            type="humanoid",
            size="Small",
            challenge=0.25,
        )
        assert creature.name == "Goblin"
        assert creature.challenge_rating == "1/4"
        assert creature.challenge_rating_decimal == 0.25
        # These are optional in OrcBrew models
        assert creature.armor_class is None
        assert creature.hit_points is None
        assert creature.hit_dice is None
        assert creature.alignment is None

    def test_orcbrew_creature_converts_challenge_to_string(self) -> None:
        """Test that numeric challenge is converted to challenge_rating string."""
        creature = OrcBrewCreature(
            name="Dragon",
            slug="dragon",
            type="dragon",
            size="Huge",
            challenge=17,
        )
        assert creature.challenge_rating == "17"
        assert creature.challenge_rating_decimal == 17.0

    def test_orcbrew_creature_handles_fractional_cr(self) -> None:
        """Test fractional challenge ratings are converted correctly."""
        # Test 1/8
        creature = OrcBrewCreature(
            name="Tiny Creature",
            slug="tiny-creature",
            type="beast",
            size="Tiny",
            challenge=0.125,
        )
        assert creature.challenge_rating == "1/8"
        assert creature.challenge_rating_decimal == 0.125

        # Test 1/2
        creature2 = OrcBrewCreature(
            name="Medium Creature",
            slug="medium-creature",
            type="beast",
            size="Medium",
            challenge=0.5,
        )
        assert creature2.challenge_rating == "1/2"


class TestOrcBrewWeapon:
    """Tests for OrcBrewWeapon model with relaxed constraints."""

    def test_orcbrew_weapon_minimal_fields(self) -> None:
        """Test OrcBrewWeapon with minimal fields (range, long_range, is_simple being None)."""
        weapon = OrcBrewWeapon(
            name="Club",
            slug="club",
            damage_dice="1d4",
            damage_type="Bludgeoning",
        )
        assert weapon.name == "Club"
        assert weapon.damage_dice == "1d4"
        assert weapon.damage_type == "Bludgeoning"
        # These are optional in OrcBrew models
        assert weapon.range is None
        assert weapon.long_range is None
        assert weapon.is_simple is None


class TestOrcBrewArmor:
    """Tests for OrcBrewArmor model with relaxed constraints."""

    def test_orcbrew_armor_minimal_fields(self) -> None:
        """Test OrcBrewArmor with minimal fields (category being None)."""
        armor = OrcBrewArmor(
            name="Leather Armor",
            slug="leather-armor",
        )
        assert armor.name == "Leather Armor"
        assert armor.slug == "leather-armor"
        # These are optional in OrcBrew models
        assert armor.category is None


class TestOrcBrewMagicItem:
    """Tests for OrcBrewMagicItem model with relaxed constraints."""

    def test_orcbrew_magic_item_minimal_fields(self) -> None:
        """Test OrcBrewMagicItem with minimal fields."""
        item = OrcBrewMagicItem(
            name="Ring of Protection",
            slug="ring-of-protection",
        )
        assert item.name == "Ring of Protection"
        assert item.slug == "ring-of-protection"
        # All fields are optional in OrcBrew models
        assert item.rarity is None
        assert item.requires_attunement is None
        assert item.type is None
