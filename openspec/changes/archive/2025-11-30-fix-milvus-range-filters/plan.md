# Fix Milvus Range Filters Implementation Plan

**Goal:** Enable range filter parameters (`level_min`, `level_max`, `{field}_min`, `{field}_max`) in Milvus semantic search by converting them to proper comparison operators (`>=`, `<=`).

**Architecture:** The `_build_filter_expression()` method will be extended to detect `_min`/`_max` suffixes on filter keys, strip the suffix to get the actual field name, and generate appropriate comparison operators instead of equality checks.

**Tech Stack:** Python 3.11+, Milvus Lite, pytest

---

## Task 1: Add Unit Tests for Range Filter Expression Building

**Files:**

- Modify: `tests/test_cache/test_milvus.py` (add tests to `TestMilvusCacheBuildFilterExpression` class starting after line 398)

**Step 1: Write the failing test for `level_min` conversion**

Add this test to the `TestMilvusCacheBuildFilterExpression` class:

```python
def test_build_filter_level_min(self, tmp_path: Path):
    """Test filter expression converts level_min to >= operator."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"level_min": 4})
    assert result == "level >= 4"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression::test_build_filter_level_min -v`

Expected: FAIL with `AssertionError: assert 'level_min == 4' == 'level >= 4'`

**Step 3: Write the failing test for `level_max` conversion**

```python
def test_build_filter_level_max(self, tmp_path: Path):
    """Test filter expression converts level_max to <= operator."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"level_max": 3})
    assert result == "level <= 3"
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression::test_build_filter_level_max -v`

Expected: FAIL with `AssertionError: assert 'level_max == 3' == 'level <= 3'`

**Step 5: Write the failing test for combined range filters**

```python
def test_build_filter_level_min_and_max(self, tmp_path: Path):
    """Test filter expression with both level_min and level_max."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"level_min": 3, "level_max": 6})
    assert "level >= 3" in result
    assert "level <= 6" in result
    assert " and " in result
```

**Step 6: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression::test_build_filter_level_min_and_max -v`

Expected: FAIL

**Step 7: Write the failing test for range filter combined with exact filter**

```python
def test_build_filter_range_with_exact_filter(self, tmp_path: Path):
    """Test filter expression combines range filter with exact filter."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"level_min": 3, "school": "evocation"})
    assert "level >= 3" in result
    assert 'school == "evocation"' in result
    assert " and " in result
```

**Step 8: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression::test_build_filter_range_with_exact_filter -v`

Expected: FAIL

**Step 9: Write the failing test for generic field minimum range support**

```python
def test_build_filter_generic_field_min(self, tmp_path: Path):
    """Test filter expression works with any field_min pattern."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"armor_class_min": 15})
    assert result == "armor_class >= 15"
```

**Step 10: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression::test_build_filter_generic_field_min -v`

Expected: FAIL

**Step 11: Write the failing test for generic field maximum range support**

```python
def test_build_filter_generic_field_max(self, tmp_path: Path):
    """Test filter expression works with any field_max pattern."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"challenge_rating_max": 5})
    assert result == "challenge_rating <= 5"
```

