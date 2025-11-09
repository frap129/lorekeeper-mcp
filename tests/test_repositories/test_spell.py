"""Tests for SpellRepository implementation."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.models.spell import Spell
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
    mock_client.get_spells.assert_called_once_with(level=3)
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

    # Client should be called with all filters
    mock_client.get_spells.assert_called_once_with(level=3, school="Evocation")
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
    mock_client.get_spells.assert_called_once_with(level=9)


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
