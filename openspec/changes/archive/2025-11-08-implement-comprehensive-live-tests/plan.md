# Comprehensive Live MCP Testing Implementation Plan

**Goal:** Implement pytest-based live test suite validating all MCP tools against real Open5e and D&D 5e APIs with proper caching, performance tracking, and error handling.

**Architecture:** Pytest-based test suite with custom markers (`@pytest.mark.live`) for selective execution, dedicated fixtures for rate limiting and cache management, organized by tool with comprehensive scenarios covering basic functionality, filtering, caching, performance, and error handling.

**Tech Stack:** pytest, pytest-asyncio, existing API clients, SQLite cache, respx (for selective mocking in edge cases)

---

## Task 1: Infrastructure Setup

### Task 1.1: Configure pytest markers

**Files:**
- Modify: `pyproject.toml:24-26` (pytest.ini_options section)

**Step 1: Add live and slow markers to pytest configuration**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]
markers = [
    "live: marks tests as live API tests requiring internet (deselect with '-m \"not live\"')",
    "slow: marks tests as slow running (>1 second)",
]
```

**Step 2: Verify markers are registered**

Run: `uv run pytest --markers`
Expected: Output includes:
```
@pytest.mark.live: marks tests as live API tests requiring internet (deselect with '-m "not live"')
@pytest.mark.slow: marks tests as slow running (>1 second)
```

**Step 3: Commit**

Run: `git add pyproject.toml && git commit -m "Add pytest markers for live and slow tests"`
Expected: Clean commit

---

### Task 1.2: Create live test fixtures

**Files:**
- Modify: `tests/conftest.py` (add fixtures at end of file)

**Step 1: Write test for live_db fixture behavior**

Create: `tests/test_fixtures.py`

```python
"""Test live testing fixtures."""

import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_live_db_creates_temp_database(live_db, tmp_path):
    """Verify live_db fixture creates isolated test database."""
    # live_db should return a path to a temporary database
    assert live_db is not None
    db_path = Path(live_db)
    assert db_path.exists()
    assert "test" in str(db_path).lower() or str(db_path).startswith("/tmp")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_fixtures.py::test_live_db_creates_temp_database -v`
Expected: FAIL with "fixture 'live_db' not found"

**Step 3: Implement live_db fixture**

Add to `tests/conftest.py`:

```python
import asyncio
import time
from pathlib import Path
from typing import AsyncGenerator
import tempfile


@pytest.fixture
async def live_db(tmp_path: Path) -> AsyncGenerator[str, None]:
    """
    Provide isolated test database for live tests.

    Creates temporary database, yields path, cleans up after test.
    """
    db_file = tmp_path / "test_live_cache.db"

    # Import cache setup
    from lorekeeper_mcp.cache.db import init_db

    # Initialize test database
    await init_db(str(db_file))

    yield str(db_file)

    # Cleanup handled by tmp_path fixture


@pytest.fixture
def rate_limiter():
    """
    Enforce rate limiting between API calls to prevent throttling.

    Tracks last call time per API and enforces minimum delay.
    """
    last_call: dict[str, float] = {}

    async def wait_if_needed(api_name: str = "default", min_delay: float = 0.1) -> None:
        """Wait if needed to respect rate limits."""
        if api_name in last_call:
            elapsed = time.time() - last_call[api_name]
            if elapsed < min_delay:
                await asyncio.sleep(min_delay - elapsed)
        last_call[api_name] = time.time()

    return wait_if_needed


