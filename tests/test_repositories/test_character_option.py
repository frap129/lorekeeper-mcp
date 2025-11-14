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


@pytest.mark.asyncio
async def test_character_option_repository_search_feats_no_limit_defaults_to_100(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test feat lookup defaults to api_limit=100 when no limit specified."""
    mock_cache.get_entities.return_value = []
    # Create 25 mock feats to return from API
    mock_feats = [{"name": f"Feat {i}", "slug": f"feat-{i}"} for i in range(25)]
    mock_client.get_feats.return_value = mock_feats
    mock_cache.store_entities.return_value = 25

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(option_type="feat")

    # Should return all 25 feats (no client-side limit applied)
    assert len(results) == 25
    # Verify client.get_feats was called with limit=100
    mock_client.get_feats.assert_called_once_with(limit=100)


@pytest.mark.asyncio
async def test_character_option_repository_search_feats_with_explicit_limit(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test feat lookup respects explicit limit specified by user."""
    mock_cache.get_entities.return_value = []
    # Create 25 mock feats to return from API
    mock_feats = [{"name": f"Feat {i}", "slug": f"feat-{i}"} for i in range(25)]
    mock_client.get_feats.return_value = mock_feats
    mock_cache.store_entities.return_value = 25

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(option_type="feat", limit=5)

    # Should return only 5 feats (user-specified limit applied on client side)
    assert len(results) == 5
    # Verify client.get_feats was called with limit=5 (not the default 100)
    mock_client.get_feats.assert_called_once_with(limit=5)


@pytest.mark.asyncio
async def test_character_option_repository_search_with_document_filter() -> None:
    """Test CharacterOptionRepository.search passes document filter to cache."""
    # Mock client and cache
    mock_client = MagicMock()
    mock_client.get_classes = AsyncMock(return_value=[])

    mock_cache = MagicMock()
    mock_cache.get_entities = AsyncMock(return_value=[])
    mock_cache.store_entities = AsyncMock(return_value=0)

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)

    # Search with document filter
    await repo.search(option_type="class", document=["srd-5e"])

    # Verify cache was called with document filter
    mock_cache.get_entities.assert_called_once()
    call_args = mock_cache.get_entities.call_args
    # Check that document was passed to cache
    assert call_args[1].get("document") == ["srd-5e"]


@pytest.mark.asyncio
async def test_character_option_repository_search_document_not_passed_to_api() -> None:
    """Test that document filter is NOT passed to API (cache-only filter)."""
    # Mock client and cache
    mock_client = MagicMock()
    mock_client.get_classes = AsyncMock(return_value=[])

    mock_cache = MagicMock()
    mock_cache.get_entities = AsyncMock(return_value=[])  # Cache miss
    mock_cache.store_entities = AsyncMock(return_value=0)

    repo = CharacterOptionRepository(client=mock_client, cache=mock_cache)

    # Search with document filter (cache miss)
    await repo.search(option_type="class", document="srd-5e")

    # Verify API was called WITHOUT document parameter
    mock_client.get_classes.assert_called_once()
    call_kwargs = mock_client.get_classes.call_args[1]
    assert "document" not in call_kwargs
