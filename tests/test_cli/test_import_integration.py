"""Integration tests for import command."""

import asyncio
from pathlib import Path

import pytest
from click.testing import CliRunner

from lorekeeper_mcp.cache.db import get_cached_entity, query_cached_entities
from lorekeeper_mcp.cli import cli


def test_import_sample_file_end_to_end(tmp_path: Path, monkeypatch, caplog) -> None:
    """Test complete import workflow with sample file.

    Verifies:
    - Successful import execution
    - Database initialization and entity storage
    - Specific spell fields (name, level, school)
    - Specific creature fields (name, type, challenge_rating)
    """
    import asyncio

    # Setup test database
    test_db = tmp_path / "test.db"

    # Patch settings to use the test database
    from lorekeeper_mcp.config import settings

    monkeypatch.setattr(settings, "db_path", str(test_db))

    # Get sample file path
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    sample_file = fixtures_dir / "sample.orcbrew"

    assert sample_file.exists(), f"Sample file not found: {sample_file}"

    # Run import command
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--db-path", str(test_db), "import", str(sample_file)],
    )

    assert result.exit_code == 0, f"Import failed: {result.output or result.exception}"

    # Verify database was populated by querying entities
    # Use asyncio.run for the queries since we're in a sync context
    spells = asyncio.run(query_cached_entities("spells", db_path=str(test_db)))
    assert len(spells) == 2, f"Expected 2 spells, got {len(spells)}"

    # Verify specific spell fields
    magic_missile = asyncio.run(get_cached_entity("spells", "magic-missile", db_path=str(test_db)))
    assert magic_missile is not None, "Magic Missile spell not found"
    assert magic_missile["name"] == "Magic Missile"
    assert magic_missile["level"] == 1
    assert magic_missile["school"] == "Evocation"

    fireball = asyncio.run(get_cached_entity("spells", "fireball", db_path=str(test_db)))
    assert fireball is not None, "Fireball spell not found"
    assert fireball["name"] == "Fireball"
    assert fireball["level"] == 3
    assert fireball["school"] == "Evocation"

    # Verify creatures were imported (note: monsters → creatures)
    creatures = asyncio.run(query_cached_entities("creatures", db_path=str(test_db)))
    assert len(creatures) == 2, f"Expected 2 creatures, got {len(creatures)}"

    # Verify specific creature fields
    goblin = asyncio.run(get_cached_entity("creatures", "goblin", db_path=str(test_db)))
    assert goblin is not None, "Goblin creature not found"
    assert goblin["name"] == "Goblin"
    assert goblin["type"] == "humanoid"
    assert goblin["challenge_rating"] == 0.25

    dragon = asyncio.run(get_cached_entity("creatures", "dragon-red-adult", db_path=str(test_db)))
    assert dragon is not None, "Adult Red Dragon creature not found"
    assert dragon["name"] == "Adult Red Dragon"
    assert dragon["type"] == "dragon"
    assert dragon["challenge_rating"] == 17


def test_import_dry_run(caplog) -> None:
    """Test import with --dry-run flag.

    Verifies:
    - Dry run completes successfully without importing
    - Output contains entity count information
    """
    import logging

    caplog.set_level(logging.INFO)

    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    sample_file = fixtures_dir / "sample.orcbrew"

    runner = CliRunner()
    result = runner.invoke(cli, ["import", str(sample_file), "--dry-run"])

    assert result.exit_code == 0, f"Dry run failed: {result.output or result.exception}"

    # Check captured logs
    log_output = caplog.text.lower()
    assert (
        "dry run mode" in log_output
    ), f"Expected 'dry run mode' in logs. caplog: {caplog.text}, output: {result.output}"
    # Verify output contains entity type information
    assert (
        "spells:" in log_output or "creatures:" in log_output
    ), f"Expected entity counts in logs. caplog: {caplog.text}"


def test_import_nonexistent_file() -> None:
    """Test import with file that doesn't exist.

    Verifies:
    - Command fails with non-zero exit code
    - Error message indicates file not found
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["import", "nonexistent.orcbrew"])

    assert result.exit_code != 0, "Expected import to fail for nonexistent file"
    # Verify error output contains relevant information
    output_lower = (result.output or "").lower()
    assert (
        "does not exist" in output_lower or "not found" in output_lower or "error" in output_lower
    ), f"Expected error message in output. output: {result.output}"


@pytest.mark.live
@pytest.mark.slow
def test_import_megapak_file(tmp_path: Path, monkeypatch) -> None:
    """Test importing the full MegaPak file (live test)."""
    megapak_file = Path("MegaPak_-_WotC_Books.orcbrew")

    if not megapak_file.exists():
        pytest.skip("MegaPak file not found")

    from lorekeeper_mcp.cache.db import init_db
    from lorekeeper_mcp.config import settings

    # Setup test database
    test_db = tmp_path / "megapak_test.db"
    monkeypatch.setattr(settings, "db_path", str(test_db))
    asyncio.run(init_db())

    # Run import
    runner = CliRunner()
    result = runner.invoke(cli, ["--db-path", str(test_db), "-v", "import", str(megapak_file)])

    assert result.exit_code == 0, f"Import failed: {result.output or result.exception}"
    assert "Import complete!" in result.output

    # Verify counts
    spells = asyncio.run(query_cached_entities("spells", db_path=str(test_db)))
    creatures = asyncio.run(query_cached_entities("creatures", db_path=str(test_db)))

    # MegaPak should have hundreds of entities
    assert len(spells) > 100, f"Expected > 100 spells, got {len(spells)}"
    assert len(creatures) > 50, f"Expected > 50 creatures, got {len(creatures)}"
