# Remove D&D 5e API Client Implementation Plan

**Goal:** Remove the D&D 5e API client and all its dependencies, consolidating on Open5e API as the sole data source.

**Architecture:** Delete `dnd5e_api.py` and update all imports, factory methods, repositories, tools, tests, and configuration that reference it. The Open5e v2 client already provides equivalent functionality for all entity types.

**Tech Stack:** Python 3.11+, pytest, respx for HTTP mocking

---

## Task 1: Remove D&D 5e API Client Module

**Files:**
- Delete: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Modify: `src/lorekeeper_mcp/api_clients/__init__.py:4,16,22`

**Step 1: Delete the D&D 5e API client file**

```bash
rm src/lorekeeper_mcp/api_clients/dnd5e_api.py
```

**Step 2: Update api_clients/__init__.py to remove Dnd5eApiClient export**

Change from:
```python
"""API client package for external D&D 5e data sources."""

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)
from lorekeeper_mcp.api_clients.factory import ClientFactory
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

__all__ = [
    "ApiClientError",
    "ApiError",
    "BaseHttpClient",
    "CacheError",
    "ClientFactory",
    "Dnd5eApiClient",
    "NetworkError",
    "Open5eV1Client",
    "Open5eV2Client",
    "ParseError",
]
```

To:
```python
"""API client package for external D&D 5e data sources."""

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)
from lorekeeper_mcp.api_clients.factory import ClientFactory
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

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

**Step 3: Run tests to verify removal breaks expected places**

```bash
uv run pytest tests/test_api_clients/test_factory.py -v
```

Expected: FAIL - tests reference `Dnd5eApiClient` and `create_dnd5e_api`

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove dnd5e_api.py module and exports"
```

---

## Task 2: Update ClientFactory

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/factory.py`

**Step 1: Read current factory.py to understand structure**

```bash
# Read factory.py to see current implementation
```

**Step 2: Remove create_dnd5e_api method from ClientFactory**

Remove the `create_dnd5e_api` method entirely. The factory should only have:
- `create_open5e_v1()`
- `create_open5e_v2()`

**Step 3: Run factory tests**

```bash
uv run pytest tests/test_api_clients/test_factory.py -v
```

Expected: FAIL - test `test_create_dnd5e_api` still exists

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/factory.py
git commit -m "refactor: remove create_dnd5e_api from ClientFactory"
```

---

## Task 3: Update Factory Tests

**Files:**
- Modify: `tests/test_api_clients/test_factory.py`

**Step 1: Remove test_create_dnd5e_api test**

Remove this test entirely:
```python
async def test_create_dnd5e_api() -> None:
    """Test creating D&D 5e API client via factory."""
    client = ClientFactory.create_dnd5e_api()

    assert isinstance(client, Dnd5eApiClient)
    assert client.base_url == "https://www.dnd5eapi.co/api/2014"
    assert client.source_api == "dnd5e_api"

    await client.close()
```

**Step 2: Remove Dnd5eApiClient import**

Change from:
```python
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.factory import ClientFactory
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
```

To:
```python
from lorekeeper_mcp.api_clients.factory import ClientFactory
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
```

**Step 3: Run factory tests to verify they pass**

```bash
uv run pytest tests/test_api_clients/test_factory.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add tests/test_api_clients/test_factory.py
git commit -m "test: remove dnd5e_api tests from factory tests"
```

---

## Task 4: Delete D&D 5e API Client Tests

**Files:**
- Delete: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Delete the test file**

```bash
rm tests/test_api_clients/test_dnd5e_api.py
```

**Step 2: Verify test collection works**

```bash
uv run pytest tests/test_api_clients/ --collect-only
```

Expected: No import errors, tests collected successfully

**Step 3: Commit**

```bash
git add -A
git commit -m "test: remove test_dnd5e_api.py"
```

---

