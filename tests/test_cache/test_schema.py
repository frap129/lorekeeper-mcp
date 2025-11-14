"""Tests for cache schema definitions."""

import tempfile
from pathlib import Path

import aiosqlite
import pytest

from lorekeeper_mcp.cache.schema import (
    ENTITY_TYPES,
    INDEXED_FIELDS,
    SCHEMA_VERSION,
    get_create_table_sql,
    get_index_sql,
    get_table_name,
    init_entity_cache,
)


def test_schema_version_exists():
    """Schema version constant is defined."""
    assert isinstance(SCHEMA_VERSION, int)
    assert SCHEMA_VERSION > 0


def test_entity_types_defined():
    """All entity types are listed."""
    assert "spells" in ENTITY_TYPES
    assert "monsters" in ENTITY_TYPES
    assert "weapons" in ENTITY_TYPES
    assert "armor" in ENTITY_TYPES
    assert len(ENTITY_TYPES) >= 4  # At least these core types


def test_get_table_name():
    """Table names match entity types."""
    assert get_table_name("spells") == "spells"
    assert get_table_name("monsters") == "monsters"


def test_get_create_table_sql_for_spells():
    """Spells table has correct schema."""
    sql = get_create_table_sql("spells")
    assert "CREATE TABLE" in sql and "spells" in sql
    assert "slug TEXT PRIMARY KEY" in sql
    assert "name TEXT NOT NULL" in sql
    assert "data TEXT NOT NULL" in sql  # JSON blob
    assert "source_api TEXT NOT NULL" in sql
    assert "created_at REAL NOT NULL" in sql
    assert "updated_at REAL NOT NULL" in sql
    # Spell-specific indexed fields
    assert "level INTEGER" in sql
    assert "school TEXT" in sql
    assert "concentration BOOLEAN" in sql
    assert "ritual BOOLEAN" in sql


def test_get_create_table_sql_for_monsters():
    """Monsters table has correct schema with monster-specific fields."""
    sql = get_create_table_sql("monsters")
    assert "CREATE TABLE" in sql and "monsters" in sql
    assert "slug TEXT PRIMARY KEY" in sql
    # Monster-specific indexed fields
    assert "challenge_rating REAL" in sql
    assert "type TEXT" in sql
    assert "size TEXT" in sql


def test_get_create_table_sql_with_empty_indexed_fields():
    """Entity type with no indexed fields generates correct schema."""
    sql = get_create_table_sql("backgrounds")
    assert "CREATE TABLE" in sql and "backgrounds" in sql
    assert "slug TEXT PRIMARY KEY" in sql
    assert "name TEXT NOT NULL" in sql
    assert "data TEXT NOT NULL" in sql
    assert "source_api TEXT NOT NULL" in sql
    assert "created_at REAL NOT NULL" in sql
    assert "updated_at REAL NOT NULL" in sql
    # Should not have any indexed fields
    assert "background" not in sql.lower()[sql.lower().find("updated_at") :]


@pytest.mark.asyncio
async def test_init_entity_cache_creates_tables():
    """Initialize creates all entity tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        await init_entity_cache(str(db_path))

        # Verify database exists
        assert db_path.exists()

        # Verify tables created
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in await cursor.fetchall()}

            assert "spells" in tables
            assert "monsters" in tables
            assert "weapons" in tables
            assert "armor" in tables


@pytest.mark.asyncio
async def test_init_entity_cache_creates_indexes():
    """Initialize creates indexes on filtered fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        await init_entity_cache(str(db_path))

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = {row[0] for row in await cursor.fetchall()}

            # Check for spell indexes
            assert "idx_spells_level" in indexes
            assert "idx_spells_school" in indexes

            # Check for monster indexes
            assert "idx_monsters_challenge_rating" in indexes
            assert "idx_monsters_type" in indexes


@pytest.mark.asyncio
async def test_init_entity_cache_enables_wal_mode():
    """Initialize enables WAL mode for concurrent access."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        await init_entity_cache(str(db_path))

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("PRAGMA journal_mode")
            mode = (await cursor.fetchone())[0]
            assert mode.lower() == "wal"


def test_get_index_sql():
    """Index SQL generated correctly."""
    indexes = get_index_sql("spells")
    assert len(indexes) > 0
    assert any("idx_spells_level" in sql for sql in indexes)
    assert any("ON spells(level)" in sql for sql in indexes)


def test_document_field_in_schema():
    """Test that all entity tables include document column."""
    sql = get_create_table_sql("spells")

    # Document field should be present
    assert "document TEXT" in sql


def test_document_is_indexed():
    """Test that document is added to indexed fields for filtering."""
    # Document field should be in indexed fields for all entity types
    for entity_type in ["spells", "creatures", "weapons", "armor"]:
        indexed = INDEXED_FIELDS.get(entity_type, [])
        field_names = [name for name, _ in indexed]
        assert "document" in field_names


@pytest.mark.asyncio
async def test_document_index_created():
    """Test that document index is created during initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        await init_entity_cache(str(db_path))

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = {row[0] for row in await cursor.fetchall()}

            # Check for document indexes on core tables
            assert "idx_spells_document" in indexes
            assert "idx_creatures_document" in indexes
            assert "idx_weapons_document" in indexes
            assert "idx_armor_document" in indexes