**Step 12: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression::test_build_filter_generic_field_max -v`

Expected: FAIL

**Step 13: Commit the failing tests**

```bash
git add tests/test_cache/test_milvus.py
git commit -m "test: add failing tests for range filter expression building"
```

---

## Task 2: Implement Range Filter Support in `_build_filter_expression`

**Files:**

- Modify: `src/lorekeeper_mcp/cache/milvus.py:289-322` (the `_build_filter_expression` method)

**Step 1: Update `_build_filter_expression` to detect and handle `_min`/`_max` suffixes**

Replace the current `_build_filter_expression` method (lines 289-322) with:

```python
def _build_filter_expression(self, filters: dict[str, Any]) -> str:
    """Build Milvus filter expression from keyword filters.

    Converts Python filter dict to Milvus boolean expression syntax.
    Supports:
    - Exact match: {"level": 3} -> 'level == 3'
    - Range min: {"level_min": 3} -> 'level >= 3'
    - Range max: {"level_max": 6} -> 'level <= 6'
    - String values: {"school": "Evocation"} -> 'school == "Evocation"'
    - List values (IN): {"document": ["srd", "phb"]} -> 'document in ["srd", "phb"]'

    Args:
        filters: Dictionary of field names to filter values.
            Field names ending in '_min' are converted to >= operators.
            Field names ending in '_max' are converted to <= operators.

    Returns:
        Milvus filter expression string, or empty string if no filters.
    """
    expressions: list[str] = []

    for field, value in filters.items():
        if value is None:
            continue

        # Detect range filter suffixes and determine operator
        if field.endswith("_min"):
            actual_field = field[:-4]  # Remove '_min' suffix
            operator = ">="
        elif field.endswith("_max"):
            actual_field = field[:-4]  # Remove '_max' suffix
            operator = "<="
        else:
            actual_field = field
            operator = "=="

        if isinstance(value, str):
            expressions.append(f'{actual_field} {operator} "{value}"')
        elif isinstance(value, bool):
            # Milvus uses lowercase boolean literals
            expressions.append(f"{actual_field} {operator} {str(value).lower()}")
        elif isinstance(value, int | float):
            expressions.append(f"{actual_field} {operator} {value}")
        elif isinstance(value, list):
            # Handle list of values (IN clause) - only for equality operator
            if operator != "==":
                # Range operators don't make sense with lists, skip
                logger.warning(
                    "Range operator %s not supported with list values for field %s",
                    operator,
                    field,
                )
                continue
            if all(isinstance(v, str) for v in value):
                quoted = [f'"{v}"' for v in value]
                expressions.append(f"{actual_field} in [{', '.join(quoted)}]")
            else:
                expressions.append(f"{actual_field} in {value}")

    return " and ".join(expressions)
```

**Step 2: Run the unit tests to verify they pass**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheBuildFilterExpression -v`

Expected: All tests PASS (existing tests + new range filter tests)

**Step 3: Commit the implementation**

```bash
git add src/lorekeeper_mcp/cache/milvus.py
git commit -m "feat: add range filter support (_min/_max) to Milvus filter expressions"
```

---

## Task 3: Add Integration Test for Semantic Search with Range Filters

**Files:**

- Modify: `tests/test_cache/test_milvus.py` (add tests to `TestMilvusCacheHybridSearchAccuracy` class after line 1169)

**Step 1: Write the integration test for semantic search with level_min filter**

Add this test to the `TestMilvusCacheHybridSearchAccuracy` class:

```python
@pytest.mark.asyncio
async def test_hybrid_search_level_min_filter(self, tmp_path: Path):
    """Test hybrid search with level_min filter only returns spells at or above level."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    entities = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "desc": "A bright streak flashes and explodes into fire.",
            "level": 3,
            "document": "srd",
        },
        {
            "slug": "fire-bolt",
            "name": "Fire Bolt",
            "desc": "A mote of fire at a creature dealing fire damage.",
            "level": 0,
            "document": "srd",
        },
        {
            "slug": "fire-storm",
            "name": "Fire Storm",
            "desc": "A storm of fire dealing massive fire damage.",
            "level": 7,
            "document": "srd",
        },
        {
            "slug": "wall-of-fire",
            "name": "Wall of Fire",
            "desc": "Create a wall of fire that damages creatures.",
            "level": 4,
            "document": "srd",
        },
    ]
    await cache.store_entities(entities, "spells")

    # Search for fire spells with level >= 4
    result = await cache.semantic_search("spells", "fire damage", level_min=4)

    # Should only return spells at level 4 or higher
    assert len(result) == 2
    returned_slugs = {r["slug"] for r in result}
    assert returned_slugs == {"fire-storm", "wall-of-fire"}
    for r in result:
        assert r["level"] >= 4
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheHybridSearchAccuracy::test_hybrid_search_level_min_filter -v`

Expected: PASS

**Step 3: Write the integration test for semantic search with level_max filter**

