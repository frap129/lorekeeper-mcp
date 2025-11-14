"""Tests for entity type mapper."""

import pytest

from lorekeeper_mcp.parsers.entity_mapper import (
    map_entity_type,
    normalize_entity,
)


def test_map_known_entity_types() -> None:
    """Test mapping known OrcBrew entity types to LoreKeeper types."""
    assert map_entity_type("orcpub.dnd.e5/spells") == "spells"
    assert map_entity_type("orcpub.dnd.e5/monsters") == "creatures"
    assert map_entity_type("orcpub.dnd.e5/classes") == "classes"
    assert map_entity_type("orcpub.dnd.e5/races") == "species"


def test_map_unknown_entity_type_returns_none() -> None:
    """Test unknown entity types return None."""
    assert map_entity_type("unknown.type") is None
    assert map_entity_type("orcpub.dnd.e5/unknown") is None


def test_normalize_spell_entity() -> None:
    """Test normalizing a spell entity."""
    orcbrew_spell = {
        "key": "fireball",
        "name": "Fireball",
        "level": 3,
        "school": "Evocation",
        "description": "A burst of flame",
        "_source_book": "Test Book",
    }

    result = normalize_entity(orcbrew_spell, "orcpub.dnd.e5/spells")

    assert result["slug"] == "fireball"
    assert result["name"] == "Fireball"
    assert result["source"] == "Test Book"
    assert result["source_api"] == "orcbrew"
    assert result["level"] == 3
    assert result["school"] == "Evocation"
    assert "data" in result
    assert result["data"]["description"] == "A burst of flame"


def test_normalize_entity_missing_key_and_name() -> None:
    """Test normalizing entity without key or name raises error."""
    invalid_entity = {"level": 3}

    with pytest.raises(ValueError, match="missing both 'key' and 'name'"):
        normalize_entity(invalid_entity, "orcpub.dnd.e5/spells")


def test_normalize_entity_generates_slug_from_name() -> None:
    """Test slug generation when key is missing."""
    entity = {
        "name": "Magic Missile",
        "level": 1,
        "_source_book": "Test",
    }

    result = normalize_entity(entity, "orcpub.dnd.e5/spells")

    assert result["slug"] == "magic-missile"
    assert result["name"] == "Magic Missile"


def test_normalize_entity_uses_option_pack_as_source() -> None:
    """Test that option-pack field is used as source."""
    entity = {
        "key": "test",
        "name": "Test",
        "option-pack": "Player's Handbook",
        "_source_book": "Ignored",
    }

    result = normalize_entity(entity, "orcpub.dnd.e5/spells")

    assert result["source"] == "Player's Handbook"


def test_orcbrew_entity_includes_document() -> None:
    """Test that OrcBrew entities include book name as document."""
    entity = {
        "key": "test-spell",
        "name": "Test Spell",
        "_source_book": "Homebrew Grimoire",
        "level": 3,
        "school": "evocation",
    }

    normalized = normalize_entity(entity, "orcpub.dnd.e5/spells")

    assert normalized["document"] == "Homebrew Grimoire"


def test_orcbrew_entity_with_option_pack() -> None:
    """Test that option-pack overrides _source_book for document name."""
    entity = {
        "key": "test-spell",
        "name": "Test Spell",
        "_source_book": "Default",
        "option-pack": "Custom Pack",
        "level": 3,
    }

    normalized = normalize_entity(entity, "orcpub.dnd.e5/spells")

    assert normalized["document"] == "Custom Pack"
