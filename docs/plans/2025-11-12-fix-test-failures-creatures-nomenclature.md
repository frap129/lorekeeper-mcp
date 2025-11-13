# Fix Test Failures: Creatures Nomenclature & Cache Isolation

**Goal:** Fix all 46 failing tests by migrating from Open5e v1 monsters to v2 creatures and resolving test isolation issues.

**Architecture:** The project currently uses Open5e v1 `/monsters/` endpoint which is deprecated/empty. We need to migrate to v2 `/creatures/` endpoint. Additionally, a singleton cache in RepositoryFactory persists across tests causing isolation failures. The fix involves updating the API client, database table references, schema, and test fixtures.

**Tech Stack:** Python 3.11+, pytest, aiosqlite, Open5e API v2, httpx

---

## Background

**Test Failures:**
- 12 integration tests fail with `sqlite3.OperationalError: no such table` (cache isolation bug)
- 34 live tests return empty results (wrong API endpoint)

**Root Causes:**
1. MonsterRepository uses Open5eV1Client which calls `/v1/monsters/` (deprecated)
2. Should use Open5eV2Client calling `/v2/creatures/` (current)
3. RepositoryFactory._cache_instance singleton persists across tests
4. Schema has both "monsters" and "creatures" tables but code uses wrong one

---

## Task 1: Add Challenge Rating Index to Creatures Schema

**Files:**
- Modify: `src/lorekeeper_mcp/cache/schema.py:115-118`
- Test: Run existing tests to verify schema change doesn't break anything

**Step 1: Update creatures indexed fields**

In `src/lorekeeper_mcp/cache/schema.py`, find the "creatures" entry in INDEXED_FIELDS (around line 115) and update it:

```python
    # Task 1.7: Creatures
    "creatures": [
        ("challenge_rating", "REAL"),  # ADD THIS LINE
        ("type", "TEXT"),
        ("size", "TEXT"),
    ],
```

**Step 2: Verify schema change**

Run: `uv run pytest tests/test_cache/test_schema.py -v`
Expected: All schema tests PASS

**Step 3: Commit schema update**

```bash
git add src/lorekeeper_mcp/cache/schema.py
git commit -m "fix(schema): add challenge_rating index to creatures table"
```

---

## Task 2: Update MonsterRepository to Use Creatures Table

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/monster.py:58,68,85`
- Test: `tests/test_repositories/test_monster.py`

**Step 1: Write failing test for creatures table usage**

In `tests/test_repositories/test_monster.py`, add at the end before existing tests:

```python
@pytest.mark.asyncio
async def test_repository_uses_creatures_table(mock_cache):
    """Verify MonsterRepository uses 'creatures' table not 'monsters'."""
    from lorekeeper_mcp.repositories.monster import MonsterRepository

    mock_client = AsyncMock()
    mock_client.get_creatures = AsyncMock(return_value=[])

    repository = MonsterRepository(client=mock_client, cache=mock_cache)
    await repository.get_all()

    # Verify cache was called with "creatures" not "monsters"
    mock_cache.get_entities.assert_called_once_with("creatures")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repositories/test_monster.py::test_repository_uses_creatures_table -v`
Expected: FAIL - cache called with "monsters" not "creatures"

**Step 3: Update MonsterRepository get_all method**

In `src/lorekeeper_mcp/repositories/monster.py`, update line 58:

```python
    async def get_all(self) -> list[Monster]:
        """Retrieve all monsters using cache-aside pattern.

        Returns:
            List of all Monster objects
        """
        # Try cache first
        cached = await self.cache.get_entities("creatures")  # CHANGED from "monsters"

        if cached:
            return [Monster.model_validate(monster) for monster in cached]

        # Cache miss - fetch from API
        monsters: list[Monster] = await self.client.get_creatures()  # CHANGED from get_monsters

        # Store in cache
        monster_dicts = [monster.model_dump() for monster in monsters]
        await self.cache.store_entities(monster_dicts, "creatures")  # CHANGED from "monsters"

        return monsters
