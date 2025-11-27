"""Tests for canonical Spell model."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.models import Spell


class TestSpell:
    """Tests for Spell model."""

    def test_spell_minimal_fields(self) -> None:
        """Test Spell with minimal required fields."""
        spell = Spell(
            name="Fireball",
            slug="fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
        )
        assert spell.name == "Fireball"
        assert spell.level == 3
        assert spell.school == "Evocation"

    def test_spell_normalizes_key_to_slug(self) -> None:
        """Test that key is normalized to slug."""
        spell = Spell(
            name="Fireball",
            key="fireball-key",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
        )
        assert spell.slug == "fireball-key"

    def test_spell_normalizes_school_from_dict(self) -> None:
        """Test that school object is normalized to string."""
        spell = Spell(
            name="Fireball",
            slug="fireball",
            level=3,
            school={"name": "Evocation", "key": "evocation"},
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
        )
        assert spell.school == "Evocation"

    def test_spell_extracts_classes_from_objects(self) -> None:
        """Test that class objects are normalized to list of strings."""
        spell = Spell(
            name="Fireball",
            slug="fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            classes=[
                {"index": "wizard", "name": "Wizard"},
                {"index": "sorcerer", "name": "Sorcerer"},
            ],
        )
        assert spell.classes == ["wizard", "sorcerer"]

    def test_spell_generates_slug_from_name(self) -> None:
        """Test that slug is generated from name if not provided."""
        spell = Spell(
            name="Magic Missile",
            level=1,
            school="Evocation",
            casting_time="1 action",
            range="120 feet",
            duration="Instantaneous",
        )
        assert spell.slug == "magic-missile"

    def test_spell_cantrip_level_zero(self) -> None:
        """Test cantrip with level 0."""
        spell = Spell(
            name="Fire Bolt",
            slug="fire-bolt",
            level=0,
            school="Evocation",
            casting_time="1 action",
            range="120 feet",
            duration="Instantaneous",
        )
        assert spell.level == 0

    def test_spell_invalid_level_raises_error(self) -> None:
        """Test that invalid spell level raises error."""
        with pytest.raises(ValidationError):
            Spell(
                name="Invalid",
                slug="invalid",
                level=10,  # Invalid: max is 9
                school="Evocation",
                casting_time="1 action",
                range="Self",
                duration="Instantaneous",
            )