## Task 5: Update CharacterOptionRepository

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/character_option.py:5,193`

**Step 1: Remove Dnd5eApiClient import and isinstance check**

Change from:
```python
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.repositories.base import Repository
```

To:
```python
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.repositories.base import Repository
```

**Step 2: Update _search_feats method**

Change from:
```python
        # If we have the D&D 5e API client, use Open5e v2 instead for better feat data
        if isinstance(self.client, Dnd5eApiClient):
            open5e_client = Open5eV2Client()
            feats: list[dict[str, Any]] = await open5e_client.get_feats(
                limit=api_limit, **api_filters
            )
        else:
            # Use provided client (e.g., in tests with mocks)
            feats = await self.client.get_feats(limit=api_limit, **api_filters)
```

To:
```python
        # Use provided client (Open5e v2 or test mock)
        feats: list[dict[str, Any]] = await self.client.get_feats(
            limit=api_limit, **api_filters
        )
```

**Step 3: Run character option repository tests**

```bash
uv run pytest tests/test_repositories/test_character_option.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/repositories/character_option.py
git commit -m "refactor: remove Dnd5eApiClient dependency from CharacterOptionRepository"
```

---

## Task 6: Update RepositoryFactory

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/factory.py`

**Step 1: Read current factory.py**

Examine the file to understand what D&D 5e API references exist.

**Step 2: Remove Dnd5eApiClient import if present**

Remove any import of `Dnd5eApiClient` from the factory.

**Step 3: Update factory methods to use Open5e clients**

Ensure all repository factory methods use Open5e clients instead of D&D 5e API client:
- `create_equipment_repository()` - use Open5eV2Client
- `create_character_option_repository()` - use Open5eV2Client
- `create_rule_repository()` - use Open5eV2Client

**Step 4: Run repository factory tests**

```bash
uv run pytest tests/test_repositories/test_factory.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/repositories/factory.py
git commit -m "refactor: update RepositoryFactory to use Open5e clients only"
```

---

## Task 7: Update SpellRepository

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/spell.py`

**Step 1: Remove Dnd5eApiClient import if present**

Check if `Dnd5eApiClient` is imported and remove it.

**Step 2: Update _map_to_api_params to remove D&D 5e specific mappings**

The `_map_to_api_params` method has special handling for D&D 5e API. Remove the D&D 5e specific branch:

Change from:
```python
def _map_to_api_params(self, **filters: Any) -> dict[str, Any]:
    # Check client type for API-specific mappings
    if isinstance(self.client, Dnd5eApiClient):
        # D&D 5e API mappings
        ...
    else:
        # Open5e mappings
        ...
```

To:
```python
def _map_to_api_params(self, **filters: Any) -> dict[str, Any]:
    # Open5e v2 API mappings only
    ...
```

**Step 3: Run spell repository tests**

```bash
uv run pytest tests/test_repositories/test_spell.py -v
```

Expected: Some tests may fail if they test D&D 5e specific mappings

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/repositories/spell.py
git commit -m "refactor: remove Dnd5eApiClient mappings from SpellRepository"
```

---

## Task 8: Update Spell Repository Tests

**Files:**
- Modify: `tests/test_repositories/test_spell.py`

**Step 1: Remove Dnd5eApiClient import**

Change from:
```python
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.models.spell import Spell
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
```

To:
```python
from lorekeeper_mcp.api_clients.models.spell import Spell
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
```

**Step 2: Remove D&D 5e specific parameter mapping tests**

Remove these tests:
- `test_repository_parameter_mapping_with_dnd5e_client`
- `test_dnd5e_parameter_mapping`

**Step 3: Run spell repository tests**

```bash
uv run pytest tests/test_repositories/test_spell.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add tests/test_repositories/test_spell.py
git commit -m "test: remove D&D 5e API tests from spell repository tests"
```

---

## Task 9: Update Integration Tests

**Files:**
- Modify: `tests/test_tools/test_integration.py:14,586-613`