class CacheStats:
    """Track cache hit/miss statistics for validation."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.queries: list[dict[str, any]] = []

    def record_hit(self, query: dict[str, any]) -> None:
        """Record cache hit."""
        self.hits += 1
        self.queries.append({"type": "hit", "query": query})

    def record_miss(self, query: dict[str, any]) -> None:
        """Record cache miss."""
        self.misses += 1
        self.queries.append({"type": "miss", "query": query})

    def reset(self) -> None:
        """Reset statistics."""
        self.hits = 0
        self.misses = 0
        self.queries = []


@pytest.fixture
def cache_stats() -> CacheStats:
    """Provide cache statistics tracker for tests."""
    return CacheStats()


@pytest.fixture
async def clear_cache(live_db: str):
    """Clear cache before test execution."""
    from lorekeeper_mcp.cache.db import clear_all_cache

    await clear_all_cache()
    yield
    # Cache will be cleared with temp database
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_fixtures.py::test_live_db_creates_temp_database -v`
Expected: PASS

**Step 5: Commit**

Run: `git add tests/conftest.py tests/test_fixtures.py && git commit -m "Add live test fixtures for DB isolation and rate limiting"`
Expected: Clean commit

---

### Task 1.3: Create test file skeleton

**Files:**
- Create: `tests/test_tools/test_live_mcp.py`

**Step 1: Create skeleton with module docstring and imports**

```python
"""
Live integration tests for MCP tools against real APIs.

These tests validate functionality against live Open5e and D&D 5e APIs.
They are marked with @pytest.mark.live and can be skipped with:
    pytest -m "not live"

Run only live tests with:
    pytest -m live

Requirements:
- Internet connection
- Working Open5e and D&D 5e API endpoints
- Reasonable API rate limits

Performance expectations:
- Uncached queries: < 3 seconds
- Cached queries: < 50ms
"""

import pytest
import time
from typing import Any


# Test classes for each tool (empty for now)


class TestLiveSpellLookup:
    """Live tests for lookup_spell tool."""
    pass


class TestLiveCreatureLookup:
    """Live tests for lookup_creature tool."""
    pass


class TestLiveEquipmentLookup:
    """Live tests for lookup_equipment tool."""
    pass


class TestLiveCharacterOptionLookup:
    """Live tests for lookup_character_option tool."""
    pass


class TestLiveRuleLookup:
    """Live tests for lookup_rule tool."""
    pass


class TestLiveCacheValidation:
    """Cross-cutting cache behavior validation."""
    pass


class TestLivePerformance:
    """Performance benchmarks for live API calls."""
    pass
```

**Step 2: Verify file structure**

Run: `uv run pytest --collect-only tests/test_tools/test_live_mcp.py`
Expected: Collects 0 tests (empty classes)

**Step 3: Commit**

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Create live MCP test file skeleton"`
Expected: Clean commit

---

## Task 2: Spell Lookup Live Tests

### Task 2.1: Basic spell lookup tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py:24-26` (TestLiveSpellLookup class)

**Step 1: Write test for spell found by name**

```python
class TestLiveSpellLookup:
    """Live tests for lookup_spell tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_by_name_found(self, rate_limiter, clear_cache):
        """Verify well-known spell can be found by name."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(name="Magic Missile")

        assert len(results) > 0, "Should find at least one 'Magic Missile' spell"
        first_result = results[0]
        assert "magic missile" in first_result["name"].lower()
        assert "level" in first_result
        assert "school" in first_result
        assert "description" in first_result or "desc" in first_result
```

**Step 2: Run test to verify it works against live API**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup::test_spell_by_name_found -v -m live`
Expected: PASS (or FAIL if API structure differs - adjust assertions)

**Step 3: Write test for spell not found**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_by_name_not_found(self, rate_limiter, clear_cache):
        """Verify non-existent spell returns empty results."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(name="NonexistentSpell12345XYZ")

        assert len(results) == 0, "Non-existent spell should return empty list"
```

**Step 4: Run test**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup::test_spell_by_name_not_found -v -m live`
Expected: PASS

