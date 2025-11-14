# Document Tracking and Filtering Implementation Plan

**Goal:** Add document name tracking to all cached entities and enable filtering by document name across repositories and tools.

**Architecture:** Extend cache schema with a single `document` column for the document name, update API client normalization to populate document names from APIs, modify repositories to support document filtering, and expose document filters through MCP tools. The `source_api` field remains for internal tracking only.

**Tech Stack:** SQLite (cache), aiosqlite (async DB), Pydantic (models), Python Protocol (abstraction)

---

## Task 1: Add Document Column to Cache Schema

**Files:**
- Modify: `src/lorekeeper_mcp/cache/schema.py:1-237`
- Test: `tests/test_cache/test_schema.py`

**Step 1: Write failing test for document field in schema**

```python
# tests/test_cache/test_schema.py
import pytest
from lorekeeper_mcp.cache.schema import get_create_table_sql, INDEXED_FIELDS

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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_schema.py::test_document_field_in_schema -v`
Expected: FAIL with "AssertionError: assert 'document TEXT' in [SQL without document field]"

**Step 3: Add document field to base schema**

```python
# src/lorekeeper_mcp/cache/schema.py
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

    # Add document field to base schema
    return f"""CREATE TABLE IF NOT EXISTS {entity_type} (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    source_api TEXT NOT NULL,
    document TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL{fields_sql}
)"""
```

**Step 4: Add document to all entity indexed fields**

```python
# src/lorekeeper_mcp/cache/schema.py
# After ENTITY_TYPES definition, add document field to INDEXED_FIELDS

# Document field for ALL entity types (user-facing filter)
DOCUMENT_FIELD = ("document", "TEXT")

# Update INDEXED_FIELDS to include document field for all types
for entity_type in ENTITY_TYPES:
    if entity_type not in INDEXED_FIELDS:
        INDEXED_FIELDS[entity_type] = []
    # Prepend document field to each entity type's indexed fields
    INDEXED_FIELDS[entity_type] = [DOCUMENT_FIELD] + INDEXED_FIELDS[entity_type]
```

**Step 5: Update index creation to include document index**

```python
# src/lorekeeper_mcp/cache/schema.py
async def init_entity_cache(db_path: str) -> None:
    """Initialize entity cache tables and indexes."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")

        for entity_type in ENTITY_TYPES:
            table_sql = get_create_table_sql(entity_type)
            await db.execute(table_sql)

            # Create index on name field
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
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_schema.py::test_document_field_in_schema -v`
Expected: PASS

**Step 7: Run all cache schema tests**

Run: `uv run pytest tests/test_cache/test_schema.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/cache/schema.py tests/test_cache/test_schema.py
git commit -m "feat(cache): add document field to entity cache schema"
```

---

## Task 2: Update Cache DB Layer for Document Field

**Files:**
- Test: `tests/test_cache/test_db.py`

**Step 1: Write failing test for storing document name**

```python
# tests/test_cache/test_db.py
import pytest
from lorekeeper_mcp.cache.db import bulk_cache_entities, query_cached_entities, get_cached_entity

@pytest.mark.asyncio
async def test_cache_entity_with_document(tmp_path):
    """Test that entities with document name are stored correctly."""
    from lorekeeper_mcp.cache.schema import init_entity_cache

    db_path = str(tmp_path / "test.db")
    await init_entity_cache(db_path)

    spell = {
        "slug": "fireball",
        "name": "Fireball",
        "level": 3,
        "school": "evocation",
        "document": "System Reference Document 5.1",
    }

    count = await bulk_cache_entities([spell], "spells", db_path=db_path)
    assert count == 1

    # Verify document is preserved
    cached = await get_cached_entity("spells", "fireball", db_path=db_path)
    assert cached is not None
    assert cached["document"] == "System Reference Document 5.1"


@pytest.mark.asyncio
async def test_query_entities_by_document(tmp_path):
    """Test filtering entities by document name."""
    from lorekeeper_mcp.cache.schema import init_entity_cache

    db_path = str(tmp_path / "test.db")
    await init_entity_cache(db_path)

    spells = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "level": 3,
            "document": "System Reference Document 5.1",
        },
        {
            "slug": "homebrew-spell",
            "name": "Homebrew Spell",
            "level": 3,
            "document": "Homebrew Grimoire",
        },
    ]

    await bulk_cache_entities(spells, "spells", db_path=db_path)

    # Filter by document
    srd_spells = await query_cached_entities("spells", db_path=db_path, document="System Reference Document 5.1")
    assert len(srd_spells) == 1
    assert srd_spells[0]["slug"] == "fireball"

    homebrew_spells = await query_cached_entities("spells", db_path=db_path, document="Homebrew Grimoire")
    assert len(homebrew_spells) == 1
    assert homebrew_spells[0]["slug"] == "homebrew-spell"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_cache_entity_with_document -v`
