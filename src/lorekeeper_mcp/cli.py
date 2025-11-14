"""Command-line interface for LoreKeeper MCP."""

import logging
import sys

import click

from lorekeeper_mcp import __version__

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--db-path",
    type=click.Path(),
    envvar="LOREKEEPER_DB_PATH",
    help="Path to SQLite database file",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
@click.pass_context
def cli(ctx: click.Context, db_path: str | None, verbose: bool) -> None:
    """LoreKeeper MCP - D&D 5e content management and import tools."""
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store options in context for subcommands
    ctx.obj["db_path"] = db_path
    ctx.obj["verbose"] = verbose

    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def main() -> None:
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