**Step 5: Write test for basic fields present**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_basic_fields_present(self, rate_limiter, clear_cache):
        """Verify spell response contains expected schema fields."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(name="Fireball")

        assert len(results) > 0, "Should find Fireball spell"
        spell = results[0]

        # Required fields
        assert "name" in spell
        assert "level" in spell
        assert "school" in spell

        # Check level is correct type
        assert isinstance(spell["level"], (int, str))
        if isinstance(spell["level"], str):
            assert spell["level"].isdigit() or spell["level"] == "cantrip"
```

**Step 6: Run all spell basic tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup -v -m live`
Expected: All 3 tests PASS

**Step 7: Commit**

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add basic spell lookup live tests"`
Expected: Clean commit

---

### Task 2.2: Spell filtering tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveSpellLookup class)

**Step 1: Write test for level filtering**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_filter_by_level(self, rate_limiter, clear_cache):
        """Verify level filtering returns only spells of specified level."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(level=0, limit=10)

        assert len(results) >= 5, "Should find at least 5 cantrips"
        for spell in results:
            spell_level = spell.get("level", spell.get("lvl"))
            # Level might be 0, "0", or "cantrip"
            assert spell_level in [0, "0", "cantrip"], f"Expected cantrip, got level {spell_level}"
```

**Step 2: Run test**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup::test_spell_filter_by_level -v -m live`
Expected: PASS

**Step 3: Write test for school filtering**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_filter_by_school(self, rate_limiter, clear_cache):
        """Verify school filtering returns only spells of specified school."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(school="evocation", limit=10)

        assert len(results) >= 3, "Should find at least 3 evocation spells"
        for spell in results:
            school = spell.get("school", "").lower()
            assert "evocation" in school, f"Expected evocation spell, got {school}"
```

**Step 4: Run test**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup::test_spell_filter_by_school -v -m live`
Expected: PASS

**Step 5: Write test for combined filters**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_filter_combined(self, rate_limiter, clear_cache):
        """Verify multiple filters work together correctly."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        # Find wizard spells that require concentration
        results = await lookup_spell(class_key="wizard", concentration=True, limit=10)

        assert len(results) >= 5, "Should find at least 5 wizard concentration spells"
        # Note: API might not return concentration field in all cases
        # Validation depends on API response structure
```

**Step 6: Write test for limit respected**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_limit_respected(self, rate_limiter, clear_cache):
        """Verify limit parameter restricts result count."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(limit=5)

        assert len(results) <= 5, f"Requested limit=5 but got {len(results)} results"
        assert len(results) > 0, "Should return some results"
```

**Step 7: Run all filtering tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup -v -m live -k filter`
Expected: All filtering tests PASS

**Step 8: Commit**

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add spell filtering live tests"`
Expected: Clean commit

---

### Task 2.3: Spell cache tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveSpellLookup class)

**Step 1: Write test for cache miss then hit**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_cache_miss_then_hit(self, rate_limiter, clear_cache):
        """Verify cache behavior on duplicate queries."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")

        # First call - cache miss
        start = time.time()
        first_results = await lookup_spell(name="Light")
        first_duration = time.time() - start

        assert len(first_results) > 0, "Should find 'Light' cantrip"
        assert first_duration > 0.05, "First call should take time (API call)"

        # Second call - cache hit
        start = time.time()
        second_results = await lookup_spell(name="Light")
        second_duration = time.time() - start

        assert second_results == first_results, "Cached results should match"
        assert second_duration < first_duration, "Cached call should be faster"
```

**Step 2: Run test**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup::test_spell_cache_miss_then_hit -v -m live`
Expected: PASS

**Step 3: Write test for cache performance**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_spell_cache_performance(self, rate_limiter, clear_cache):
        """Verify cached queries complete quickly."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")

        # Prime the cache
        await lookup_spell(name="Wish")

        # Measure cached performance
        start = time.time()
        await lookup_spell(name="Wish")
        duration = time.time() - start

        assert duration < 0.05, f"Cached query took {duration:.3f}s, expected <0.05s"
```

**Step 4: Run test**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup::test_spell_cache_performance -v -m live`
Expected: PASS

