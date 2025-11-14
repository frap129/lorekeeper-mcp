"""Tests for CLI interface."""

from click.testing import CliRunner

from lorekeeper_mcp.cli import cli


def test_cli_help() -> None:
    """Test CLI --help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "LoreKeeper MCP" in result.output
    assert "Options:" in result.output


def test_cli_version() -> None:
    """Test CLI --version output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_import_command_missing_file() -> None:
    """Test import command with non-existent file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["import", "nonexistent.orcbrew"])

    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "not found" in result.output.lower()


def test_import_command_help() -> None:
    """Test import command --help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["import", "--help"])

    assert result.exit_code == 0
    assert "import" in result.output.lower()
    assert "--dry-run" in result.output
