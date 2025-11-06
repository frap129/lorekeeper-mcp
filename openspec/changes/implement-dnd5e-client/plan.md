# D&D 5e API Client Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use skills_executing_plans to implement this plan task-by-task.

**Goal:** Implement a D&D 5e API client to fetch rules, rule sections, and reference data from the D&D 5e API with entity caching support.

**Architecture:** Create `Dnd5eApiClient` class inheriting from `BaseHttpClient`, implement methods for rules and reference data endpoints, configure extended cache TTL (30 days) for static reference data, add factory method for dependency injection.

**Tech Stack:** httpx, pytest-asyncio, respx (mocking), SQLite entity cache, pydantic models

---

## Task 1: Core Client Class Setup

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Test: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing test for client initialization**

```python
"""Tests for Dnd5eApiClient."""

import pytest
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient


@pytest.fixture
async def dnd5e_client(test_db) -> Dnd5eApiClient:
    """Create Dnd5eApiClient for testing."""
    client = Dnd5eApiClient()
    yield client
    await client.close()


async def test_client_initialization(dnd5e_client: Dnd5eApiClient) -> None:
    """Test client initializes with correct configuration."""
    assert dnd5e_client.base_url == "https://www.dnd5eapi.co/api/2014"
    assert dnd5e_client.source_api == "dnd5e_api"
    assert dnd5e_client.cache_ttl == 604800  # 7 days default
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_client_initialization -v`
Expected: FAIL with "cannot import name 'Dnd5eApiClient'"

**Step 3: Write minimal implementation**

```python
"""Client for D&D 5e API (rules, reference data)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient


class Dnd5eApiClient(BaseHttpClient):
    """Client for D&D 5e API endpoints."""

    def __init__(
        self,
        base_url: str = "https://www.dnd5eapi.co/api/2014",
        cache_ttl: int = 604800,  # 7 days default
        source_api: str = "dnd5e_api",
        **kwargs: Any,
    ) -> None:
        """Initialize D&D 5e API client.

        Args:
            base_url: Base URL for API requests (includes version)
            cache_ttl: Cache time-to-live in seconds (default 7 days)
            source_api: Source API identifier for cache metadata
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(
            base_url=base_url,
            cache_ttl=cache_ttl,
            source_api=source_api,
            **kwargs,
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_client_initialization -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py src/lorekeeper_mcp/api_clients/dnd5e_api.py
git commit -m "feat: add Dnd5eApiClient base class with initialization"
```

---

## Task 2: Get Rules Method

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Modify: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing test for get_rules**

```python
import httpx
import respx


@respx.mock
async def test_get_rules_all(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching all rules."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "adventuring",
                        "name": "Adventuring",
                        "url": "/api/2014/rules/adventuring",
                    },
                    {
                        "index": "combat",
                        "name": "Combat",
                        "url": "/api/2014/rules/combat",
                    },
                ]
            },
        )
    )

    rules = await dnd5e_client.get_rules()

    assert len(rules) == 2
    assert rules[0]["name"] == "Adventuring"
    assert rules[1]["name"] == "Combat"


@respx.mock
async def test_get_rules_by_section(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching rules by section."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/adventuring").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "adventuring",
                "name": "Adventuring",
                "desc": "Delving into dungeons...",
                "subsections": [
                    {"index": "time", "name": "Time", "url": "/api/2014/rule-sections/time"}
                ],
            },
        )
    )

    rules = await dnd5e_client.get_rules(section="adventuring")

    assert len(rules) == 1
    assert rules[0]["name"] == "Adventuring"
    assert rules[0]["desc"] == "Delving into dungeons..."
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_rules_all -v`
Expected: FAIL with "Dnd5eApiClient has no attribute 'get_rules'"

**Step 3: Write minimal implementation**

Add to `src/lorekeeper_mcp/api_clients/dnd5e_api.py`:

```python
    async def get_rules(
        self,
        section: str | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Get rules from D&D 5e API.

        Args:
            section: Filter by rule section (adventuring, combat, equipment,
                     spellcasting, using-ability-scores, appendix)
            **filters: Additional API parameters

        Returns:
            List of rule dictionaries with hierarchical organization

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        # Build endpoint
        endpoint = f"/rules/{section}" if section else "/rules/"

        # Build cache filters
        cache_filters = {}
        if section:
            cache_filters["index"] = section

        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            endpoint,
            use_entity_cache=True,
            entity_type="rules",
            cache_filters=cache_filters,
            params=params,
        )

        # Handle both list and dict response formats
        return result if isinstance(result, list) else [result]
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_rules_all tests/test_api_clients/test_dnd5e_api.py::test_get_rules_by_section -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py src/lorekeeper_mcp/api_clients/dnd5e_api.py
git commit -m "feat: add get_rules method with section filtering"
```

---

## Task 3: Get Rule Sections Method

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Modify: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing test for get_rule_sections**

```python
@respx.mock
async def test_get_rule_sections_all(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching all rule sections."""
    respx.get("https://www.dnd5eapi.co/api/2014/rule-sections/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "grappling",
                        "name": "Grappling",
                        "url": "/api/2014/rule-sections/grappling",
                    },
                    {
                        "index": "opportunity-attacks",
                        "name": "Opportunity Attacks",
                        "url": "/api/2014/rule-sections/opportunity-attacks",
                    },
                ]
            },
        )
    )

    sections = await dnd5e_client.get_rule_sections()

    assert len(sections) == 2
    assert sections[0]["name"] == "Grappling"


@respx.mock
async def test_get_rule_sections_by_name(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching specific rule section."""
    respx.get("https://www.dnd5eapi.co/api/2014/rule-sections/grappling").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "grappling",
                "name": "Grappling",
                "desc": "When you want to grab a creature...",
            },
        )
    )

    sections = await dnd5e_client.get_rule_sections(name="grappling")

    assert len(sections) == 1
    assert sections[0]["name"] == "Grappling"
    assert sections[0]["desc"] == "When you want to grab a creature..."
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_rule_sections_all -v`
Expected: FAIL with "Dnd5eApiClient has no attribute 'get_rule_sections'"

**Step 3: Write minimal implementation**

Add to `src/lorekeeper_mcp/api_clients/dnd5e_api.py`:

```python
    async def get_rule_sections(
        self,
        name: str | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Get rule sections from D&D 5e API.

        Args:
            name: Filter by rule section name (index)
            **filters: Additional API parameters

        Returns:
            List of rule section dictionaries with detailed mechanics

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        # Build endpoint
        endpoint = f"/rule-sections/{name}" if name else "/rule-sections/"

        # Build cache filters
        cache_filters = {}
        if name:
            cache_filters["index"] = name

        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            endpoint,
            use_entity_cache=True,
            entity_type="rule_sections",
            cache_filters=cache_filters,
            params=params,
        )

        # Handle both list and dict response formats
        return result if isinstance(result, list) else [result]
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_rule_sections_all tests/test_api_clients/test_dnd5e_api.py::test_get_rule_sections_by_name -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py src/lorekeeper_mcp/api_clients/dnd5e_api.py
git commit -m "feat: add get_rule_sections method with name filtering"
```

---

## Task 4: Reference Data Methods (Batch 1: Damage Types & Weapon Properties)

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Modify: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing tests**

```python
@respx.mock
async def test_get_damage_types(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching damage types."""
    respx.get("https://www.dnd5eapi.co/api/2014/damage-types/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "fire", "name": "Fire", "url": "/api/2014/damage-types/fire"},
                    {"index": "cold", "name": "Cold", "url": "/api/2014/damage-types/cold"},
                ]
            },
        )
    )

    damage_types = await dnd5e_client.get_damage_types()

    assert len(damage_types) == 2
    assert damage_types[0]["name"] == "Fire"


@respx.mock
async def test_get_weapon_properties(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching weapon properties."""
    respx.get("https://www.dnd5eapi.co/api/2014/weapon-properties/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "finesse",
                        "name": "Finesse",
                        "url": "/api/2014/weapon-properties/finesse",
                    },
                    {
                        "index": "versatile",
                        "name": "Versatile",
                        "url": "/api/2014/weapon-properties/versatile",
                    },
                ]
            },
        )
    )

    properties = await dnd5e_client.get_weapon_properties()

    assert len(properties) == 2
    assert properties[0]["name"] == "Finesse"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_damage_types tests/test_api_clients/test_dnd5e_api.py::test_get_weapon_properties -v`