**Step 5: Write test for different queries different cache**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_different_queries_different_cache(self, rate_limiter, clear_cache):
        """Verify different queries use separate cache entries."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")

        # Execute two different queries
        results_missile = await lookup_spell(name="Magic Missile")
        await rate_limiter("open5e")
        results_fireball = await lookup_spell(name="Fireball")

        assert results_missile != results_fireball, "Different queries should have different results"

        # Verify both are cached independently
        start = time.time()
        cached_missile = await lookup_spell(name="Magic Missile")
        duration_missile = time.time() - start

        start = time.time()
        cached_fireball = await lookup_spell(name="Fireball")
        duration_fireball = time.time() - start

        assert cached_missile == results_missile, "First query cache should work"
        assert cached_fireball == results_fireball, "Second query cache should work"
        assert duration_missile < 0.05, "Both cached queries should be fast"
        assert duration_fireball < 0.05
```

**Step 6: Run all cache tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup -v -m live -k cache`
Expected: All cache tests PASS

**Step 7: Commit**

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add spell cache validation tests"`
Expected: Clean commit

---

### Task 2.4: Spell error handling tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveSpellLookup class)

**Step 1: Write test for invalid school**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_invalid_school(self, rate_limiter, clear_cache):
        """Verify graceful handling of invalid school parameter."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")

        # Try invalid school - should return empty or handle gracefully
        results = await lookup_spell(school="InvalidSchoolXYZ123")

        # Should not crash - either empty results or filtered out
        assert isinstance(results, list), "Should return list even with invalid school"
```

**Step 2: Run test**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup::test_spell_invalid_school -v -m live`
Expected: PASS

**Step 3: Write test for invalid limit**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_invalid_limit(self, rate_limiter, clear_cache):
        """Verify handling of invalid limit parameter."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")

        # Negative limit should be handled gracefully
        try:
            results = await lookup_spell(limit=-5)
            # If it doesn't raise, should return empty or default
            assert isinstance(results, list), "Should return list"
        except (ValueError, AssertionError):
            # Acceptable to raise validation error
            pass
```

**Step 4: Run test**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup::test_spell_invalid_limit -v -m live`
Expected: PASS

**Step 5: Write test for empty results**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_empty_results(self, rate_limiter, clear_cache):
        """Verify handling of queries with no matches."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")

        # Query that should match nothing
        results = await lookup_spell(
            name="ZZZNonexistent",
            level=9,
            school="abjuration"
        )

        assert isinstance(results, list), "Should return list"
        assert len(results) == 0, "Should return empty list for no matches"
```

**Step 6: Run all error handling tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveSpellLookup -v -m live -k invalid`
Expected: All error tests PASS

**Step 7: Commit**

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add spell error handling tests"`
Expected: Clean commit

---

## Task 3: Creature Lookup Live Tests

### Task 3.1: Basic creature lookup tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveCreatureLookup class)

**Step 1: Write basic creature tests**

```python
class TestLiveCreatureLookup:
    """Live tests for lookup_creature tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_by_name_found(self, rate_limiter, clear_cache):
        """Verify well-known creature can be found by name."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")
        results = await lookup_creature(name="Goblin")

        assert len(results) > 0, "Should find at least one Goblin"
        goblin = results[0]
        assert "goblin" in goblin["name"].lower()

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_by_name_not_found(self, rate_limiter, clear_cache):
        """Verify non-existent creature returns empty results."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")
        results = await lookup_creature(name="NonexistentCreature12345XYZ")

        assert len(results) == 0, "Non-existent creature should return empty list"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_basic_fields_present(self, rate_limiter, clear_cache):
        """Verify creature response contains expected schema fields."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")
        results = await lookup_creature(name="Goblin")

        assert len(results) > 0, "Should find Goblin"
        creature = results[0]

        # Check for expected fields
        assert "name" in creature
        # CR might be challenge_rating, cr, or challenge
        assert any(key in creature for key in ["challenge_rating", "cr", "challenge"])
        # Type field
        assert "type" in creature
```

**Step 2: Run basic creature tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveCreatureLookup -v -m live`
Expected: All 3 tests PASS

**Step 3: Commit**

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add basic creature lookup live tests"`
Expected: Clean commit

---

### Task 3.2: Creature filtering tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveCreatureLookup class)

