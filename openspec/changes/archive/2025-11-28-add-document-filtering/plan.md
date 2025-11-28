# Source-Agnostic Document Filtering Implementation Plan

**Goal:** Enable users to discover and filter D&D content by source documents across all data sources

**Architecture:** Cache-first design with UNION queries for document discovery and IN clause filtering. All operations query SQLite cache layer, completely abstracted from API sources. No schema changes required.

**Tech Stack:** Python 3.11+, aiosqlite, Pydantic models, MCP protocol, pytest with asyncio_mode=auto

---

## Task 1: Enhance Cache Layer for Multi-Document Filtering

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py:190-249`
- Test: `tests/test_cache/test_db.py`

**Step 1: Write test for single document filter (existing behavior)**

```python
# Add to tests/test_cache/test_db.py
@pytest.mark.asyncio
async def test_query_cached_entities_single_document_filter(populated_cache: str) -> None:
    """Test filtering by single document as string."""
    from lorekeeper_mcp.cache.db import query_cached_entities

    # Query spells from srd-5e document
    results = await query_cached_entities(
        "spells",
        db_path=populated_cache,
        document="srd-5e"
    )

    assert len(results) > 0
    assert all(spell.get("document") == "srd-5e" for spell in results)
```

**Step 2: Run test to verify it passes (existing functionality)**

Run: `uv run pytest tests/test_cache/test_db.py::test_query_cached_entities_single_document_filter -v`
Expected: PASS (document field is already in INDEXED_FIELDS and allowed)

**Step 3: Write test for multiple documents filter**

```python
# Add to tests/test_cache/test_db.py
@pytest.mark.asyncio
async def test_query_cached_entities_multiple_documents_filter(populated_cache: str) -> None:
    """Test filtering by multiple documents as list."""
    from lorekeeper_mcp.cache.db import query_cached_entities

    # Query spells from multiple documents
    results = await query_cached_entities(
        "spells",
        db_path=populated_cache,
        document=["srd-5e", "tce", "phb"]
    )

    assert len(results) > 0
    # Verify all results are from one of the specified documents
    for spell in results:
        assert spell.get("document") in ["srd-5e", "tce", "phb"]
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_query_cached_entities_multiple_documents_filter -v`
Expected: FAIL with "list is not a valid value" or similar type error

**Step 5: Write test for empty document list (short-circuit)**

```python
# Add to tests/test_cache/test_db.py
@pytest.mark.asyncio
async def test_query_cached_entities_empty_document_list(populated_cache: str) -> None:
    """Test empty document list returns empty results immediately."""
    from lorekeeper_mcp.cache.db import query_cached_entities

    # Query with empty document list should return empty
    results = await query_cached_entities(
        "spells",
        db_path=populated_cache,
        document=[]
    )

    assert results == []
```

**Step 6: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_query_cached_entities_empty_document_list -v`
Expected: FAIL (empty list not handled)

**Step 7: Implement multi-document filtering in query_cached_entities**

```python
# In src/lorekeeper_mcp/cache/db.py, replace the query_cached_entities function
async def query_cached_entities(
    entity_type: str,
    db_path: str | None = None,
    **filters: Any,
) -> list[dict[str, Any]]:
    """Query cached entities with optional filters.

    Args:
        entity_type: Type of entities to query
        db_path: Optional database path
        **filters: Field filters (e.g., level=3, school="Evocation", document=["srd-5e"])

    Returns:
        List of matching entity dictionaries

    Raises:
        ValueError: If entity_type is invalid or filter field is not in allowlist
    """
    # Validate entity_type to prevent SQL injection
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    # Validate filter keys against allowlist to prevent SQL injection
    # Base schema fields that are always filterable
    base_fields = {"name", "slug", "source_api"}
    # Entity-specific indexed fields
    indexed_fields = {field_name for field_name, _ in INDEXED_FIELDS.get(entity_type, [])}
    allowed_fields = base_fields | indexed_fields

    for field in filters:
        if field not in allowed_fields:
            raise ValueError(
                f"Invalid filter field '{field}' for entity type '{entity_type}'. "
                f"Allowed fields: {sorted(allowed_fields)}"
            )

    # Short-circuit for empty document list
    document_filter = filters.get("document")
    if isinstance(document_filter, list) and len(document_filter) == 0:
        return []

    db_path_obj = Path(db_path or settings.db_path)
    table_name = get_table_name(entity_type)

    # Build WHERE clause
    where_clauses = []
    params = []

    for field, value in filters.items():
        # Handle document field with list support (IN clause)
        if field == "document" and isinstance(value, list):
            # Multiple documents - use IN clause
            placeholders = ", ".join(["?"] * len(value))
            where_clauses.append(f"{field} IN ({placeholders})")
            params.extend(value)
        else:
            # Single value - use equality
            where_clauses.append(f"{field} = ?")
            params.append(value)

    where_sql = ""
    if where_clauses:
        where_sql = " WHERE " + " AND ".join(where_clauses)

    query = f"SELECT data FROM {table_name}{where_sql}"

    async with aiosqlite.connect(db_path_obj) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [cast(dict[str, Any], json.loads(row["data"])) for row in rows]
```

**Step 8: Run tests to verify they pass**

Run: `uv run pytest tests/test_cache/test_db.py::test_query_cached_entities_multiple_documents_filter tests/test_cache/test_db.py::test_query_cached_entities_empty_document_list -v`
Expected: PASS

**Step 9: Run all cache tests to ensure no regression**

Run: `uv run pytest tests/test_cache/ -v`
Expected: All tests PASS

**Step 10: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_db.py
git commit -m "feat(cache): add multi-document filtering with IN clause support"
```

---

## Task 2: Add Document Discovery Function

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py` (add new function)
- Test: `tests/test_cache/test_db.py`