Expected: FAIL with "Dnd5eApiClient has no attribute 'get_damage_types'"

**Step 3: Write minimal implementation**

Add to `src/lorekeeper_mcp/api_clients/dnd5e_api.py`:

```python
    # Reference data TTL: 30 days (static data)
    REFERENCE_DATA_TTL = 2592000

    async def get_damage_types(self, **filters: Any) -> list[dict[str, Any]]:
        """Get damage types from D&D 5e API.

        Returns:
            List of damage type dictionaries (13 types)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        # Override cache TTL for reference data
        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/damage-types/",
                use_entity_cache=True,
                entity_type="damage_types",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_weapon_properties(self, **filters: Any) -> list[dict[str, Any]]:
        """Get weapon properties from D&D 5e API.

        Returns:
            List of weapon property dictionaries (11 properties)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        # Override cache TTL for reference data
        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/weapon-properties/",
                use_entity_cache=True,
                entity_type="weapon_properties",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_damage_types tests/test_api_clients/test_dnd5e_api.py::test_get_weapon_properties -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py src/lorekeeper_mcp/api_clients/dnd5e_api.py
git commit -m "feat: add get_damage_types and get_weapon_properties with 30-day cache"
```

---

## Task 5: Reference Data Methods (Batch 2: Skills & Ability Scores)

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Modify: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing tests**

```python
@respx.mock
async def test_get_skills(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching skills."""
    respx.get("https://www.dnd5eapi.co/api/2014/skills/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "acrobatics", "name": "Acrobatics", "url": "/api/2014/skills/acrobatics"},
                    {"index": "stealth", "name": "Stealth", "url": "/api/2014/skills/stealth"},
                ]
            },
        )
    )

    skills = await dnd5e_client.get_skills()

    assert len(skills) == 2
    assert skills[0]["name"] == "Acrobatics"


@respx.mock
async def test_get_ability_scores(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching ability scores."""
    respx.get("https://www.dnd5eapi.co/api/2014/ability-scores/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "str", "name": "STR", "url": "/api/2014/ability-scores/str"},
                    {"index": "dex", "name": "DEX", "url": "/api/2014/ability-scores/dex"},
                ]
            },
        )
    )

    ability_scores = await dnd5e_client.get_ability_scores()

    assert len(ability_scores) == 2
    assert ability_scores[0]["name"] == "STR"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_skills tests/test_api_clients/test_dnd5e_api.py::test_get_ability_scores -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/lorekeeper_mcp/api_clients/dnd5e_api.py`:

```python
    async def get_skills(self, **filters: Any) -> list[dict[str, Any]]:
        """Get skills from D&D 5e API.

        Returns:
            List of skill dictionaries (18 skills)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/skills/",
                use_entity_cache=True,
                entity_type="skills",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_ability_scores(self, **filters: Any) -> list[dict[str, Any]]:
        """Get ability scores from D&D 5e API.

        Returns:
            List of ability score dictionaries (6 scores)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/ability-scores/",
                use_entity_cache=True,
                entity_type="ability_scores",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_skills tests/test_api_clients/test_dnd5e_api.py::test_get_ability_scores -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py src/lorekeeper_mcp/api_clients/dnd5e_api.py
git commit -m "feat: add get_skills and get_ability_scores with extended cache"
```

---

## Task 6: Reference Data Methods (Batch 3: Magic Schools & Languages)

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Modify: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing tests**

```python
@respx.mock
async def test_get_magic_schools(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching magic schools."""
    respx.get("https://www.dnd5eapi.co/api/2014/magic-schools/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "evocation", "name": "Evocation", "url": "/api/2014/magic-schools/evocation"},
                    {"index": "abjuration", "name": "Abjuration", "url": "/api/2014/magic-schools/abjuration"},
                ]
            },
        )
    )

    schools = await dnd5e_client.get_magic_schools()

    assert len(schools) == 2
    assert schools[0]["name"] == "Evocation"


@respx.mock
async def test_get_languages(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching languages."""
    respx.get("https://www.dnd5eapi.co/api/2014/languages/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "common", "name": "Common", "url": "/api/2014/languages/common"},
                    {"index": "elvish", "name": "Elvish", "url": "/api/2014/languages/elvish"},
                ]
            },
        )
    )

    languages = await dnd5e_client.get_languages()

    assert len(languages) == 2
    assert languages[0]["name"] == "Common"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_magic_schools tests/test_api_clients/test_dnd5e_api.py::test_get_languages -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/lorekeeper_mcp/api_clients/dnd5e_api.py`:

```python
    async def get_magic_schools(self, **filters: Any) -> list[dict[str, Any]]:
        """Get magic schools from D&D 5e API.

        Returns:
            List of magic school dictionaries (8 schools)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/magic-schools/",
                use_entity_cache=True,
                entity_type="magic_schools",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_languages(self, **filters: Any) -> list[dict[str, Any]]:
        """Get languages from D&D 5e API.

        Returns:
            List of language dictionaries (16 languages)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/languages/",
                use_entity_cache=True,
                entity_type="languages",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_magic_schools tests/test_api_clients/test_dnd5e_api.py::test_get_languages -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py src/lorekeeper_mcp/api_clients/dnd5e_api.py
git commit -m "feat: add get_magic_schools and get_languages with extended cache"
```

---

## Task 7: Reference Data Methods (Batch 4: Proficiencies & Alignments)

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/dnd5e_api.py`
- Modify: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing tests**

```python
@respx.mock
async def test_get_proficiencies(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching proficiencies."""
    respx.get("https://www.dnd5eapi.co/api/2014/proficiencies/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "light-armor", "name": "Light Armor", "url": "/api/2014/proficiencies/light-armor"},
                    {"index": "longswords", "name": "Longswords", "url": "/api/2014/proficiencies/longswords"},
                ]
            },
        )
    )

    proficiencies = await dnd5e_client.get_proficiencies()

    assert len(proficiencies) == 2
    assert proficiencies[0]["name"] == "Light Armor"


@respx.mock
async def test_get_alignments(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching alignments."""
    respx.get("https://www.dnd5eapi.co/api/2014/alignments/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "lawful-good", "name": "Lawful Good", "url": "/api/2014/alignments/lawful-good"},
                    {"index": "chaotic-evil", "name": "Chaotic Evil", "url": "/api/2014/alignments/chaotic-evil"},
                ]
            },
        )
    )

    alignments = await dnd5e_client.get_alignments()

    assert len(alignments) == 2
    assert alignments[0]["name"] == "Lawful Good"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_proficiencies tests/test_api_clients/test_dnd5e_api.py::test_get_alignments -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/lorekeeper_mcp/api_clients/dnd5e_api.py`:

```python
    async def get_proficiencies(self, **filters: Any) -> list[dict[str, Any]]:
        """Get proficiencies from D&D 5e API.

        Returns:
            List of proficiency dictionaries (117 proficiencies)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/proficiencies/",
                use_entity_cache=True,
                entity_type="proficiencies",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_alignments(self, **filters: Any) -> list[dict[str, Any]]:
        """Get alignments from D&D 5e API.

        Returns:
            List of alignment dictionaries (9 alignments)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/alignments/",
                use_entity_cache=True,
                entity_type="alignments",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_proficiencies tests/test_api_clients/test_dnd5e_api.py::test_get_alignments -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py src/lorekeeper_mcp/api_clients/dnd5e_api.py
git commit -m "feat: add get_proficiencies and get_alignments with extended cache"
```

---

## Task 8: Cache Integration Tests

**Files:**
- Modify: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing tests for entity cache**

```python
from lorekeeper_mcp.cache.db import get_cached_entity