Expected: FAIL (document field not handled by bulk_cache_entities)

**Step 3: Verify bulk_cache_entities handles document field**

```python
# src/lorekeeper_mcp/cache/db.py
# No changes needed - bulk_cache_entities already extracts all indexed fields
# dynamically from INDEXED_FIELDS, including the newly added "document" field
# The function at lines 117-146 will automatically handle it
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_db.py::test_cache_entity_with_document -v`
Expected: PASS

**Step 5: Run test for document filtering**

Run: `uv run pytest tests/test_cache/test_db.py::test_query_entities_by_document -v`
Expected: PASS

**Step 6: Run all cache DB tests**

Run: `uv run pytest tests/test_cache/test_db.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add tests/test_cache/test_db.py
git commit -m "test(cache): add tests for document name storage and filtering"
```

---

## Task 3: Normalize Open5e V2 Document Names

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/open5e_v2.py:1-250`
- Modify: `src/lorekeeper_mcp/api_clients/models/spell.py`
- Modify: `src/lorekeeper_mcp/api_clients/models/monster.py`
- Modify: `src/lorekeeper_mcp/api_clients/models/weapon.py`
- Modify: `src/lorekeeper_mcp/api_clients/models/armor.py`
- Test: `tests/test_api_clients/test_open5e_v2.py`

**Step 1: Write failing test for document name extraction**

```python
# tests/test_api_clients/test_open5e_v2.py
import pytest
import respx
from httpx import Response
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

@pytest.mark.asyncio
@respx.mock
async def test_spell_includes_document_name():
    """Test that spells include document name from API."""
    mock_response = {
        "results": [
            {
                "slug": "fireball",
                "name": "Fireball",
                "level": 3,
                "school": {"key": "evocation", "name": "Evocation"},
                "document": {
                    "key": "srd-2014",
                    "name": "System Reference Document 5.1",
                    "publisher": "Wizards of the Coast",
                },
            }
        ]
    }

    respx.get("https://api.open5e.com/v2/spells/").mock(
        return_value=Response(200, json=mock_response)
    )

    client = Open5eV2Client()
    spells = await client.get_spells()

    assert len(spells) == 1
    spell_dict = spells[0].model_dump()

    # Verify document name is extracted
    assert spell_dict["document"] == "System Reference Document 5.1"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_spell_includes_document_name -v`
Expected: FAIL with KeyError or assertion failure on document field

**Step 3: Add document name extraction helper function**

```python
# src/lorekeeper_mcp/api_clients/open5e_v2.py (add after imports, around line 8)
def _extract_document_name(entity: dict[str, Any]) -> str | None:
    """Extract document name from Open5e v2 entity.

    Args:
        entity: Raw entity data from Open5e v2 API

    Returns:
        Document name or None if not available
    """
    if isinstance(entity.get("document"), dict):
        return entity["document"].get("name")
    return None
```

**Step 4: Update get_spells to extract document name**

```python
# src/lorekeeper_mcp/api_clients/open5e_v2.py (modify get_spells, around line 154-158)
async def get_spells(
    self,
    level: int | None = None,
    school: str | None = None,
    name: str | None = None,
    level_gte: int | None = None,
    level_lte: int | None = None,
    **kwargs: Any,
) -> list[Spell]:
    """Get spells from Open5e API v2."""
    params: dict[str, Any] = {}

    if level is not None:
        params["level"] = level

    if level_gte is not None:
        params["level__gte"] = level_gte
    if level_lte is not None:
        params["level__lte"] = level_lte

    if school:
        params["school__key"] = school.lower()

    if name:
        params["name__icontains"] = name

    params.update(kwargs)

    result = await self.make_request(
        "/spells/",
        params=params,
    )

    spell_dicts: list[dict[str, Any]] = (
        result if isinstance(result, list) else result.get("results", [])
    )

    # Extract document name for each spell
    for spell in spell_dicts:
        document_name = _extract_document_name(spell)
        if document_name:
            spell["document"] = document_name

    return [Spell.model_validate(spell) for spell in spell_dicts]
```

**Step 5: Update Spell model to include document field**

```python
# src/lorekeeper_mcp/api_clients/models/spell.py
from pydantic import BaseModel, Field

