# Remove Deprecated Features Implementation Plan

**Goal:** Remove deprecated features (Monster alias, SQLite backend, deprecated toggles, clear cache stubs) and standardize tool naming to `search_*` convention while preserving hybrid search architecture.

**Architecture:** The codebase transitions from supporting dual cache backends (SQLite/Milvus) to Milvus-only. The hybrid search architecture is PRESERVED: all tools support both semantic search (`semantic_query`) AND structured filtering parameters. Tools are renamed from `lookup_*` to `search_*` for consistency.

**Tech Stack:** Python 3.11+, Pydantic, Milvus Lite, sentence-transformers

---


## Task 1: Remove Monster Model Alias

**Files:**
- Modify: `src/lorekeeper_mcp/models/creature.py:81-110`
- Modify: `src/lorekeeper_mcp/models/__init__.py:8,17`
- Modify: `tests/test_models/test_creature.py:113-131`

**Step 1: Write failing test to verify Monster removal**

Create test that imports should fail:

```python
# tests/test_models/test_creature.py - add at end of file
def test_monster_import_removed() -> None:
    """Test that Monster class no longer exists."""
    from lorekeeper_mcp.models import Creature

    # Creature should exist
    assert Creature is not None

    # Monster should NOT be importable from models
    with pytest.raises(ImportError):
        from lorekeeper_mcp.models import Monster  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models/test_creature.py::test_monster_import_removed -v`
Expected: FAIL (Monster is still importable)

**Step 3: Remove Monster class from creature.py**

```python
# src/lorekeeper_mcp/models/creature.py
# DELETE lines 80-110 (entire Monster class including import of warnings at line 3)

# Line 3: Remove "import warnings"

# Lines 81-110: DELETE entirely:
# class Monster(Creature):
#     """Deprecated alias for Creature.
#     ...
```

**Step 4: Remove Monster from __init__.py exports**

```python
# src/lorekeeper_mcp/models/__init__.py
# Line 8: Change from:
from lorekeeper_mcp.models.creature import Creature, Monster
# To:
from lorekeeper_mcp.models.creature import Creature

# Lines 12-20: Change __all__ from:
__all__ = [
    "Armor",
    "BaseEntity",
    "Creature",
    "MagicItem",
    "Monster",
    "Spell",
    "Weapon",
]
# To:
__all__ = [
    "Armor",
    "BaseEntity",
    "Creature",
    "MagicItem",
    "Spell",
    "Weapon",
]
```

**Step 5: Remove old Monster deprecation test**

```python
# tests/test_models/test_creature.py
# DELETE lines 113-131 (test_monster_alias_with_deprecation_warning)
# Also remove "import warnings" from line 3
# Also remove "Monster" from import on line 8
```

**Step 6: Run tests to verify changes**

Run: `uv run pytest tests/test_models/test_creature.py -v`
Expected: PASS (Monster removed, new test passes)

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/models/creature.py src/lorekeeper_mcp/models/__init__.py tests/test_models/test_creature.py
git commit -m "feat!: remove deprecated Monster model alias

BREAKING CHANGE: Monster class removed, use Creature instead"
```


---

## Task 2: Remove Deprecated API Client Models Module

**Files:**
- Delete: `src/lorekeeper_mcp/api_clients/models/__init__.py`
- Delete: `src/lorekeeper_mcp/api_clients/models/` (directory)
- Modify: `src/lorekeeper_mcp/api_clients/__init__.py:19-20,25,29,35,36`
- Modify: `tests/test_api_clients/test_models.py:6-12`

**Step 1: Write failing test for api_clients.models removal**

```python
# tests/test_api_clients/test_models.py - add test
def test_api_clients_models_module_removed() -> None:
    """Test that api_clients.models submodule no longer exists."""
    with pytest.raises(ImportError):
        from lorekeeper_mcp.api_clients import models  # noqa: F401

    with pytest.raises(ImportError):
        from lorekeeper_mcp.api_clients.models import Creature  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_clients/test_models.py::test_api_clients_models_module_removed -v`
Expected: FAIL (module still exists)

**Step 3: Delete api_clients/models directory**

```bash
rm -rf src/lorekeeper_mcp/api_clients/models/
```

**Step 4: Remove model re-exports from api_clients/__init__.py**

```python
# src/lorekeeper_mcp/api_clients/__init__.py
# Line 1-4: Keep docstring but update:
"""API clients for external D&D data sources."""

# DELETE lines 19-20:
# # Re-export models for backward compatibility (deprecated)
# from lorekeeper_mcp.models import Armor, Creature, MagicItem, Spell, Weapon

# UPDATE __all__ to remove models (lines 22-37):
__all__ = [
    "ApiClientError",
    "ApiError",
    "BaseHttpClient",
    "CacheError",
    "ClientFactory",
    "NetworkError",
    "Open5eV1Client",
    "Open5eV2Client",
    "ParseError",
]
```

**Step 5: Update test imports to use canonical models**

```python
# tests/test_api_clients/test_models.py
# Lines 6-12: Change from:
from lorekeeper_mcp.models import Armor, Creature, Spell, Weapon
from lorekeeper_mcp.models.base import BaseEntity as BaseModel

# Alias for backward compatibility in tests - these tests are for the Creature model
# but use "monster" terminology which is deprecated
Monster = Creature

# To:
from lorekeeper_mcp.models import Armor, Creature, Spell, Weapon
from lorekeeper_mcp.models.base import BaseEntity as BaseModel
```

**Step 6: Run tests to verify changes**

Run: `uv run pytest tests/test_api_clients/test_models.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add -A
git commit -m "feat!: remove deprecated api_clients.models module