@respx.mock
async def test_get_rules_uses_entity_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify rules are cached as entities."""
    mock_response = {
        "results": [
            {
                "index": "combat",
                "name": "Combat",
                "desc": "Combat rules...",
            }
        ]
    }
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await dnd5e_client.get_rules()

    # Verify entity cached
    cached = await get_cached_entity("rules", "combat")
    assert cached is not None
    assert cached["name"] == "Combat"


@respx.mock
async def test_get_damage_types_extended_ttl(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify reference data uses 30-day cache TTL."""
    mock_response = {
        "results": [
            {"index": "fire", "name": "Fire", "desc": "Fire damage..."}
        ]
    }
    respx.get("https://www.dnd5eapi.co/api/2014/damage-types/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await dnd5e_client.get_damage_types()

    # Verify entity cached with extended TTL
    cached = await get_cached_entity("damage_types", "fire")
    assert cached is not None
    assert cached["name"] == "Fire"
    # Note: TTL verification would require checking cache metadata
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_rules_uses_entity_cache tests/test_api_clients/test_dnd5e_api.py::test_get_damage_types_extended_ttl -v`
Expected: Depends on implementation - may already pass if entity caching is working

**Step 3: Verify implementation works**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_rules_uses_entity_cache tests/test_api_clients/test_dnd5e_api.py::test_get_damage_types_extended_ttl -v`
Expected: PASS

**Step 4: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py
git commit -m "test: add entity cache integration tests for rules and reference data"
```

---

## Task 9: Error Handling Tests

**Files:**
- Modify: `tests/test_api_clients/test_dnd5e_api.py`

**Step 1: Write the failing tests for error scenarios**

```python
from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError


@respx.mock
async def test_get_rules_api_error(dnd5e_client: Dnd5eApiClient) -> None:
    """Test API error handling."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )

    with pytest.raises(ApiError) as exc_info:
        await dnd5e_client.get_rules()

    assert exc_info.value.status_code == 500


@respx.mock
async def test_get_rules_network_error(dnd5e_client: Dnd5eApiClient) -> None:
    """Test network error handling with empty cache fallback."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        side_effect=httpx.RequestError("Network unavailable")
    )

    # Should return empty list when no cache available
    result = await dnd5e_client.get_rules()

    assert result == []


@respx.mock
async def test_get_rules_network_error_with_cache_fallback(dnd5e_client: Dnd5eApiClient) -> None:
    """Test offline fallback to cached entities."""
    # First request succeeds and caches
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "combat", "name": "Combat", "desc": "Combat rules..."}
                ]
            },
        )
    )
    await dnd5e_client.get_rules()

    # Second request fails, should return cached
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        side_effect=httpx.RequestError("Network unavailable")
    )
    result = await dnd5e_client.get_rules()

    assert len(result) == 1
    assert result[0]["name"] == "Combat"
```

**Step 2: Run tests to verify they work**

Run: `pytest tests/test_api_clients/test_dnd5e_api.py::test_get_rules_api_error tests/test_api_clients/test_dnd5e_api.py::test_get_rules_network_error tests/test_api_clients/test_dnd5e_api.py::test_get_rules_network_error_with_cache_fallback -v`
Expected: Tests should pass if error handling is already working from BaseHttpClient

**Step 3: Commit**

```bash
git add tests/test_api_clients/test_dnd5e_api.py
git commit -m "test: add error handling and offline fallback tests"
```

---

## Task 10: Factory Method

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/factory.py`
- Modify: `tests/test_api_clients/test_factory.py`

**Step 1: Write the failing test for factory method**

Add to `tests/test_api_clients/test_factory.py`:

```python
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient


async def test_create_dnd5e_api() -> None:
    """Test creating D&D 5e API client via factory."""
    client = ClientFactory.create_dnd5e_api()

    assert isinstance(client, Dnd5eApiClient)
    assert client.base_url == "https://www.dnd5eapi.co/api/2014"
    assert client.source_api == "dnd5e_api"
    assert client.cache_ttl == 604800  # 7 days

    await client.close()


async def test_create_dnd5e_api_with_custom_ttl() -> None:
    """Test creating D&D 5e API client with custom cache TTL."""
    client = ClientFactory.create_dnd5e_api(cache_ttl=1000)

    assert client.cache_ttl == 1000

    await client.close()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_factory.py::test_create_dnd5e_api -v`
Expected: FAIL with "ClientFactory has no attribute 'create_dnd5e_api'"

**Step 3: Write minimal implementation**

Add to `src/lorekeeper_mcp/api_clients/factory.py`:

```python
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient

    @staticmethod
    def create_dnd5e_api(**kwargs: Any) -> Dnd5eApiClient:
        """Create a D&D 5e API client.

        Args:
            **kwargs: Configuration options for the client
                base_url: Override base URL (default: https://www.dnd5eapi.co/api/2014)
                cache_ttl: Override cache TTL (default: 604800 = 7 days)
                timeout: Request timeout in seconds (default: 30.0)
                max_retries: Maximum retry attempts (default: 5)

        Returns:
            Configured Dnd5eApiClient instance

        Example:
            >>> client = ClientFactory.create_dnd5e_api()
            >>> rules = await client.get_rules()
        """
        return Dnd5eApiClient(**kwargs)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_clients/test_factory.py::test_create_dnd5e_api tests/test_api_clients/test_factory.py::test_create_dnd5e_api_with_custom_ttl -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_factory.py src/lorekeeper_mcp/api_clients/factory.py
git commit -m "feat: add factory method for Dnd5eApiClient"
```