class Spell(BaseModel):
    """D&D 5e spell model."""

    slug: str
    name: str
    # ... existing fields ...

    # Document name (e.g., "System Reference Document 5.1", "Adventurer's Guide")
    document: str | None = None

    # ... rest of fields ...
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_spell_includes_document_name -v`
Expected: PASS

**Step 7: Apply document name extraction to creatures, weapons, and armor**

```python
# src/lorekeeper_mcp/api_clients/open5e_v2.py
# Update _transform_creature_response method (around line 90-103)
def _transform_creature_response(self, creature: dict[str, Any]) -> dict[str, Any] | None:
    """Transform Open5e v2 creature response to Monster model format."""
    if creature.get("hit_dice") is None:
        return None

    transformed = creature.copy()

    # ... existing transformations ...

    # Extract document name
    document_name = _extract_document_name(creature)
    if document_name:
        transformed["document"] = document_name

    return transformed

# Update get_weapons method (around line 200-202)
async def get_weapons(...) -> list[Weapon]:
    """Get weapons from Open5e API v2."""
    # ... existing code ...

    weapon_dicts: list[dict[str, Any]] = (
        result if isinstance(result, list) else result.get("results", [])
    )

    # Extract document name
    for weapon in weapon_dicts:
        document_name = _extract_document_name(weapon)
        if document_name:
            weapon["document"] = document_name

    return [Weapon.model_validate(weapon) for weapon in weapon_dicts]

# Update get_armor method (around line 244-246)
async def get_armor(...) -> list[Armor]:
    """Get armor from Open5e API v2."""
    # ... existing code ...

    armor_dicts: list[dict[str, Any]] = (
        result if isinstance(result, list) else result.get("results", [])
    )

    # Extract document name
    for armor_item in armor_dicts:
        document_name = _extract_document_name(armor_item)
        if document_name:
            armor_item["document"] = document_name

    return [Armor.model_validate(armor) for armor_dicts in armor_dicts]
```

**Step 8: Update Monster, Weapon, and Armor models**

```python
# src/lorekeeper_mcp/api_clients/models/monster.py
class Monster(BaseModel):
    """D&D 5e monster/creature model."""
    # ... existing fields ...

    # Document name
    document: str | None = None

# src/lorekeeper_mcp/api_clients/models/weapon.py
class Weapon(BaseModel):
    """Weapon model."""
    # ... existing fields ...

    # Document name
    document: str | None = None

# src/lorekeeper_mcp/api_clients/models/armor.py
class Armor(BaseModel):
    """Armor model."""
    # ... existing fields ...

    # Document name
    document: str | None = None
```

**Step 9: Run all Open5e v2 tests**

Run: `uv run pytest tests/test_api_clients/test_open5e_v2.py -v`
Expected: All tests PASS

**Step 10: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/open5e_v2.py src/lorekeeper_mcp/api_clients/models/*.py tests/test_api_clients/test_open5e_v2.py
git commit -m "feat(api): extract document name from Open5e v2 entities"
```

---

## Task 4: Add SRD Document Name to D&D 5e API Entities

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Test: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write failing test for SRD document name**

```python
# tests/test_api_clients/test_dnd5e_api.py
import pytest
import respx
from httpx import Response
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient

@pytest.mark.asyncio
@respx.mock
async def test_spell_includes_srd_document_name():
    """Test that D&D 5e API spells include SRD document name."""
    mock_response = {
        "results": [
            {
                "index": "fireball",
                "name": "Fireball",
                "url": "/api/spells/fireball",
            }
        ]
    }

    respx.get("https://www.dnd5eapi.co/api/spells").mock(
        return_value=Response(200, json=mock_response)
    )

    client = Dnd5eApiClient()
    spells = await client.get_spells()

    assert len(spells) == 1
    spell_dict = spells[0].model_dump()

    # D&D 5e API content is all SRD - same as Open5e's SRD document
    assert spell_dict["document"] == "System Reference Document 5.1"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_clients/test_dnd5e_api.py::test_spell_includes_srd_document_name -v`
Expected: FAIL with KeyError or assertion failure

**Step 3: Add SRD document name constant**

```python
# src/lorekeeper_mcp/api_clients/dnd5e_api.py (add constant at top)
# All D&D 5e API content is from the SRD - same document as Open5e's srd-2014
SRD_DOCUMENT_NAME = "System Reference Document 5.1"
```

**Step 4: Update get_spells to add document name**

```python
# src/lorekeeper_mcp/api_clients/dnd5e_api.py
async def get_spells(self, **filters: Any) -> list[Spell]:
    """Fetch all spells from D&D 5e API."""
    data = await self.make_request("/spells")
    results = data.get("results", [])

    spells = []
    for spell_ref in results:
        spell_url = spell_ref.get("url", "")
        if spell_url:
            spell_data = await self.make_request(spell_url)
            # Add SRD document name
            spell_data["document"] = SRD_DOCUMENT_NAME
            try:
                spells.append(Spell.model_validate(spell_data))
            except Exception:
                continue

    return spells
```

