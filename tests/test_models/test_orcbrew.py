"""Tests for OrcBrew-specific validation models."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.models import Armor, Creature, MagicItem, Spell, Weapon
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


class TestOrcBrewSpellToCanonical:
    """Tests for OrcBrewSpell.to_canonical() method."""

    def test_to_canonical_returns_spell_instance(self) -> None:
        """Test that to_canonical returns a Spell instance."""
        orcbrew_spell = OrcBrewSpell(
            name="Fireball",
            slug="fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
        )
        canonical = orcbrew_spell.to_canonical()
        assert isinstance(canonical, Spell)

    def test_to_canonical_preserves_required_fields(self) -> None:
        """Test that required fields are preserved in conversion."""
        orcbrew_spell = OrcBrewSpell(
            name="Magic Missile",
            slug="magic-missile",
            level=1,
            school="Evocation",
            casting_time="1 action",
            range="120 feet",
            duration="Instantaneous",
            desc="A dart of magical force",
        )
        canonical = orcbrew_spell.to_canonical()
        assert canonical.name == "Magic Missile"
        assert canonical.slug == "magic-missile"
        assert canonical.level == 1
        assert canonical.school == "Evocation"
        assert canonical.casting_time == "1 action"
        assert canonical.range == "120 feet"
        assert canonical.duration == "Instantaneous"
        assert canonical.desc == "A dart of magical force"

    def test_to_canonical_uses_defaults_for_missing_fields(self) -> None:
        """Test that default values are used for optional OrcBrew fields."""
        orcbrew_spell = OrcBrewSpell(
            name="Custom Spell",
            slug="custom-spell",
            level=2,
            school="Conjuration",
            # No casting_time, range, or duration
        )
        canonical = orcbrew_spell.to_canonical()
        # Should use defaults for missing required fields
        assert canonical.casting_time == "Unknown"
        assert canonical.range == "Self"
        assert canonical.duration == "Instantaneous"

    def test_to_canonical_preserves_optional_fields(self) -> None:
        """Test that optional fields are preserved when present."""
        orcbrew_spell = OrcBrewSpell(
            name="Hex",
            slug="hex",
            level=1,
            school="Enchantment",
            casting_time="1 bonus action",
            range="90 feet",
            duration="Concentration, up to 1 hour",
            concentration=True,
            classes=["warlock"],
            higher_level="Cast at higher levels for longer duration",
        )
        canonical = orcbrew_spell.to_canonical()
        assert canonical.concentration is True
        assert canonical.classes == ["warlock"]
        assert canonical.higher_level == "Cast at higher levels for longer duration"


class TestOrcBrewCreatureToCanonical:
    """Tests for OrcBrewCreature.to_canonical() method."""

    def test_to_canonical_returns_creature_instance(self) -> None:
        """Test that to_canonical returns a Creature instance."""
        orcbrew_creature = OrcBrewCreature(
            name="Goblin",
            slug="goblin",
            type="humanoid",
            size="Small",
            alignment="neutral evil",
            armor_class=15,
            hit_points=7,
            hit_dice="2d6",
            challenge_rating="1/4",
        )
        canonical = orcbrew_creature.to_canonical()
        assert isinstance(canonical, Creature)

    def test_to_canonical_preserves_required_fields(self) -> None:
        """Test that required fields are preserved in conversion."""
        orcbrew_creature = OrcBrewCreature(
            name="Dragon",
            slug="dragon",
            type="dragon",
            size="Huge",
            alignment="chaotic evil",
            armor_class=19,
            hit_points=200,
            hit_dice="20d12+100",
            challenge_rating="17",
            desc="A fearsome beast",
        )
        canonical = orcbrew_creature.to_canonical()
        assert canonical.name == "Dragon"
        assert canonical.slug == "dragon"
        assert canonical.type == "dragon"
        assert canonical.size == "Huge"
        assert canonical.alignment == "chaotic evil"
        assert canonical.armor_class == 19
        assert canonical.hit_points == 200
        assert canonical.hit_dice == "20d12+100"
        assert canonical.challenge_rating == "17"
        assert canonical.desc == "A fearsome beast"

    def test_to_canonical_uses_defaults_for_missing_fields(self) -> None:
        """Test that default values are used for optional OrcBrew fields."""
        orcbrew_creature = OrcBrewCreature(
            name="Custom Creature",
            slug="custom-creature",
            type="beast",
            size="Medium",
            # No alignment, armor_class, hit_points, hit_dice, challenge_rating
        )
        canonical = orcbrew_creature.to_canonical()
        # Should use defaults for missing required fields
        assert canonical.alignment == "unaligned"
        assert canonical.armor_class == 10
        assert canonical.hit_points == 1
        assert canonical.hit_dice == "1d8"
        assert canonical.challenge_rating == "0"

    def test_to_canonical_preserves_ability_scores(self) -> None:
        """Test that ability scores are preserved when present."""
        orcbrew_creature = OrcBrewCreature(
            name="Orc",
            slug="orc",
            type="humanoid",
            size="Medium",
            alignment="chaotic evil",
            armor_class=13,
            hit_points=15,
            hit_dice="2d8+6",
            challenge_rating="1/2",
            strength=16,
            dexterity=12,
            constitution=16,
            intelligence=7,
            wisdom=11,
            charisma=10,
        )
        canonical = orcbrew_creature.to_canonical()
        assert canonical.strength == 16
        assert canonical.dexterity == 12
        assert canonical.constitution == 16
        assert canonical.intelligence == 7
        assert canonical.wisdom == 11
        assert canonical.charisma == 10


class TestOrcBrewWeaponToCanonical:
    """Tests for OrcBrewWeapon.to_canonical() method."""

    def test_to_canonical_returns_weapon_instance(self) -> None:
        """Test that to_canonical returns a Weapon instance."""
        orcbrew_weapon = OrcBrewWeapon(
            name="Longsword",
            slug="longsword",
            damage_dice="1d8",
            damage_type="Slashing",
            range=5,
            long_range=5,
            distance_unit="feet",
            is_simple=False,
            is_improvised=False,
        )
        canonical = orcbrew_weapon.to_canonical()
        assert isinstance(canonical, Weapon)

    def test_to_canonical_preserves_required_fields(self) -> None:
        """Test that required fields are preserved in conversion."""
        orcbrew_weapon = OrcBrewWeapon(
            name="Shortbow",
            slug="shortbow",
            damage_dice="1d6",
            damage_type="Piercing",
            range=80,
            long_range=320,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
            properties=["Ammunition", "Two-Handed"],
            desc="A simple ranged weapon",
        )
        canonical = orcbrew_weapon.to_canonical()
        assert canonical.name == "Shortbow"
        assert canonical.slug == "shortbow"
        assert canonical.damage_dice == "1d6"
        assert canonical.damage_type == "Piercing"
        assert canonical.range == 80
        assert canonical.long_range == 320
        assert canonical.distance_unit == "feet"
        assert canonical.is_simple is True
        assert canonical.is_improvised is False
        assert canonical.properties == ["Ammunition", "Two-Handed"]
        assert canonical.desc == "A simple ranged weapon"

    def test_to_canonical_uses_defaults_for_missing_fields(self) -> None:
        """Test that default values are used for optional OrcBrew fields."""
        orcbrew_weapon = OrcBrewWeapon(
            name="Custom Weapon",
            slug="custom-weapon",
            damage_dice="1d4",
            damage_type="Bludgeoning",
            # No range, long_range, distance_unit, is_simple, is_improvised
        )
        canonical = orcbrew_weapon.to_canonical()
        # Should use defaults for missing required fields
        assert canonical.range == 5
        assert canonical.long_range == 5
        assert canonical.distance_unit == "feet"
        assert canonical.is_simple is True
        assert canonical.is_improvised is False


class TestOrcBrewArmorToCanonical:
    """Tests for OrcBrewArmor.to_canonical() method."""

    def test_to_canonical_returns_armor_instance(self) -> None:
        """Test that to_canonical returns an Armor instance."""
        orcbrew_armor = OrcBrewArmor(
            name="Chain Mail",
            slug="chain-mail",
            category="Heavy",
        )
        canonical = orcbrew_armor.to_canonical()
        assert isinstance(canonical, Armor)

    def test_to_canonical_preserves_required_fields(self) -> None:
        """Test that required fields are preserved in conversion."""
        orcbrew_armor = OrcBrewArmor(
            name="Plate Armor",
            slug="plate-armor",
            category="Heavy",
            base_ac=18,
            cost="1500 gp",
            weight=65.0,
            stealth_disadvantage=True,
            strength_required=15,
            desc="Full plate armor",
        )
        canonical = orcbrew_armor.to_canonical()
        assert canonical.name == "Plate Armor"
        assert canonical.slug == "plate-armor"
        assert canonical.category == "Heavy"
        assert canonical.base_ac == 18
        assert canonical.cost == "1500 gp"
        assert canonical.weight == 65.0
        assert canonical.stealth_disadvantage is True
        assert canonical.strength_required == 15
        assert canonical.desc == "Full plate armor"

    def test_to_canonical_uses_defaults_for_missing_fields(self) -> None:
        """Test that default values are used for optional OrcBrew fields."""
        orcbrew_armor = OrcBrewArmor(
            name="Custom Armor",
            slug="custom-armor",
            # No category
        )
        canonical = orcbrew_armor.to_canonical()
        # Should use default for missing required field
        assert canonical.category == "Light"


class TestOrcBrewMagicItemToCanonical:
    """Tests for OrcBrewMagicItem.to_canonical() method."""

    def test_to_canonical_returns_magic_item_instance(self) -> None:
        """Test that to_canonical returns a MagicItem instance."""
        orcbrew_item = OrcBrewMagicItem(
            name="Ring of Protection",
            slug="ring-of-protection",
        )
        canonical = orcbrew_item.to_canonical()
        assert isinstance(canonical, MagicItem)

    def test_to_canonical_preserves_all_fields(self) -> None:
        """Test that all fields are preserved in conversion."""
        orcbrew_item = OrcBrewMagicItem(
            name="Staff of Power",
            slug="staff-of-power",
            rarity="very rare",
            requires_attunement=True,
            type="staff",
            wondrous=False,
            weight=6.0,
            desc="A powerful magical staff",
        )
        canonical = orcbrew_item.to_canonical()
        assert canonical.name == "Staff of Power"
        assert canonical.slug == "staff-of-power"
        assert canonical.rarity == "very rare"
        assert canonical.requires_attunement is True
        assert canonical.type == "staff"
        assert canonical.wondrous is False
        assert canonical.weight == 6.0
        assert canonical.desc == "A powerful magical staff"

    def test_to_canonical_handles_minimal_fields(self) -> None:
        """Test that conversion works with minimal fields."""
        orcbrew_item = OrcBrewMagicItem(
            name="Mystery Item",
            slug="mystery-item",
        )
        canonical = orcbrew_item.to_canonical()
        # All fields should be preserved (even if None)
        assert canonical.name == "Mystery Item"
        assert canonical.slug == "mystery-item"
        assert canonical.rarity is None
        assert canonical.requires_attunement is None
