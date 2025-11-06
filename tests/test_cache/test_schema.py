"""Tests for cache schema definitions."""

from lorekeeper_mcp.cache.schema import (
    ENTITY_TYPES,
    SCHEMA_VERSION,
    get_create_table_sql,
    get_table_name,
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