**Step 5: Update other D&D 5e API methods (monsters, equipment, etc.)**

```python
# src/lorekeeper_mcp/api_clients/dnd5e_api.py
# Apply the same pattern to get_monsters, get_equipment, etc.

async def get_monsters(self, **filters: Any) -> list[Monster]:
    """Fetch all monsters from D&D 5e API."""
    data = await self.make_request("/monsters")
    results = data.get("results", [])

    monsters = []
    for monster_ref in results:
        monster_url = monster_ref.get("url", "")
        if monster_url:
            monster_data = await self.make_request(monster_url)
            # Add SRD document name
            monster_data["document"] = SRD_DOCUMENT_NAME
            try:
                monsters.append(Monster.model_validate(monster_data))
            except Exception:
                continue

    return monsters

# Repeat for other entity types that use D&D 5e API
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_api_clients/test_dnd5e_api.py::test_spell_includes_srd_document_name -v`
Expected: PASS

**Step 7: Run all D&D 5e API tests**

Run: `uv run pytest tests/test_api_clients/test_dnd5e_api.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/dnd5e_api.py tests/test_api_clients/test_dnd5e_api.py
git commit -m "feat(api): add SRD document name to D&D 5e API entities"
```

---

## Task 5: Extract OrcBrew Book Name as Document

**Files:**
- Modify: `src/lorekeeper_mcp/parsers/entity_mapper.py:40-87`
- Test: `tests/test_parsers/test_entity_mapper.py`

**Step 1: Write failing test for OrcBrew book as document**

```python
# tests/test_parsers/test_entity_mapper.py
import pytest
from lorekeeper_mcp.parsers.entity_mapper import normalize_entity

def test_orcbrew_entity_includes_document():
    """Test that OrcBrew entities include book name as document."""
    entity = {
        "key": "test-spell",
        "name": "Test Spell",
        "_source_book": "Homebrew Grimoire",
        "level": 3,
        "school": "evocation",
    }

    normalized = normalize_entity(entity, "orcpub.dnd.e5/spells")

    assert normalized["document"] == "Homebrew Grimoire"


def test_orcbrew_entity_with_option_pack():
    """Test that option-pack overrides _source_book for document name."""
    entity = {
        "key": "test-spell",
        "name": "Test Spell",
        "_source_book": "Default",
        "option-pack": "Custom Pack",
        "level": 3,
    }

    normalized = normalize_entity(entity, "orcpub.dnd.e5/spells")

    assert normalized["document"] == "Custom Pack"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_parsers/test_entity_mapper.py::test_orcbrew_entity_includes_document -v`
Expected: FAIL with KeyError on document

**Step 3: Update normalize_entity to include document field**

```python
# src/lorekeeper_mcp/parsers/entity_mapper.py (modify normalize_entity, around line 40-87)
def normalize_entity(
    entity: dict[str, Any],
    orcbrew_type: str,
) -> dict[str, Any]:
    """Normalize OrcBrew entity to LoreKeeper format."""
    # Extract or generate slug
    slug = entity.get("key")
    if not slug:
        name = entity.get("name", "")
        if not name:
            raise ValueError("Entity missing both 'key' and 'name' fields")
        slug = name.lower().replace(" ", "-").replace("'", "")

    # Extract name
    name = entity.get("name", slug.replace("-", " ").title())

    # Extract source book (for backward compatibility in data field)
    source = entity.get("_source_book", "Unknown")
    if "option-pack" in entity:
        source = entity["option-pack"]

    # Extract document name (book name is the document)
    document = entity.get("option-pack") or entity.get("_source_book", "Unknown")

    # Build normalized entity
    normalized: dict[str, Any] = {
        "slug": slug,
        "name": name,
        "source": source,  # Keep for backward compatibility in data
        "source_api": "orcbrew",
        "document": document,  # Book name as document
        "data": {k: v for k, v in entity.items() if not k.startswith("_")},
    }

    # Copy indexed fields to top level for filtering
    lorekeeper_type = map_entity_type(orcbrew_type)
    if lorekeeper_type:
        normalized.update(_extract_indexed_fields(entity, lorekeeper_type))

    return normalized
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_parsers/test_entity_mapper.py::test_orcbrew_entity_includes_document -v`
Expected: PASS

**Step 5: Run all entity mapper tests**

