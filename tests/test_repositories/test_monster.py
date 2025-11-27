"""Tests for CreatureRepository implementation (formerly MonsterRepository)."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.models import Creature
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
    client.get_creatures = AsyncMock()
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
def creatures(monster_data: list[dict[str, Any]]) -> list[Creature]:
    """Convert monster data to Creature models."""
    return [Creature.model_validate(data) for data in monster_data]


@pytest.mark.asyncio
async def test_monster_repository_get_all_from_cache(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test that get_all returns cached monsters when available."""
    # Cache hit - monsters already cached
    mock_cache.get_entities.return_value = monster_data
    mock_client.get_creatures.return_value = []

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    assert len(results) == 3
    assert results[0].name == "Goblin"
    # API should not be called since cache hit
    mock_client.get_creatures.assert_not_called()
    # Cache should be queried with "creatures" table
    mock_cache.get_entities.assert_called_once_with("creatures")


@pytest.mark.asyncio
async def test_monster_repository_get_all_cache_miss(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test that get_all fetches from API on cache miss and stores in cache."""
    # Cache miss - empty cache
    mock_cache.get_entities.return_value = []
    # Create Creature objects from monster_data
    creatures = [Creature.model_validate(data) for data in monster_data]
    mock_client.get_creatures.return_value = creatures
    mock_cache.store_entities.return_value = 3

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    assert len(results) == 3
    # API should be called since cache miss
    mock_client.get_creatures.assert_called_once()
    # Results should be stored in cache with "creatures" table
    mock_cache.store_entities.assert_called_once()
    call_args = mock_cache.store_entities.call_args
    assert call_args[0][1] == "creatures"


@pytest.mark.asyncio
async def test_monster_repository_search_by_type(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search filtering by monster type."""
    # Cache hit with type filter
    humanoid_monsters = [monster_data[0], monster_data[1]]  # Goblin and Orc
    mock_cache.get_entities.return_value = humanoid_monsters
    mock_client.get_creatures.return_value = []

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(type="humanoid")

    assert len(results) == 2
    assert all(monster.type == "humanoid" for monster in results)
    mock_cache.get_entities.assert_called_once_with("creatures", type="humanoid")


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
    mock_cache.get_entities.assert_called_once_with("creatures", size="Huge")


@pytest.mark.asyncio
async def test_monster_repository_search_cache_miss_with_filters(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search with cache miss fetches from API."""
    # Cache miss
    mock_cache.get_entities.return_value = []
    # API returns filtered results
    humanoid_creatures = [Creature.model_validate(monster_data[0])]
    mock_client.get_creatures.return_value = humanoid_creatures
    mock_cache.store_entities.return_value = 1

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(type="humanoid")

    assert len(results) == 1
    assert results[0].type == "humanoid"
    mock_client.get_creatures.assert_called_once_with(limit=None, type="humanoid")
    mock_cache.store_entities.assert_called_once()
    # Verify store_entities uses "creatures" table
    call_args = mock_cache.store_entities.call_args
    assert call_args[0][1] == "creatures"


@pytest.mark.asyncio
async def test_monster_repository_search_by_challenge_rating(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search filtering by challenge rating."""
    # Cache miss
    mock_cache.get_entities.return_value = []
    # Filter by CR
    high_cr_creatures = [Creature.model_validate(monster_data[2])]
    mock_client.get_creatures.return_value = high_cr_creatures
    mock_cache.store_entities.return_value = 1

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(challenge_rating="16")

    assert len(results) == 1
    assert results[0].challenge_rating == "16"
    mock_client.get_creatures.assert_called_once_with(limit=None, challenge_rating="16")


@pytest.mark.asyncio
async def test_monster_repository_search_multiple_filters(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search with multiple filters."""
    mock_cache.get_entities.return_value = []
    mock_client.get_creatures.return_value = []

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    await repo.search(type="humanoid", size="Medium")

    # Client should be called with all filters
    mock_client.get_creatures.assert_called_once_with(limit=None, type="humanoid", size="Medium")
    mock_cache.get_entities.assert_called_once_with("creatures", type="humanoid", size="Medium")


@pytest.mark.asyncio
async def test_monster_repository_search_no_filters_returns_all(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test search with no filters returns all monsters."""
    mock_cache.get_entities.return_value = monster_data

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search()

    assert len(results) == 3
    mock_cache.get_entities.assert_called_once_with("creatures")


@pytest.mark.asyncio
async def test_monster_repository_search_empty_result(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search that returns no results."""
    mock_cache.get_entities.return_value = []
    mock_client.get_creatures.return_value = []

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(type="nonexistent")

    assert results == []
    mock_client.get_creatures.assert_called_once_with(limit=None, type="nonexistent")


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
    creatures = [Creature.model_validate(data) for data in monster_data]
    mock_client.get_creatures.return_value = creatures
    mock_cache.store_entities.return_value = len(monster_data)

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    # Verify cache-aside pattern:
    # 1. Check cache first with "creatures" table
    mock_cache.get_entities.assert_called_once_with("creatures")
    # 2. On miss, fetch from API using get_creatures
    mock_client.get_creatures.assert_called_once_with()
    # 3. Store in cache with "creatures" table
    mock_cache.store_entities.assert_called_once()
    # 4. Return results
    assert len(results) == 3


@pytest.mark.asyncio
async def test_monster_repository_uses_creatures_table_and_get_creatures(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test that repository uses 'creatures' table and calls get_creatures method."""
    # Cache miss - empty cache
    mock_cache.get_entities.return_value = []
    creatures = [Creature.model_validate(data) for data in monster_data]
    mock_client.get_creatures.return_value = creatures
    mock_cache.store_entities.return_value = 3

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    await repo.get_all()

    # Should use "creatures" table for cache operations
    mock_cache.get_entities.assert_called_once_with("creatures")
    # Should call get_creatures instead of get_monsters
    mock_client.get_creatures.assert_called_once_with()
    # Should store in "creatures" table
    mock_cache.store_entities.assert_called_once()
    # Verify the store_entities call uses "creatures" table
    call_args = mock_cache.store_entities.call_args
    assert call_args[0][1] == "creatures"


@pytest.mark.asyncio
async def test_monster_repository_search_uses_creatures_table_and_get_creatures(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test that search uses 'creatures' table and calls get_creatures method."""
    # Cache miss
    mock_cache.get_entities.return_value = []
    humanoid_creatures = [Creature.model_validate(monster_data[0])]
    mock_client.get_creatures.return_value = humanoid_creatures
    mock_cache.store_entities.return_value = 1

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    await repo.search(type="humanoid")

    # Should use "creatures" table for cache operations
    mock_cache.get_entities.assert_called_once_with("creatures", type="humanoid")
    # Should call get_creatures instead of get_monsters
    mock_client.get_creatures.assert_called_once_with(limit=None, type="humanoid")
    # Should store in "creatures" table
    call_args = mock_cache.store_entities.call_args
    assert call_args[0][1] == "creatures"


@pytest.mark.asyncio
async def test_repository_maps_v2_type_to_type_key_with_lowercase(mock_cache: MagicMock) -> None:
    """Verify repository maps type to lowercase (type parameter, not type__key)."""

    mock_v2_client = AsyncMock(spec=Open5eV2Client)
    mock_v2_client.get_creatures = AsyncMock(return_value=[])

    mock_cache.get_entities = AsyncMock(return_value=[])

    repository = MonsterRepository(client=mock_v2_client, cache=mock_cache)
    await repository.search(type="Beast")

    # Verify v2 client was called with type and lowercase value
    call_kwargs = mock_v2_client.get_creatures.call_args.kwargs
    assert call_kwargs.get("type") == "beast"
    # Ensure type__key parameter is not passed
    assert "type__key" not in call_kwargs


@pytest.mark.asyncio
async def test_repository_maps_v2_size_to_size_key_with_lowercase(mock_cache: MagicMock) -> None:
    """Verify repository maps size to lowercase (size parameter, not size__key)."""

    mock_v2_client = AsyncMock(spec=Open5eV2Client)
    mock_v2_client.get_creatures = AsyncMock(return_value=[])

    mock_cache.get_entities = AsyncMock(return_value=[])

    repository = MonsterRepository(client=mock_v2_client, cache=mock_cache)
    await repository.search(size="Large")

    # Verify v2 client was called with size and lowercase value
    call_kwargs = mock_v2_client.get_creatures.call_args.kwargs
    assert call_kwargs.get("size") == "large"
    # Ensure size__key parameter is not passed
    assert "size__key" not in call_kwargs


@pytest.mark.asyncio
async def test_repository_maps_v2_cr_exact_to_challenge_rating_decimal(
    mock_cache: MagicMock,
) -> None:
    """Verify repository maps exact cr to challenge_rating_decimal as float."""

    mock_v2_client = AsyncMock(spec=Open5eV2Client)
    mock_v2_client.get_creatures = AsyncMock(return_value=[])

    mock_cache.get_entities = AsyncMock(return_value=[])

    repository = MonsterRepository(client=mock_v2_client, cache=mock_cache)
    await repository.search(cr=1)

    # Verify v2 client was called with challenge_rating_decimal as float
    call_kwargs = mock_v2_client.get_creatures.call_args.kwargs
    assert call_kwargs.get("challenge_rating_decimal") == 1.0
    assert isinstance(call_kwargs.get("challenge_rating_decimal"), float)


@pytest.mark.asyncio
async def test_repository_maps_v2_challenge_rating_to_challenge_rating_decimal(
    mock_cache: MagicMock,
) -> None:
    """Verify repository maps cache field challenge_rating to challenge_rating_decimal."""

    mock_v2_client = AsyncMock(spec=Open5eV2Client)
    mock_v2_client.get_creatures = AsyncMock(return_value=[])

    mock_cache.get_entities = AsyncMock(return_value=[])

    repository = MonsterRepository(client=mock_v2_client, cache=mock_cache)
    await repository.search(challenge_rating=21)

    # Verify v2 client was called with challenge_rating_decimal as float
    call_kwargs = mock_v2_client.get_creatures.call_args.kwargs
    assert call_kwargs.get("challenge_rating_decimal") == 21.0
    assert isinstance(call_kwargs.get("challenge_rating_decimal"), float)


@pytest.mark.asyncio
async def test_repository_maps_v2_type_to_type_without_key_suffix(mock_cache: MagicMock) -> None:
    """Verify repository maps type parameter WITHOUT __key suffix (API expects 'type' not 'type__key')."""

    mock_v2_client = AsyncMock(spec=Open5eV2Client)
    mock_v2_client.get_creatures = AsyncMock(return_value=[])

    mock_cache.get_entities = AsyncMock(return_value=[])

    repository = MonsterRepository(client=mock_v2_client, cache=mock_cache)
    await repository.search(type="Beast")

    # Verify v2 client was called with 'type' (not 'type__key') and lowercase value
    call_kwargs = mock_v2_client.get_creatures.call_args.kwargs
    assert call_kwargs.get("type") == "beast", "Should use 'type' parameter, not 'type__key'"
    # Ensure type__key parameter is not passed
    assert "type__key" not in call_kwargs, "Should not use 'type__key' parameter"


@pytest.mark.asyncio
async def test_repository_maps_v2_size_to_size_without_key_suffix(mock_cache: MagicMock) -> None:
    """Verify repository maps size parameter WITHOUT __key suffix (API expects 'size' not 'size__key')."""

    mock_v2_client = AsyncMock(spec=Open5eV2Client)
    mock_v2_client.get_creatures = AsyncMock(return_value=[])

    mock_cache.get_entities = AsyncMock(return_value=[])

    repository = MonsterRepository(client=mock_v2_client, cache=mock_cache)
    await repository.search(size="Large")

    # Verify v2 client was called with 'size' (not 'size__key') and lowercase value
    call_kwargs = mock_v2_client.get_creatures.call_args.kwargs
    assert call_kwargs.get("size") == "large", "Should use 'size' parameter, not 'size__key'"
    # Ensure size__key parameter is not passed
    assert "size__key" not in call_kwargs, "Should not use 'size__key' parameter"


@pytest.mark.asyncio
async def test_search_monsters_by_document(
    mock_cache: MagicMock, mock_client: MagicMock, monster_data: list[dict[str, Any]]
) -> None:
    """Test filtering monsters by document name."""
    # Add document to test data
    monster_with_doc = monster_data[0].copy()
    monster_with_doc["document"] = "System Reference Document 5.1"

    mock_cache.get_entities.return_value = [monster_with_doc]

    repo = MonsterRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(document="System Reference Document 5.1")

    # Verify cache was called with document filter
    mock_cache.get_entities.assert_called_once()
    call_kwargs = mock_cache.get_entities.call_args[1]
    assert call_kwargs["document"] == "System Reference Document 5.1"

    assert len(results) == 1
    assert results[0].slug == "goblin"


@pytest.mark.asyncio
async def test_monster_repository_search_with_document_filter() -> None:
    """Test MonsterRepository.search passes document filter to cache."""
    # Mock client and cache
    mock_client = MagicMock()
    mock_client.get_creatures = AsyncMock(return_value=[])

    mock_cache = MagicMock()
    mock_cache.get_entities = AsyncMock(return_value=[])
    mock_cache.store_entities = AsyncMock(return_value=0)

    repo = MonsterRepository(client=mock_client, cache=mock_cache)

    # Search with document filter
    await repo.search(document=["srd-5e"])

    # Verify cache was called with document filter
    mock_cache.get_entities.assert_called_once()
    call_args = mock_cache.get_entities.call_args
    # Check that document was passed to cache
    assert call_args[1].get("document") == ["srd-5e"]


@pytest.mark.asyncio
async def test_monster_repository_search_document_not_passed_to_api() -> None:
    """Test that document filter is NOT passed to API (cache-only filter)."""
    # Mock client and cache
    mock_client = MagicMock()
    mock_client.get_creatures = AsyncMock(return_value=[])

    mock_cache = MagicMock()
    mock_cache.get_entities = AsyncMock(return_value=[])  # Cache miss
    mock_cache.store_entities = AsyncMock(return_value=0)

    repo = MonsterRepository(client=mock_client, cache=mock_cache)

    # Search with document filter (cache miss)
    await repo.search(type="humanoid", document="srd-5e")

    # Verify API was called WITHOUT document parameter
    mock_client.get_creatures.assert_called_once()
    call_kwargs = mock_client.get_creatures.call_args[1]
    assert "document" not in call_kwargs
    # But type should be passed
    assert call_kwargs.get("type") == "humanoid"
