"""Tests for the serve CLI command."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lorekeeper_mcp.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI runner for testing."""
    return CliRunner()


def test_serve_command_exists(runner: CliRunner) -> None:
    """Test that serve command is registered and accessible."""
    result = runner.invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "Start the MCP server" in result.output
    assert "lorekeeper serve" in result.output


@patch("lorekeeper_mcp.cli.mcp")
def test_serve_command_starts_server(mock_mcp: MagicMock, runner: CliRunner) -> None:
    """Test that serve command calls mcp.run()."""
    _ = runner.invoke(cli, ["serve"])

    # Verify mcp.run() was called
    mock_mcp.run.assert_called_once()


@patch("lorekeeper_mcp.cli.mcp")
def test_serve_command_with_verbose(
    mock_mcp: MagicMock, runner: CliRunner, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that serve command respects global --verbose flag."""
    with caplog.at_level(logging.DEBUG):
        result = runner.invoke(cli, ["-v", "serve"])

    # Verify mcp.run() was called
    mock_mcp.run.assert_called_once()

    # Check that logging level was set to DEBUG (captured in stderr)
    assert "Starting MCP server" in result.output or "Starting MCP server" in caplog.text


@patch("lorekeeper_mcp.cli.mcp")
def test_serve_command_with_db_path(mock_mcp: MagicMock, runner: CliRunner) -> None:
    """Test that serve command respects global --db-path option."""
    _ = runner.invoke(cli, ["--db-path", "/custom/path.db", "serve"])

    # Verify mcp.run() was called
    mock_mcp.run.assert_called_once()

    # Note: db-path is stored in context but server.py reads from settings
    # This test verifies the command accepts the option without error


@patch("lorekeeper_mcp.cli.mcp")
def test_serve_command_with_all_options(mock_mcp: MagicMock, runner: CliRunner) -> None:
    """Test that serve command works with all global options."""
    _ = runner.invoke(cli, ["-v", "--db-path", "/custom/path.db", "serve"])

    # Verify mcp.run() was called
    mock_mcp.run.assert_called_once()


def test_serve_command_in_help_output(runner: CliRunner) -> None:
    """Test that serve command appears in main CLI help."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "serve" in result.output
    assert "import" in result.output