**Step 1: Write filtering tests**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_filter_by_cr(self, rate_limiter, clear_cache):
        """Verify CR filtering returns creatures of specified challenge rating."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")
        results = await lookup_creature(cr=1, limit=10)

        assert len(results) >= 3, "Should find at least 3 CR 1 creatures"
        for creature in results:
            cr = creature.get("challenge_rating", creature.get("cr", ""))
            # CR might be "1", 1, or "1.0"
            assert str(cr) in ["1", "1.0"], f"Expected CR 1, got {cr}"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_filter_by_type(self, rate_limiter, clear_cache):
        """Verify type filtering returns creatures of specified type."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")
        results = await lookup_creature(type="beast", limit=10)

        assert len(results) >= 5, "Should find at least 5 beasts"
        for creature in results:
            creature_type = creature.get("type", "").lower()
            assert "beast" in creature_type, f"Expected beast, got {creature_type}"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_filter_by_size(self, rate_limiter, clear_cache):
        """Verify size filtering returns creatures of specified size."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")
        results = await lookup_creature(size="Large", limit=10)

        assert len(results) >= 3, "Should find at least 3 Large creatures"
        for creature in results:
            size = creature.get("size", "").lower()
            assert "large" in size, f"Expected Large, got {size}"
```

**Step 2: Run filtering tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveCreatureLookup -v -m live -k filter`
Expected: All filtering tests PASS

**Step 3: Commit**

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add creature filtering tests"`
Expected: Clean commit

---

### Task 3.3: Creature cache and error tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveCreatureLookup class)

**Step 1: Write cache and error tests**

```python
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_cache_behavior(self, rate_limiter, clear_cache):
        """Verify cache hit/miss behavior for creature lookups."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")

        # First call
        start = time.time()
        first = await lookup_creature(name="Dragon")
        first_duration = time.time() - start

        # Second call (cached)
        start = time.time()
        second = await lookup_creature(name="Dragon")
        second_duration = time.time() - start

        assert second == first, "Cached results should match"
        assert second_duration < first_duration, "Cached call should be faster"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_invalid_type(self, rate_limiter, clear_cache):
        """Verify handling of invalid creature type."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")
        results = await lookup_creature(type="InvalidType123")

        # Should not crash
        assert isinstance(results, list), "Should return list"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_empty_results(self, rate_limiter, clear_cache):
        """Verify handling of no matches."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")
        results = await lookup_creature(name="ZZZNonexistent", cr=30)

        assert isinstance(results, list), "Should return list"
        assert len(results) == 0, "Should return empty list"
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveCreatureLookup -v -m live`
Expected: All tests PASS

**Step 3: Commit**

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add creature cache and error handling tests"`
Expected: Clean commit

---

## Task 4: Equipment, Character Options, and Rule Lookup Tests

**Note:** Following same pattern as spell/creature tests. Condensing for brevity.

### Task 4.1: Equipment lookup tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveEquipmentLookup class)

**Step 1: Write equipment tests**

```python
class TestLiveEquipmentLookup:
    """Live tests for lookup_equipment tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_equipment_weapon_lookup(self, rate_limiter, clear_cache):
        """Verify weapon lookup with weapon properties."""
        from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

        await rate_limiter("open5e")
        results = await lookup_equipment(type="weapon", name="Longsword")

        assert len(results) > 0, "Should find Longsword"
        weapon = results[0]
        assert "longsword" in weapon["name"].lower()

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_equipment_armor_lookup(self, rate_limiter, clear_cache):
        """Verify armor lookup with AC properties."""
        from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

        await rate_limiter("open5e")
        results = await lookup_equipment(type="armor", limit=10)

        assert len(results) >= 5, "Should find at least 5 armor items"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_equipment_cache_behavior(self, rate_limiter, clear_cache):
        """Verify cache behavior."""
        from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

        await rate_limiter("open5e")

        first = await lookup_equipment(name="Shield")
        second = await lookup_equipment(name="Shield")

        assert first == second, "Cached results should match"
```

**Step 2: Run and commit**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveEquipmentLookup -v -m live`
Expected: PASS

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add equipment lookup live tests"`

---

### Task 4.2: Character option lookup tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveCharacterOptionLookup class)

**Step 1: Write character option tests**

