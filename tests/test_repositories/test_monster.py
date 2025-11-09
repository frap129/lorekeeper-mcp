"""Tests for MonsterRepository implementation."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.models.monster import Monster
from lorekeeper_mcp.repositories.monster import MonsterRepository


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
    client.get_monsters = AsyncMock()
    return client


@pytest.fixture
def monster_data() -> list[dict[str, Any]]:
    """Provide sample monster data for testing."""
    return [
        {
            "name": "Goblin",
            "slug": "goblin",
            "size": "Small",
            "type": "humanoid",
            "alignment": "Neutral Evil",
            "armor_class": 15,
            "hit_points": 7,
            "hit_dice": "2d6",
            "challenge_rating": "1/4",
        },
        {
            "name": "Orc",
            "slug": "orc",
            "size": "Medium",
            "type": "humanoid",
            "alignment": "Chaotic Evil",
            "armor_class": 13,
            "hit_points": 15,
            "hit_dice": "2d8 + 6",
            "challenge_rating": "1/2",
        },
        {
            "name": "Dragon",
            "slug": "dragon",
            "size": "Huge",
            "type": "dragon",
            "alignment": "Chaotic Evil",
            "armor_class": 20,
            "hit_points": 195,
            "hit_dice": "17d12 + 85",
            "challenge_rating": "16",
        },
    ]


@pytest.fixture
def monsters(monster_data: list[dict[str, Any]]) -> list[Monster]:
    """Convert monster data to Monster models."""
    return [Monster.model_validate(data) for data in monster_data]


@pytest.mark.asyncio
async def test_monster_repository_get_all_from_cache(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test that get_all returns cached monsters when available."""
    # Cache hit - monsters already cached
    mock_cache.get_entities.return_value = monster_data
    mock_client.get_monsters.return_value = []

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    assert len(results) == 3
    assert results[0].name == "Goblin"
    # API should not be called since cache hit
    mock_client.get_monsters.assert_not_called()
    # Cache should be queried
    mock_cache.get_entities.assert_called_once_with("monsters")


@pytest.mark.asyncio
async def test_monster_repository_get_all_cache_miss(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test that get_all fetches from API on cache miss and stores in cache."""
    # Cache miss - empty cache
    mock_cache.get_entities.return_value = []
    # Create Monster objects from monster_data
    monsters = [Monster.model_validate(data) for data in monster_data]
    mock_client.get_monsters.return_value = monsters
    mock_cache.store_entities.return_value = 3

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    assert len(results) == 3
    # API should be called since cache miss
    mock_client.get_monsters.assert_called_once()
    # Results should be stored in cache
    mock_cache.store_entities.assert_called_once()


@pytest.mark.asyncio
async def test_monster_repository_search_by_type(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search filtering by monster type."""
    # Cache hit with type filter
    humanoid_monsters = [monster_data[0], monster_data[1]]  # Goblin and Orc
    mock_cache.get_entities.return_value = humanoid_monsters
    mock_client.get_monsters.return_value = []

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(type="humanoid")

    assert len(results) == 2
    assert all(monster.type == "humanoid" for monster in results)
    mock_cache.get_entities.assert_called_once_with("monsters", type="humanoid")


@pytest.mark.asyncio
async def test_monster_repository_search_by_size(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search filtering by monster size."""
    # Cache hit with size filter
    huge_monsters = [monster_data[2]]  # Dragon
    mock_cache.get_entities.return_value = huge_monsters

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(size="Huge")

    assert len(results) == 1
    assert results[0].name == "Dragon"
    assert results[0].size == "Huge"
    mock_cache.get_entities.assert_called_once_with("monsters", size="Huge")


@pytest.mark.asyncio
async def test_monster_repository_search_cache_miss_with_filters(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search with cache miss fetches from API."""
    # Cache miss
    mock_cache.get_entities.return_value = []
    # API returns filtered results
    humanoid_monsters = [Monster.model_validate(monster_data[0])]
    mock_client.get_monsters.return_value = humanoid_monsters
    mock_cache.store_entities.return_value = 1

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(type="humanoid")

    assert len(results) == 1
    assert results[0].type == "humanoid"
    mock_client.get_monsters.assert_called_once_with(type="humanoid")
    mock_cache.store_entities.assert_called_once()


@pytest.mark.asyncio
async def test_monster_repository_search_by_challenge_rating(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search filtering by challenge rating."""
    # Cache miss
    mock_cache.get_entities.return_value = []
    # Filter by CR
    high_cr_monsters = [Monster.model_validate(monster_data[2])]
    mock_client.get_monsters.return_value = high_cr_monsters
    mock_cache.store_entities.return_value = 1

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(challenge_rating="16")

    assert len(results) == 1
    assert results[0].challenge_rating == "16"
    mock_client.get_monsters.assert_called_once_with(challenge_rating="16")


@pytest.mark.asyncio
async def test_monster_repository_search_multiple_filters(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search with multiple filters."""
    mock_cache.get_entities.return_value = []
    mock_client.get_monsters.return_value = []

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    await repo.search(type="humanoid", size="Medium")

    # Client should be called with all filters
    mock_client.get_monsters.assert_called_once_with(type="humanoid", size="Medium")
    mock_cache.get_entities.assert_called_once_with("monsters", type="humanoid", size="Medium")


@pytest.mark.asyncio
async def test_monster_repository_search_no_filters_returns_all(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search with no filters returns all monsters."""
    mock_cache.get_entities.return_value = monster_data

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search()

    assert len(results) == 3
    mock_cache.get_entities.assert_called_once_with("monsters")


@pytest.mark.asyncio
async def test_monster_repository_search_empty_result(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search that returns no results."""
    mock_cache.get_entities.return_value = []
    mock_client.get_monsters.return_value = []

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(type="nonexistent")

    assert results == []
    mock_client.get_monsters.assert_called_once_with(type="nonexistent")


@pytest.mark.asyncio
async def test_monster_repository_cache_aside_pattern(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
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
    monsters = [Monster.model_validate(data) for data in monster_data]
    mock_client.get_monsters.return_value = monsters
    mock_cache.store_entities.return_value = len(monster_data)

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    # Verify cache-aside pattern:
    # 1. Check cache first
    mock_cache.get_entities.assert_called_once_with("monsters")
    # 2. On miss, fetch from API
    mock_client.get_monsters.assert_called_once_with()
    # 3. Store in cache
    mock_cache.store_entities.assert_called_once()
    # 4. Return results
    assert len(results) == 3