```

**Step 4: Update MonsterRepository search method**

In `src/lorekeeper_mcp/repositories/monster.py`, update line 85 and surrounding code:

```python
    async def search(self, **filters: Any) -> list[Monster]:
        """Search for monsters with optional filters using cache-aside pattern.

        Args:
            **filters: Optional filters (type, size, challenge_rating, etc.)

        Returns:
            List of Monster objects matching the filters
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("creatures", **filters)  # CHANGED from "monsters"

        if cached:
            results = [Monster.model_validate(monster) for monster in cached]
            return results[:limit] if limit else results

        # Cache miss - fetch from API with filters and limit
        api_params = self._map_to_api_params(**filters)
        monsters: list[Monster] = await self.client.get_creatures(limit=limit, **api_params)  # CHANGED from get_monsters

        # Store in cache if we got results
        if monsters:
            monster_dicts = [monster.model_dump() for monster in monsters]
            await self.cache.store_entities(monster_dicts, "creatures")  # CHANGED from "monsters"

        return monsters
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_repositories/test_monster.py::test_repository_uses_creatures_table -v`
Expected: PASS

**Step 6: Run all monster repository tests**

Run: `uv run pytest tests/test_repositories/test_monster.py -v`
Expected: Some tests may fail because mock client doesn't have get_creatures method yet

**Step 7: Commit repository update**

```bash
git add src/lorekeeper_mcp/repositories/monster.py tests/test_repositories/test_monster.py
git commit -m "fix(repository): use creatures table instead of monsters"
```

---

## Task 3: Add get_creatures Method to MonsterClient Protocol

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/monster.py:11-16`
- Test: `tests/test_repositories/test_monster.py`

**Step 1: Update MonsterClient protocol**

In `src/lorekeeper_mcp/repositories/monster.py`, update the protocol (lines 11-16):

```python
class MonsterClient(Protocol):
    """Protocol for monster API client."""

    async def get_creatures(self, **filters: Any) -> list[Monster]:
        """Fetch creatures from API with optional filters."""
        ...
```

**Step 2: Verify tests still work**

Run: `uv run pytest tests/test_repositories/test_monster.py -v`
Expected: Tests should pass (protocol change is compatible)

**Step 3: Commit protocol update**

```bash
git add src/lorekeeper_mcp/repositories/monster.py
git commit -m "fix(protocol): update MonsterClient to use get_creatures"
```

---

## Task 4: Update Open5eV1Client to Support get_creatures

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/open5e_v1.py:20-48`
- Test: `tests/test_api_clients/test_open5e_v1.py`

**Step 1: Add get_creatures alias method**

In `src/lorekeeper_mcp/api_clients/open5e_v1.py`, add after the get_monsters method (around line 48):

```python
    async def get_creatures(
        self,
        challenge_rating: str | None = None,
        **filters: Any,
    ) -> list[Monster]:
        """Get creatures from Open5e API v1 (alias for get_monsters).

        This method exists for protocol compatibility. V1 uses /monsters/ endpoint,
        while v2 uses /creatures/ endpoint. Both return Monster models.

        Args:
            challenge_rating: Filter by CR (e.g., "1/4", "5")
            **filters: Additional API parameters

        Returns:
            List of Monster models
        """
        return await self.get_monsters(challenge_rating=challenge_rating, **filters)
```

**Step 2: Write test for get_creatures**

In `tests/test_api_clients/test_open5e_v1.py`, add test after existing monster tests:

```python
@pytest.mark.asyncio
@respx.mock
async def test_get_creatures_alias(client):
    """Test get_creatures is an alias for get_monsters."""
    mock_response = {
        "results": [
            {
                "name": "Goblin",
                "slug": "goblin",
                "size": "Small",
                "type": "humanoid",
                "alignment": "neutral evil",
                "armor_class": 15,
                "hit_points": 7,
                "hit_dice": "2d6",
                "challenge_rating": "1/4",
                "strength": 8,
                "dexterity": 14,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 8,
                "charisma": 8,
                "speed": {"walk": 30},
                "document_url": "https://example.com",
            }
        ]
    }

    respx.get("https://api.open5e.com/v1/monsters/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    creatures = await client.get_creatures(challenge_rating="1/4")

    assert len(creatures) == 1
    assert creatures[0].name == "Goblin"
    assert creatures[0].challenge_rating == "1/4"
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/test_api_clients/test_open5e_v1.py::test_get_creatures_alias -v`
Expected: PASS

**Step 4: Commit v1 client update**

```bash
git add src/lorekeeper_mcp/api_clients/open5e_v1.py tests/test_api_clients/test_open5e_v1.py
git commit -m "feat(client): add get_creatures alias to Open5eV1Client"
```

---

## Task 5: Update MonsterRepository API Parameter Mapping for V2

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/monster.py:102-136`
- Test: `tests/test_repositories/test_monster.py`

**Step 1: Write test for v2 parameter mapping**

In `tests/test_repositories/test_monster.py`, add test:

```python
@pytest.mark.asyncio
async def test_repository_maps_v2_challenge_rating_params(mock_cache):
    """Verify repository maps cr_min/cr_max to v2 parameters."""
    from lorekeeper_mcp.repositories.monster import MonsterRepository
    from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
    from unittest.mock import AsyncMock

    mock_v2_client = AsyncMock(spec=Open5eV2Client)
    mock_v2_client.get_creatures = AsyncMock(return_value=[])

    mock_cache.get_entities = AsyncMock(return_value=[])

    repository = MonsterRepository(client=mock_v2_client, cache=mock_cache)
    await repository.search(cr_min=5, cr_max=10)

    # Verify v2 client was called with correct decimal parameters
    call_kwargs = mock_v2_client.get_creatures.call_args.kwargs
    assert call_kwargs.get("challenge_rating_decimal__gte") == 5
    assert call_kwargs.get("challenge_rating_decimal__lte") == 10
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repositories/test_monster.py::test_repository_maps_v2_challenge_rating_params -v`
Expected: FAIL - parameters not mapped correctly

**Step 3: Update _map_to_api_params method**

In `src/lorekeeper_mcp/repositories/monster.py`, replace the entire `_map_to_api_params` method (around line 102):

```python
    def _map_to_api_params(self, **filters: Any) -> dict[str, Any]:
        """Map repository parameters to API-specific filter operators.

        Converts repository-level filter parameters to API-specific operators
        based on the client type. Open5e v2 uses operators like `challenge_rating_decimal__gte`
        and `challenge_rating_decimal__lte`, while v1 uses `challenge_rating`.

        Args:
            **filters: Repository-level filter parameters

        Returns:
            Dictionary of API-specific parameters ready for API calls
        """
        params: dict[str, Any] = {}

        if isinstance(self.client, Open5eV2Client):
            # Map to Open5e v2 filter operators
            if "armor_class_min" in filters:
                params["armor_class__gte"] = filters["armor_class_min"]
            if "hit_points_min" in filters:
                params["hit_points__gte"] = filters["hit_points_min"]
            if "cr_min" in filters:
                params["challenge_rating_decimal__gte"] = filters["cr_min"]
            if "cr_max" in filters:
                params["challenge_rating_decimal__lte"] = filters["cr_max"]
            # Pass through exact matches
            for key in ["type", "size", "challenge_rating"]:
                if key in filters:
                    params[key] = filters[key]

        elif isinstance(self.client, Open5eV1Client):
            # V1 API: pass through filters as-is
            params = dict(filters)

        else:
            # For unknown client types, pass through filters as-is
            params = dict(filters)

        return params
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_repositories/test_monster.py::test_repository_maps_v2_challenge_rating_params -v`
Expected: PASS

**Step 5: Run all monster repository tests**

Run: `uv run pytest tests/test_repositories/test_monster.py -v`
Expected: All tests PASS

**Step 6: Commit parameter mapping update**

```bash
git add src/lorekeeper_mcp/repositories/monster.py tests/test_repositories/test_monster.py
git commit -m "fix(repository): map cr_min/max to v2 decimal parameters"
```

---

## Task 6: Update RepositoryFactory to Use Open5eV2Client

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/factory.py:70-87`
- Test: `tests/test_repositories/test_factory.py`

**Step 1: Write test for v2 client default**

In `tests/test_repositories/test_factory.py`, find the test for monster repository creation and update/add:

```python
def test_create_monster_repository_default_uses_v2():
    """Test that create_monster_repository uses Open5eV2Client by default."""
    from lorekeeper_mcp.repositories.factory import RepositoryFactory
    from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

    # Clear any cached instance
    RepositoryFactory._cache_instance = None

    repo = RepositoryFactory.create_monster_repository()

    assert isinstance(repo.client, Open5eV2Client)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repositories/test_factory.py::test_create_monster_repository_default_uses_v2 -v`
Expected: FAIL - currently uses Open5eV1Client

**Step 3: Update factory to use Open5eV2Client**

In `src/lorekeeper_mcp/repositories/factory.py`, update imports (add Open5eV2Client, keep V1 for backward compat):

```python
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
```

Then update the `create_monster_repository` method (around line 70):

```python
    @staticmethod
    def create_monster_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> MonsterRepository:
        """Create a MonsterRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to shared SQLiteCache.

        Returns:
            A configured MonsterRepository instance.
        """
        if client is None:
            client = Open5eV2Client()  # CHANGED from Open5eV1Client
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return MonsterRepository(client=client, cache=cache)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_repositories/test_factory.py::test_create_monster_repository_default_uses_v2 -v`
Expected: PASS

**Step 5: Run all factory tests**

Run: `uv run pytest tests/test_repositories/test_factory.py -v`
Expected: All tests PASS

**Step 6: Commit factory update**

```bash
git add src/lorekeeper_mcp/repositories/factory.py tests/test_repositories/test_factory.py
git commit -m "fix(factory): use Open5eV2Client for monster repository"
```

---

## Task 7: Fix Test Isolation - Clear RepositoryFactory Cache

**Files:**
- Modify: `tests/test_tools/conftest.py:10-26`
- Test: Run integration tests to verify isolation

**Step 1: Update cleanup fixture**

In `tests/test_tools/conftest.py`, update the `cleanup_tool_contexts` fixture:

```python
@pytest.fixture(autouse=True)
def cleanup_tool_contexts():
    """Clear all tool repository contexts after each test."""
    from lorekeeper_mcp.tools import (
        character_option_lookup,
        creature_lookup,
        equipment_lookup,
        rule_lookup,
        spell_lookup,
    )
    from lorekeeper_mcp.repositories.factory import RepositoryFactory

    yield
    spell_lookup._repository_context.clear()
    creature_lookup._repository_context.clear()
    character_option_lookup._repository_context.clear()
    equipment_lookup._repository_context.clear()
    rule_lookup._repository_context.clear()

    # Clear the factory cache singleton to prevent test isolation issues
    RepositoryFactory._cache_instance = None
```

**Step 2: Run integration tests to verify fix**

Run: `uv run pytest tests/test_tools/test_integration.py -v`
Expected: All 17 integration tests PASS (no more "no such table" errors)

**Step 3: Commit test isolation fix**

```bash
git add tests/test_tools/conftest.py
git commit -m "fix(tests): clear RepositoryFactory cache for test isolation"
```

---

## Task 8: Update Test Mocks to Use get_creatures

**Files:**
- Modify: `tests/test_tools/conftest.py:55-87`
- Test: Run tool tests to verify mocks work

**Step 1: Update mock_open5e_v1_client fixture**

In `tests/test_tools/conftest.py`, update the fixture (around line 55):

```python
@pytest.fixture
def mock_open5e_v1_client():
    """Mock Open5eV1Client."""
    # Convert dict response to Monster models for get_creatures
    monster_obj = Monster(
        name="Ancient Red Dragon",
        slug="ancient-red-dragon",
        desc="A large red dragon",
        size="Gargantuan",
        type="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+252",
        strength=30,
        dexterity=10,
        constitution=29,
        intelligence=18,
        wisdom=15,
        charisma=23,
        challenge_rating="24",
        speed={"walk": 40, "climb": 40, "fly": 80},
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        document_url="https://example.com/dragon",
    )

    client = MagicMock()
    client.get_monsters = AsyncMock(return_value=[monster_obj])
    client.get_creatures = AsyncMock(return_value=[monster_obj])  # ADD THIS LINE
    client.get_classes = AsyncMock(return_value={"count": 0, "results": []})
    client.get_races = AsyncMock(return_value={"count": 0, "results": []})
    client.get_magic_items = AsyncMock(return_value={"count": 0, "results": []})
    return client
```

**Step 2: Update mock_open5e_v2_client fixture**

In `tests/test_tools/conftest.py`, update the fixture (around line 90):

```python
@pytest.fixture
def mock_open5e_v2_client(mock_spell_response):
    """Mock Open5eV2Client."""
    # Convert dict response to Spell models for get_spells
    spell_obj = Spell(
        name="Fireball",
        slug="fireball",
        level=3,
        school="evocation",
        casting_time="1 action",
        range="150 feet",
        components="V,S,M",
        material="a tiny ball of bat guano and sulfur",
        duration="Instantaneous",
        concentration=False,
        ritual=False,
        desc="A bright streak flashes...",
        document_url="https://example.com/fireball",
        higher_level="When you cast this spell...",
        damage_type=None,
    )

    client = MagicMock()
    client.get_spells = AsyncMock(return_value=[spell_obj])
    client.get_creatures = AsyncMock(return_value=[])  # ADD THIS LINE
    client.get_backgrounds = AsyncMock(return_value=[])
    client.get_feats = AsyncMock(return_value=[])
    client.get_weapons = AsyncMock(return_value=[])
    client.get_armor = AsyncMock(return_value=[])
    client.get_conditions = AsyncMock(return_value=[])
    return client
```

**Step 3: Run tool tests to verify mocks**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py -v`
Expected: All tests PASS

**Step 4: Commit mock updates**

```bash
git add tests/test_tools/conftest.py
git commit -m "fix(tests): add get_creatures to mock clients"
```

---

## Task 9: Run All Tests to Verify Fixes

**Files:**
- Test: All test files

**Step 1: Run full test suite**

Run: `just test`
Expected: All tests PASS except live tests (they need actual API)

**Step 2: Check for any remaining failures**

If any tests fail, investigate and fix. Common issues:
- Mock methods not matching actual API
- Cache table name mismatches
- Missing imports

**Step 3: Run integration tests specifically**

Run: `uv run pytest tests/test_tools/test_integration.py -v`
Expected: All 17 integration tests PASS (previously 12 failed)

**Step 4: Document the changes**

Create a summary of what was fixed:
- Migrated from Open5e v1 monsters to v2 creatures
- Fixed test isolation by clearing RepositoryFactory cache
- Updated schema to include challenge_rating for creatures
- Updated all repository and client code

---

## Task 10: Run Live Tests to Verify API Integration

**Files:**
- Test: `tests/test_tools/test_live_mcp.py`

**Step 1: Run live creature lookup tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py::TestLiveCreatureLookup -v --tb=short`
Expected: Tests PASS (creatures now returned from API)

**Step 2: Run all live tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py -v`
Expected: All 34 live tests PASS

**Step 3: If any live tests fail, debug**

Common issues:
- API rate limiting (wait between tests)
- API structure changes (verify response format)
- Network issues (retry)

**Step 4: Commit final verification**

```bash
git add -A
git commit -m "test: verify all live tests pass with creatures endpoint"
```

---

## Task 11: Update Documentation

**Files:**
- Modify: `docs/apis/open5e-api.md`
- Modify: `docs/architecture.md`
- Create: `docs/migrations/2025-11-12-monsters-to-creatures.md`

**Step 1: Document the migration**

Create `docs/migrations/2025-11-12-monsters-to-creatures.md`:

```markdown
# Migration: Monsters to Creatures (Open5e v1 → v2)

## Date
2025-11-12

## Summary
Migrated MonsterRepository from Open5e API v1 `/monsters/` endpoint to v2 `/creatures/` endpoint.

## Changes

### API Clients
- **RepositoryFactory**: Now uses `Open5eV2Client` by default for monster repository
- **Open5eV1Client**: Added `get_creatures()` alias method for backward compatibility
- **Open5eV2Client**: Already had `get_creatures()` method

### Database Schema
- **creatures table**: Added `challenge_rating` indexed field (was missing)
- **monsters table**: Kept for backward compatibility but no longer used by default

### Repositories
- **MonsterRepository**:
  - Changed from `"monsters"` to `"creatures"` table
  - Updated `get_all()` and `search()` methods
  - Added v2 parameter mapping for `cr_min`/`cr_max` → `challenge_rating_decimal__gte`/`lte`

### Tests
- Fixed test isolation by clearing `RepositoryFactory._cache_instance`
- Updated mock clients to include `get_creatures()` method

## Migration Path

### For Users
No action required. The change is transparent.

### For Developers
If you have custom code using MonsterRepository:
- Repository now uses `"creatures"` table by default
- API client defaults to Open5eV2Client
- To use v1 explicitly: `RepositoryFactory.create_monster_repository(client=Open5eV1Client())`

## Testing
- All 17 integration tests pass
- All 34 live tests pass
- No breaking changes to public API
```

**Step 2: Update architecture docs**

In `docs/architecture.md`, find the section on repositories and update to mention creatures:

```markdown
### Monster/Creature Repository

The MonsterRepository handles D&D creature data from Open5e API v2. It:
- Uses the `/v2/creatures/` endpoint (v1 `/monsters/` is deprecated)
- Caches results in the `creatures` database table
- Supports filtering by CR, type, size, armor class, and hit points
- Maps repository parameters to API-specific operators
```

**Step 3: Update API documentation**

In `docs/apis/open5e-api.md`, update the section on monsters/creatures:

```markdown
### Creatures (formerly Monsters)

**Endpoint**: `https://api.open5e.com/v2/creatures/`

**Current**: Open5e v2 uses "creatures" nomenclature
**Legacy**: Open5e v1 used "monsters" (deprecated)

**Note**: Both refer to the same entity type. Our codebase uses:
- Database table: `creatures`
- API client: `Open5eV2Client.get_creatures()`
- Repository: `MonsterRepository` (name kept for compatibility)
```

**Step 4: Commit documentation updates**

```bash
git add docs/migrations/2025-11-12-monsters-to-creatures.md docs/architecture.md docs/apis/open5e-api.md
git commit -m "docs: document monsters to creatures migration"
```

---

## Task 12: Final Verification and Cleanup

**Files:**
- All files

**Step 1: Run complete test suite**

Run: `just test`
Expected: All tests PASS

**Step 2: Run linting and type checks**

Run: `just check`
Expected: No errors

**Step 3: Verify live tests one more time**

Run: `uv run pytest tests/test_tools/test_live_mcp.py -v --tb=short`
Expected: All 34 tests PASS

**Step 4: Review all commits**

Run: `git log --oneline -20`
Expected: Clean, descriptive commit messages following conventional commits

**Step 5: Create summary of changes**

Summary:
- Fixed 12 integration test failures (cache isolation bug)
- Fixed 34 live test failures (wrong API endpoint)
- Migrated from Open5e v1 monsters to v2 creatures
- Updated schema, repository, factory, and tests
- All 46 previously failing tests now pass
- No breaking changes to public API

---

## Rollback Plan

If issues arise after deployment:

1. **Revert factory to v1**:
   ```python
   # In factory.py
   client = Open5eV1Client()  # Revert from Open5eV2Client
   ```

2. **Revert repository to monsters table**:
   ```python
   # In monster.py
   cached = await self.cache.get_entities("monsters")  # Revert from "creatures"
   ```

3. **Revert commits**:
   ```bash
   git revert HEAD~12..HEAD
   ```

---

## Success Criteria

- ✅ All 395 tests pass (none fail)
- ✅ Live tests return data from API
- ✅ Integration tests don't have "no such table" errors
- ✅ Type checking passes
- ✅ Linting passes
- ✅ Documentation updated
- ✅ No breaking changes to public API

---

## Notes

**Why keep both tables?**
- `monsters` table exists for backward compatibility
- `creatures` table is the new standard
- Future: migrate all old cached data from monsters → creatures

**Why keep MonsterRepository name?**
- Changing class name would break imports
- Name is part of public API
- Future: can add `CreatureRepository = MonsterRepository` alias

**API differences:**
- v1: Uses `challenge_rating` string parameter
- v2: Uses `challenge_rating_decimal__gte/lte` float parameters
- Repository handles mapping automatically