**Step 1: Remove Dnd5eApiClient import**

Change from:
```python
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
```

To:
```python
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
```

**Step 2: Update test_repository_factory_creates_instances**

Change from:
```python
async def test_repository_factory_creates_instances():
    """Test that repository factory creates properly configured instances."""
    v1_client = Open5eV1Client()
    v2_client = Open5eV2Client()
    dnd5e_client = Dnd5eApiClient()

    try:
        # Create all repositories
        spell_repo = RepositoryFactory.create_spell_repository(client=v2_client)
        monster_repo = RepositoryFactory.create_monster_repository(client=v1_client)
        equipment_repo = RepositoryFactory.create_equipment_repository(client=dnd5e_client)
        char_opt_repo = RepositoryFactory.create_character_option_repository(client=dnd5e_client)
        rule_repo = RepositoryFactory.create_rule_repository(client=dnd5e_client)
        ...
    finally:
        await v1_client.close()
        await v2_client.close()
        await dnd5e_client.close()
```

To:
```python
async def test_repository_factory_creates_instances():
    """Test that repository factory creates properly configured instances."""
    v1_client = Open5eV1Client()
    v2_client = Open5eV2Client()

    try:
        # Create all repositories
        spell_repo = RepositoryFactory.create_spell_repository(client=v2_client)
        monster_repo = RepositoryFactory.create_monster_repository(client=v1_client)
        equipment_repo = RepositoryFactory.create_equipment_repository(client=v2_client)
        char_opt_repo = RepositoryFactory.create_character_option_repository(client=v2_client)
        rule_repo = RepositoryFactory.create_rule_repository(client=v2_client)
        ...
    finally:
        await v1_client.close()
        await v2_client.close()
```

**Step 3: Update mock URLs in tests to use Open5e instead of D&D 5e API**

Several tests mock D&D 5e API URLs. These need to be updated:
- `test_equipment_lookup_weapons` - change from dnd5eapi.co to api.open5e.com
- `test_equipment_lookup_armor` - change from dnd5eapi.co to api.open5e.com
- `test_character_option_lookup_class` - change from dnd5eapi.co to api.open5e.com
- `test_character_option_lookup_race` - change from dnd5eapi.co to api.open5e.com
- `test_rule_lookup_*` tests - change from dnd5eapi.co to api.open5e.com

**Step 4: Run integration tests**

```bash
uv run pytest tests/test_tools/test_integration.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_tools/test_integration.py
git commit -m "test: update integration tests to use Open5e API only"
```

---

## Task 10: Update Tool Test Fixtures

**Files:**
- Modify: `tests/test_tools/conftest.py:130-142`

**Step 1: Remove mock_dnd5e_client fixture**

Remove this fixture entirely:
```python
@pytest.fixture
def mock_dnd5e_client():
    """Mock Dnd5eApiClient."""
    client = MagicMock()
    client.get_rules = AsyncMock(return_value={"count": 0, "results": []})
    client.get_damage_types = AsyncMock(return_value={"count": 0, "results": []})
    client.get_weapon_properties = AsyncMock(return_value={"count": 0, "results": []})
    client.get_skills = AsyncMock(return_value={"count": 0, "results": []})
    client.get_ability_scores = AsyncMock(return_value={"count": 0, "results": []})
    client.get_magic_schools = AsyncMock(return_value={"count": 0, "results": []})
    client.get_languages = AsyncMock(return_value={"count": 0, "results": []})
    client.get_proficiencies = AsyncMock(return_value={"count": 0, "results": []})
    client.get_alignments = AsyncMock(return_value={"count": 0, "results": []})
    return client
```

**Step 2: Update mock_open5e_v2_client to include rule methods**