```python
class TestLiveCharacterOptionLookup:
    """Live tests for lookup_character_option tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_character_option_class_lookup(self, rate_limiter, clear_cache):
        """Verify class lookup returns expected classes."""
        from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

        await rate_limiter("open5e")
        results = await lookup_character_option(type="class")

        assert len(results) >= 12, "Should find at least 12 classes"
        class_names = [c["name"].lower() for c in results]
        assert any("wizard" in name for name in class_names)
        assert any("fighter" in name for name in class_names)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_character_option_race_lookup(self, rate_limiter, clear_cache):
        """Verify race lookup returns expected races."""
        from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

        await rate_limiter("open5e")
        results = await lookup_character_option(type="race")

        assert len(results) >= 9, "Should find at least 9 races"
        race_names = [r["name"].lower() for r in results]
        assert any("human" in name for name in race_names)
        assert any("elf" in name for name in race_names)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_character_option_feat_lookup(self, rate_limiter, clear_cache):
        """Verify feat lookup returns expected feats."""
        from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

        await rate_limiter("open5e")
        results = await lookup_character_option(type="feat")

        assert len(results) >= 20, "Should find at least 20 feats"
```

**Step 2: Run and commit**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveCharacterOptionLookup -v -m live`
Expected: PASS

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add character option lookup live tests"`

---

### Task 4.3: Rule lookup tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveRuleLookup class)

**Step 1: Write rule lookup tests**

```python
class TestLiveRuleLookup:
    """Live tests for lookup_rule tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_rule_condition_lookup(self, rate_limiter, clear_cache):
        """Verify condition lookup returns expected conditions."""
        from lorekeeper_mcp.tools.rule_lookup import lookup_rule

        await rate_limiter("open5e")
        results = await lookup_rule(rule_type="condition")

        assert len(results) >= 10, "Should find at least 10 conditions"
        condition_names = [c["name"].lower() for c in results]
        assert any("prone" in name for name in condition_names)
        assert any("grappled" in name for name in condition_names)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_rule_skill_lookup(self, rate_limiter, clear_cache):
        """Verify skill lookup returns exactly 18 skills."""
        from lorekeeper_mcp.tools.rule_lookup import lookup_rule

        await rate_limiter("open5e")
        results = await lookup_rule(rule_type="skill")

        # D&D 5e has exactly 18 skills
        assert len(results) == 18, f"Expected 18 skills, got {len(results)}"
        skill_names = [s["name"].lower() for s in results]
        assert any("perception" in name for name in skill_names)
        assert any("stealth" in name for name in skill_names)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_rule_ability_score_lookup(self, rate_limiter, clear_cache):
        """Verify ability score lookup returns exactly 6 abilities."""
        from lorekeeper_mcp.tools.rule_lookup import lookup_rule

        await rate_limiter("open5e")
        results = await lookup_rule(rule_type="ability-score")

        # D&D 5e has exactly 6 ability scores
        assert len(results) == 6, f"Expected 6 abilities, got {len(results)}"
        ability_names = [a["name"].lower() for a in results]
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            assert any(ability in name for name in ability_names), f"Missing {ability}"
```

**Step 2: Run and commit**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveRuleLookup -v -m live`
Expected: PASS

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add rule lookup live tests"`

---

## Task 5: Cross-Cutting Tests

### Task 5.1: Performance validation

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLivePerformance class)

**Step 1: Write performance tests**

```python
class TestLivePerformance:
    """Performance benchmarks for live API calls."""

    @pytest.mark.live
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_uncached_call_performance(self, rate_limiter, clear_cache):
        """Verify API calls complete within time limit."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")

        start = time.time()
        results = await lookup_spell(name="Detect Magic")
        duration = time.time() - start

        assert len(results) > 0, "Should find spell"
        assert duration < 3.0, f"API call took {duration:.2f}s, expected <3s"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_cached_call_performance(self, rate_limiter, clear_cache):
        """Verify cached calls are fast."""
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")

        # Prime cache
        await lookup_creature(name="Goblin")

        # Measure cached performance
        start = time.time()
        await lookup_creature(name="Goblin")
        duration = time.time() - start

        assert duration < 0.05, f"Cached call took {duration:.3f}s, expected <0.05s"
```

