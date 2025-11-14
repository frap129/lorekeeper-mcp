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