Add the missing methods that were only in D&D 5e client:
```python
@pytest.fixture
def mock_open5e_v2_client(mock_spell_response):
    """Mock Open5eV2Client."""
    # ... existing code ...
    client.get_rules = AsyncMock(return_value=[])
    client.get_damage_types_v2 = AsyncMock(return_value=[])
    client.get_weapon_properties_v2 = AsyncMock(return_value=[])
    client.get_skills_v2 = AsyncMock(return_value=[])
    client.get_abilities = AsyncMock(return_value=[])
    client.get_spell_schools_v2 = AsyncMock(return_value=[])
    client.get_languages_v2 = AsyncMock(return_value=[])
    client.get_alignments_v2 = AsyncMock(return_value=[])
    return client
```

**Step 3: Run tool tests**

```bash
uv run pytest tests/test_tools/ -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add tests/test_tools/conftest.py
git commit -m "test: remove mock_dnd5e_client fixture, update mock_open5e_v2_client"
```

---

## Task 11: Update Configuration

**Files:**
- Modify: `src/lorekeeper_mcp/config.py:24`
- Modify: `tests/test_config.py:19,30,41`

**Step 1: Remove dnd5e_base_url from Settings**

Change from:
```python
class Settings(BaseSettings):
    ...
    open5e_base_url: str = Field(default="https://api.open5e.com")
    dnd5e_base_url: str = Field(default="https://www.dnd5eapi.co/api")
```

To:
```python
class Settings(BaseSettings):
    ...
    open5e_base_url: str = Field(default="https://api.open5e.com")
```

**Step 2: Update test_config.py to remove dnd5e_base_url assertions**

Remove these assertions:
```python
assert settings.dnd5e_base_url == "https://www.dnd5eapi.co/api"
```

And:
```python
monkeypatch.setenv("DND5E_BASE_URL", "https://test.dnd5eapi.co/api")
...
assert test_settings.dnd5e_base_url == "https://test.dnd5eapi.co/api"
```

**Step 3: Run config tests**

```bash
uv run pytest tests/test_config.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/config.py tests/test_config.py
git commit -m "refactor: remove dnd5e_base_url from configuration"
```

---

## Task 12: Update list_documents Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/list_documents.py:4,39`

**Step 1: Update docstring to remove D&D 5e API reference**

Change from:
```python
"""Tool for listing available D&D content documents across all sources.

This module provides document discovery functionality that shows all documents
available in the cache across all sources (Open5e, D&D 5e API, OrcBrew).
"""
```

To:
```python
"""Tool for listing available D&D content documents across all sources.

This module provides document discovery functionality that shows all documents
available in the cache across all sources (Open5e, OrcBrew).
"""
```

**Step 2: Update source filter documentation**

Change from:
```python
        source: Optional source filter. Valid values:
            - "open5e_v2": Open5e API documents (SRD, Kobold Press, etc.)
            - "dnd5e_api": Official D&D 5e API (SRD only)
            - "orcbrew": Imported OrcBrew homebrew files
            - None (default): Show documents from all sources
```

To:
```python
        source: Optional source filter. Valid values:
            - "open5e_v2": Open5e API documents (SRD, Kobold Press, etc.)
            - "orcbrew": Imported OrcBrew homebrew files
            - None (default): Show documents from all sources
```

**Step 3: Run list_documents tests**

```bash
uv run pytest tests/test_tools/test_list_documents.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/tools/list_documents.py
git commit -m "docs: remove D&D 5e API references from list_documents tool"
```

---

## Task 13: Update RuleRepository Protocol

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/rule.py:47`

**Step 1: Rename get_conditions_dnd5e to get_conditions in protocol**

Change from:
```python
class RuleClient(Protocol):
    ...
    async def get_conditions_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch conditions from API."""
        ...
```

To:
```python
class RuleClient(Protocol):
    ...
    async def get_conditions(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch conditions from API."""
        ...
```

**Step 2: Update _search_conditions method**

Change from:
```python
            conditions: list[dict[str, Any]] = await self.client.get_conditions_dnd5e(
                limit=limit, **filters
            )
