"""Tests for canonical equipment models."""

from lorekeeper_mcp.models import Armor, MagicItem, Weapon


class TestWeapon:
    """Tests for Weapon model."""

    def test_weapon_minimal_fields(self) -> None:
        """Test Weapon with required fields."""
        weapon = Weapon(
            name="Dagger",
            slug="dagger",
            damage_dice="1d4",
            damage_type="Piercing",
            range=20.0,
            long_range=60.0,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
        )
        assert weapon.name == "Dagger"
        assert weapon.damage_dice == "1d4"
        assert weapon.damage_type == "Piercing"

    def test_weapon_normalizes_key_to_slug(self) -> None:
        """Test that key is normalized to slug."""
        weapon = Weapon(
            name="Dagger",
            key="srd-2024_dagger",
            damage_dice="1d4",
            damage_type="Piercing",
            range=20.0,
            long_range=60.0,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
        )
        assert weapon.slug == "srd-2024_dagger"

    def test_weapon_extracts_damage_type_from_dict(self) -> None:
        """Test that damage_type object is normalized to string."""
        weapon = Weapon(
            name="Dagger",
            slug="dagger",
            damage_dice="1d4",
            damage_type={"name": "Piercing", "key": "piercing"},
            range=20.0,
            long_range=60.0,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
        )
        assert weapon.damage_type == "Piercing"

    def test_weapon_with_properties(self) -> None:
        """Test Weapon with property list."""
        weapon = Weapon(
            name="Longsword",
            slug="longsword",
            damage_dice="1d8",
            damage_type="Slashing",
            range=0.0,
            long_range=0.0,
            distance_unit="feet",
            is_simple=False,
            is_improvised=False,
            properties=["Versatile"],
            versatile_dice="1d10",
        )
        assert weapon.properties == ["Versatile"]
        assert weapon.versatile_dice == "1d10"

    def test_weapon_extracts_properties_from_complex_structure(self) -> None:
        """Test that complex property objects are normalized to strings."""
        weapon = Weapon(
            name="Dagger",
            slug="dagger",
            damage_dice="1d4",
            damage_type="Piercing",
            range=20.0,
            long_range=60.0,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
            properties=[
                {"property": {"name": "Finesse", "type": None}},
                {"property": {"name": "Light", "type": None}},
            ],
        )
        assert weapon.properties == ["Finesse", "Light"]


class TestArmor:
    """Tests for Armor model."""

    def test_armor_minimal_fields(self) -> None:
        """Test Armor with required fields."""
        armor = Armor(
            name="Chain Mail",
            slug="chain-mail",
            category="Heavy",
        )
        assert armor.name == "Chain Mail"
        assert armor.category == "Heavy"

    def test_armor_with_all_fields(self) -> None:
        """Test Armor with all optional fields."""
        armor = Armor(
            name="Chain Mail",
            slug="chain-mail",
            category="Heavy",
            base_ac=16,
            cost="75 gp",
            weight=55.0,
            stealth_disadvantage=True,
            strength_required=13,
        )
        assert armor.base_ac == 16
        assert armor.stealth_disadvantage is True
        assert armor.strength_required == 13


class TestMagicItem:
    """Tests for MagicItem model."""

    def test_magic_item_minimal_fields(self) -> None:
        """Test MagicItem with required fields."""
        item = MagicItem(
            name="Bag of Holding",
            slug="bag-of-holding",
        )
        assert item.name == "Bag of Holding"

    def test_magic_item_with_attunement(self) -> None:
        """Test MagicItem with attunement requirement."""
        item = MagicItem(
            name="Ring of Protection",
            slug="ring-of-protection",
            rarity="rare",
            requires_attunement=True,
            type="ring",
        )
        assert item.requires_attunement is True
        assert item.rarity == "rare"