Run: `uv run pytest tests/test_parsers/test_entity_mapper.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/parsers/entity_mapper.py tests/test_parsers/test_entity_mapper.py
git commit -m "feat(parser): extract OrcBrew book name as document field"
```

---

## Task 6: Add Document Filtering to Repositories

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/spell.py:72-116`
- Modify: `src/lorekeeper_mcp/repositories/monster.py`
- Modify: `src/lorekeeper_mcp/repositories/equipment.py`
- Test: `tests/test_repositories/test_spell.py`

**Step 1: Write failing test for repository document filtering**

```python
# tests/test_repositories/test_spell.py
import pytest
from lorekeeper_mcp.repositories.spell import SpellRepository
from lorekeeper_mcp.api_clients.models.spell import Spell

@pytest.mark.asyncio
async def test_search_spells_by_document(mock_cache, mock_client):
    """Test filtering spells by document name."""
    # Setup mock cache with spells from different documents
    srd_spell = Spell(
        slug="fireball",
        name="Fireball",
        level=3,
        school="evocation",
        document="System Reference Document 5.1",
    )

    mock_cache.get_entities.return_value = [srd_spell.model_dump()]

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(document="System Reference Document 5.1")

    # Verify cache was called with document filter
    mock_cache.get_entities.assert_called_once()
    call_kwargs = mock_cache.get_entities.call_args[1]
    assert call_kwargs["document"] == "System Reference Document 5.1"

    assert len(results) == 1
    assert results[0].slug == "fireball"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repositories/test_spell.py::test_search_spells_by_document -v`
Expected: FAIL (document filter not handled)

**Step 3: Update SpellRepository.search to support document filter**

```python
# src/lorekeeper_mcp/repositories/spell.py (modify search method, around line 72-116)
async def search(self, **filters: Any) -> list[Spell]:
    """Search for spells with optional filters using cache-aside pattern.

    Args:
        **filters: Optional filters (level, school, document, etc.)

    Returns:
        List of Spell objects matching the filters
    """
    # Extract limit parameter (not a cache filter field)
    limit = filters.pop("limit", None)

    # Extract class_key as it's not a cacheable field
    class_key = filters.pop("class_key", None)

    # Document filter IS cacheable - keep it in filters
    # (it's now in INDEXED_FIELDS so cache supports it)

    # Try cache first with all valid cache filter fields (including document)
    cached = await self.cache.get_entities("spells", **filters)

    if cached:
        results = [Spell.model_validate(spell) for spell in cached]
        # Client-side filter by class_key if specified
        if class_key:
            results = [
                spell
                for spell in results
                if hasattr(spell, "classes")
                and class_key.lower() in [c.lower() for c in spell.classes]
            ]
        return results[:limit] if limit else results

    # Cache miss - fetch from API
    # Note: APIs don't support document filtering, so we filter client-side after fetch
    document = filters.pop("document", None)

    if class_key is not None:
        filters["class_key"] = class_key

    api_params = self._map_to_api_params(**filters)
    spells: list[Spell] = await self.client.get_spells(limit=limit, **api_params)

    # Apply document filter client-side if fetching from API
    if document:
        spells = [spell for spell in spells if spell.document == document]

    # Store in cache if we got results
    if spells:
        spell_dicts = [spell.model_dump() for spell in spells]
        await self.cache.store_entities(spell_dicts, "spells")

    return spells
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_repositories/test_spell.py::test_search_spells_by_document -v`
Expected: PASS

**Step 5: Apply same pattern to MonsterRepository**

```python
# src/lorekeeper_mcp/repositories/monster.py
# Apply the same document filtering logic to the search method
async def search(self, **filters: Any) -> list[Monster]:
    """Search for monsters with optional filters."""
    limit = filters.pop("limit", None)

    # Document filter is cacheable

    # Try cache first
    cached = await self.cache.get_entities("creatures", **filters)

    if cached:
        results = [Monster.model_validate(creature) for creature in cached]
        return results[:limit] if limit else results

    # Cache miss - fetch from API
    document = filters.pop("document", None)

    api_params = self._map_to_api_params(**filters)
    monsters: list[Monster] = await self.client.get_monsters(limit=limit, **api_params)

    # Apply document filter client-side if needed
    if document:
        monsters = [m for m in monsters if m.document == document]

    if monsters:
        monster_dicts = [m.model_dump() for m in monsters]
        await self.cache.store_entities(monster_dicts, "creatures")

    return monsters