```python
@pytest.mark.asyncio
async def test_hybrid_search_level_max_filter(self, tmp_path: Path):
    """Test hybrid search with level_max filter only returns spells at or below level."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    entities = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "desc": "A bright streak flashes and explodes into fire.",
            "level": 3,
            "document": "srd",
        },
        {
            "slug": "fire-bolt",
            "name": "Fire Bolt",
            "desc": "A mote of fire at a creature dealing fire damage.",
            "level": 0,
            "document": "srd",
        },
        {
            "slug": "fire-storm",
            "name": "Fire Storm",
            "desc": "A storm of fire dealing massive fire damage.",
            "level": 7,
            "document": "srd",
        },
        {
            "slug": "wall-of-fire",
            "name": "Wall of Fire",
            "desc": "Create a wall of fire that damages creatures.",
            "level": 4,
            "document": "srd",
        },
    ]
    await cache.store_entities(entities, "spells")

    # Search for fire spells with level <= 3
    result = await cache.semantic_search("spells", "fire damage", level_max=3)

    # Should only return spells at level 3 or lower
    assert len(result) == 2
    returned_slugs = {r["slug"] for r in result}
    assert returned_slugs == {"fireball", "fire-bolt"}
    for r in result:
        assert r["level"] <= 3
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheHybridSearchAccuracy::test_hybrid_search_level_max_filter -v`

Expected: PASS

**Step 5: Write the integration test for semantic search with combined range filters**

```python
@pytest.mark.asyncio
async def test_hybrid_search_level_range_filter(self, tmp_path: Path):
    """Test hybrid search with both level_min and level_max filters."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    entities = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "desc": "A bright streak flashes and explodes into fire.",
            "level": 3,
            "document": "srd",
        },
        {
            "slug": "fire-bolt",
            "name": "Fire Bolt",
            "desc": "A mote of fire at a creature dealing fire damage.",
            "level": 0,
            "document": "srd",
        },
        {
            "slug": "fire-storm",
            "name": "Fire Storm",
            "desc": "A storm of fire dealing massive fire damage.",
            "level": 7,
            "document": "srd",
        },
        {
            "slug": "wall-of-fire",
            "name": "Wall of Fire",
            "desc": "Create a wall of fire that damages creatures.",
            "level": 4,
            "document": "srd",
        },
        {
            "slug": "delayed-blast-fireball",
            "name": "Delayed Blast Fireball",
            "desc": "A delayed fire explosion.",
            "level": 7,
            "document": "srd",
        },
    ]
    await cache.store_entities(entities, "spells")

    # Search for fire spells with level between 3 and 5 (inclusive)
    result = await cache.semantic_search("spells", "fire damage", level_min=3, level_max=5)

    # Should only return spells at levels 3, 4, or 5
    assert len(result) == 2
    returned_slugs = {r["slug"] for r in result}
    assert returned_slugs == {"fireball", "wall-of-fire"}
    for r in result:
        assert 3 <= r["level"] <= 5
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_cache/test_milvus.py::TestMilvusCacheHybridSearchAccuracy::test_hybrid_search_level_range_filter -v`

Expected: PASS

**Step 7: Commit the integration tests**

```bash
git add tests/test_cache/test_milvus.py
git commit -m "test: add integration tests for semantic search with range filters"
```

---

## Task 4: Run Full Test Suite to Verify No Regressions

**Files:**

- None (validation only)

**Step 1: Run all Milvus cache tests**

Run: `uv run pytest tests/test_cache/test_milvus.py -v`

Expected: All tests PASS

**Step 2: Run the full test suite**

Run: `just test`

Expected: All tests PASS (no regressions in other modules)

**Step 3: Run type checking**

Run: `just type-check`

Expected: No errors

**Step 4: Run linting**

Run: `just lint`

Expected: No errors

---

## Task 5: Run Live Tests to Verify End-to-End Functionality

**Files:**

- None (validation only)

**Step 1: Run live tests**

Run: `uv run pytest -v -m live`

Expected: All live tests PASS

**Step 2: Manual verification (if cache is populated)**

If you have a populated cache, test manually:

```bash
# Start MCP server or use CLI to test
# Example: search for fire spells at level 4+
```

Verify that `search_spell(search="fire", level_min=4)` returns expected results (spells level 4 and above).

---

## Task 6: Final Commit and Cleanup

**Files:**

- Modify: `openspec/changes/fix-milvus-range-filters/tasks.md`

**Step 1: Update tasks.md to mark all tasks complete**

Edit `openspec/changes/fix-milvus-range-filters/tasks.md`:

```markdown
## 1. Implementation

- [x] 1.1 Update `_build_filter_expression()` in `milvus.py` to detect `_min`/`_max` suffixes and convert to range operators (`>=`/`<=`)
- [x] 1.2 Add unit tests for range filter expression building
- [x] 1.3 Add integration test for `semantic_search` with range filters

## 2. Validation

- [x] 2.1 Run existing test suite to ensure no regressions
- [x] 2.2 Run live tests to verify fix works end-to-end
- [x] 2.3 Manual verification: `search_spell(search="fire", level_min=4)` returns expected results
```