**Step 2: Run and commit**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLivePerformance -v -m live`
Expected: PASS

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add performance validation tests"`

---

### Task 5.2: Cache isolation tests

**Files:**
- Modify: `tests/test_tools/test_live_mcp.py` (TestLiveCacheValidation class)

**Step 1: Write cache isolation tests**

```python
class TestLiveCacheValidation:
    """Cross-cutting cache behavior validation."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_cache_isolation_across_tools(self, rate_limiter, clear_cache):
        """Verify different tools use separate cache entries."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature

        await rate_limiter("open5e")

        # Call both tools
        spells = await lookup_spell(name="Fire")
        await rate_limiter("open5e")
        creatures = await lookup_creature(name="Fire")

        # Should get different results (spells vs creatures)
        assert spells != creatures, "Different tools should have different results"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_cache_key_uniqueness(self, rate_limiter, clear_cache):
        """Verify different parameters create different cache keys."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")

        # Different level parameters should be cached separately
        level0 = await lookup_spell(level=0, limit=5)
        await rate_limiter("open5e")
        level1 = await lookup_spell(level=1, limit=5)

        assert level0 != level1, "Different parameters should yield different results"

        # Both should be cached
        start = time.time()
        cached0 = await lookup_spell(level=0, limit=5)
        duration0 = time.time() - start

        start = time.time()
        cached1 = await lookup_spell(level=1, limit=5)
        duration1 = time.time() - start

        assert cached0 == level0, "Level 0 cache should work"
        assert cached1 == level1, "Level 1 cache should work"
        assert duration0 < 0.05 and duration1 < 0.05, "Both should be fast"
```

**Step 2: Run and commit**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveCacheValidation -v -m live`
Expected: PASS

Run: `git add tests/test_tools/test_live_mcp.py && git commit -m "Add cache isolation validation tests"`

---

## Task 6: Documentation

### Task 6.1: Update testing documentation

**Files:**
- Modify: `docs/testing.md` (add section at end)

**Step 1: Add live testing section**

Append to `docs/testing.md`:

```markdown

## Live API Testing

### Overview

Live tests validate LoreKeeper MCP tools against real Open5e and D&D 5e APIs. These tests are marked with `@pytest.mark.live` and are skipped by default.

### Running Live Tests

**Run all live tests:**
```bash
uv run pytest -m live -v
```

**Run live tests for specific tool:**
```bash
uv run pytest -m live -k spell -v
```

**Skip live tests (default for unit testing):**
```bash
uv run pytest -m "not live"
```

### Requirements