BREAKING CHANGE: Import models from lorekeeper_mcp.models instead of api_clients.models"
```


---

## Task 3: Remove Monster Repository Aliases and Rename File

> **DEPENDENCY**: This task MUST be completed before Task 7 (Simplify lookup_creature).
> Both tasks modify `creature_lookup.py`. Task 3 updates imports to use `CreatureRepository`,
> and Task 7 simplifies the function signature. Complete Task 3 first to avoid merge conflicts.

**Files:**
- Rename: `src/lorekeeper_mcp/repositories/monster.py` → `src/lorekeeper_mcp/repositories/creature.py`
- Modify: `src/lorekeeper_mcp/repositories/creature.py:296-303` (delete aliases)
- Modify: `src/lorekeeper_mcp/repositories/factory.py:9,92-108`
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py:35,40,51`

**Step 1: Write failing test for CreatureRepository import from creature.py**

```python
# tests/test_repositories/test_creature.py - add test
def test_creature_repository_imports_from_creature_module() -> None:
    """Test CreatureRepository imports from repositories.creature not monster."""
    from lorekeeper_mcp.repositories.creature import CreatureRepository
    assert CreatureRepository is not None

    # monster.py should not exist
    with pytest.raises(ImportError):
        from lorekeeper_mcp.repositories.monster import MonsterRepository  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repositories/test_creature.py::test_creature_repository_imports_from_creature_module -v`
