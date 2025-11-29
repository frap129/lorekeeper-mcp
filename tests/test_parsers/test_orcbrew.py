"""Tests for OrcBrew parser."""

import json
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


def test_parse_edn_file_with_nan_tokens(tmp_path: Path) -> None:
    """Test parsing EDN file containing unsupported NaN tokens.

    OrcBrew MegaPak files can contain values like ``##NaN`` for fields such as
    stealth. The underlying ``edn_format`` library does not support these
    tokens, so the parser should sanitize them to ``nil`` (Python ``None``)
    before parsing.
    """
    test_file = tmp_path / "nan_tokens.orcbrew"
    test_file.write_text(
        '{"Test Book" {:orcpub.dnd.e5/monsters {:weird '
        '{:key :weird :name "Weird" :challenge ##NaN, :stealth ##NaN}}}}'
    )

    parser = OrcBrewParser()
    result = parser.parse_file(test_file)

    assert result["Test Book"]["orcpub.dnd.e5/monsters"]["weird"]["challenge"] is None
    assert result["Test Book"]["orcpub.dnd.e5/monsters"]["weird"]["stealth"] is None


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


def test_parse_edn_file_with_utf8_bom(tmp_path: Path) -> None:
    """Test parsing EDN file with UTF-8 BOM (Byte Order Mark).

    Some text editors and Windows tools add a BOM at the start of UTF-8 files.
    The parser should handle this transparently.
    """
    test_file = tmp_path / "test_bom.orcbrew"
    # Write with BOM: \ufeff is the UTF-8 BOM character
    content = '{"Test Book" {:orcpub.dnd.e5/spells {:fireball {:key :fireball :name "Fireball"}}}}'
    with test_file.open("w", encoding="utf-8-sig") as f:
        f.write(content)

    parser = OrcBrewParser()
    result = parser.parse_file(test_file)

    assert result is not None
    assert isinstance(result, dict)
    assert "Test Book" in result


def test_parse_edn_file_with_arrays(tmp_path: Path) -> None:
    """Test parsing EDN file containing arrays (lists).

    EDN arrays are parsed as edn_format.ImmutableList objects. The parser
    should convert these to Python lists so that downstream code can process
    them correctly.
    """
    test_file = tmp_path / "arrays.orcbrew"
    # EDN uses [] for vectors (arrays/lists)
    test_file.write_text(
        '{"Test Book" {:orcpub.dnd.e5/spells {:magic-missile '
        '{:key :magic-missile :name "Magic Missile" :components ["V" "S"]}}}}'
    )

    parser = OrcBrewParser()
    result = parser.parse_file(test_file)

    components = result["Test Book"]["orcpub.dnd.e5/spells"]["magic-missile"]["components"]
    assert isinstance(components, list), f"Expected list, got {type(components).__name__}"
    assert components == ["V", "S"]


def test_parse_edn_file_with_arrays_is_json_serializable(tmp_path: Path) -> None:
    """Test that parsed EDN with arrays can be JSON serialized.

    This is critical because entities are stored in the cache as JSON.
    edn_format.ImmutableList objects fail JSON serialization with:
    "Object of type ImmutableList is not JSON serializable"
    """
    test_file = tmp_path / "arrays_json.orcbrew"
    test_file.write_text(
        '{"Test Book" {:orcpub.dnd.e5/spells {:fireball '
        '{:key :fireball :name "Fireball" :damage-types ["fire"] '
        ':classes ["wizard" "sorcerer"]}}}}'
    )

    parser = OrcBrewParser()
    result = parser.parse_file(test_file)

    # This will raise TypeError if ImmutableList was not converted
    json_str = json.dumps(result)
    assert '"damage-types": ["fire"]' in json_str
    assert '"classes": ["wizard", "sorcerer"]' in json_str


def test_parse_edn_file_with_sets(tmp_path: Path) -> None:
    """Test parsing EDN file containing sets.

    EDN sets are parsed as frozenset objects. The parser should convert
    these to Python lists so they can be JSON serialized.
    """
    test_file = tmp_path / "sets.orcbrew"
    # EDN uses #{} for sets
    test_file.write_text(
        '{"Test Book" {:orcpub.dnd.e5/spells {:fireball '
        '{:key :fireball :name "Fireball" :tags #{"fire" "damage"}}}}}'
    )

    parser = OrcBrewParser()
    result = parser.parse_file(test_file)

    tags = result["Test Book"]["orcpub.dnd.e5/spells"]["fireball"]["tags"]
    assert isinstance(tags, list), f"Expected list, got {type(tags).__name__}"
    assert set(tags) == {"fire", "damage"}


def test_parse_edn_file_with_sets_is_json_serializable(tmp_path: Path) -> None:
    """Test that parsed EDN with sets can be JSON serialized.

    frozenset objects fail JSON serialization with:
    "Object of type frozenset is not JSON serializable"
    """
    test_file = tmp_path / "sets_json.orcbrew"
    test_file.write_text(
        '{"Test Book" {:orcpub.dnd.e5/monsters {:goblin '
        '{:key :goblin :name "Goblin" :damage-immunities #{"poison" "fire"}}}}}'
    )

    parser = OrcBrewParser()
    result = parser.parse_file(test_file)

    # This will raise TypeError if frozenset was not converted
    json_str = json.dumps(result)
    assert "damage-immunities" in json_str
    # Check both values are present (order may vary since sets are unordered)
    assert "poison" in json_str
    assert "fire" in json_str
