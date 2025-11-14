"""Command-line interface for LoreKeeper MCP."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

import click

from lorekeeper_mcp import __version__
from lorekeeper_mcp.cache.db import bulk_cache_entities
from lorekeeper_mcp.cache.schema import init_entity_cache
from lorekeeper_mcp.config import settings
from lorekeeper_mcp.parsers.entity_mapper import map_entity_type, normalize_entity
from lorekeeper_mcp.parsers.orcbrew import OrcBrewParser

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


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dry-run",
    is_flag=True,
    help="Parse file but don't import to database",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing entities (default behavior with upsert)",
)
@click.pass_context
def import_cmd(ctx: click.Context, file: Path, dry_run: bool, force: bool) -> None:
    """Import D&D content from an OrcBrew (.orcbrew) file.

    Parses the EDN-formatted file and imports entities into the local cache.
    Supports spells, creatures, classes, equipment, and more.

    Example:
        lorekeeper import MegaPak_-_WotC_Books.orcbrew
    """
    db_path_str = str(ctx.obj.get("db_path") or settings.db_path)
    verbose = ctx.obj.get("verbose", False)

    logger.info(f"Starting import of '{file.name}'...")

    # Parse file
    try:
        parser = OrcBrewParser()
        parsed_data = parser.parse_file(file)
        entities_by_type = parser.extract_entities(parsed_data)
        logger.info(f"Found {len(entities_by_type)} entity types to import")
    except Exception as e:
        logger.error(f"Failed to parse file: {e}")
        raise click.ClickException(str(e)) from e

    if dry_run:
        logger.info("Dry run mode - no data will be imported")
        _print_import_summary(entities_by_type)
        return

    # Import entities by type
    asyncio.run(_import_entities(entities_by_type, db_path_str, verbose))

    logger.info("Import complete!")


def _print_import_summary(entities_by_type: dict[str, list[dict[str, Any]]]) -> None:
    """Print summary of entities to be imported."""
    for orcbrew_type, entities in entities_by_type.items():
        lorekeeper_type = map_entity_type(orcbrew_type)
        if lorekeeper_type:
            logger.info(f"  {lorekeeper_type}: {len(entities)} entities")
        else:
            logger.warning(f"  {orcbrew_type}: {len(entities)} entities (UNSUPPORTED - will skip)")


async def _import_entities(
    entities_by_type: dict[str, list[dict[str, Any]]],
    db_path: str,
    verbose: bool,
) -> None:
    """Import entities to database."""
    # Initialize database if needed
    await init_entity_cache(db_path)

    total_imported = 0
    total_skipped = 0

    for orcbrew_type, entities in entities_by_type.items():
        lorekeeper_type = map_entity_type(orcbrew_type)

        if not lorekeeper_type:
            logger.warning(
                f"Skipping {len(entities)} entities of unsupported type '{orcbrew_type}'"
            )
            total_skipped += len(entities)
            continue

        logger.info(f"Importing {lorekeeper_type}... ({len(entities)} entities)")

        # Normalize entities
        normalized_entities = []
        skipped_count = 0

        for entity in entities:
            try:
                normalized = normalize_entity(entity, orcbrew_type)
                normalized_entities.append(normalized)
            except ValueError as e:
                if verbose:
                    logger.warning(f"Skipping entity: {e}")
                skipped_count += 1

        # Bulk insert
        try:
            imported_count = await bulk_cache_entities(
                normalized_entities,
                lorekeeper_type,
                db_path=db_path,
                source_api="orcbrew",
            )
            logger.info(f"✓ Imported {imported_count} {lorekeeper_type}")
            if skipped_count > 0:
                logger.warning(f"  Skipped {skipped_count} entities due to missing required fields")

            total_imported += imported_count
            total_skipped += skipped_count
        except Exception as e:
            logger.error(f"Failed to import {lorekeeper_type}: {e}")
            raise

    logger.info(f"Total: {total_imported} imported, {total_skipped} skipped")


# Register import command with alternate name to avoid Python keyword
cli.add_command(import_cmd, name="import")


def main() -> None:
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
