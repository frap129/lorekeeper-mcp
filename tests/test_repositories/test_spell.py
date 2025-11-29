"""Tests for SpellRepository implementation."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.models import Spell
from lorekeeper_mcp.repositories.spell import SpellRepository


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create mock cache for testing."""
    cache = MagicMock()
    cache.get_entities = AsyncMock()
    cache.store_entities = AsyncMock()
    return cache


@pytest.fixture
def mock_client() -> MagicMock:
    """Create mock API client for testing."""
    client = MagicMock()
    client.get_spells = AsyncMock()
    return client


@pytest.fixture
def spell_data() -> list[dict[str, Any]]:
    """Provide sample spell data for testing."""
    return [
        {
            "name": "Fireball",
            "slug": "fireball",
            "level": 3,
            "school": "Evocation",
            "casting_time": "1 action",
            "range": "150 feet",
            "components": "V, S, M",
            "duration": "Instantaneous",
        },
        {
            "name": "Magic Missile",
            "slug": "magic-missile",
            "level": 1,
            "school": "Evocation",
            "casting_time": "1 action",
            "range": "120 feet",
            "components": "V, S",
            "duration": "Instantaneous",
        },
        {
            "name": "Mage Armor",
            "slug": "mage-armor",
            "level": 1,
            "school": "Abjuration",
            "casting_time": "1 action",
            "range": "Touch",
            "components": "V, S, M",
            "duration": "8 hours",
        },
    ]


@pytest.fixture
def spells(spell_data: list[dict[str, Any]]) -> list[Spell]:
    """Convert spell data to Spell models."""
    return [Spell.model_validate(data) for data in spell_data]


@pytest.mark.asyncio
async def test_spell_repository_get_all_from_cache(
    mock_cache: MagicMock, mock_client: MagicMock, spell_data: list[dict[str, Any]]
) -> None:
    """Test that get_all returns cached spells when available."""
    # Cache hit - spells already cached
    mock_cache.get_entities.return_value = spell_data
    mock_client.get_spells.return_value = []

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    assert len(results) == 3
    assert results[0].name == "Fireball"
    # API should not be called since cache hit
    mock_client.get_spells.assert_not_called()
    # Cache should be queried
    mock_cache.get_entities.assert_called_once_with("spells")


@pytest.mark.asyncio
async def test_spell_repository_get_all_cache_miss(
    mock_cache: MagicMock, mock_client: MagicMock, spell_data: list[dict[str, Any]]
) -> None:
    """Test that get_all fetches from API on cache miss and stores in cache."""
    # Cache miss - empty cache
    mock_cache.get_entities.return_value = []
    # Create Spell objects from spell_data
    spells = [Spell.model_validate(data) for data in spell_data]
    mock_client.get_spells.return_value = spells
    mock_cache.store_entities.return_value = 3

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    assert len(results) == 3
    # API should be called since cache miss
    mock_client.get_spells.assert_called_once()
    # Results should be stored in cache
    mock_cache.store_entities.assert_called_once()


@pytest.mark.asyncio
async def test_spell_repository_search_by_level(
    mock_cache: MagicMock, mock_client: MagicMock, spell_data: list[dict[str, Any]]
) -> None:
    """Test search filtering by spell level."""
    # Cache hit with level filter
    level_3_spells = [spell_data[0]]  # Only Fireball is level 3
    mock_cache.get_entities.return_value = level_3_spells
    mock_client.get_spells.return_value = []

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(level=3)

    assert len(results) == 1
    assert results[0].name == "Fireball"
    assert results[0].level == 3
    mock_cache.get_entities.assert_called_once_with("spells", level=3)


@pytest.mark.asyncio
async def test_spell_repository_search_by_school(
    mock_cache: MagicMock, mock_client: MagicMock, spell_data: list[dict[str, Any]]
) -> None:
    """Test search filtering by spell school."""
    # Cache hit with school filter
    evocation_spells = [spell_data[0], spell_data[1]]  # Fireball and Magic Missile
    mock_cache.get_entities.return_value = evocation_spells

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(school="Evocation")

    assert len(results) == 2
    assert all(spell.school == "Evocation" for spell in results)
    mock_cache.get_entities.assert_called_once_with("spells", school="Evocation")