**Step 2: Commit the task update**

```bash
git add openspec/changes/fix-milvus-range-filters/tasks.md
git commit -m "docs: mark fix-milvus-range-filters tasks complete"
```

---

## Summary of All Code Changes

### File: `src/lorekeeper_mcp/cache/milvus.py`

**Lines 289-322** - Replace `_build_filter_expression` method to add `_min`/`_max` suffix detection:

```python
def _build_filter_expression(self, filters: dict[str, Any]) -> str:
    """Build Milvus filter expression from keyword filters.

    Converts Python filter dict to Milvus boolean expression syntax.
    Supports:
    - Exact match: {"level": 3} -> 'level == 3'
    - Range min: {"level_min": 3} -> 'level >= 3'
    - Range max: {"level_max": 6} -> 'level <= 6'
    - String values: {"school": "Evocation"} -> 'school == "Evocation"'
    - List values (IN): {"document": ["srd", "phb"]} -> 'document in ["srd", "phb"]'

    Args:
        filters: Dictionary of field names to filter values.
            Field names ending in '_min' are converted to >= operators.
            Field names ending in '_max' are converted to <= operators.

    Returns:
        Milvus filter expression string, or empty string if no filters.
    """
    expressions: list[str] = []

    for field, value in filters.items():
        if value is None:
            continue

        # Detect range filter suffixes and determine operator
        if field.endswith("_min"):
            actual_field = field[:-4]  # Remove '_min' suffix
            operator = ">="
        elif field.endswith("_max"):
            actual_field = field[:-4]  # Remove '_max' suffix
            operator = "<="
        else:
            actual_field = field
            operator = "=="

        if isinstance(value, str):
            expressions.append(f'{actual_field} {operator} "{value}"')
        elif isinstance(value, bool):
            # Milvus uses lowercase boolean literals
            expressions.append(f"{actual_field} {operator} {str(value).lower()}")
        elif isinstance(value, int | float):
            expressions.append(f"{actual_field} {operator} {value}")
        elif isinstance(value, list):
            # Handle list of values (IN clause) - only for equality operator
            if operator != "==":
                # Range operators don't make sense with lists, skip
                logger.warning(
                    "Range operator %s not supported with list values for field %s",
                    operator,
                    field,
                )
                continue
            if all(isinstance(v, str) for v in value):
                quoted = [f'"{v}"' for v in value]
                expressions.append(f"{actual_field} in [{', '.join(quoted)}]")
            else:
                expressions.append(f"{actual_field} in {value}")

    return " and ".join(expressions)
```

### File: `tests/test_cache/test_milvus.py`

**After line 398** - Add these unit tests to `TestMilvusCacheBuildFilterExpression`:

```python
def test_build_filter_level_min(self, tmp_path: Path):
    """Test filter expression converts level_min to >= operator."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"level_min": 4})
    assert result == "level >= 4"

def test_build_filter_level_max(self, tmp_path: Path):
    """Test filter expression converts level_max to <= operator."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"level_max": 3})
    assert result == "level <= 3"

def test_build_filter_level_min_and_max(self, tmp_path: Path):
    """Test filter expression with both level_min and level_max."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"level_min": 3, "level_max": 6})
    assert "level >= 3" in result
    assert "level <= 6" in result
    assert " and " in result

def test_build_filter_range_with_exact_filter(self, tmp_path: Path):
    """Test filter expression combines range filter with exact filter."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"level_min": 3, "school": "evocation"})
    assert "level >= 3" in result
    assert 'school == "evocation"' in result
    assert " and " in result

def test_build_filter_generic_field_min(self, tmp_path: Path):
    """Test filter expression works with any field_min pattern."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"armor_class_min": 15})
    assert result == "armor_class >= 15"

def test_build_filter_generic_field_max(self, tmp_path: Path):
    """Test filter expression works with any field_max pattern."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    result = cache._build_filter_expression({"challenge_rating_max": 5})
    assert result == "challenge_rating <= 5"
```

**After line 1169** - Add these integration tests to `TestMilvusCacheHybridSearchAccuracy`:

```python
@pytest.mark.asyncio
async def test_hybrid_search_level_min_filter(self, tmp_path: Path):
    """Test hybrid search with level_min filter only returns spells at or above level."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    entities = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "desc": "A bright streak flashes and explodes into fire.",
            "level": 3,
            "document": "srd",
        },
        {
            "slug": "fire-bolt",
            "name": "Fire Bolt",
            "desc": "A mote of fire at a creature dealing fire damage.",
            "level": 0,
            "document": "srd",
        },
        {
            "slug": "fire-storm",
            "name": "Fire Storm",
            "desc": "A storm of fire dealing massive fire damage.",
            "level": 7,
            "document": "srd",
        },
        {
            "slug": "wall-of-fire",
            "name": "Wall of Fire",
            "desc": "Create a wall of fire that damages creatures.",
            "level": 4,
            "document": "srd",
        },
    ]
    await cache.store_entities(entities, "spells")

    # Search for fire spells with level >= 4
    result = await cache.semantic_search("spells", "fire damage", level_min=4)

    # Should only return spells at level 4 or higher
    assert len(result) == 2
    returned_slugs = {r["slug"] for r in result}
    assert returned_slugs == {"fire-storm", "wall-of-fire"}
    for r in result:
        assert r["level"] >= 4

@pytest.mark.asyncio
async def test_hybrid_search_level_max_filter(self, tmp_path: Path):
    """Test hybrid search with level_max filter only returns spells at or below level."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    entities = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "desc": "A bright streak flashes and explodes into fire.",
            "level": 3,
            "document": "srd",
        },
        {
            "slug": "fire-bolt",
            "name": "Fire Bolt",
            "desc": "A mote of fire at a creature dealing fire damage.",
            "level": 0,
            "document": "srd",
        },
        {
            "slug": "fire-storm",
            "name": "Fire Storm",
            "desc": "A storm of fire dealing massive fire damage.",
            "level": 7,
            "document": "srd",
        },
        {
            "slug": "wall-of-fire",
            "name": "Wall of Fire",
            "desc": "Create a wall of fire that damages creatures.",
            "level": 4,
            "document": "srd",
        },
    ]
    await cache.store_entities(entities, "spells")

    # Search for fire spells with level <= 3
    result = await cache.semantic_search("spells", "fire damage", level_max=3)

    # Should only return spells at level 3 or lower
    assert len(result) == 2
    returned_slugs = {r["slug"] for r in result}
    assert returned_slugs == {"fireball", "fire-bolt"}
    for r in result:
        assert r["level"] <= 3

@pytest.mark.asyncio
async def test_hybrid_search_level_range_filter(self, tmp_path: Path):
    """Test hybrid search with both level_min and level_max filters."""
    from lorekeeper_mcp.cache.milvus import MilvusCache

    db_path = tmp_path / "test_milvus.db"
    cache = MilvusCache(str(db_path))

    entities = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "desc": "A bright streak flashes and explodes into fire.",
            "level": 3,
            "document": "srd",
        },
        {
            "slug": "fire-bolt",
            "name": "Fire Bolt",
            "desc": "A mote of fire at a creature dealing fire damage.",
            "level": 0,
            "document": "srd",
        },
        {
            "slug": "fire-storm",
            "name": "Fire Storm",
            "desc": "A storm of fire dealing massive fire damage.",
            "level": 7,
            "document": "srd",
        },
        {
            "slug": "wall-of-fire",
            "name": "Wall of Fire",
            "desc": "Create a wall of fire that damages creatures.",
            "level": 4,
            "document": "srd",
        },
        {
            "slug": "delayed-blast-fireball",
            "name": "Delayed Blast Fireball",
            "desc": "A delayed fire explosion.",
            "level": 7,
            "document": "srd",
        },
    ]
    await cache.store_entities(entities, "spells")

    # Search for fire spells with level between 3 and 5 (inclusive)
    result = await cache.semantic_search("spells", "fire damage", level_min=3, level_max=5)

    # Should only return spells at levels 3, 4, or 5
    assert len(result) == 2
    returned_slugs = {r["slug"] for r in result}
    assert returned_slugs == {"fireball", "wall-of-fire"}
    for r in result:
        assert 3 <= r["level"] <= 5
```

---

## Commit Sequence

1. `test: add failing tests for range filter expression building`
2. `feat: add range filter support (_min/_max) to Milvus filter expressions`
3. `test: add integration tests for semantic search with range filters`
4. `docs: mark fix-milvus-range-filters tasks complete`