```

**Step 6: Apply same pattern to EquipmentRepository**

```python
# src/lorekeeper_mcp/repositories/equipment.py
# Apply document filtering to weapon and armor search methods
```

**Step 7: Run all repository tests**

Run: `uv run pytest tests/test_repositories/ -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/repositories/*.py tests/test_repositories/*.py
git commit -m "feat(repository): add document filtering support to all repositories"
```

---

## Task 7: Add Document Filtering to MCP Tools

**Files:**
- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py:64-76`
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py`
- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py`
- Test: `tests/test_tools/test_spell_lookup.py`

**Step 1: Write failing test for tool document filtering**

```python
# tests/test_tools/test_spell_lookup.py
import pytest
from lorekeeper_mcp.tools.spell_lookup import lookup_spell, _repository_context
from lorekeeper_mcp.repositories.spell import SpellRepository
from lorekeeper_mcp.api_clients.models.spell import Spell
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_lookup_spell_with_document_filter():
    """Test looking up spells filtered by document name."""
    # Create mock repository
    mock_repo = MagicMock(spec=SpellRepository)
    srd_spell = Spell(
        slug="fireball",
        name="Fireball",
        level=3,
        school="evocation",
        document="System Reference Document 5.1",
    )
    mock_repo.search.return_value = [srd_spell]

    # Inject mock repository
    _repository_context["repository"] = mock_repo

    try:
        results = await lookup_spell(document="System Reference Document 5.1", level=3)

        # Verify repository was called with document filter
        mock_repo.search.assert_called_once()
        call_kwargs = mock_repo.search.call_args[1]
        assert call_kwargs["document"] == "System Reference Document 5.1"

        # Verify results include document
        assert len(results) == 1
        assert results[0]["document"] == "System Reference Document 5.1"
    finally:
        _repository_context.clear()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_lookup_spell_with_document_filter -v`
Expected: FAIL (document parameter not accepted)

**Step 3: Add document parameter to lookup_spell**

```python
# src/lorekeeper_mcp/tools/spell_lookup.py (modify function signature, around line 64-76)
async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    level_min: int | None = None,
    level_max: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    casting_time: str | None = None,
    damage_type: str | None = None,
    document: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e spells using the repository pattern.

    This tool provides comprehensive spell lookup functionality with support for filtering
    by multiple criteria including document/source filtering. Results include complete
    spell descriptions, components, damage, effects, and source document information.

    Args:
        name: Filter by spell name (partial match)
        level: Filter by exact spell level (0-9)
        level_min: Minimum spell level (inclusive)
        level_max: Maximum spell level (inclusive)
        school: Filter by magic school
        class_key: Filter by class that can cast the spell
        concentration: Filter by concentration requirement
        ritual: Filter by ritual casting capability
        casting_time: Filter by casting time
        damage_type: Filter by damage type
        document: Filter by document name (e.g., "System Reference Document 5.1", "Adventurer's Guide")
        limit: Maximum number of results to return

    Returns:
        List of spell dictionaries with complete data and document information
    """
    repository = _get_repository()

    # Build filter dictionary
    filters: dict[str, Any] = {"limit": limit}

    if name is not None:
        filters["name"] = name
    if level is not None:
        filters["level"] = level
    if level_min is not None:
        filters["level_min"] = level_min
    if level_max is not None:
        filters["level_max"] = level_max
    if school is not None:
        filters["school"] = school
    if class_key is not None:
        filters["class_key"] = class_key
    if concentration is not None:
        filters["concentration"] = concentration
    if ritual is not None:
        filters["ritual"] = ritual
    if casting_time is not None:
        filters["casting_time"] = casting_time
    if damage_type is not None:
        filters["damage_type"] = damage_type
    if document is not None:
        filters["document"] = document

    spells = await repository.search(**filters)
    return [spell.model_dump() for spell in spells]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_lookup_spell_with_document_filter -v`
Expected: PASS

**Step 5: Add document filter to creature_lookup**

```python
# src/lorekeeper_mcp/tools/creature_lookup.py
async def lookup_creature(
    name: str | None = None,
    challenge_rating: float | None = None,
    challenge_rating_min: float | None = None,
    challenge_rating_max: float | None = None,
    type: str | None = None,
    size: str | None = None,
    document: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e creatures/monsters.

    Args:
        [existing args]
        document: Filter by document name
        limit: Maximum results

    Returns:
        List of creature dictionaries with document information
    """
    repository = _get_repository()

    filters: dict[str, Any] = {"limit": limit}
    # ... existing filter building ...

    if document is not None:
        filters["document"] = document

    creatures = await repository.search(**filters)
    return [creature.model_dump() for creature in creatures]
```

**Step 6: Add document filter to equipment_lookup**

```python
# src/lorekeeper_mcp/tools/equipment_lookup.py
async def lookup_weapon(
    name: str | None = None,
    category: str | None = None,
    damage_type: str | None = None,
    document: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search and retrieve weapons with optional document filtering."""
    # ... add document to filters ...
```

**Step 7: Run all tool tests**

Run: `uv run pytest tests/test_tools/ -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/*.py tests/test_tools/*.py
git commit -m "feat(tools): add document filtering parameter to all MCP tools"
```

---

## Task 8: Add Integration Tests for Document Filtering

**Files:**
- Create: `tests/test_tools/test_document_filtering.py`

**Step 1: Write integration test for end-to-end document filtering**

```python
# tests/test_tools/test_document_filtering.py
"""Integration tests for document filtering across the stack."""
import pytest
from lorekeeper_mcp.cache.schema import init_entity_cache
from lorekeeper_mcp.cache.db import bulk_cache_entities
from lorekeeper_mcp.tools.spell_lookup import lookup_spell


@pytest.mark.asyncio
async def test_end_to_end_document_filtering(tmp_path):
    """Test document filtering from tool through repository to cache."""
    # Setup test database
    db_path = str(tmp_path / "test.db")
    await init_entity_cache(db_path)

    # Populate cache with spells from different documents
    spells = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "level": 3,
            "school": "evocation",
            "document": "System Reference Document 5.1",
        },
        {
            "slug": "custom-blast",
            "name": "Custom Blast",
            "level": 3,
            "school": "evocation",
            "document": "Homebrew Grimoire",
        },
        {
            "slug": "advanced-spell",
            "name": "Advanced Spell",
            "level": 3,
            "document": "Adventurer's Guide",
        },
    ]

    await bulk_cache_entities(spells, "spells", db_path=db_path)

    # Create repository with test cache
    from lorekeeper_mcp.cache.sqlite import SQLiteCache
    cache = SQLiteCache(db_path=db_path)
    from lorekeeper_mcp.repositories.spell import SpellRepository
    from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

    repo = SpellRepository(client=Open5eV2Client(), cache=cache)

    # Inject repository into tool context
    from lorekeeper_mcp.tools.spell_lookup import _repository_context
    _repository_context["repository"] = repo

    try:
        # Test 1: Filter by SRD document
        srd_results = await lookup_spell(document="System Reference Document 5.1")
        assert len(srd_results) == 1
        assert srd_results[0]["slug"] == "fireball"

        # Test 2: Filter by homebrew document
        homebrew_results = await lookup_spell(document="Homebrew Grimoire")
        assert len(homebrew_results) == 1
        assert homebrew_results[0]["slug"] == "custom-blast"

        # Test 3: Combine document filter with other filters
        level3_srd = await lookup_spell(level=3, document="System Reference Document 5.1")
        assert len(level3_srd) == 1
        assert level3_srd[0]["slug"] == "fireball"

    finally:
        _repository_context.clear()


@pytest.mark.asyncio
async def test_document_in_tool_responses(tmp_path):
    """Test that tool responses include document name."""
    db_path = str(tmp_path / "test.db")
    await init_entity_cache(db_path)

    spell = {
        "slug": "test-spell",
        "name": "Test Spell",
        "level": 2,
        "document": "Test Document",
    }

    await bulk_cache_entities([spell], "spells", db_path=db_path)

    # Setup and query
    from lorekeeper_mcp.cache.sqlite import SQLiteCache
    from lorekeeper_mcp.repositories.spell import SpellRepository
    from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell, _repository_context

    cache = SQLiteCache(db_path=db_path)
    repo = SpellRepository(client=Open5eV2Client(), cache=cache)
    _repository_context["repository"] = repo

    try:
        results = await lookup_spell(name="test")

        assert len(results) == 1
        result = results[0]

        # Verify document field is present
        assert result["document"] == "Test Document"

    finally:
        _repository_context.clear()
```

**Step 2: Run integration test**

Run: `uv run pytest tests/test_tools/test_document_filtering.py -v`
Expected: PASS (if all previous tasks completed correctly)

**Step 3: Commit**

```bash
git add tests/test_tools/test_document_filtering.py
git commit -m "test: add integration tests for document filtering"
```

---

## Task 9: Update Documentation

**Files:**
- Create: `docs/document-filtering.md`

**Step 1: Create document filtering documentation**

```markdown
# Document Filtering in LoreKeeper

## Overview

LoreKeeper tracks the source document for every cached entity, enabling filtering by document across all tools and repositories. This allows AI assistants to answer questions like "show me SRD-only spells" or "only use content from this homebrew book".

## Document Names

Every entity includes a `document` field containing the document name:

### Open5e v2
Documents from Open5e include the document name from the API (e.g., "System Reference Document 5.1", "Adventurer's Guide", "Tome of Beasts").

### D&D 5e API
All content from the D&D 5e API is SRD content, normalized to **"System Reference Document 5.1"** (the same document name as Open5e's SRD).

### OrcBrew
The top-level book name from the .orcbrew file becomes the document (e.g., "Homebrew Grimoire", "Test Content Pack").

## Using Document Filters

### In Tools

All lookup tools accept a `document` parameter:

```python
# Filter spells from the SRD
spells = await lookup_spell(document="System Reference Document 5.1", level=3)

# Filter creatures from a specific book
creatures = await lookup_creature(document="Adventurer's Guide")

# Filter weapons from homebrew
weapons = await lookup_weapon(document="Homebrew Grimoire", category="martial")
```

### In Repositories

Repositories support document filtering through the search method:

```python
repository = RepositoryFactory.create_spell_repository()
spells = await repository.search(document="System Reference Document 5.1", level=3)
```

### In Cache Queries

Direct cache queries support document filtering:

```python
from lorekeeper_mcp.cache.db import query_cached_entities

spells = await query_cached_entities(
    "spells",
    document="System Reference Document 5.1",
    level=3
)
```

## SRD Content from Multiple APIs

Both Open5e and the D&D 5e API provide SRD content. LoreKeeper normalizes both to use the same document name: **"System Reference Document 5.1"**.

This means filtering by `document="System Reference Document 5.1"` returns SRD content from **both** APIs (whichever LoreKeeper has cached). Users don't need to know which API provided the data.

## Performance

Document filtering uses indexed database queries for optimal performance:
- `document` has a database index on all entity tables
- Filters are applied at the database level (no client-side filtering when cache hits)
- Combines efficiently with other indexed fields (level, type, etc.)

## Backward Compatibility

Document filtering is fully backward compatible:
- The `document` parameter is optional on all tools
- Existing tool calls work unchanged
- The `source_api` field remains for internal tracking but is not exposed as a user-facing filter
```

**Step 2: Commit documentation**

```bash
git add docs/document-filtering.md
git commit -m "docs: add document filtering guide"
```

---

## Task 10: Run Full Test Suite and Fix Failures

**Files:**
- All test files

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: Identify any failing tests from schema/model changes

**Step 2: Fix any test failures one by one**

For each failure:
- Read the error message
- Identify the root cause
- Update the test or implementation as needed
- Re-run the specific test

Run: `uv run pytest tests/path/to/test_file.py::test_function -v`

**Step 3: Verify all tests pass**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit fixes**

```bash
git add tests/
git commit -m "fix(tests): update tests for document field changes"
```

---

## Task 11: Run Live Tests

**Files:**
- `tests/test_tools/test_live_mcp.py`

**Step 1: Run live MCP tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py -v -m live`
Expected: All live tests PASS

**Step 2: Verify document names in live responses**

Manually inspect test output to confirm:
- Entities from Open5e v2 include document names from the API
- Entities from D&D 5e API have "System Reference Document 5.1"
- All responses include the document field

**Step 3: Fix any live test failures**

If failures occur:
- Check API response format changes
- Verify normalization logic handles real API data
- Update transformation functions as needed

**Step 4: Commit any fixes**

```bash
git add src/ tests/
git commit -m "fix(api): handle real API data for document names"
```

---

## Task 12: Run Quality Checks

**Files:**
- All modified files

**Step 1: Run type checking**

Run: `just type-check`
Expected: No type errors

**Step 2: Run linting**

Run: `just lint`
Expected: No linting errors

**Step 3: Run formatting**

Run: `just format`
Expected: All files properly formatted

**Step 4: Run all quality checks**

Run: `just check`
Expected: All checks PASS

**Step 5: Commit formatting changes if any**

```bash
git add -u
git commit -m "style: apply formatting fixes"
```

---

## Summary

This plan implements document tracking and filtering with a minimal, correct design:

1. **Cache layer**: Added single `document TEXT` column (indexed for filtering)
2. **API clients**: Extract document names from Open5e v2, normalize D&D 5e API to "System Reference Document 5.1", extract OrcBrew book names
3. **Repositories**: Added document filtering support with cache-first queries
4. **Tools**: Exposed document filter as optional parameter on all MCP tools
5. **Tests**: Comprehensive unit and integration tests for all layers
6. **Documentation**: Complete guide for using document filters

**Key Design Decisions:**
- Single indexed `document TEXT` column stores the document name
- `source_api` remains for internal tracking only (not a user filter)
- Both Open5e and D&D 5e API use "System Reference Document 5.1" for SRD content
- Users filter by document name only - they don't care which API provided the data
- All changes are additive and backward compatible
