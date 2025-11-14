"""Cache schema definitions for entity-based tables."""

from pathlib import Path

import aiosqlite

SCHEMA_VERSION = 1

ENTITY_TYPES = [
    "spells",
    "monsters",
    "weapons",
    "armor",
    "magicitems",
    "classes",
    "races",
    "backgrounds",
    "feats",
    "conditions",
    "rules",
    "rule_sections",
    "planes",
    "sections",
    # Task 1.6: Item-related
    "items",
    "itemsets",
    "itemcategories",
    # Task 1.7: Creatures
    "creatures",
    "creaturetypes",
    "creaturesets",
    # Task 1.8: Reference data
    "damagetypes",
    "languages",
    "alignments",
    "spellschools",
    "sizes",
    "itemrarities",
    "environments",
    "abilities",
    "ability_scores",
    "skills",
    # Task 1.9: Character options
    "species",
    # Task 1.10: Rules and metadata
    "rulesets",
    "documents",
    "licenses",
    "publishers",
    "gamesystems",
    # Task 1.11: Additional content
    "images",
    "weaponproperties",
    "services",
    # Task 1.12-1.15: D&D 5e API specific entities
    "subclasses",
    "subraces",
    "traits",
    "equipment",
    "features",
]

# Indexed fields per entity type for filtering
# Each field is a tuple of (field_name, field_type)
# Note: 'name' and 'slug' are always available for filtering as they're in the base schema
# Document field for ALL entity types (user-facing filter)
DOCUMENT_FIELD = ("document", "TEXT")

INDEXED_FIELDS = {
    "spells": [
        DOCUMENT_FIELD,
        ("level", "INTEGER"),
        ("school", "TEXT"),
        ("concentration", "BOOLEAN"),
        ("ritual", "BOOLEAN"),
    ],
    "monsters": [
        DOCUMENT_FIELD,
        ("challenge_rating", "REAL"),
        ("type", "TEXT"),
        ("size", "TEXT"),
    ],
    "weapons": [
        DOCUMENT_FIELD,
        ("category", "TEXT"),
        ("damage_type", "TEXT"),
    ],
    "armor": [
        DOCUMENT_FIELD,
        ("category", "TEXT"),
        ("armor_class", "INTEGER"),
    ],
    "magicitems": [
        DOCUMENT_FIELD,
        ("type", "TEXT"),
        ("rarity", "TEXT"),
        ("requires_attunement", "BOOLEAN"),
    ],
    "classes": [DOCUMENT_FIELD, ("hit_die", "INTEGER")],
    "races": [DOCUMENT_FIELD, ("size", "TEXT")],
    "backgrounds": [DOCUMENT_FIELD],
    "feats": [DOCUMENT_FIELD],
    "conditions": [DOCUMENT_FIELD],
    "rules": [DOCUMENT_FIELD, ("parent", "TEXT")],
    "rule_sections": [DOCUMENT_FIELD, ("parent", "TEXT")],
    "planes": [DOCUMENT_FIELD],
    "sections": [DOCUMENT_FIELD, ("parent", "TEXT")],
    # Task 1.6: Item-related (no special indexed fields)
    "items": [DOCUMENT_FIELD],
    "itemsets": [DOCUMENT_FIELD],
    "itemcategories": [DOCUMENT_FIELD],
    # Task 1.7: Creatures
    "creatures": [
        DOCUMENT_FIELD,
        ("challenge_rating", "REAL"),
        ("type", "TEXT"),
        ("size", "TEXT"),
    ],
    "creaturetypes": [DOCUMENT_FIELD],
    "creaturesets": [DOCUMENT_FIELD],
    # Task 1.8: Reference data (no special indexed fields)
    "damagetypes": [DOCUMENT_FIELD],
    "languages": [DOCUMENT_FIELD],
    "alignments": [DOCUMENT_FIELD],
    "spellschools": [DOCUMENT_FIELD],
    "sizes": [DOCUMENT_FIELD],
    "itemrarities": [DOCUMENT_FIELD],
    "environments": [DOCUMENT_FIELD],
    "abilities": [DOCUMENT_FIELD],
    "ability_scores": [DOCUMENT_FIELD],
    "skills": [DOCUMENT_FIELD],
    # Task 1.9: Character options
    "species": [DOCUMENT_FIELD],
    # Task 1.10: Rules and metadata
    "rulesets": [DOCUMENT_FIELD],
    "documents": [DOCUMENT_FIELD],
    "licenses": [DOCUMENT_FIELD],
    "publishers": [DOCUMENT_FIELD],
    "gamesystems": [DOCUMENT_FIELD],
    # Task 1.11: Additional content
    "images": [DOCUMENT_FIELD],
    "weaponproperties": [DOCUMENT_FIELD],
    "services": [DOCUMENT_FIELD],
    # Task 1.12-1.15: D&D 5e API specific entities
    "subclasses": [DOCUMENT_FIELD],
    "subraces": [DOCUMENT_FIELD],
    "traits": [DOCUMENT_FIELD],
    "equipment": [DOCUMENT_FIELD],
    "features": [DOCUMENT_FIELD],
}


def get_table_name(entity_type: str) -> str:
    """Get table name for entity type."""
    return entity_type


def get_create_table_sql(entity_type: str) -> str:
    """Generate CREATE TABLE SQL for entity type."""
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Unknown entity type: {entity_type}")

    indexed_fields = INDEXED_FIELDS.get(entity_type, [])

    # Build indexed field definitions
    field_definitions = []
    for field_name, field_type in indexed_fields:
        field_definitions.append(f"    {field_name} {field_type}")

    fields_sql = ",\n".join(field_definitions)
    if fields_sql:
        fields_sql = ",\n" + fields_sql

    # Note: document field is now part of indexed_fields for all entity types
    return f"""CREATE TABLE IF NOT EXISTS {entity_type} (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    source_api TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL{fields_sql}
)"""


def get_index_sql(entity_type: str) -> list[str]:
    """Generate CREATE INDEX statements for entity type.

    Args:
        entity_type: Type of entity (spells, monsters, etc.)

    Returns:
        List of CREATE INDEX SQL statements
    """
    indexed_fields = INDEXED_FIELDS.get(entity_type, [])
    indexes = []

    for field_name, _field_type in indexed_fields:
        index_name = f"idx_{entity_type}_{field_name}"
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {entity_type}({field_name})"
        indexes.append(sql)

    return indexes


async def init_entity_cache(db_path: str) -> None:
    """Initialize entity cache tables and indexes.

    Creates all entity tables defined in ENTITY_TYPES with their indexed fields,
    enables WAL mode for concurrent access, and creates indexes for efficient filtering.

    Args:
        db_path: Path to SQLite database file
    """
    # Ensure parent directory exists
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode for concurrent access
        await db.execute("PRAGMA journal_mode=WAL")

        # Create all entity tables
        for entity_type in ENTITY_TYPES:
            table_sql = get_create_table_sql(entity_type)
            await db.execute(table_sql)

            # Create index on name field for all entity types (for filtering)
            await db.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{entity_type}_name ON {entity_type}(name)"
            )

            # Create index on document for document filtering
            await db.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{entity_type}_document ON {entity_type}(document)"
            )

            # Create indexes for entity-specific fields
            for index_sql in get_index_sql(entity_type):
                await db.execute(index_sql)

        await db.commit()
