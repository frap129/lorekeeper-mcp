"""Tests for entity type mapper."""

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
