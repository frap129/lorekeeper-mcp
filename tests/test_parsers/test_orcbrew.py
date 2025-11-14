"""Tests for OrcBrew parser."""

from pathlib import Path

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
