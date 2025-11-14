"""Integration tests for import command."""

from pathlib import Path

from click.testing import CliRunner

from lorekeeper_mcp.cli import cli


def test_import_sample_file_end_to_end(tmp_path: Path) -> None:
    """Test complete import workflow with sample file."""
    # Setup test database path
    test_db = tmp_path / "test.db"

    # Get sample file path
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    sample_file = fixtures_dir / "sample.orcbrew"

    assert sample_file.exists(), f"Sample file not found: {sample_file}"

    # Run import command
    runner = CliRunner()
    result = runner.invoke(cli, ["--db-path", str(test_db), "import", str(sample_file)])

    # Should exit successfully
    assert result.exit_code == 0, f"Import failed: {result.output or result.exception}"


def test_import_dry_run() -> None:
    """Test import with --dry-run flag."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    sample_file = fixtures_dir / "sample.orcbrew"

    runner = CliRunner()
    result = runner.invoke(cli, ["import", str(sample_file), "--dry-run"])

    # Should exit successfully and not fail
    assert result.exit_code == 0


def test_import_nonexistent_file() -> None:
    """Test import with file that doesn't exist."""
    runner = CliRunner()
    result = runner.invoke(cli, ["import", "nonexistent.orcbrew"])

    assert result.exit_code != 0