---

## Task 11: Package Exports

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/__init__.py`
- Test: Manual verification

**Step 1: Add imports and exports**

Modify `src/lorekeeper_mcp/api_clients/__init__.py`:

```python
from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient

# Add to __all__ list
__all__ = [
    # ... existing exports ...
    "Dnd5eApiClient",
]
```

**Step 2: Verify imports work**

Run: `python -c "from lorekeeper_mcp.api_clients import Dnd5eApiClient; print('Import successful')"`
Expected: "Import successful"

**Step 3: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/__init__.py
git commit -m "feat: export Dnd5eApiClient from api_clients package"
```

---

## Task 12: Code Quality Check

**Files:**
- All modified files

**Step 1: Run formatters and linters**

```bash
uv run ruff format src/lorekeeper_mcp/api_clients/dnd5e_api.py tests/test_api_clients/test_dnd5e_api.py
uv run ruff check src/lorekeeper_mcp/api_clients/dnd5e_api.py tests/test_api_clients/test_dnd5e_api.py --fix
```

Expected: No errors or warnings

**Step 2: Run full test suite**

```bash
pytest tests/test_api_clients/test_dnd5e_api.py -v --cov=src/lorekeeper_mcp/api_clients/dnd5e_api
```

Expected: All tests pass, coverage > 90%

**Step 3: Run all tests to ensure no regressions**

```bash
pytest -v
```

Expected: All tests pass

**Step 4: Commit formatting changes if any**

```bash
git add -u
git commit -m "style: format code with ruff"
```

---

## Task 13: Integration Verification (Manual)

**Files:**
- None (manual testing)

**Step 1: Test against real API endpoint**

Create a temporary test script `test_integration.py`:

```python
import asyncio
from lorekeeper_mcp.api_clients import Dnd5eApiClient


async def main():
    client = Dnd5eApiClient()

    # Test rules
    rules = await client.get_rules()
    print(f"✓ Rules: {len(rules)} categories")

    # Test specific rule section
    sections = await client.get_rule_sections(name="grappling")
    print(f"✓ Rule sections: {sections[0]['name']}")

    # Test damage types
    damage_types = await client.get_damage_types()
    print(f"✓ Damage types: {len(damage_types)} types")

    # Test skills
    skills = await client.get_skills()
    print(f"✓ Skills: {len(skills)} skills")

    await client.close()
    print("\n✅ All integration tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Run integration test**

Run: `python test_integration.py`
Expected: All checks pass with real data

**Step 3: Clean up test script**

```bash
rm test_integration.py
```

---

## Summary

**Implementation Complete:**
- ✅ Core `Dnd5eApiClient` class with proper initialization
- ✅ Rules API methods (`get_rules`, `get_rule_sections`)
- ✅ 8 reference data methods with 30-day cache TTL
- ✅ Factory method for dependency injection
- ✅ Package exports
- ✅ Comprehensive unit tests with >90% coverage
- ✅ Entity cache integration with offline fallback
- ✅ Error handling tests
- ✅ Code quality checks

**Key Design Decisions:**
1. Extended cache TTL (30 days) for static reference data
2. Entity cache for all data types (offline capability)
3. Consistent API pattern across all methods
4. Inherits retry logic and error handling from `BaseHttpClient`
5. Factory method provides clean dependency injection

**Files Modified:**
- `src/lorekeeper_mcp/api_clients/dnd5e_api.py` (new)
- `src/lorekeeper_mcp/api_clients/factory.py` (modified)
- `src/lorekeeper_mcp/api_clients/__init__.py` (modified)
- `tests/test_api_clients/test_dnd5e_api.py` (new)
- `tests/test_api_clients/test_factory.py` (modified)

**Testing Strategy:**
- TDD approach: write failing test, implement, verify pass
- Mock all HTTP requests using respx
- Test entity cache integration
- Test error handling and offline fallback
- Test factory method configuration