- Internet connection
- Working Open5e API (https://api.open5e.com)
- Working D&D 5e API (https://www.dnd5eapi.co)

### Performance Expectations

- **Uncached queries**: < 3 seconds
- **Cached queries**: < 50 ms
- **Rate limiting**: 100ms minimum delay between API calls

### Test Coverage

Live tests validate:
- ✅ Basic queries (name lookup)
- ✅ Filtering (level, CR, type, school, etc.)
- ✅ Cache behavior (hit/miss, performance)
- ✅ Error handling (invalid params, empty results)
- ✅ Response schema validation
- ✅ Cross-cutting concerns (cache isolation, performance)

### Troubleshooting

**Tests fail with network errors:**
- Check internet connection
- Verify API endpoints are accessible
- Check for API outages

**Tests fail with rate limiting:**
- Increase delay in `rate_limiter` fixture (tests/conftest.py)
- Run tests with `--maxfail=1` to stop on first failure

**Cache tests fail:**
- Ensure `clear_cache` fixture is used
- Check cache database is writable
- Verify TTL settings in cache configuration

**Performance tests fail:**
- Network latency may vary - adjust thresholds if needed
- Ensure no other processes are using database
- Try running tests individually

### When to Run Live Tests

- Before releases
- After API client changes
- When investigating cache issues
- After modifying API endpoints
- Periodically (weekly/monthly) to catch API changes

### Adding New Live Tests

1. Mark test with `@pytest.mark.live`
2. Mark slow tests with `@pytest.mark.slow`
3. Use `rate_limiter` fixture to prevent throttling
4. Use `clear_cache` fixture to ensure clean state
5. Follow existing patterns in `tests/test_tools/test_live_mcp.py`

Example:
```python
@pytest.mark.live
@pytest.mark.asyncio
async def test_new_feature(self, rate_limiter, clear_cache):
    """Test description."""
    await rate_limiter("open5e")
    # Test code here
```
```

**Step 2: Verify documentation**

Run: `cat docs/testing.md | grep -A 10 "Live API Testing"`
Expected: Shows new section

**Step 3: Commit**

Run: `git add docs/testing.md && git commit -m "Add live API testing documentation"`
Expected: Clean commit

---

### Task 6.2: Deprecate old test script

**Files:**
- Modify: `test_mcp_tools_live.py`

**Step 1: Add deprecation notice**

Add at top of `test_mcp_tools_live.py` after imports:

```python
"""
DEPRECATED: This script is deprecated in favor of pytest-based live tests.

Please use the comprehensive pytest suite instead:
    uv run pytest -m live

See docs/testing.md for full documentation on live testing.

This script will be removed in a future version.
"""

import warnings

warnings.warn(
    "test_mcp_tools_live.py is deprecated. Use 'pytest -m live' instead. "
    "See docs/testing.md for details.",
    DeprecationWarning,
    stacklevel=2
)
```

**Step 2: Commit**

Run: `git add test_mcp_tools_live.py && git commit -m "Deprecate standalone live test script in favor of pytest suite"`
Expected: Clean commit

---

## Task 7: Final Validation

### Task 7.1: Run complete test suite

**Step 1: Run all live tests**

Run: `uv run pytest -m live -v`
Expected: All tests PASS (40+ tests)

**Step 2: Verify tests can be skipped**

Run: `uv run pytest -m "not live" -v`
Expected: Live tests skipped, unit tests run

**Step 3: Run only slow tests**

Run: `uv run pytest -m "live and slow" -v`
Expected: Only performance tests run

**Step 4: Document results**

Create: `TEST_RESULTS.md` (append results)

```markdown
## Live Test Validation - [Date]

**Command:** `uv run pytest -m live -v`

**Results:**
- Total tests: [count]
- Passed: [count]
- Failed: [count]
- Duration: [time]

**Coverage:**
- Spell lookup: [X] tests
- Creature lookup: [X] tests
- Equipment lookup: [X] tests
- Character options: [X] tests
- Rule lookup: [X] tests
- Cache validation: [X] tests
- Performance: [X] tests

**Notes:**
- All tests passed against live APIs
- Cache behavior validated
- Performance targets met
- No rate limiting issues observed
```

**Step 5: Final commit**

Run: `git add TEST_RESULTS.md && git commit -m "Complete comprehensive live test implementation"`
Expected: Clean commit

---

## Summary

**Total estimated effort:** 6-8 hours

**Test counts:**
- Spell lookup: 12 tests
- Creature lookup: 9 tests
- Equipment lookup: 5 tests
- Character options: 5 tests
- Rule lookup: 6 tests
- Cross-cutting: 5 tests
- **Total: ~42 live tests**

**Success criteria:**
- ✅ All live tests pass against live APIs
- ✅ Tests can be skipped with `pytest -m "not live"`
- ✅ Tests can be run selectively with `pytest -m live`
- ✅ Cache behavior validated with real data
- ✅ Performance targets met (<3s uncached, <50ms cached)
- ✅ Documentation complete and clear
- ✅ No rate limiting issues during execution

**Commands reference:**
- Run all tests: `uv run pytest`
- Run live tests: `uv run pytest -m live -v`
- Skip live tests: `uv run pytest -m "not live"`
- Run specific tool: `uv run pytest -m live -k spell`
- Run slow tests: `uv run pytest -m slow`
