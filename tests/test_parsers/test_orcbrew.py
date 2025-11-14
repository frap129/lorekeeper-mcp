"""Tests for OrcBrew parser."""

from pathlib import Path

import pytest

from lorekeeper_mcp.parsers.orcbrew import OrcBrewParser


def test_parser_initialization() -> None:
    """Test OrcBrewParser can be instantiated."""
    parser = OrcBrewParser()
    assert parser is not None


def test_parse_simple_edn_file(tmp_path: Path) -> None:
    """Test parsing a simple valid EDN file."""
    # Create test EDN file
    test_file = tmp_path / "test.orcbrew"
    test_file.write_text(
        '{"Test Book" {:orcpub.dnd.e5/spells {:fireball {:key :fireball :name "Fireball"}}}}'
    )

    parser = OrcBrewParser()
    result = parser.parse_file(test_file)

    assert result is not None
    assert isinstance(result, dict)
    assert "Test Book" in result


def test_extract_entities_from_parsed_data() -> None:
    """Test extracting entities from parsed OrcBrew data."""
    parser = OrcBrewParser()

    # Simulated parsed data structure
    parsed_data = {
        "Test Book": {
            "orcpub.dnd.e5/spells": {
                "fireball": {
                    "key": "fireball",
                    "name": "Fireball",
                    "level": 3,
                    "school": "Evocation",
                }
            },
            "orcpub.dnd.e5/monsters": {
                "goblin": {
                    "key": "goblin",
                    "name": "Goblin",
                    "type": "humanoid",
                }
            },
        }
    }

    entities = parser.extract_entities(parsed_data)

    assert len(entities) == 2
    assert "orcpub.dnd.e5/spells" in entities
    assert "orcpub.dnd.e5/monsters" in entities
    assert len(entities["orcpub.dnd.e5/spells"]) == 1
    assert entities["orcpub.dnd.e5/spells"][0]["name"] == "Fireball"


def test_parse_nonexistent_file() -> None:
    """Test parsing a file that doesn't exist."""
    parser = OrcBrewParser()

    with pytest.raises(FileNotFoundError):
        parser.parse_file(Path("/nonexistent/file.orcbrew"))


def test_parse_invalid_edn(tmp_path: Path) -> None:
    """Test parsing invalid EDN syntax."""
    test_file = tmp_path / "invalid.orcbrew"
    test_file.write_text("{invalid edn syntax")

    parser = OrcBrewParser()

    with pytest.raises(ValueError, match="Failed to parse EDN"):
        parser.parse_file(test_file)


def test_extract_entities_with_empty_data() -> None:
    """Test extracting entities from empty data."""
    parser = OrcBrewParser()

    result = parser.extract_entities({})

    assert result == {}


def test_extract_entities_skips_invalid_structures() -> None:
    """Test that invalid data structures are skipped with warnings."""
    parser = OrcBrewParser()

    invalid_data = {
        "Book1": "not-a-dict",  # Should be skipped
        "Book2": {
            "orcpub.dnd.e5/spells": "not-a-dict",  # Should be skipped
        },
    }

    result = parser.extract_entities(invalid_data)

    assert len(result) == 0
