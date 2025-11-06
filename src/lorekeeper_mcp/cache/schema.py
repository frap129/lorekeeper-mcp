"""Cache schema definitions for entity-based tables."""

SCHEMA_VERSION = 1

ENTITY_TYPES = [
    "spells",
    "monsters",
    "weapons",
    "armor",
    "classes",
    "races",
    "backgrounds",
    "feats",
    "conditions",
    "rules",
    "rule_sections",
]

# Indexed fields per entity type for filtering
# Each field is a tuple of (field_name, field_type)
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