Expected: FAIL (creature.py doesn't exist yet)

**Step 3: Rename monster.py to creature.py and remove aliases**

```bash
git mv src/lorekeeper_mcp/repositories/monster.py src/lorekeeper_mcp/repositories/creature.py
```

Then edit `src/lorekeeper_mcp/repositories/creature.py`:
```python
# DELETE lines 296-303 (the backward-compatible aliases):
# # Backward-compatible aliases (deprecated)
# # Note: Protocols cannot be subclassed for deprecation warnings easily,
# # so we just create direct aliases. Users who import Monster* names
# # will get the Creature* classes without warning. The deprecation
# # warning for the Monster model class is in models/creature.py.
# MonsterClient = CreatureClient
# MonsterCache = CreatureCache
# MonsterRepository = CreatureRepository

# UPDATE docstring at line 1-5:
"""Repository for creatures with cache-aside pattern."""
# (remove the note about being formerly named monster.py)
```

**Step 4: Update factory.py imports and method names**

```python
# src/lorekeeper_mcp/repositories/factory.py
# Line 9: Change from:
from lorekeeper_mcp.repositories.monster import MonsterRepository
# To:
from lorekeeper_mcp.repositories.creature import CreatureRepository

# Lines 91-108: Rename method and update return type:
# Change from create_monster_repository to create_creature_repository:
    @staticmethod
    def create_creature_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> CreatureRepository:
        """Create a CreatureRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured CreatureRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return CreatureRepository(client=client, cache=cache)
```

**Step 5: Update creature_lookup.py imports**

```python
# src/lorekeeper_mcp/tools/creature_lookup.py
# Line 35: Change from:
from lorekeeper_mcp.repositories.monster import MonsterRepository
# To:
from lorekeeper_mcp.repositories.creature import CreatureRepository

# Line 40: Change return type annotation:
def _get_repository() -> CreatureRepository:

# Line 49-51: Update cast and factory call:
    if "repository" in _repository_context:
        return cast(CreatureRepository, _repository_context["repository"])
    return RepositoryFactory.create_creature_repository()

# Update docstring references to MonsterRepository -> CreatureRepository
```

**Step 6: Run tests to verify changes**

Run: `uv run pytest tests/test_repositories/ tests/test_tools/test_creature_lookup.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add -A
git commit -m "refactor!: rename monster repository to creature

BREAKING CHANGE: MonsterRepository renamed to CreatureRepository, monster.py renamed to creature.py"
```


---

## Task 4: Remove SQLite Cache Backend

**Files:**
- Delete: `src/lorekeeper_mcp/cache/sqlite.py`
- Delete: `src/lorekeeper_mcp/cache/db.py`
- Delete: `src/lorekeeper_mcp/cache/schema.py`
- Modify: `src/lorekeeper_mcp/cache/__init__.py`
- Modify: `src/lorekeeper_mcp/cache/factory.py`
- Modify: `src/lorekeeper_mcp/config.py`
- Delete: `tests/test_cache/test_sqlite.py`
- Delete: `tests/test_cache/test_db.py`
- Delete: `tests/test_cache/test_schema.py`
- Modify: `tests/test_cache/test_factory.py`
- Modify: `tests/test_config.py` (remove db_path tests)
- Modify: `tests/test_config_milvus.py` (remove cache_backend tests)

**Step 1: Write failing test for SQLite removal**

```python
# tests/test_cache/test_factory.py - add test
def test_backend_parameter_removed() -> None:
    """Test that backend parameter no longer exists."""
    from lorekeeper_mcp.cache.factory import create_cache

    # backend parameter should not exist
    with pytest.raises(TypeError) as exc_info:
        create_cache(backend="milvus", db_path="/tmp/test.db")

    assert "backend" in str(exc_info.value)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache/test_factory.py::test_sqlite_backend_removed -v`
Expected: FAIL (sqlite backend still works)

**Step 3: Delete SQLite-related source files**

```bash
rm src/lorekeeper_mcp/cache/sqlite.py
rm src/lorekeeper_mcp/cache/db.py
rm src/lorekeeper_mcp/cache/schema.py
```

**Step 4: Update cache/__init__.py**

```python
# src/lorekeeper_mcp/cache/__init__.py
"""Caching module for API responses.

This module provides Milvus-based caching with semantic/vector search support
for storing and retrieving D&D entity data.

Use the factory functions to create cache instances:

    from lorekeeper_mcp.cache import create_cache, get_cache_from_config

    # Create Milvus cache
    cache = create_cache(db_path="~/.lorekeeper/milvus.db")

    # Create from environment configuration
    cache = get_cache_from_config()
"""

from lorekeeper_mcp.cache.embedding import EmbeddingService
from lorekeeper_mcp.cache.factory import create_cache, get_cache_from_config
from lorekeeper_mcp.cache.milvus import MilvusCache
from lorekeeper_mcp.cache.protocol import CacheProtocol

__all__ = [
    "CacheProtocol",
    "EmbeddingService",
    "MilvusCache",
    "create_cache",
    "get_cache_from_config",
]
```

**Step 5: Update cache/factory.py**

```python
# src/lorekeeper_mcp/cache/factory.py
"""Cache factory for creating Milvus cache instances.

This module provides factory functions for creating MilvusCache instances
with semantic/vector search capabilities.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorekeeper_mcp.cache.protocol import CacheProtocol

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_MILVUS_DB_PATH = "~/.lorekeeper/milvus.db"


def create_cache(
    db_path: str | None = None,
) -> "CacheProtocol":
    """Create a MilvusCache instance.

    Args:
        db_path: Path to Milvus database file. If not provided, uses default path.

    Returns:
        MilvusCache instance conforming to CacheProtocol.
    """
    from lorekeeper_mcp.cache.milvus import MilvusCache

    if db_path is None:
        db_path = str(Path(DEFAULT_MILVUS_DB_PATH).expanduser())
    logger.info("Creating MilvusCache with db_path: %s", db_path)
    return MilvusCache(db_path)


def get_cache_from_config() -> "CacheProtocol":
    """Create a MilvusCache instance based on environment configuration.

    Reads configuration from environment variables:
    - LOREKEEPER_MILVUS_DB_PATH: Path for Milvus database

    Returns:
        MilvusCache instance conforming to CacheProtocol.
    """
    db_path = os.environ.get("LOREKEEPER_MILVUS_DB_PATH", DEFAULT_MILVUS_DB_PATH)
    return create_cache(db_path=db_path)
```

**Step 6: Update config.py - remove SQLite config**

```python
# src/lorekeeper_mcp/config.py
# DELETE lines 40-41 (db_path field and its validator):
#     # Legacy SQLite configuration (for backward compatibility)
#     db_path: Path = Field(default=Path("./data/cache.db"))

# DELETE lines 60-64 (expand_db_path validator):
#     @field_validator("db_path", mode="before")
#     @classmethod
#     def expand_db_path(cls, v: str | Path) -> Path:
#         """Expand tilde in SQLite database path."""
#         return Path(v).expanduser()

# DELETE line 36 (cache_backend field):
#     cache_backend: str = Field(default="milvus")

# UPDATE docstring to remove SQLite references
```

**Step 7: Delete SQLite test files**

```bash
rm tests/test_cache/test_sqlite.py
rm tests/test_cache/test_db.py
rm tests/test_cache/test_schema.py
```

**Step 8: Update test_factory.py - remove SQLite tests**

```python
# tests/test_cache/test_factory.py
# DELETE TestCreateCache.test_create_cache_sqlite_backend method
# DELETE TestCreateCache.test_create_cache_case_insensitive_backend method (remove SQLite part)
# DELETE TestGetCacheFromConfig.test_get_cache_from_config_uses_env_backend method (SQLite test)
# DELETE any other tests that reference SQLiteCache

# Keep only Milvus-related tests and the new test_sqlite_backend_removed test
```

**Step 9: Update test_config.py - remove db_path tests**

```python
# tests/test_config.py
# UPDATE test_settings_loads_defaults:
#   - REMOVE assertion: assert settings.db_path == Path("./data/cache.db")
#   - Keep other assertions unchanged

# UPDATE test_settings_respects_env_vars:
#   - REMOVE line: monkeypatch.setenv("LOREKEEPER_DB_PATH", "./data/test.db")
#   - REMOVE assertion: assert test_settings.db_path == Path("./data/test.db")
#   - Keep other assertions unchanged
```

**Step 10: Update test_config_milvus.py - remove cache_backend tests**

```python
# tests/test_config_milvus.py
# DELETE entire TestCacheBackendConfig class (lines 7-44)
# This includes:
#   - test_cache_backend_default_is_milvus
#   - test_cache_backend_from_env
#   - test_cache_backend_case_preserved

# UPDATE TestConfigIntegration.test_config_integrates_with_cache_factory:
#   - REMOVE monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")
#   - REMOVE backend=settings.cache_backend from create_cache() call
#   - Just use create_cache(db_path=str(settings.milvus_db_path))
```

**Step 11: Run tests to verify changes**

Run: `uv run pytest tests/test_cache/ tests/test_config.py tests/test_config_milvus.py -v`
Expected: PASS

**Step 12: Commit**

```bash
git add -A
git commit -m "feat!: remove SQLite cache backend

BREAKING CHANGE: SQLite cache backend removed. Use Milvus (default) instead.
- Removed sqlite.py, db.py, schema.py
- Removed LOREKEEPER_CACHE_BACKEND and LOREKEEPER_SQLITE_DB_PATH env vars
- All caching now uses Milvus with semantic search"
```


---

## Task 5: Rename search_dnd_content to search_all and Remove Deprecated Toggles

**Files:**
- Rename: `src/lorekeeper_mcp/tools/search_dnd_content.py` → `src/lorekeeper_mcp/tools/search_all.py`
- Rename: `tests/test_tools/test_search_dnd_content.py` → `tests/test_tools/test_search_all.py`
- Modify: `src/lorekeeper_mcp/tools/__init__.py`
- Modify: `src/lorekeeper_mcp/server.py`

**Step 1: Write failing test for renamed function and removed toggles**

```python
# tests/test_tools/test_search_all.py - new file (copy from test_search_dnd_content.py first)
import pytest
import inspect


def test_search_all_exists_and_deprecated_toggles_removed() -> None:
    """Test that search_all exists and deprecated toggles are removed."""
    from lorekeeper_mcp.tools.search_all import search_all

    sig = inspect.signature(search_all)
    params = set(sig.parameters.keys())

    # Should have these parameters
    expected = {"query", "content_types", "documents", "limit"}
    assert params == expected, f"Expected {expected}, got {params}"

    # Deprecated toggles should NOT exist
    removed = {"enable_fuzzy", "enable_semantic", "semantic"}
    assert removed.isdisjoint(params), f"Found removed params: {removed & params}"


def test_search_dnd_content_import_removed() -> None:
    """Test that old search_dnd_content import no longer exists."""
    with pytest.raises(ImportError):
        from lorekeeper_mcp.tools.search_dnd_content import search_dnd_content  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_search_all.py::test_search_all_exists_and_deprecated_toggles_removed -v`
Expected: FAIL (file doesn't exist yet)

**Step 3: Rename file and function**

```bash
git mv src/lorekeeper_mcp/tools/search_dnd_content.py src/lorekeeper_mcp/tools/search_all.py
```

Then edit `src/lorekeeper_mcp/tools/search_all.py`:
```python
# Update module docstring
"""Unified search tool for D&D content across multiple types.

This module provides the search_all tool that searches across all entity types
using semantic/vector search via the Open5e unified search endpoint.
"""

# Rename function from search_dnd_content to search_all
async def search_all(
    query: str,
    content_types: list[str] | None = None,
    documents: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search across all D&D content with semantic matching.
    ...
    """
    # Implementation stays the same, just remove enable_fuzzy/enable_semantic/semantic params
```

**Step 4: Rename test file and update imports**

```bash
git mv tests/test_tools/test_search_dnd_content.py tests/test_tools/test_search_all.py
```

Update `tests/test_tools/test_search_all.py`:
- Change all imports from `search_dnd_content` to `search_all`
- Update function calls from `search_dnd_content(...)` to `search_all(...)`
- Remove any tests using `enable_fuzzy`, `enable_semantic`, or `semantic` parameters

**Step 5: Update tools/__init__.py exports**

```python
# src/lorekeeper_mcp/tools/__init__.py
# Change:
from lorekeeper_mcp.tools.search_dnd_content import search_dnd_content
# To:
from lorekeeper_mcp.tools.search_all import search_all

# Update __all__ to replace "search_dnd_content" with "search_all"
```

**Step 6: Update server.py tool registration**

```python
# src/lorekeeper_mcp/server.py
# Update import and tool registration from search_dnd_content to search_all
```

**Step 7: Run tests to verify changes**

Run: `uv run pytest tests/test_tools/test_search_all.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add -A
git commit -m "feat!: rename search_dnd_content to search_all

BREAKING CHANGE: search_dnd_content renamed to search_all.
Removed deprecated enable_fuzzy, enable_semantic, semantic parameters."
```


---

## Task 6: Rename lookup_spell to search_spell (Keep All Filters)

**Files:**
- Rename: `src/lorekeeper_mcp/tools/spell_lookup.py` → `src/lorekeeper_mcp/tools/search_spell.py`
- Rename: `tests/test_tools/test_spell_lookup.py` → `tests/test_tools/test_search_spell.py`
- Modify: `src/lorekeeper_mcp/tools/__init__.py`
- Modify: `src/lorekeeper_mcp/server.py`

**Step 1: Write failing test for renamed function**

```python
# tests/test_tools/test_search_spell.py - new file (copy from test_spell_lookup.py first)
import pytest
import inspect


def test_search_spell_exists_with_all_filters() -> None:
    """Test that search_spell exists and preserves all filter parameters."""
    from lorekeeper_mcp.tools.search_spell import search_spell

    sig = inspect.signature(search_spell)
    params = set(sig.parameters.keys())

    # All structured filters should be preserved
    expected = {
        "name", "level", "level_min", "level_max", "school", "class_key",
        "concentration", "ritual", "casting_time", "damage_type",
        "documents", "semantic_query", "limit"
    }
    assert params == expected, f"Expected {expected}, got {params}"


def test_lookup_spell_import_removed() -> None:
    """Test that old lookup_spell import no longer exists."""
    with pytest.raises(ImportError):
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_search_spell.py::test_search_spell_exists_with_all_filters -v`
Expected: FAIL (file doesn't exist yet)

**Step 3: Rename file and function**

```bash
git mv src/lorekeeper_mcp/tools/spell_lookup.py src/lorekeeper_mcp/tools/search_spell.py
```

Then edit `src/lorekeeper_mcp/tools/search_spell.py`:
```python
# Update module docstring
"""Spell search tool with hybrid semantic and structured filtering.

This module provides spell lookup functionality using both semantic/vector search
and structured filtering through the repository pattern.
"""

# Rename function from lookup_spell to search_spell
# KEEP ALL EXISTING PARAMETERS - only the function name changes
async def search_spell(
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
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search for D&D 5e spells with hybrid search.

    Supports both semantic search (via semantic_query) and structured filtering.
    Can use either approach independently or combine them for hybrid search.
    ...
    """
    # Implementation stays the same
```

**Step 4: Remove clear_spell_cache function (deprecated stub)**

```python
# DELETE the clear_spell_cache function entirely from search_spell.py
```

**Step 5: Rename test file and update imports**

```bash
git mv tests/test_tools/test_spell_lookup.py tests/test_tools/test_search_spell.py
```

Update `tests/test_tools/test_search_spell.py`:
- Change all imports from `lookup_spell` to `search_spell`
- Update function calls from `lookup_spell(...)` to `search_spell(...)`
- Remove any tests for `clear_spell_cache`

**Step 6: Update tools/__init__.py exports**

```python
# src/lorekeeper_mcp/tools/__init__.py
# Change:
from lorekeeper_mcp.tools.spell_lookup import lookup_spell
# To:
from lorekeeper_mcp.tools.search_spell import search_spell

# Update __all__ to replace "lookup_spell" with "search_spell"
```

**Step 7: Update server.py tool registration**

```python
# src/lorekeeper_mcp/server.py
# Update import and tool registration from lookup_spell to search_spell
```

**Step 8: Run tests to verify changes**

Run: `uv run pytest tests/test_tools/test_search_spell.py -v`
Expected: PASS

**Step 9: Commit**

```bash
git add -A
git commit -m "feat!: rename lookup_spell to search_spell

BREAKING CHANGE: lookup_spell renamed to search_spell.
All filter parameters preserved for hybrid search.
Removed deprecated clear_spell_cache function."
```


---

## Task 7: Rename lookup_creature to search_creature (Keep All Filters)

> **DEPENDENCY**: Task 3 (Remove Monster Repository Aliases) MUST be completed first.
> This task assumes `creature_lookup.py` already imports from `CreatureRepository`.

**Files:**
- Rename: `src/lorekeeper_mcp/tools/creature_lookup.py` → `src/lorekeeper_mcp/tools/search_creature.py`
- Rename: `tests/test_tools/test_creature_lookup.py` → `tests/test_tools/test_search_creature.py`
- Modify: `src/lorekeeper_mcp/tools/__init__.py`
- Modify: `src/lorekeeper_mcp/server.py`

**Step 1: Write failing test for renamed function**

```python
# tests/test_tools/test_search_creature.py - new file (copy from test_creature_lookup.py first)
import pytest
import inspect


def test_search_creature_exists_with_all_filters() -> None:
    """Test that search_creature exists and preserves all filter parameters."""
    from lorekeeper_mcp.tools.search_creature import search_creature

    sig = inspect.signature(search_creature)
    params = set(sig.parameters.keys())

    # All structured filters should be preserved
    expected = {
        "name", "cr", "cr_min", "cr_max", "type", "size",
        "armor_class_min", "hit_points_min",
        "documents", "semantic_query", "limit"
    }
    assert params == expected, f"Expected {expected}, got {params}"


def test_lookup_creature_import_removed() -> None:
    """Test that old lookup_creature import no longer exists."""
    with pytest.raises(ImportError):
        from lorekeeper_mcp.tools.creature_lookup import lookup_creature  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_search_creature.py::test_search_creature_exists_with_all_filters -v`
Expected: FAIL (file doesn't exist yet)

**Step 3: Rename file and function**

```bash
git mv src/lorekeeper_mcp/tools/creature_lookup.py src/lorekeeper_mcp/tools/search_creature.py
```

Then edit `src/lorekeeper_mcp/tools/search_creature.py`:
```python
# Update module docstring
"""Creature search tool with hybrid semantic and structured filtering.

This module provides creature lookup functionality using both semantic/vector search
and structured filtering through the repository pattern.
"""

# Rename function from lookup_creature to search_creature
# KEEP ALL EXISTING PARAMETERS - only the function name changes
async def search_creature(
    name: str | None = None,
    cr: float | None = None,
    cr_min: float | None = None,
    cr_max: float | None = None,
    type: str | None = None,  # noqa: A002
    size: str | None = None,
    armor_class_min: int | None = None,
    hit_points_min: int | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search for D&D 5e creatures with hybrid search.

    Supports both semantic search (via semantic_query) and structured filtering.
    Can use either approach independently or combine them for hybrid search.
    ...
    """
    # Implementation stays the same
```

**Step 4: Remove clear_creature_cache function (deprecated stub)**

```python
# DELETE the clear_creature_cache function entirely from search_creature.py
```

**Step 5: Rename test file and update imports**

```bash
git mv tests/test_tools/test_creature_lookup.py tests/test_tools/test_search_creature.py
```

Update `tests/test_tools/test_search_creature.py`:
- Change all imports from `lookup_creature` to `search_creature`
- Update function calls from `lookup_creature(...)` to `search_creature(...)`
- Remove any tests for `clear_creature_cache`

**Step 6: Update tools/__init__.py exports**

```python
# src/lorekeeper_mcp/tools/__init__.py
# Change:
from lorekeeper_mcp.tools.creature_lookup import lookup_creature
# To:
from lorekeeper_mcp.tools.search_creature import search_creature

# Update __all__ to replace "lookup_creature" with "search_creature"
```

**Step 7: Update server.py tool registration**

```python
# src/lorekeeper_mcp/server.py
# Update import and tool registration from lookup_creature to search_creature
```

**Step 8: Run tests to verify changes**

Run: `uv run pytest tests/test_tools/test_search_creature.py -v`
Expected: PASS

**Step 9: Commit**

```bash
git add -A
git commit -m "feat!: rename lookup_creature to search_creature

BREAKING CHANGE: lookup_creature renamed to search_creature.
All filter parameters preserved for hybrid search.
Removed deprecated clear_creature_cache function."
```


---

## Task 8: Rename lookup_equipment to search_equipment (Keep All Filters)

**Files:**
- Rename: `src/lorekeeper_mcp/tools/equipment_lookup.py` → `src/lorekeeper_mcp/tools/search_equipment.py`
- Rename: `tests/test_tools/test_equipment_lookup.py` → `tests/test_tools/test_search_equipment.py`
- Modify: `src/lorekeeper_mcp/tools/__init__.py`
- Modify: `src/lorekeeper_mcp/server.py`

**Step 1: Write failing test for renamed function**

```python
# tests/test_tools/test_search_equipment.py - new file (copy from test_equipment_lookup.py first)
import pytest
import inspect


def test_search_equipment_exists_with_all_filters() -> None:
    """Test that search_equipment exists and preserves all filter parameters."""
    from lorekeeper_mcp.tools.search_equipment import search_equipment

    sig = inspect.signature(search_equipment)
    params = set(sig.parameters.keys())

    # All structured filters should be preserved
    expected = {
        "type", "name", "rarity", "damage_dice", "is_simple", "requires_attunement",
        "cost_min", "cost_max", "weight_max", "is_finesse", "is_light", "is_magic",
        "documents", "semantic_query", "limit"
    }
    assert params == expected, f"Expected {expected}, got {params}"


def test_lookup_equipment_import_removed() -> None:
    """Test that old lookup_equipment import no longer exists."""
    with pytest.raises(ImportError):
        from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_search_equipment.py::test_search_equipment_exists_with_all_filters -v`
Expected: FAIL (file doesn't exist yet)

**Step 3: Rename file and function**

```bash
git mv src/lorekeeper_mcp/tools/equipment_lookup.py src/lorekeeper_mcp/tools/search_equipment.py
```

Then edit `src/lorekeeper_mcp/tools/search_equipment.py`:
```python
# Update module docstring
"""Equipment search tool with hybrid semantic and structured filtering.

This module provides equipment lookup (weapons, armor, magic items) using both
semantic/vector search and structured filtering through the repository pattern.
"""

# Rename function from lookup_equipment to search_equipment
# KEEP ALL EXISTING PARAMETERS - only the function name changes
async def search_equipment(
    type: EquipmentType = "all",  # noqa: A002
    name: str | None = None,
    rarity: str | None = None,
    damage_dice: str | None = None,
    is_simple: bool | None = None,
    requires_attunement: bool | None = None,
    cost_min: int | None = None,
    cost_max: int | None = None,
    weight_max: float | None = None,
    is_finesse: bool | None = None,
    is_light: bool | None = None,
    is_magic: bool | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search for D&D 5e equipment with hybrid search.

    Supports both semantic search (via semantic_query) and structured filtering.
    Can use either approach independently or combine them for hybrid search.
    ...
    """
    # Implementation stays the same
```

**Step 4: Rename test file and update imports**

```bash
git mv tests/test_tools/test_equipment_lookup.py tests/test_tools/test_search_equipment.py
```

Update `tests/test_tools/test_search_equipment.py`:
- Change all imports from `lookup_equipment` to `search_equipment`
- Update function calls from `lookup_equipment(...)` to `search_equipment(...)`

**Step 5: Update tools/__init__.py exports**

```python
# src/lorekeeper_mcp/tools/__init__.py
# Change:
from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment
# To:
from lorekeeper_mcp.tools.search_equipment import search_equipment

# Update __all__ to replace "lookup_equipment" with "search_equipment"
```

**Step 6: Update server.py tool registration**

```python
# src/lorekeeper_mcp/server.py
# Update import and tool registration from lookup_equipment to search_equipment
```

**Step 7: Run tests to verify changes**

Run: `uv run pytest tests/test_tools/test_search_equipment.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add -A
git commit -m "feat!: rename lookup_equipment to search_equipment

BREAKING CHANGE: lookup_equipment renamed to search_equipment.
All filter parameters preserved for hybrid search."
```


---

## Task 9: Rename lookup_character_option to search_character_option (Keep All Filters)

**Files:**
- Rename: `src/lorekeeper_mcp/tools/character_option_lookup.py` → `src/lorekeeper_mcp/tools/search_character_option.py`
- Rename: `tests/test_tools/test_character_option_lookup.py` → `tests/test_tools/test_search_character_option.py`
- Modify: `src/lorekeeper_mcp/tools/__init__.py`
- Modify: `src/lorekeeper_mcp/server.py`

**Step 1: Write failing test for renamed function**

```python
# tests/test_tools/test_search_character_option.py - new file (copy from test_character_option_lookup.py first)
import pytest
import inspect


def test_search_character_option_exists_with_all_filters() -> None:
    """Test that search_character_option exists and preserves all filter parameters."""
    from lorekeeper_mcp.tools.search_character_option import search_character_option

    sig = inspect.signature(search_character_option)
    params = set(sig.parameters.keys())

    # All structured filters should be preserved
    expected = {"type", "name", "documents", "semantic_query", "limit"}
    assert params == expected, f"Expected {expected}, got {params}"


def test_lookup_character_option_import_removed() -> None:
    """Test that old lookup_character_option import no longer exists."""
    with pytest.raises(ImportError):
        from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_search_character_option.py::test_search_character_option_exists_with_all_filters -v`
Expected: FAIL (file doesn't exist yet)

**Step 3: Rename file and function**

```bash
git mv src/lorekeeper_mcp/tools/character_option_lookup.py src/lorekeeper_mcp/tools/search_character_option.py
```

Then edit `src/lorekeeper_mcp/tools/search_character_option.py`:
```python
# Update module docstring
"""Character option search tool with hybrid semantic and structured filtering.

This module provides character option lookup (classes, races, backgrounds, feats)
using both semantic/vector search and structured filtering through the repository pattern.
"""

# Rename function from lookup_character_option to search_character_option
# KEEP ALL EXISTING PARAMETERS - only the function name changes
async def search_character_option(
    type: OptionType,  # noqa: A002
    name: str | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search for D&D 5e character options with hybrid search.

    Supports both semantic search (via semantic_query) and structured filtering.
    Can use either approach independently or combine them for hybrid search.
    ...
    """
    # Implementation stays the same
```

**Step 4: Remove clear_character_option_cache function (deprecated stub)**

```python
# DELETE the clear_character_option_cache function entirely from search_character_option.py
```

**Step 5: Rename test file and update imports**

```bash
git mv tests/test_tools/test_character_option_lookup.py tests/test_tools/test_search_character_option.py
```

Update `tests/test_tools/test_search_character_option.py`:
- Change all imports from `lookup_character_option` to `search_character_option`
- Update function calls from `lookup_character_option(...)` to `search_character_option(...)`
- Remove any tests for `clear_character_option_cache`

**Step 6: Update tools/__init__.py exports**

```python
# src/lorekeeper_mcp/tools/__init__.py
# Change:
from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option
# To:
from lorekeeper_mcp.tools.search_character_option import search_character_option

# Update __all__ to replace "lookup_character_option" with "search_character_option"
```

**Step 7: Update server.py tool registration**

```python
# src/lorekeeper_mcp/server.py
# Update import and tool registration from lookup_character_option to search_character_option
```

**Step 8: Run tests to verify changes**

Run: `uv run pytest tests/test_tools/test_search_character_option.py -v`
Expected: PASS

**Step 9: Commit**

```bash
git add -A
git commit -m "feat!: rename lookup_character_option to search_character_option

BREAKING CHANGE: lookup_character_option renamed to search_character_option.
All filter parameters preserved for hybrid search.
Removed deprecated clear_character_option_cache function."
```


---

## Task 10: Rename lookup_rule to search_rule (Keep All Filters)

**Files:**
- Rename: `src/lorekeeper_mcp/tools/rule_lookup.py` → `src/lorekeeper_mcp/tools/search_rule.py`
- Rename: `tests/test_tools/test_rule_lookup.py` → `tests/test_tools/test_search_rule.py`
- Modify: `src/lorekeeper_mcp/tools/__init__.py`
- Modify: `src/lorekeeper_mcp/server.py`

**Step 1: Write failing test for renamed function**

```python
# tests/test_tools/test_search_rule.py - new file (copy from test_rule_lookup.py first)
import pytest
import inspect


def test_search_rule_exists_with_all_filters() -> None:
    """Test that search_rule exists and preserves all filter parameters."""
    from lorekeeper_mcp.tools.search_rule import search_rule

    sig = inspect.signature(search_rule)
    params = set(sig.parameters.keys())

    # All structured filters should be preserved
    expected = {"rule_type", "name", "section", "documents", "semantic_query", "limit"}
    assert params == expected, f"Expected {expected}, got {params}"


def test_lookup_rule_import_removed() -> None:
    """Test that old lookup_rule import no longer exists."""
    with pytest.raises(ImportError):
        from lorekeeper_mcp.tools.rule_lookup import lookup_rule  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_search_rule.py::test_search_rule_exists_with_all_filters -v`
Expected: FAIL (file doesn't exist yet)

**Step 3: Rename file and function**

```bash
git mv src/lorekeeper_mcp/tools/rule_lookup.py src/lorekeeper_mcp/tools/search_rule.py
```

Then edit `src/lorekeeper_mcp/tools/search_rule.py`:
```python
# Update module docstring
"""Rule search tool with hybrid semantic and structured filtering.

This module provides rule lookup (conditions, damage types, skills, etc.)
using both semantic/vector search and structured filtering through the repository pattern.
"""

# Rename function from lookup_rule to search_rule
# KEEP ALL EXISTING PARAMETERS - only the function name changes
async def search_rule(
    rule_type: RuleType,
    name: str | None = None,
    section: str | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search for D&D 5e rules with hybrid search.

    Supports both semantic search (via semantic_query) and structured filtering.
    Can use either approach independently or combine them for hybrid search.
    ...
    """
    # Implementation stays the same
```

**Step 4: Rename test file and update imports**

```bash
git mv tests/test_tools/test_rule_lookup.py tests/test_tools/test_search_rule.py
```

Update `tests/test_tools/test_search_rule.py`:
- Change all imports from `lookup_rule` to `search_rule`
- Update function calls from `lookup_rule(...)` to `search_rule(...)`

**Step 5: Update tools/__init__.py exports**

```python
# src/lorekeeper_mcp/tools/__init__.py
# Change:
from lorekeeper_mcp.tools.rule_lookup import lookup_rule
# To:
from lorekeeper_mcp.tools.search_rule import search_rule

# Update __all__ to replace "lookup_rule" with "search_rule"
```

**Step 6: Update server.py tool registration**

```python
# src/lorekeeper_mcp/server.py
# Update import and tool registration from lookup_rule to search_rule
```

**Step 7: Run tests to verify changes**

Run: `uv run pytest tests/test_tools/test_search_rule.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add -A
git commit -m "feat!: rename lookup_rule to search_rule

BREAKING CHANGE: lookup_rule renamed to search_rule.
All filter parameters preserved for hybrid search."
```


---

## Task 11: Update CLI and Environment Configuration

**Files:**
- Modify: `src/lorekeeper_mcp/cli.py:24-28`
- Modify: `.env.example`

**Step 1: Update CLI to remove SQLite reference**

```python
# src/lorekeeper_mcp/cli.py
# Lines 24-28: Change from:
@click.option(
    "--db-path",
    type=click.Path(),
    envvar="LOREKEEPER_DB_PATH",
    help="Path to SQLite database file",
)
# To:
@click.option(
    "--db-path",
    type=click.Path(),
    envvar="LOREKEEPER_MILVUS_DB_PATH",
    help="Path to Milvus database file",
)
```

**Step 2: Update .env.example**

```bash
# .env.example - Updated content:
# =============================================================================
# LoreKeeper MCP Configuration
# =============================================================================
# All environment variables use the LOREKEEPER_ prefix.
# Copy this file to .env and customize as needed.

# =============================================================================
# Cache Configuration
# =============================================================================

# Path to Milvus Lite database file
# Supports ~ for home directory expansion
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db

# =============================================================================
# Embedding Model Configuration
# =============================================================================

# Sentence-transformers model for generating embeddings
# Default: all-MiniLM-L6-v2 (384 dimensions, ~80MB download)
# The model is downloaded automatically on first use
#
# Alternative lightweight models:
# - paraphrase-MiniLM-L3-v2 (smaller, faster, less accurate)
# - all-mpnet-base-v2 (larger, slower, more accurate)
#
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2

# =============================================================================
# Logging Configuration
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOREKEEPER_LOG_LEVEL=INFO

# Debug mode - enables verbose logging and other debugging features
LOREKEEPER_DEBUG=false

# =============================================================================
# API Endpoints
# =============================================================================

# Base URL for the Open5e D&D 5e API
LOREKEEPER_OPEN5E_BASE_URL=https://api.open5e.com
```

**Step 3: Run tests to verify CLI still works**

Run: `uv run pytest tests/test_cli_basic.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/cli.py .env.example
git commit -m "chore: update CLI and env config for Milvus-only

- Updated --db-path to use LOREKEEPER_MILVUS_DB_PATH
- Removed SQLite references from .env.example"
```


---

## Task 12: Update Documentation

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/cache.md`
- Modify: `docs/tools.md`

**Step 1: Update docs/architecture.md**

Remove all SQLite and Monster references. Update to reflect Milvus-only architecture
with semantic search as the primary data retrieval method.

**Step 2: Update docs/cache.md**

Remove SQLite backend documentation. Update to document Milvus-only caching
with semantic/vector search capabilities.

**Step 3: Update docs/tools.md**

Update tool documentation to reflect renamed tools with preserved hybrid search signatures:
- `search_spell(name, level, level_min, level_max, school, class_key, concentration, ritual, casting_time, damage_type, documents, semantic_query, limit)`
- `search_creature(name, cr, cr_min, cr_max, type, size, armor_class_min, hit_points_min, documents, semantic_query, limit)`
- `search_equipment(type, name, rarity, damage_dice, is_simple, requires_attunement, cost_min, cost_max, weight_max, is_finesse, is_light, is_magic, documents, semantic_query, limit)`
- `search_character_option(type, name, documents, semantic_query, limit)`
- `search_rule(rule_type, name, section, documents, semantic_query, limit)`
- `search_all(query, content_types, documents, limit)`

**Step 4: Commit**

```bash
git add docs/
git commit -m "docs: update documentation for semantic-only architecture

- Removed SQLite and Monster references
- Updated tool signatures to semantic-only
- Documented Milvus-only caching"
```


---

## Task 13: Final Validation

**Step 1: Run full test suite**

```bash
just test
```

Expected: All tests PASS

**Step 2: Run type checking**

```bash
just type-check
```

Expected: No type errors related to changes

**Step 3: Run linting**

```bash
just lint
```

Expected: No linting errors

**Step 4: Run live tests**

```bash
uv run pytest -m live -v
```

Expected: All live tests PASS

**Step 5: Verify MCP server starts**

```bash
just serve
```

Expected: Server starts without errors. Press Ctrl+C to stop.

**Step 6: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: address validation issues from deprecated features removal"
```

---

## Summary of Breaking Changes

1. **Monster Model Removed**: Use `Creature` instead of `Monster`
2. **api_clients.models Module Removed**: Import from `lorekeeper_mcp.models`
3. **MonsterRepository Renamed**: Use `CreatureRepository` from `repositories.creature`
4. **SQLite Backend Removed**: Only Milvus backend supported
5. **Tool Names Changed**:
   - `lookup_spell` → `search_spell`
   - `lookup_creature` → `search_creature`
   - `lookup_equipment` → `search_equipment`
   - `lookup_character_option` → `search_character_option`
   - `lookup_rule` → `search_rule`
   - `search_dnd_content` → `search_all`
6. **Deprecated Toggle Parameters Removed** from `search_all`:
   - Removed: `enable_fuzzy`, `enable_semantic`, `semantic`
7. **Deprecated Clear Cache Functions Removed**:
   - `clear_spell_cache()`, `clear_creature_cache()`, `clear_character_option_cache()`
8. **All Structured Filters PRESERVED**: Hybrid search architecture maintained

## Migration Guide for Users

### Before (Old API)
```python
# Old tool names
spells = await lookup_spell(level=3, school="evocation")
creatures = await lookup_creature(cr_min=5, type="dragon")

# Old unified search with deprecated toggles
results = await search_dnd_content(query="fire", enable_semantic=True)

# Monster model
from lorekeeper_mcp.models import Monster
monster = Monster(...)

# SQLite cache
cache = create_cache(backend="sqlite")
```

### After (New API)
```python
# New tool names (same parameters!)
spells = await search_spell(level=3, school="evocation")
creatures = await search_creature(cr_min=5, type="dragon")

# Renamed unified search (semantic always on)
results = await search_all(query="fire")

# Creature model
from lorekeeper_mcp.models import Creature
creature = Creature(...)

# Milvus cache (only option)
cache = create_cache()  # Milvus is default and only backend

# Hybrid search examples (all filters preserved!)
# Structured filtering only
spells = await search_spell(level=3, school="evocation")

# Semantic search only
spells = await search_spell(semantic_query="fire damage explosion")

# Hybrid: combine semantic + structured
spells = await search_spell(semantic_query="fire damage", level=3, school="evocation")
```
