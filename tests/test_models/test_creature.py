"""Tests for canonical Creature model."""

import warnings

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.models import Creature, Monster


class TestCreature:
    """Tests for Creature model."""

    def test_creature_minimal_fields(self) -> None:
        """Test Creature with minimal required fields."""
        creature = Creature(
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
        assert creature.name == "Goblin"
        assert creature.size == "Small"
        assert creature.challenge_rating == "1/4"

    def test_creature_normalizes_key_to_slug(self) -> None:
        """Test that key is normalized to slug."""
        creature = Creature(
            name="Goblin",
            key="goblin-key",
            size="Small",
            type="humanoid",
            alignment="neutral evil",
            armor_class=15,
            hit_points=7,
            hit_dice="2d6",
            challenge_rating="1/4",
        )
        assert creature.slug == "goblin-key"

    def test_creature_with_ability_scores(self) -> None:
        """Test Creature with ability scores."""
        creature = Creature(
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
        )
        assert creature.strength == 8
        assert creature.dexterity == 14

    def test_creature_invalid_ability_score_below_minimum(self) -> None:
        """Test that ability scores below 1 are rejected."""
        with pytest.raises(ValidationError):
            Creature(
                name="Invalid",
                slug="invalid",
                size="Medium",
                type="humanoid",
                alignment="neutral",
                armor_class=10,
                hit_points=10,
                hit_dice="2d6",
                challenge_rating="1",
                strength=0,
            )

    def test_creature_normalizes_challenge_to_challenge_rating(self) -> None:
        """Test that OrcBrew 'challenge' field is normalized to challenge_rating."""
        creature = Creature(
            name="Goblin",
            slug="goblin",
            size="Small",
            type="humanoid",
            alignment="neutral evil",
            armor_class=15,
            hit_points=7,
            hit_dice="2d6",
            challenge=0.25,  # OrcBrew format
        )
        assert creature.challenge_rating == "1/4"
        assert creature.challenge_rating_decimal == 0.25

    def test_creature_handles_integer_challenge(self) -> None:
        """Test that integer challenge is converted properly."""
        creature = Creature(
            name="Adult Red Dragon",
            slug="adult-red-dragon",
            size="Huge",
            type="dragon",
            alignment="chaotic evil",
            armor_class=19,
            hit_points=256,
            hit_dice="19d12+133",
            challenge=17,  # Integer challenge
        )
        assert creature.challenge_rating == "17"
        assert creature.challenge_rating_decimal == 17.0

    def test_monster_alias_with_deprecation_warning(self) -> None:
        """Test that Monster alias works but emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
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
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            assert "Creature" in str(w[0].message)
