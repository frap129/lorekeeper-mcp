"""Integration tests for import command."""

import asyncio
import logging
from pathlib import Path

import pytest
from click.testing import CliRunner

from lorekeeper_mcp.cache import MilvusCache
from lorekeeper_mcp.cli import cli
from lorekeeper_mcp.config import settings


def test_import_sample_file_end_to_end(tmp_path: Path, monkeypatch, caplog) -> None:
    """Test complete import workflow with sample file.

    Verifies:
    - Successful import execution
    - Cache initialization and entity storage
    - Specific spell fields (name, level, school)
    - Specific creature fields (name, type, challenge_rating)
    """
    # Setup test Milvus database
    test_db = tmp_path / "test_milvus.db"

    # Patch settings to use the test Milvus database
    monkeypatch.setattr(settings, "cache_backend", "milvus")
    monkeypatch.setattr(settings, "milvus_db_path", test_db)

    # Get sample file path
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    sample_file = fixtures_dir / "sample.orcbrew"

    assert sample_file.exists(), f"Sample file not found: {sample_file}"

    # Run import command
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["import", str(sample_file)],
    )

    assert result.exit_code == 0, f"Import failed: {result.output or result.exception}"

    # Verify database was populated by querying entities using MilvusCache directly
    cache = MilvusCache(str(test_db))

    spells = asyncio.run(cache.get_entities("spells"))
    assert len(spells) == 2, f"Expected 2 spells, got {len(spells)}"

    # Verify specific spell fields
    magic_missiles = asyncio.run(cache.get_entities("spells", name="Magic Missile"))
    assert len(magic_missiles) == 1, "Magic Missile spell not found"
    magic_missile = magic_missiles[0]
    assert magic_missile["name"] == "Magic Missile"
    assert magic_missile["level"] == 1
    assert magic_missile["school"] == "Evocation"

    fireballs = asyncio.run(cache.get_entities("spells", name="Fireball"))
    assert len(fireballs) == 1, "Fireball spell not found"
    fireball = fireballs[0]
    assert fireball["name"] == "Fireball"
    assert fireball["level"] == 3
    assert fireball["school"] == "Evocation"

    # Verify creatures were imported (note: monsters → creatures)
    creatures = asyncio.run(cache.get_entities("creatures"))
    assert len(creatures) == 2, f"Expected 2 creatures, got {len(creatures)}"

    # Verify specific creature fields
    goblins = asyncio.run(cache.get_entities("creatures", name="Goblin"))
    assert len(goblins) == 1, "Goblin creature not found"
    goblin = goblins[0]
    assert goblin["name"] == "Goblin"
    assert goblin["type"] == "humanoid"
    # challenge_rating is now validated through OrcBrewCreature model which converts
    # numeric challenge to string format (e.g., 0.25 -> "1/4")
    assert goblin["challenge_rating"] == "1/4"

    dragons = asyncio.run(cache.get_entities("creatures", name="Adult Red Dragon"))
    assert len(dragons) == 1, "Adult Red Dragon creature not found"
    dragon = dragons[0]
    assert dragon["name"] == "Adult Red Dragon"
    assert dragon["type"] == "dragon"
    assert dragon["challenge_rating"] == "17"

    # Clean up
    cache.close()


def test_import_dry_run(caplog) -> None:
    """Test import with --dry-run flag.

    Verifies:
    - Dry run completes successfully without importing
    - Output contains entity count information
    """
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

    # Setup test Milvus database
    test_db = tmp_path / "megapak_milvus.db"
    monkeypatch.setattr(settings, "cache_backend", "milvus")
    monkeypatch.setattr(settings, "milvus_db_path", test_db)

    # Run import
    runner = CliRunner()
    result = runner.invoke(cli, ["-v", "import", str(megapak_file)])

    assert result.exit_code == 0, f"Import failed: {result.output or result.exception}"
    assert "Import complete!" in result.output

    # Verify counts using MilvusCache
    cache = MilvusCache(str(test_db))
    spells = asyncio.run(cache.get_entities("spells"))
    creatures = asyncio.run(cache.get_entities("creatures"))

    # MegaPak should have hundreds of entities
    assert len(spells) > 100, f"Expected > 100 spells, got {len(spells)}"
    assert len(creatures) > 50, f"Expected > 50 creatures, got {len(creatures)}"

    cache.close()