```

To:
```python
            conditions: list[dict[str, Any]] = await self.client.get_conditions(
                limit=limit, **filters
            )
```

**Step 3: Run rule repository tests**

```bash
uv run pytest tests/test_repositories/test_rule.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/repositories/rule.py
git commit -m "refactor: rename get_conditions_dnd5e to get_conditions in RuleRepository"
```

---

## Task 14: Run Full Test Suite

**Step 1: Run all tests**

```bash
uv run pytest -v
```

Expected: All tests PASS

**Step 2: Run type checking**

```bash
just type-check
```

Expected: No type errors

**Step 3: Run linting**

```bash
just lint
```

Expected: No lint errors

**Step 4: Run live tests**

```bash
uv run pytest -m live -v
```

Expected: All live tests PASS (critical per AGENTS.md)

**Step 5: Commit any remaining fixes**

```bash
git add -A
git commit -m "fix: address remaining test and lint issues"
```

---

## Task 15: Update Documentation

**Files:**
- Modify: `docs/apis/5e-srd-api.md` (if exists, delete or update)
- Modify: `README.md` (if references D&D 5e API)

**Step 1: Check for D&D 5e API documentation**

```bash
ls docs/apis/
```

**Step 2: Remove or update 5e-srd-api.md**

If the file exists and is solely about D&D 5e API, delete it. If it contains useful information, update it to reference Open5e instead.

**Step 3: Update README.md if needed**

Search for D&D 5e API references and update them.

**Step 4: Commit**

```bash
git add -A
git commit -m "docs: remove D&D 5e API references from documentation"
```

---

## Task 16: Archive Completed Specs

**Files:**
- Move: `openspec/specs/dnd5e-api-client/` to archive
- Move: `openspec/specs/complete-dnd5e-client/` to archive

**Step 1: Archive the specs**

```bash
mkdir -p openspec/changes/archive/dnd5e-api-client
mv openspec/specs/dnd5e-api-client openspec/changes/archive/
mv openspec/specs/complete-dnd5e-client openspec/changes/archive/
```

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: archive D&D 5e API client specs"
```

---

## Task 17: Final Verification

**Step 1: Run complete quality checks**

```bash
just check
```

Expected: All checks pass

**Step 2: Run live tests one more time**

```bash
uv run pytest -m live -v
```

Expected: All live tests PASS

**Step 3: Verify no D&D 5e API references remain in source code**

```bash
rg -i "dnd5e" src/ --type py
rg -i "dnd5eapi" src/ --type py
```

Expected: No results (or only in archived files)

**Step 4: Final commit if needed**

```bash
git add -A
git commit -m "chore: final cleanup after D&D 5e API removal"
```

---

## Summary of Files Changed

### Deleted Files:
- `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- `tests/test_api_clients/test_dnd5e_api.py`

### Modified Source Files:
- `src/lorekeeper_mcp/api_clients/__init__.py`
- `src/lorekeeper_mcp/api_clients/factory.py`
- `src/lorekeeper_mcp/repositories/character_option.py`
- `src/lorekeeper_mcp/repositories/factory.py`
- `src/lorekeeper_mcp/repositories/spell.py`
- `src/lorekeeper_mcp/repositories/rule.py`
- `src/lorekeeper_mcp/tools/list_documents.py`
- `src/lorekeeper_mcp/config.py`

### Modified Test Files:
- `tests/test_api_clients/test_factory.py`
- `tests/test_repositories/test_spell.py`
- `tests/test_tools/test_integration.py`
- `tests/test_tools/conftest.py`
- `tests/test_config.py`

### Documentation:
- `docs/apis/5e-srd-api.md` (delete or archive)
- `README.md` (update if needed)

### Specs to Archive:
- `openspec/specs/dnd5e-api-client/`
- `openspec/specs/complete-dnd5e-client/`