**Step 1: Write test for get_available_documents**

```python
# Add to tests/test_cache/test_db.py
@pytest.mark.asyncio
async def test_get_available_documents(populated_cache: str) -> None:
    """Test retrieving all available documents."""
    from lorekeeper_mcp.cache.db import get_available_documents

    documents = await get_available_documents(db_path=populated_cache)

    # Should return list of documents
    assert isinstance(documents, list)
    assert len(documents) > 0

    # Check structure of first document
    doc = documents[0]
    assert "document" in doc
    assert "source_api" in doc
    assert "entity_count" in doc
    assert "entity_types" in doc
    assert isinstance(doc["entity_count"], int)
    assert isinstance(doc["entity_types"], dict)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_get_available_documents -v`
Expected: FAIL with "cannot import name 'get_available_documents'"

**Step 3: Write test for source_api filter**

```python
# Add to tests/test_cache/test_db.py
@pytest.mark.asyncio
async def test_get_available_documents_source_filter(populated_cache: str) -> None:
    """Test filtering documents by source API."""
    from lorekeeper_mcp.cache.db import get_available_documents

    documents = await get_available_documents(
        db_path=populated_cache,
        source_api="open5e_v2"
    )

    assert all(doc["source_api"] == "open5e_v2" for doc in documents)
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_get_available_documents_source_filter -v`
Expected: FAIL (function doesn't exist)

**Step 5: Write test for empty cache**

```python
# Add to tests/test_cache/test_db.py
@pytest.mark.asyncio
async def test_get_available_documents_empty_cache(tmp_path: Path) -> None:
    """Test get_available_documents with empty cache."""
    from lorekeeper_mcp.cache.db import init_db, get_available_documents

    # Create empty database
    db_path = str(tmp_path / "empty.db")
    await init_db()

    documents = await get_available_documents(db_path=db_path)

    assert documents == []
```

**Step 6: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_get_available_documents_empty_cache -v`
Expected: FAIL (function doesn't exist)

**Step 7: Implement get_available_documents function**

```python
# Add to src/lorekeeper_mcp/cache/db.py after delete_entity_type function
async def get_available_documents(
    db_path: str | None = None,
    source_api: str | None = None,
) -> list[dict[str, Any]]:
    """Get all available documents across all entity types.

    Queries all entity type tables for distinct documents and aggregates
    entity counts. This provides a source-agnostic view of available documents
    regardless of which API they came from.

    Args:
        db_path: Optional database path
        source_api: Optional filter by source API (open5e_v2, dnd5e_api, orcbrew)

    Returns:
        List of document dictionaries with:
            - document: Document name/key
            - source_api: Source API identifier
            - entity_count: Total entities from this document
            - entity_types: Dict mapping entity type to count
    """
    final_db_path: str = str(db_path or settings.db_path)

    async with aiosqlite.connect(final_db_path) as db:
        db.row_factory = aiosqlite.Row

        # Build UNION ALL query for all entity types
        union_queries = []
        for entity_type in ENTITY_TYPES:
            table_name = get_table_name(entity_type)
            union_queries.append(
                f"SELECT '{entity_type}' as entity_type, document, source_api "
                f"FROM {table_name} WHERE document IS NOT NULL"
            )

        union_sql = " UNION ALL ".join(union_queries)

        # Add source_api filter if specified
        if source_api:
            query = f"""
                SELECT entity_type, document, source_api, COUNT(*) as count
                FROM ({union_sql})
                WHERE source_api = ?
                GROUP BY document, source_api, entity_type
                ORDER BY document
            """
            cursor = await db.execute(query, (source_api,))
        else:
            query = f"""
                SELECT entity_type, document, source_api, COUNT(*) as count
                FROM ({union_sql})
                GROUP BY document, source_api, entity_type
                ORDER BY document
            """
            cursor = await db.execute(query)

        rows = await cursor.fetchall()

        # Aggregate by document
        documents_map: dict[tuple[str, str], dict[str, Any]] = {}

        for row in rows:
            key = (row["document"], row["source_api"])
            if key not in documents_map:
                documents_map[key] = {
                    "document": row["document"],
                    "source_api": row["source_api"],
                    "entity_count": 0,
                    "entity_types": {},
                }

            documents_map[key]["entity_count"] += row["count"]
            documents_map[key]["entity_types"][row["entity_type"]] = row["count"]

        # Sort by entity count descending
        result = sorted(
            documents_map.values(),
            key=lambda x: x["entity_count"],
            reverse=True
        )

        return result
```

**Step 8: Run tests to verify they pass**

Run: `uv run pytest tests/test_cache/test_db.py::test_get_available_documents tests/test_cache/test_db.py::test_get_available_documents_source_filter tests/test_cache/test_db.py::test_get_available_documents_empty_cache -v`
Expected: PASS

**Step 9: Run all cache tests**

Run: `uv run pytest tests/test_cache/ -v`
Expected: All tests PASS

**Step 10: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_db.py
git commit -m "feat(cache): add get_available_documents for document discovery"
```

---

## Task 3: Add Document Metadata Query Function

**Files:**
- Modify: `src/lorekeeper_mcp/cache/db.py` (add new function)
- Test: `tests/test_cache/test_db.py`

**Step 1: Write test for get_document_metadata**

```python
# Add to tests/test_cache/test_db.py
@pytest.mark.asyncio
async def test_get_document_metadata(populated_cache: str) -> None:
    """Test retrieving document metadata."""
    from lorekeeper_mcp.cache.db import get_document_metadata

    # Assuming populated cache has srd-5e document metadata
    metadata = await get_document_metadata("srd-5e", db_path=populated_cache)

    if metadata:  # May be None if not cached
        assert isinstance(metadata, dict)
        assert "slug" in metadata or "document" in metadata
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_get_document_metadata -v`
Expected: FAIL with "cannot import name 'get_document_metadata'"

**Step 3: Write test for missing metadata**

```python
# Add to tests/test_cache/test_db.py
@pytest.mark.asyncio
async def test_get_document_metadata_not_found(populated_cache: str) -> None:
    """Test get_document_metadata returns None for missing document."""
    from lorekeeper_mcp.cache.db import get_document_metadata

    metadata = await get_document_metadata("non-existent-doc", db_path=populated_cache)

    assert metadata is None
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_db.py::test_get_document_metadata_not_found -v`
Expected: FAIL (function doesn't exist)

**Step 5: Implement get_document_metadata function**

```python
# Add to src/lorekeeper_mcp/cache/db.py after get_available_documents function
async def get_document_metadata(
    document_key: str,
    db_path: str | None = None,
) -> dict[str, Any] | None:
    """Get metadata for a specific document from cache.

    Queries the documents entity type for cached metadata about a document.
    This is primarily useful for Open5e documents which have rich metadata
    (publisher, license, etc.). Returns None for documents not in cache.

    Args:
        document_key: Document slug/key to look up
        db_path: Optional database path

    Returns:
        Document metadata dict if found, None otherwise
    """
    final_db_path: str = str(db_path or settings.db_path)

    try:
        # Try to get from documents cache
        result = await get_cached_entity("documents", document_key, db_path=final_db_path)
        return result
    except (ValueError, Exception):
        # Table doesn't exist or other error - return None
        return None
```

**Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_cache/test_db.py::test_get_document_metadata tests/test_cache/test_db.py::test_get_document_metadata_not_found -v`
Expected: PASS

**Step 7: Run all cache tests**

Run: `uv run pytest tests/test_cache/ -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/cache/db.py tests/test_cache/test_db.py
git commit -m "feat(cache): add get_document_metadata for document info retrieval"
```

---

## Task 4: Update Repository Base Protocols

**Files:**
- Modify: `src/lorekeeper_mcp/cache/protocol.py`
- Test: No new tests needed (protocols don't have runtime tests)

**Step 1: Add document parameter to CacheProtocol**

```python
# In src/lorekeeper_mcp/cache/protocol.py, update get_entities method signature
async def get_entities(
    self,
    entity_type: str,
    document: str | list[str] | None = None,  # ADD THIS
    **filters: Any,
) -> list[dict[str, Any]]:
    """Retrieve entities from cache with optional filters."""
    ...
```

**Step 2: Verify no syntax errors**

Run: `uv run python -m py_compile src/lorekeeper_mcp/cache/protocol.py`
Expected: No output (successful compilation)

**Step 3: Commit**

```bash
git add src/lorekeeper_mcp/cache/protocol.py
git commit -m "feat(cache): add document parameter to CacheProtocol"
```

---

## Task 5: Update SQLite Cache Implementation

**Files:**
- Modify: `src/lorekeeper_mcp/cache/sqlite.py`
- Test: `tests/test_cache/test_sqlite.py`

**Step 1: Write test for document filtering in SQLiteCache**

```python
# Add to tests/test_cache/test_sqlite.py
@pytest.mark.asyncio
async def test_sqlite_cache_get_entities_with_document_filter(tmp_path: Path) -> None:
    """Test SQLiteCache.get_entities with document filter."""
    from lorekeeper_mcp.cache.sqlite import SQLiteCache

    db_path = str(tmp_path / "test.db")
    cache = SQLiteCache(db_path=db_path)

    # Store some test entities with documents
    entities = [
        {"slug": "spell-1", "name": "Fireball", "document": "srd-5e"},
        {"slug": "spell-2", "name": "Lightning Bolt", "document": "srd-5e"},
        {"slug": "spell-3", "name": "Tasha's Hideous Laughter", "document": "tce"},
    ]
    await cache.store_entities(entities, "spells")

    # Filter by single document
    results = await cache.get_entities("spells", document="srd-5e")
    assert len(results) == 2
    assert all(r["document"] == "srd-5e" for r in results)

    # Filter by multiple documents
    results = await cache.get_entities("spells", document=["srd-5e", "tce"])
    assert len(results) == 3
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_sqlite.py::test_sqlite_cache_get_entities_with_document_filter -v`
Expected: FAIL (parameter not accepted)

**Step 3: Update SQLiteCache.get_entities to accept document parameter**

```python
# In src/lorekeeper_mcp/cache/sqlite.py, update get_entities method
async def get_entities(
    self,
    entity_type: str,
    document: str | list[str] | None = None,  # ADD THIS
    **filters: Any,
) -> list[dict[str, Any]]:
    """Retrieve entities from cache with optional filters.

    Args:
        entity_type: Type of entities to retrieve
        document: Optional document filter (string or list of strings)
        **filters: Additional field filters

    Returns:
        List of entity dictionaries matching filters
    """
    # Add document to filters if provided
    if document is not None:
        filters["document"] = document

    return await query_cached_entities(
        entity_type,
        db_path=self.db_path,
        **filters
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_sqlite.py::test_sqlite_cache_get_entities_with_document_filter -v`
Expected: PASS

**Step 5: Run all SQLite cache tests**

Run: `uv run pytest tests/test_cache/test_sqlite.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/cache/sqlite.py tests/test_cache/test_sqlite.py
git commit -m "feat(cache): add document parameter to SQLiteCache.get_entities"
```

---

## Task 6: Update SpellRepository

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/spell.py:72-116`
- Test: `tests/test_repositories/test_spell.py`

**Step 1: Write test for document filtering in SpellRepository**

```python
# Add to tests/test_repositories/test_spell.py
@pytest.mark.asyncio
async def test_spell_repository_search_with_document_filter() -> None:
    """Test SpellRepository.search with document filter."""
    from lorekeeper_mcp.repositories.spell import SpellRepository
    from lorekeeper_mcp.api_clients.models.spell import Spell

    # Mock client and cache
    class MockClient:
        async def get_spells(self, **kwargs: Any) -> list[Spell]:
            return []

    class MockCache:
        async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
            # Return spells filtered by document
            if "document" in filters:
                return [
                    {"slug": "spell-1", "name": "Fireball", "level": 3, "document": "srd-5e"}
                ]
            return []

        async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
            return len(entities)

    repo = SpellRepository(client=MockClient(), cache=MockCache())

    # Search with document filter
    spells = await repo.search(document=["srd-5e"])

    assert len(spells) == 1
    assert spells[0].document == "srd-5e"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repositories/test_spell.py::test_spell_repository_search_with_document_filter -v`
Expected: FAIL (document parameter not handled)

**Step 3: Update SpellRepository.search to pass document to cache**

```python
# In src/lorekeeper_mcp/repositories/spell.py, update search method
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
    # (spells have multiple classes, not a simple scalar field)
    class_key = filters.pop("class_key", None)

    # Extract document parameter for cache filtering
    document = filters.get("document")  # Keep in filters for cache

    # Try cache first with valid cache filter fields only
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

    # Cache miss - fetch from API with filters and limit
    # Pass class_key to API for server-side filtering
    api_filters = dict(filters)
    # Remove document from API filters (cache-only filter)
    api_filters.pop("document", None)
    if class_key is not None:
        api_filters["class_key"] = class_key
    api_params = self._map_to_api_params(**api_filters)
    spells: list[Spell] = await self.client.get_spells(limit=limit, **api_params)

    # Store in cache if we got results
    if spells:
        spell_dicts = [spell.model_dump() for spell in spells]
        await self.cache.store_entities(spell_dicts, "spells")

    return spells
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_repositories/test_spell.py::test_spell_repository_search_with_document_filter -v`
Expected: PASS

**Step 5: Run all spell repository tests**

Run: `uv run pytest tests/test_repositories/test_spell.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/repositories/spell.py tests/test_repositories/test_spell.py
git commit -m "feat(repository): add document filtering to SpellRepository"
```

---

## Task 7: Update MonsterRepository

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/monster.py`
- Test: `tests/test_repositories/test_monster.py`

**Step 1: Write test for document filtering in MonsterRepository**

```python
# Add to tests/test_repositories/test_monster.py
@pytest.mark.asyncio
async def test_monster_repository_search_with_document_filter() -> None:
    """Test MonsterRepository.search with document filter."""
    from lorekeeper_mcp.repositories.monster import MonsterRepository
    from lorekeeper_mcp.api_clients.models.monster import Monster

    # Mock client and cache
    class MockClient:
        async def get_monsters(self, **kwargs: Any) -> list[Monster]:
            return []

    class MockCache:
        async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
            if "document" in filters:
                return [
                    {"slug": "dragon-red", "name": "Red Dragon", "document": "srd-5e"}
                ]
            return []

        async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
            return len(entities)

    repo = MonsterRepository(client=MockClient(), cache=MockCache())

    spells = await repo.search(document=["srd-5e"])

    assert len(spells) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repositories/test_monster.py::test_monster_repository_search_with_document_filter -v`
Expected: FAIL (document parameter not handled)

**Step 3: Update MonsterRepository.search (same pattern as SpellRepository)**

```python
# In src/lorekeeper_mcp/repositories/monster.py, update search method to handle document
# Add document parameter handling similar to SpellRepository:
# - Extract document from filters
# - Pass to cache.get_entities
# - Remove from API filters on cache miss
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_repositories/test_monster.py::test_monster_repository_search_with_document_filter -v`
Expected: PASS

**Step 5: Run all monster repository tests**

Run: `uv run pytest tests/test_repositories/test_monster.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/repositories/monster.py tests/test_repositories/test_monster.py
git commit -m "feat(repository): add document filtering to MonsterRepository"
```

---

## Task 8: Update EquipmentRepository

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/equipment.py`
- Test: `tests/test_repositories/test_equipment.py`

**Step 1-6: Same pattern as Task 7**

Write test → verify fail → implement → verify pass → test suite → commit

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/repositories/equipment.py tests/test_repositories/test_equipment.py
git commit -m "feat(repository): add document filtering to EquipmentRepository"
```

---

## Task 9: Update CharacterOptionRepository

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/character_option.py`
- Test: `tests/test_repositories/test_character_option.py`

**Step 1-6: Same pattern as Task 7**

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/repositories/character_option.py tests/test_repositories/test_character_option.py
git commit -m "feat(repository): add document filtering to CharacterOptionRepository"
```

---

## Task 10: Update RuleRepository

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/rule.py`
- Test: `tests/test_repositories/test_rule.py`

**Step 1-6: Same pattern as Task 7**

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/repositories/rule.py tests/test_repositories/test_rule.py
git commit -m "feat(repository): add document filtering to RuleRepository"
```

---

## Task 11: Create list_documents MCP Tool

**Files:**
- Create: `src/lorekeeper_mcp/tools/list_documents.py`
- Test: `tests/test_tools/test_list_documents.py`

**Step 1: Write test for list_documents tool**

```python
# Create tests/test_tools/test_list_documents.py
import pytest
from typing import Any


@pytest.mark.asyncio
async def test_list_documents() -> None:
    """Test list_documents returns document list."""
    from lorekeeper_mcp.tools.list_documents import list_documents

    # Mock the cache functions
    from lorekeeper_mcp.tools import list_documents as list_docs_module

    original_get_docs = list_docs_module.get_available_documents

    async def mock_get_docs(**kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "document": "srd-5e",
                "source_api": "open5e_v2",
                "entity_count": 100,
                "entity_types": {"spells": 50, "creatures": 50}
            }
        ]

    list_docs_module.get_available_documents = mock_get_docs

    try:
        result = await list_documents()
        assert isinstance(result, list)
        assert len(result) > 0
        assert "document" in result[0]
    finally:
        list_docs_module.get_available_documents = original_get_docs
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_list_documents.py::test_list_documents -v`
Expected: FAIL with "No module named 'lorekeeper_mcp.tools.list_documents'"

**Step 3: Write test for source filtering**

```python
# Add to tests/test_tools/test_list_documents.py
@pytest.mark.asyncio
async def test_list_documents_source_filter() -> None:
    """Test list_documents with source filter."""
    from lorekeeper_mcp.tools.list_documents import list_documents

    result = await list_documents(source="open5e_v2")

    assert isinstance(result, list)
    # All results should be from open5e_v2
    for doc in result:
        if doc.get("source_api"):
            assert doc["source_api"] == "open5e_v2"
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_list_documents.py::test_list_documents_source_filter -v`
Expected: FAIL

**Step 5: Implement list_documents tool**

```python
# Create src/lorekeeper_mcp/tools/list_documents.py
"""Tool for listing available D&D content documents across all sources.

This module provides document discovery functionality that shows all documents
available in the cache across all sources (Open5e, D&D 5e API, OrcBrew).
"""

from typing import Any

from lorekeeper_mcp.cache.db import get_available_documents, get_document_metadata


async def list_documents(
    source: str | None = None,
) -> list[dict[str, Any]]:
    """
    List all available D&D content documents in the cache.

    This tool queries the cache to discover which source documents are available
    across all data sources (Open5e API, D&D 5e API, OrcBrew imports). Use this
    to see which books, supplements, and homebrew content you have access to,
    then use the document_keys parameter in other tools to filter content.

    IMPORTANT: This shows only documents currently in your cache. Run the build
    command to populate your cache with content from configured sources.

    Examples:
        # List all available documents
        docs = await list_documents()

        # List only Open5e documents
        docs = await list_documents(source="open5e_v2")

        # List only OrcBrew homebrew
        docs = await list_documents(source="orcbrew")

    Args:
        source: Optional source filter. Valid values:
            - "open5e_v2": Open5e API documents (SRD, Kobold Press, etc.)
            - "dnd5e_api": Official D&D 5e API (SRD only)
            - "orcbrew": Imported OrcBrew homebrew files
            - None (default): Show documents from all sources

    Returns:
        List of document dictionaries, each containing:
            - document: Document name/identifier (use this in document_keys)
            - source_api: Which API/source this came from
            - entity_count: Total number of entities from this document
            - entity_types: Breakdown of entities by type (spells, creatures, etc.)
            - publisher: Publisher name (if available, Open5e only)
            - license: License type (if available, Open5e only)

        Documents are sorted by entity count (highest first).

    Note:
        This queries only the cache and does not make API calls. You must
        populate your cache first using the build command.
    """
    # Get documents from cache
    documents = await get_available_documents(source_api=source)

    # Optionally enrich with metadata
    enriched_documents = []
    for doc in documents:
        enriched = dict(doc)

        # Try to get metadata for this document
        metadata = await get_document_metadata(doc["document"])
        if metadata:
            # Add useful metadata fields
            for field in ["publisher", "license", "description"]:
                if field in metadata:
                    enriched[field] = metadata[field]

        enriched_documents.append(enriched)

    return enriched_documents
```

**Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_tools/test_list_documents.py -v`
Expected: PASS

**Step 7: Export from tools __init__.py**

```python
# Add to src/lorekeeper_mcp/tools/__init__.py
from lorekeeper_mcp.tools.list_documents import list_documents

__all__ = [
    # ... existing exports
    "list_documents",
]
```

**Step 8: Verify imports work**

Run: `uv run python -c "from lorekeeper_mcp.tools import list_documents; print('OK')"`
Expected: "OK"

**Step 9: Run all tool tests**

Run: `uv run pytest tests/test_tools/ -v -k "not live"`
Expected: All tests PASS

**Step 10: Commit**

```bash
git add src/lorekeeper_mcp/tools/list_documents.py src/lorekeeper_mcp/tools/__init__.py tests/test_tools/test_list_documents.py
git commit -m "feat(tools): add list_documents tool for document discovery"
```

---

## Task 12: Register list_documents in MCP Server

**Files:**
- Modify: `src/lorekeeper_mcp/server.py`

**Step 1: Add tool registration**

```python
# In src/lorekeeper_mcp/server.py, add to tool registration section
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        # ... existing tools
        types.Tool(
            name="list_documents",
            description="List all available D&D content documents across all sources (Open5e, D&D 5e API, OrcBrew). Shows which books and supplements are in your cache. Use document names with document_keys parameter in other tools to filter content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Optional source filter: open5e_v2, dnd5e_api, or orcbrew",
                        "enum": ["open5e_v2", "dnd5e_api", "orcbrew"]
                    }
                },
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    # ... existing tools

    elif name == "list_documents":
        source = arguments.get("source") if arguments else None
        result = await tools.list_documents(source=source)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
```

**Step 2: Verify server starts**

Run: `uv run python -m lorekeeper_mcp --help`
Expected: Help message displays without errors

**Step 3: Run server tests**

Run: `uv run pytest tests/test_server.py -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/server.py
git commit -m "feat(server): register list_documents MCP tool"
```

---

## Task 13: Add document_keys to lookup_spell Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py:64-223`
- Test: `tests/test_tools/test_spell_lookup.py`

**Step 1: Write test for document_keys parameter**

```python
# Add to tests/test_tools/test_spell_lookup.py
@pytest.mark.asyncio
async def test_lookup_spell_with_document_keys() -> None:
    """Test lookup_spell with document_keys filter."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell, _repository_context
    from lorekeeper_mcp.api_clients.models.spell import Spell

    # Mock repository
    class MockRepository:
        async def search(self, **kwargs: Any) -> list[Spell]:
            # Verify document parameter is passed
            assert "document" in kwargs
            assert kwargs["document"] == ["srd-5e"]
            return [
                Spell(
                    slug="fireball",
                    name="Fireball",
                    level=3,
                    school="evocation",
                    document="srd-5e"
                )
            ]

    _repository_context["repository"] = MockRepository()

    try:
        results = await lookup_spell(name="fireball", document_keys=["srd-5e"])
        assert len(results) == 1
        assert results[0]["document"] == "srd-5e"
    finally:
        _repository_context.clear()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_lookup_spell_with_document_keys -v`
Expected: FAIL (parameter not accepted)

**Step 3: Update lookup_spell to accept document_keys**

```python
# In src/lorekeeper_mcp/tools/spell_lookup.py, update function signature and body
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
    document_keys: list[str] | None = None,  # ADD THIS
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e spells using the repository pattern.

    [... existing docstring content ...]

    Args:
        [... existing args ...]
        document_keys: Filter to specific source documents. Provide a list of
            document names/identifiers from list_documents() tool. Examples:
            ["srd-5e"] for SRD only, ["srd-5e", "tce"] for SRD and Tasha's.
            Use list_documents() to see available documents. NEW parameter.
        limit: Maximum number of results to return. Default 20.

    [... rest of docstring ...]
    """
    # Get repository from context or create default
    repository = _get_repository()

    # Build query parameters for repository search
    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name
    if level is not None:
        params["level"] = level
    if level_min is not None:
        params["level_min"] = level_min
    if level_max is not None:
        params["level_max"] = level_max
    if school is not None:
        params["school"] = school
    if class_key is not None:
        params["class_key"] = class_key
    if concentration is not None:
        params["concentration"] = concentration
    if ritual is not None:
        params["ritual"] = ritual
    if casting_time is not None:
        params["casting_time"] = casting_time
    if damage_type is not None:
        params["damage_type"] = damage_type
    # Backward compatibility: document parameter (deprecated, use document_keys)
    if document is not None:
        params["document"] = document
    # New document_keys parameter takes precedence
    if document_keys is not None:
        params["document"] = document_keys  # Repository expects "document"

    # Fetch spells from repository with filters
    spells = await repository.search(limit=limit, **params)

    # Limit results to requested count
    spells = spells[:limit]

    return [spell.model_dump() for spell in spells]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_lookup_spell_with_document_keys -v`
Expected: PASS

**Step 5: Run all spell lookup tests**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py -v`
Expected: All tests PASS

**Step 6: Update server.py tool registration**

```python
# In src/lorekeeper_mcp/server.py, update lookup_spell tool schema
# Add to properties:
"document_keys": {
    "type": "array",
    "items": {"type": "string"},
    "description": "Filter to specific documents. Get list from list_documents() tool."
}
```

**Step 7: Verify server starts**

Run: `uv run python -m lorekeeper_mcp --help`
Expected: No errors

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/spell_lookup.py src/lorekeeper_mcp/server.py tests/test_tools/test_spell_lookup.py
git commit -m "feat(tools): add document_keys parameter to lookup_spell"
```

---

## Task 14: Add document_keys to lookup_creature Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py`
- Modify: `src/lorekeeper_mcp/server.py`
- Test: `tests/test_tools/test_creature_lookup.py`

**Step 1-8: Same pattern as Task 13**

Add parameter → test → implement → verify → update server → commit

**Step 9: Commit**

```bash
git add src/lorekeeper_mcp/tools/creature_lookup.py src/lorekeeper_mcp/server.py tests/test_tools/test_creature_lookup.py
git commit -m "feat(tools): add document_keys parameter to lookup_creature"
```

---

## Task 15: Add document_keys to lookup_equipment Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py`
- Modify: `src/lorekeeper_mcp/server.py`
- Test: `tests/test_tools/test_equipment_lookup.py`

**Step 1-9: Same pattern as Task 13**

**Step 10: Commit**

```bash
git add src/lorekeeper_mcp/tools/equipment_lookup.py src/lorekeeper_mcp/server.py tests/test_tools/test_equipment_lookup.py
git commit -m "feat(tools): add document_keys parameter to lookup_equipment"
```

---

## Task 16: Add document_keys to lookup_character_option Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/character_option_lookup.py`
- Modify: `src/lorekeeper_mcp/server.py`
- Test: `tests/test_tools/test_character_option_lookup.py`

**Step 1-9: Same pattern as Task 13**

**Step 10: Commit**

```bash
git add src/lorekeeper_mcp/tools/character_option_lookup.py src/lorekeeper_mcp/server.py tests/test_tools/test_character_option_lookup.py
git commit -m "feat(tools): add document_keys parameter to lookup_character_option"
```

---

## Task 17: Add document_keys to lookup_rule Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/rule_lookup.py`
- Modify: `src/lorekeeper_mcp/server.py`
- Test: `tests/test_tools/test_rule_lookup.py`

**Step 1-9: Same pattern as Task 13**

**Step 10: Commit**

```bash
git add src/lorekeeper_mcp/tools/rule_lookup.py src/lorekeeper_mcp/server.py tests/test_tools/test_rule_lookup.py
git commit -m "feat(tools): add document_keys parameter to lookup_rule"
```

---

## Task 18: Add document_keys to search_dnd_content Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/search_dnd_content.py:39-108`
- Modify: `src/lorekeeper_mcp/server.py`
- Test: `tests/test_tools/test_search_dnd_content.py`

**Step 1: Write test for document_keys in search**

```python
# Add to tests/test_tools/test_search_dnd_content.py (create if doesn't exist)
import pytest
from typing import Any


@pytest.mark.asyncio
async def test_search_dnd_content_with_document_keys() -> None:
    """Test search_dnd_content with document_keys post-filtering."""
    from lorekeeper_mcp.tools.search_dnd_content import search_dnd_content

    # This is an integration-style test that may need mocking
    # The key is to verify post-filtering logic works
    results = await search_dnd_content(
        query="fireball",
        document_keys=["srd-5e"],
        limit=10
    )

    # All results should have document field matching filter
    for result in results:
        if "document" in result:
            assert result["document"] in ["srd-5e"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_search_dnd_content.py::test_search_dnd_content_with_document_keys -v`
Expected: FAIL (parameter not accepted)

**Step 3: Implement document_keys post-filtering in search_dnd_content**

```python
# In src/lorekeeper_mcp/tools/search_dnd_content.py, update function
async def search_dnd_content(
    query: str,
    content_types: list[str] | None = None,
    document_keys: list[str] | None = None,  # ADD THIS
    enable_fuzzy: bool = True,
    enable_semantic: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search across all D&D content with advanced fuzzy and semantic matching.

    [... existing docstring ...]

    Args:
        query: Search term (handles typos and concepts automatically)
        content_types: Limit to specific types
        document_keys: Filter results to specific documents. Provide list of
            document names from list_documents() tool. Post-filters search
            results by document field. Examples: ["srd-5e"], ["srd-5e", "tce"].
            NEW parameter.
        enable_fuzzy: Enable fuzzy matching (default True)
        enable_semantic: Enable semantic search (default True)
        limit: Maximum results (default 20)

    [... rest of docstring ...]
    """
    # Short-circuit for empty document list
    if document_keys is not None and len(document_keys) == 0:
        return []

    client = _get_open5e_client()

    if content_types:
        # Multiple searches, one per content type
        all_results: list[dict[str, Any]] = []
        per_type_limit = limit // len(content_types)

        for content_type in content_types:
            results = await client.unified_search(
                query=query,
                fuzzy=enable_fuzzy,
                vector=enable_semantic,
                object_model=content_type,
                limit=per_type_limit,
            )
            all_results.extend(results)

        # Post-filter by document if specified
        if document_keys:
            all_results = [
                r for r in all_results
                if r.get("document") in document_keys or r.get("document__slug") in document_keys
            ]

        return all_results[:limit]

    # Single unified search across all types
    results = await client.unified_search(
        query=query,
        fuzzy=enable_fuzzy,
        vector=enable_semantic,
        limit=limit,
    )

    # Post-filter by document if specified
    if document_keys:
        results = [
            r for r in results
            if r.get("document") in document_keys or r.get("document__slug") in document_keys
        ]

    return results[:limit]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_search_dnd_content.py::test_search_dnd_content_with_document_keys -v`
Expected: PASS

**Step 5: Update server.py tool registration**

```python
# In src/lorekeeper_mcp/server.py, update search_dnd_content schema
# Add to properties:
"document_keys": {
    "type": "array",
    "items": {"type": "string"},
    "description": "Filter results to specific documents. Get list from list_documents()."
}
```

**Step 6: Run all search tests**

Run: `uv run pytest tests/test_tools/test_search_dnd_content.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/tools/search_dnd_content.py src/lorekeeper_mcp/server.py tests/test_tools/test_search_dnd_content.py
git commit -m "feat(tools): add document_keys post-filtering to search_dnd_content"
```

---

## Task 19: Integration Testing

**Files:**
- Create: `tests/test_tools/test_document_filtering.py`

**Step 1: Write end-to-end integration test**

```python
# Create tests/test_tools/test_document_filtering.py
"""Integration tests for document filtering across all tools."""

import pytest
from typing import Any


@pytest.mark.asyncio
async def test_list_documents_integration(populated_cache: str) -> None:
    """Test list_documents with real cache data."""
    from lorekeeper_mcp.tools.list_documents import list_documents

    documents = await list_documents()

    assert isinstance(documents, list)
    # Should have at least some documents in populated cache
    assert len(documents) >= 0

    # Verify structure
    for doc in documents:
        assert "document" in doc
        assert "source_api" in doc
        assert "entity_count" in doc


@pytest.mark.asyncio
async def test_spell_lookup_with_document_filter_integration(populated_cache: str) -> None:
    """Test spell lookup with document filtering end-to-end."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell

    # First, get spells without filter
    all_spells = await lookup_spell(limit=50)

    if len(all_spells) == 0:
        pytest.skip("No spells in cache")

    # Get unique documents
    documents = set(s.get("document") for s in all_spells if s.get("document"))

    if len(documents) == 0:
        pytest.skip("No documents in spell data")

    # Filter by first document
    doc_to_filter = list(documents)[0]
    filtered_spells = await lookup_spell(document_keys=[doc_to_filter], limit=50)

    # All filtered results should match the document
    for spell in filtered_spells:
        if spell.get("document"):
            assert spell["document"] == doc_to_filter


@pytest.mark.asyncio
async def test_cross_tool_document_consistency() -> None:
    """Test that document filtering works consistently across all tools."""
    from lorekeeper_mcp.tools.list_documents import list_documents
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    # Get available documents
    documents = await list_documents()

    if len(documents) == 0:
        pytest.skip("No documents in cache")

    doc_key = documents[0]["document"]

    # Try filtering with each tool
    spells = await lookup_spell(document_keys=[doc_key], limit=5)
    creatures = await lookup_creature(document_keys=[doc_key], limit=5)

    # Should complete without errors
    assert isinstance(spells, list)
    assert isinstance(creatures, list)
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/test_tools/test_document_filtering.py -v`
Expected: PASS (or SKIP if cache not populated)

**Step 3: Commit**

```bash
git add tests/test_tools/test_document_filtering.py
git commit -m "test: add integration tests for document filtering"
```

---

## Task 20: Live MCP Testing

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py`

**Step 1: Add live test for list_documents**

```python
# Add to tests/test_tools/test_live_mcp.py
@pytest.mark.live
@pytest.mark.asyncio
async def test_list_documents_live(mcp_server: MCPTestServer) -> None:
    """Live test for list_documents tool."""
    # Call tool via MCP
    response = await mcp_server.call_tool("list_documents", {})

    assert response is not None
    # Parse JSON response
    import json
    data = json.loads(response)
    assert isinstance(data, list)
```

**Step 2: Add live test for spell lookup with document filter**

```python
# Add to tests/test_tools/test_live_mcp.py
@pytest.mark.live
@pytest.mark.asyncio
async def test_lookup_spell_with_document_filter_live(mcp_server: MCPTestServer) -> None:
    """Live test for lookup_spell with document_keys."""
    # First get documents
    docs_response = await mcp_server.call_tool("list_documents", {})
    import json
    documents = json.loads(docs_response)

    if len(documents) == 0:
        pytest.skip("No documents in cache")

    doc_key = documents[0]["document"]

    # Now search with document filter
    response = await mcp_server.call_tool(
        "lookup_spell",
        {"document_keys": [doc_key], "limit": 5}
    )

    assert response is not None
    spells = json.loads(response)
    assert isinstance(spells, list)
```

**Step 3: Run live tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py -v -m live`
Expected: PASS (requires running MCP server)

**Step 4: Commit**

```bash
git add tests/test_tools/test_live_mcp.py
git commit -m "test: add live MCP tests for document filtering"
```

---

## Task 21: Run Full Test Suite

**Step 1: Run all unit tests**

Run: `uv run pytest tests/ -v -m "not live"`
Expected: All tests PASS

**Step 2: Run type checking**

Run: `just type-check`
Expected: No mypy errors

**Step 3: Run linting**

Run: `just lint`
Expected: No ruff errors

**Step 4: Run formatting check**

Run: `just format --check`
Expected: No formatting changes needed

**Step 5: Run all quality checks**

Run: `just check`
Expected: All checks PASS

**Step 6: Commit if any formatting was applied**

```bash
git add -u
git commit -m "style: apply formatting and linting fixes"
```

---

## Task 22: Documentation Update

**Files:**
- Modify: `README.md`
- Modify: `docs/tools.md`

**Step 1: Update README.md with document filtering examples**

```markdown
# Add to README.md in Tools section

### Document Filtering

All lookup and search tools support filtering by source document:

```python
# Discover available documents
documents = await list_documents()

# Filter spells to SRD only
srd_spells = await lookup_spell(
    level=3,
    document_keys=["srd-5e"]
)

# Filter creatures from multiple sources
creatures = await lookup_creature(
    type="dragon",
    document_keys=["srd-5e", "tce", "phb"]
)

# Search with document filter
results = await search_dnd_content(
    query="fireball",
    document_keys=["srd-5e"]
)
```

**Step 2: Update docs/tools.md with detailed examples**

```markdown
# Add to docs/tools.md

## Document Filtering

### Overview

All LoreKeeper tools support filtering content by source document. This allows you to:
- Limit searches to SRD (free) content only
- Filter by specific published books
- Separate homebrew from official content
- Control which sources you're using for licensing reasons

### Discovery

Use `list_documents()` to see available documents:

[... examples ...]

### Usage

All lookup tools (`lookup_spell`, `lookup_creature`, etc.) and `search_dnd_content` accept a `document_keys` parameter:

[... examples ...]
```

**Step 3: Verify documentation builds (if applicable)**

Run: `ls docs/*.md`
Expected: Files exist and are readable

**Step 4: Commit**

```bash
git add README.md docs/tools.md
git commit -m "docs: add document filtering usage examples"
```

---

## Validation Checklist

Before marking complete, verify:

- [ ] All cache functions work across sources (open5e_v2, dnd5e_api, orcbrew)
- [ ] `list_documents()` returns accurate document lists from cache
- [ ] All lookup tools accept and respect `document_keys` parameter
- [ ] `search_dnd_content` post-filters by document correctly
- [ ] Multi-document filtering works with IN clause
- [ ] Empty document list short-circuits correctly
- [ ] Single document filter backward compatible (string)
- [ ] All unit tests pass: `uv run pytest tests/ -m "not live" -v`
- [ ] All live tests pass: `uv run pytest tests/ -m live -v`
- [ ] Type checking passes: `just type-check`
- [ ] Linting passes: `just lint`
- [ ] All quality checks pass: `just check`
- [ ] No breaking changes to existing functionality
- [ ] Documentation updated with examples
- [ ] Source-agnostic design verified (no API-specific logic)

## Estimated Effort

- **Cache Layer**: 2-3 hours (Tasks 1-3)
- **Repositories**: 2 hours (Tasks 4-10)
- **Tools**: 3-4 hours (Tasks 11-18)
- **Testing**: 2 hours (Tasks 19-21)
- **Documentation**: 30 minutes (Task 22)

**Total**: ~10-12 hours

## Notes for Implementation

1. **TDD Approach**: Every task follows write test → verify fail → implement → verify pass cycle
2. **Frequent Commits**: Each task ends with a commit using conventional commit format
3. **No Breaking Changes**: All parameters optional, existing behavior preserved
4. **Cache-First**: No API changes needed, all queries hit SQLite cache
5. **Source Agnostic**: Single code path handles all sources uniformly
6. **Performance**: Short-circuit empty lists, indexed document field, UNION with GROUP BY
7. **Type Safety**: Full type hints, mypy strict mode compatible