@pytest.mark.asyncio
async def test_spell_repository_search_cache_miss_with_filters(
    mock_cache: MagicMock, mock_client: MagicMock, spell_data: list[dict[str, Any]]
) -> None:
    """Test search with cache miss fetches from API."""
    # Cache miss
    mock_cache.get_entities.return_value = []
    # API returns filtered results
    level_3_spells = [Spell.model_validate(spell_data[0])]
    mock_client.get_spells.return_value = level_3_spells
    mock_cache.store_entities.return_value = 1

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(level=3)

    assert len(results) == 1
    assert results[0].level == 3
    mock_client.get_spells.assert_called_once_with(limit=None, level=3)
    mock_cache.store_entities.assert_called_once()


@pytest.mark.asyncio
async def test_spell_repository_search_multiple_filters(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search with multiple filters."""
    mock_cache.get_entities.return_value = []
    mock_client.get_spells.return_value = []

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    await repo.search(level=3, school="Evocation")

    # Client should be called with all filters (school is mapped to school__key and lowercased)
    mock_client.get_spells.assert_called_once_with(limit=None, level=3, school__key="evocation")
    mock_cache.get_entities.assert_called_once_with("spells", level=3, school="Evocation")


@pytest.mark.asyncio
async def test_spell_repository_search_no_filters_returns_all(
    mock_cache: MagicMock, mock_client: MagicMock, spell_data: list[dict[str, Any]]
) -> None:
    """Test search with no filters returns all spells."""
    mock_cache.get_entities.return_value = spell_data

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.search()

    assert len(results) == 3
    mock_cache.get_entities.assert_called_once_with("spells")


@pytest.mark.asyncio
async def test_spell_repository_search_empty_result(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search that returns no results."""
    mock_cache.get_entities.return_value = []
    mock_client.get_spells.return_value = []

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(level=9)

    assert results == []
    mock_client.get_spells.assert_called_once_with(limit=None, level=9)


@pytest.mark.asyncio
async def test_spell_repository_cache_aside_pattern(
    mock_cache: MagicMock, mock_client: MagicMock, spell_data: list[dict[str, Any]]
) -> None:
    """Test that cache-aside pattern is correctly implemented.

    Pattern should be:
    1. Try to get from cache
    2. On cache miss, fetch from API
    3. Store fetched results in cache
    4. Return results
    """
    # First call returns empty (cache miss)
    mock_cache.get_entities.return_value = []
    spells = [Spell.model_validate(data) for data in spell_data]
    mock_client.get_spells.return_value = spells
    mock_cache.store_entities.return_value = len(spell_data)

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    # Verify cache-aside pattern:
    # 1. Check cache first
    mock_cache.get_entities.assert_called_once_with("spells")
    # 2. On miss, fetch from API
    mock_client.get_spells.assert_called_once_with()
    # 3. Store in cache
    mock_cache.store_entities.assert_called_once()
    # 4. Return results
    assert len(results) == 3


@pytest.mark.asyncio
async def test_spell_repository_search_with_document_filter() -> None:
    """Test SpellRepository.search passes document filter to cache."""
    # Mock client and cache
    mock_client = MagicMock()
    mock_client.get_spells = AsyncMock(return_value=[])

    mock_cache = MagicMock()
    mock_cache.get_entities = AsyncMock(return_value=[])
    mock_cache.store_entities = AsyncMock(return_value=0)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Search with document filter
    await repo.search(document=["srd-5e"])

    # Verify cache was called with document filter
    mock_cache.get_entities.assert_called_once()
    call_args = mock_cache.get_entities.call_args
    # Check that document was passed to cache
    assert call_args[1].get("document") == ["srd-5e"]


@pytest.mark.asyncio
async def test_spell_repository_search_document_not_passed_to_api() -> None:
    """Test that document filter is NOT passed to API (cache-only filter)."""
    # Mock client and cache
    mock_client = MagicMock()
    mock_client.get_spells = AsyncMock(return_value=[])

    mock_cache = MagicMock()
    mock_cache.get_entities = AsyncMock(return_value=[])  # Cache miss
    mock_cache.store_entities = AsyncMock(return_value=0)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Search with document filter (cache miss)
    await repo.search(level=3, document="srd-5e")

    # Verify API was called WITHOUT document parameter
    mock_client.get_spells.assert_called_once()
    call_kwargs = mock_client.get_spells.call_args[1]
    assert "document" not in call_kwargs
    # But level should be passed
    assert call_kwargs.get("level") == 3


@pytest.mark.asyncio
async def test_search_spells_by_document(
    mock_cache: MagicMock, mock_client: MagicMock, spell_data: list[dict[str, Any]]
) -> None:
    """Test filtering spells by document name."""
    # Add document to test data
    spell_with_doc = spell_data[0].copy()
    spell_with_doc["document"] = "System Reference Document 5.1"

    mock_cache.get_entities.return_value = [spell_with_doc]

    repo = SpellRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(document="System Reference Document 5.1")

    # Verify cache was called with document filter
    mock_cache.get_entities.assert_called_once()
    call_kwargs = mock_cache.get_entities.call_args[1]
    assert call_kwargs["document"] == "System Reference Document 5.1"

    assert len(results) == 1
    assert results[0].slug == "fireball"


def test_repository_parameter_mapping_with_open5e_client() -> None:
    """Test that repository correctly maps parameters for Open5e API."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Map parameters for Open5e
    result = repo._map_to_api_params(
        name="fireball",
        school="evocation",
        level_min=3,
        level_max=5,
    )

    # Verify mappings for Open5e
    assert result["name__icontains"] == "fireball"
    assert result["school__key"] == "evocation"
    assert result["level__gte"] == 3
    assert result["level__lte"] == 5


def test_open5e_operator_mapping() -> None:
    """Test Open5e-specific filter operator mappings."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Test name__icontains mapping
    result = repo._map_to_api_params(name="magic")
    assert "name__icontains" in result
    assert result["name__icontains"] == "magic"
    assert "name" not in result

    # Test school__key mapping
    result = repo._map_to_api_params(school="conjuration")
    assert "school__key" in result
    assert result["school__key"] == "conjuration"
    assert "school" not in result

    # Test level range mappings
    result = repo._map_to_api_params(level_min=1, level_max=3)
    assert "level__gte" in result
    assert "level__lte" in result
    assert result["level__gte"] == 1
    assert result["level__lte"] == 3

    # Test exact level match
    result = repo._map_to_api_params(level=2)
    assert result["level"] == 2


def test_repository_passthrough_exact_matches() -> None:
    """Test that exact match parameters are passed through correctly."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Test pass-through parameters for Open5e
    result = repo._map_to_api_params(
        level=2,
        concentration=True,
        ritual=False,
        casting_time="1 action",
    )

    assert result["level"] == 2
    assert result["concentration"] is True
    assert result["ritual"] is False
    assert result["casting_time"] == "1 action"


def test_repository_mixed_parameters() -> None:
    """Test mapping with both transformed and pass-through parameters."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Mix of transformed and pass-through parameters
    result = repo._map_to_api_params(
        name="cure",
        school="abjuration",
        level=2,
        concentration=True,
    )

    # Verify transformed parameters
    assert result["name__icontains"] == "cure"
    assert result["school__key"] == "abjuration"

    # Verify pass-through parameters
    assert result["level"] == 2
    assert result["concentration"] is True

    # Verify old parameter names are not present
    assert "name" not in result
    assert "school" not in result or result.get("school") != "abjuration"


def test_repository_class_key_mapping() -> None:
    """Test that class_key is mapped to classes__key with srd_ prefix."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Test class_key mapping - should add srd_ prefix
    result = repo._map_to_api_params(class_key="wizard")

    assert "classes__key" in result
    assert result["classes__key"] == "srd_wizard"
    assert "class_key" not in result


def test_repository_class_key_lowercase() -> None:
    """Test that class_key is converted to lowercase with srd_ prefix."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Test class_key lowercase conversion with srd_ prefix
    result = repo._map_to_api_params(class_key="Wizard")

    assert result["classes__key"] == "srd_wizard"


class TestSpellRepositorySemanticSearch:
    """Tests for SpellRepository semantic search support."""

    @pytest.mark.asyncio
    async def test_spell_repository_search_with_search_param(self) -> None:
        """Test that search() uses semantic_search when search param provided."""

        class MockClient:
            async def get_spells(self, **filters: Any) -> list[Spell]:
                return []

        class MockCache:
            def __init__(self) -> None:
                self.semantic_search_called = False
                self.get_entities_called = False
                self.search_query = ""

            async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
                self.get_entities_called = True
                return []

            async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
                return len(entities)

            async def semantic_search(
                self, entity_type: str, query: str, limit: int = 20, **filters: Any
            ) -> list[dict[str, Any]]:
                self.semantic_search_called = True
                self.search_query = query
                return []

        cache = MockCache()
        repo = SpellRepository(client=MockClient(), cache=cache)

        # Search with search param
        await repo.search(search="fire damage spells")

        # Should call semantic_search, not get_entities
        assert cache.semantic_search_called
        assert cache.search_query == "fire damage spells"

    @pytest.mark.asyncio
    async def test_spell_repository_search_without_search_param(self) -> None:
        """Test that search() uses get_entities when no search param."""

        class MockClient:
            async def get_spells(self, **filters: Any) -> list[Spell]:
                return []

        class MockCache:
            def __init__(self) -> None:
                self.semantic_search_called = False
                self.get_entities_called = False

            async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
                self.get_entities_called = True
                return []

            async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
                return len(entities)

            async def semantic_search(
                self, entity_type: str, query: str, limit: int = 20, **filters: Any
            ) -> list[dict[str, Any]]:
                self.semantic_search_called = True
                return []

        cache = MockCache()
        repo = SpellRepository(client=MockClient(), cache=cache)

        # Search without search param
        await repo.search(level=3)

        # Should call get_entities, not semantic_search
        assert cache.get_entities_called
        assert not cache.semantic_search_called

    @pytest.mark.asyncio
    async def test_spell_repository_semantic_search_with_filters(self) -> None:
        """Test that semantic search combines with scalar filters."""

        class MockClient:
            async def get_spells(self, **filters: Any) -> list[Spell]:
                return []

        class MockCache:
            def __init__(self) -> None:
                self.semantic_filters: dict[str, Any] = {}

            async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
                return []

            async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
                return len(entities)

            async def semantic_search(
                self, entity_type: str, query: str, limit: int = 20, **filters: Any
            ) -> list[dict[str, Any]]:
                self.semantic_filters = filters
                return []

        cache = MockCache()
        repo = SpellRepository(client=MockClient(), cache=cache)

        # Search with search param AND level filter
        await repo.search(search="fire", level=3, school="Evocation")

        # Filters should be passed to semantic_search
        assert cache.semantic_filters.get("level") == 3
        assert cache.semantic_filters.get("school") == "Evocation"

    @pytest.mark.asyncio
    async def test_spell_repository_semantic_search_fallback_on_not_implemented(
        self,
    ) -> None:
        """Test that semantic search falls back when cache doesn't support it."""

        class MockClient:
            async def get_spells(self, **filters: Any) -> list[Spell]:
                return []

        class MockCache:
            def __init__(self) -> None:
                self.get_entities_called = False

            async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
                self.get_entities_called = True
                return [
                    {
                        "slug": "fireball",
                        "name": "Fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "duration": "Instantaneous",
                    }
                ]

            async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
                return len(entities)

            async def semantic_search(
                self, entity_type: str, query: str, limit: int = 20, **filters: Any
            ) -> list[dict[str, Any]]:
                raise NotImplementedError("MockCache does not support semantic search")

        cache = MockCache()
        repo = SpellRepository(client=MockClient(), cache=cache)

        # Search with search param (should fall back to get_entities)
        results = await repo.search(search="fire")

        # Should have fallen back to get_entities
        assert cache.get_entities_called
        assert len(results) == 1


def test_repository_school_lowercase() -> None:
    """Test that school is converted to lowercase."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Test school lowercase conversion
    result = repo._map_to_api_params(school="Evocation")

    assert result["school__key"] == "evocation"


def test_repository_concentration_passthrough() -> None:
    """Test that concentration parameter is passed through correctly."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    # Test concentration passthrough - True
    result = repo._map_to_api_params(concentration=True)
    assert result["concentration"] is True

    # Test concentration passthrough - False
    result = repo._map_to_api_params(concentration=False)
    assert result["concentration"] is False


def test_repository_class_and_school_together() -> None:
    """Test class_key and school mapping together."""

    mock_cache = MagicMock()
    mock_client = MagicMock(spec=Open5eV2Client)

    repo = SpellRepository(client=mock_client, cache=mock_cache)

    result = repo._map_to_api_params(
        class_key="Sorcerer",
        school="Abjuration",
        concentration=True,
    )

    assert result["classes__key"] == "srd_sorcerer"
    assert result["school__key"] == "abjuration"
    assert result["concentration"] is True
