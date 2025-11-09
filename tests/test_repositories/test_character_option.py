"""Tests for CharacterOptionRepository implementation."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.repositories.character_option import CharacterOptionRepository


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
    client.get_classes = AsyncMock()
    client.get_races = AsyncMock()
    client.get_backgrounds = AsyncMock()
    client.get_feats = AsyncMock()
    client.get_conditions = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_character_option_repository_search_classes(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search filtering by character classes."""
    mock_cache.get_entities.return_value = []
    mock_client.get_classes.return_value = [{"name": "Barbarian", "slug": "barbarian"}]
    mock_cache.store_entities.return_value = 1

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(option_type="class")

    assert len(results) == 1
    mock_client.get_classes.assert_called_once()


@pytest.mark.asyncio
async def test_character_option_repository_search_races(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search filtering by races."""
    mock_cache.get_entities.return_value = [{"name": "Human", "slug": "human"}]

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(option_type="race")

    assert len(results) == 1
    mock_client.get_races.assert_not_called()


@pytest.mark.asyncio
async def test_character_option_repository_search_backgrounds(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search filtering by backgrounds."""
    mock_cache.get_entities.return_value = []
    mock_client.get_backgrounds.return_value = [{"name": "Acolyte", "slug": "acolyte"}]
    mock_cache.store_entities.return_value = 1

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(option_type="background")

    assert len(results) == 1
    mock_client.get_backgrounds.assert_called_once()


@pytest.mark.asyncio
async def test_character_option_repository_search_feats(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search filtering by feats."""
    mock_cache.get_entities.return_value = [{"name": "Alert", "slug": "alert"}]

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(option_type="feat")

    assert len(results) == 1


@pytest.mark.asyncio
async def test_character_option_repository_search_conditions(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search filtering by conditions."""
    mock_cache.get_entities.return_value = []
    mock_client.get_conditions.return_value = [{"name": "Blinded", "slug": "blinded"}]
    mock_cache.store_entities.return_value = 1

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(option_type="condition")

    assert len(results) == 1
    mock_client.get_conditions.assert_called_once()
