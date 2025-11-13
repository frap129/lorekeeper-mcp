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
INDEXED_FIELDS = {
    "spells": [
        ("level", "INTEGER"),
        ("school", "TEXT"),
        ("concentration", "BOOLEAN"),
        ("ritual", "BOOLEAN"),
    ],
    "monsters": [
        ("challenge_rating", "REAL"),
        ("type", "TEXT"),
        ("size", "TEXT"),
    ],
    "weapons": [
        ("category", "TEXT"),
        ("damage_type", "TEXT"),
    ],
    "armor": [
        ("category", "TEXT"),
        ("armor_class", "INTEGER"),
    ],
    "magicitems": [
        ("type", "TEXT"),
        ("rarity", "TEXT"),
        ("requires_attunement", "BOOLEAN"),
    ],
    "classes": [
        ("hit_die", "INTEGER"),
    ],
    "races": [
        ("size", "TEXT"),
    ],
    "backgrounds": [],
    "feats": [],
    "conditions": [],
    "rules": [
        ("parent", "TEXT"),
    ],
    "rule_sections": [
        ("parent", "TEXT"),
    ],
    "planes": [],
    "sections": [
        ("parent", "TEXT"),
    ],
    # Task 1.6: Item-related (no special indexed fields)
    "items": [],
    "itemsets": [],
    "itemcategories": [],
    # Task 1.7: Creatures
    "creatures": [
        ("challenge_rating", "REAL"),
        ("type", "TEXT"),
        ("size", "TEXT"),
    ],
    "creaturetypes": [],
    "creaturesets": [],
    # Task 1.8: Reference data (no special indexed fields)
    "damagetypes": [],
    "languages": [],
    "alignments": [],
    "spellschools": [],
    "sizes": [],
    "itemrarities": [],
    "environments": [],
    "abilities": [],
    "ability_scores": [],
    "skills": [],
    # Task 1.9: Character options
    "species": [],
    # Task 1.10: Rules and metadata
    "rulesets": [],
    "documents": [],
    "licenses": [],
    "publishers": [],
    "gamesystems": [],
    # Task 1.11: Additional content
    "images": [],
    "weaponproperties": [],
    "services": [],
    # Task 1.12-1.15: D&D 5e API specific entities
    "subclasses": [],
    "subraces": [],
    "traits": [],
    "equipment": [],
    "features": [],
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

            # Create indexes for entity-specific fields
            for index_sql in get_index_sql(entity_type):
                await db.execute(index_sql)

        await db.commit()
