"""Tests for EquipmentRepository implementation."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon
from lorekeeper_mcp.repositories.equipment import EquipmentRepository


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
    client.get_weapons = AsyncMock()
    client.get_armor = AsyncMock()
    client.get_magic_items = AsyncMock()
    return client


@pytest.fixture
def weapon_data() -> list[dict[str, Any]]:
    """Provide sample weapon data for testing."""
    return [
        {
            "name": "Longsword",
            "key": "longsword",
            "damage_dice": "1d8",
            "damage_type": {
                "name": "Slashing",
                "key": "slashing",
                "url": "/api/damage-types/slashing",
            },
            "range": 5,
            "long_range": 5,
            "distance_unit": "feet",
            "is_simple": False,
            "is_improvised": False,
        },
        {
            "name": "Dagger",
            "key": "dagger",
            "damage_dice": "1d4",
            "damage_type": {
                "name": "Piercing",
                "key": "piercing",
                "url": "/api/damage-types/piercing",
            },
            "range": 20,
            "long_range": 60,
            "distance_unit": "feet",
            "is_simple": True,
            "is_improvised": False,
        },
    ]


@pytest.fixture
def armor_data() -> list[dict[str, Any]]:
    """Provide sample armor data for testing."""
    return [
        {
            "name": "Plate",
            "key": "plate",
            "category": "Heavy",
            "base_ac": 18,
        },
        {
            "name": "Leather",
            "key": "leather",
            "category": "Light",
            "base_ac": 11,
        },
    ]


@pytest.fixture
def weapons(weapon_data: list[dict[str, Any]]) -> list[Weapon]:
    """Convert weapon data to Weapon models."""
    return [Weapon.model_validate(data) for data in weapon_data]


@pytest.fixture
def armors(armor_data: list[dict[str, Any]]) -> list[Armor]:
    """Convert armor data to Armor models."""
    return [Armor.model_validate(data) for data in armor_data]


@pytest.mark.asyncio
async def test_equipment_repository_get_weapons_from_cache(
    mock_cache: MagicMock, mock_client: MagicMock, weapon_data: list[dict[str, Any]]
) -> None:
    """Test that get_weapons returns cached weapons when available."""
    mock_cache.get_entities.return_value = weapon_data
    mock_client.get_weapons.return_value = []

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_weapons()

    assert len(results) == 2
    assert results[0].name == "Longsword"
    # API should not be called since cache hit
    mock_client.get_weapons.assert_not_called()
    # Cache should be queried
    mock_cache.get_entities.assert_called_once_with("weapons")


@pytest.mark.asyncio
async def test_equipment_repository_get_weapons_cache_miss(
    mock_cache: MagicMock, mock_client: MagicMock, weapon_data: list[dict[str, Any]]
) -> None:
    """Test that get_weapons fetches from API on cache miss and stores in cache."""
    mock_cache.get_entities.return_value = []
    weapons = [Weapon.model_validate(data) for data in weapon_data]
    mock_client.get_weapons.return_value = weapons
    mock_cache.store_entities.return_value = 2

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_weapons()

    assert len(results) == 2
    # API should be called since cache miss
    mock_client.get_weapons.assert_called_once()
    # Results should be stored in cache
    mock_cache.store_entities.assert_called_once()


@pytest.mark.asyncio
async def test_equipment_repository_get_armor_from_cache(
    mock_cache: MagicMock, mock_client: MagicMock, armor_data: list[dict[str, Any]]
) -> None:
    """Test that get_armor returns cached armor when available."""
    mock_cache.get_entities.return_value = armor_data
    mock_client.get_armor.return_value = []

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_armor()

    assert len(results) == 2
    assert results[0].name == "Plate"
    # API should not be called since cache hit
    mock_client.get_armor.assert_not_called()
    # Cache should be queried
    mock_cache.get_entities.assert_called_once_with("armor")


@pytest.mark.asyncio
async def test_equipment_repository_get_armor_cache_miss(
    mock_cache: MagicMock, mock_client: MagicMock, armor_data: list[dict[str, Any]]
) -> None:
    """Test that get_armor fetches from API on cache miss and stores in cache."""
    mock_cache.get_entities.return_value = []
    armors = [Armor.model_validate(data) for data in armor_data]
    mock_client.get_armor.return_value = armors
    mock_cache.store_entities.return_value = 2

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_armor()

    assert len(results) == 2
    # API should be called since cache miss
    mock_client.get_armor.assert_called_once()
    # Results should be stored in cache
    mock_cache.store_entities.assert_called_once()


@pytest.mark.asyncio
async def test_equipment_repository_search_weapons(
    mock_cache: MagicMock, mock_client: MagicMock, weapon_data: list[dict[str, Any]]
) -> None:
    """Test search filtering weapons."""
    simple_weapons = [weapon_data[1]]  # Dagger is simple
    mock_cache.get_entities.return_value = simple_weapons
    mock_client.get_weapons.return_value = []

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(item_type="weapon", is_simple=True)

    assert len(results) == 1
    assert results[0].name == "Dagger"
    mock_cache.get_entities.assert_called_once_with("weapons", is_simple=True)


@pytest.mark.asyncio
async def test_equipment_repository_search_armor(
    mock_cache: MagicMock, mock_client: MagicMock, armor_data: list[dict[str, Any]]
) -> None:
    """Test search filtering armor."""
    light_armor = [armor_data[1]]  # Leather is light
    mock_cache.get_entities.return_value = light_armor

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(item_type="armor", category="Light")

    assert len(results) == 1
    assert results[0].name == "Leather"
    mock_cache.get_entities.assert_called_once_with("armor", category="Light")


@pytest.mark.asyncio
async def test_equipment_repository_search_weapons_cache_miss(
    mock_cache: MagicMock, mock_client: MagicMock, weapon_data: list[dict[str, Any]]
) -> None:
    """Test search weapons with cache miss fetches from API."""
    mock_cache.get_entities.return_value = []
    weapons = [Weapon.model_validate(weapon_data[1])]
    mock_client.get_weapons.return_value = weapons
    mock_cache.store_entities.return_value = 1

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(item_type="weapon", is_simple=True)

    assert len(results) == 1
    mock_client.get_weapons.assert_called_once_with(is_simple=True)
    mock_cache.store_entities.assert_called_once()


@pytest.mark.asyncio
async def test_equipment_repository_search_armor_cache_miss(
    mock_cache: MagicMock, mock_client: MagicMock, armor_data: list[dict[str, Any]]
) -> None:
    """Test search armor with cache miss fetches from API."""
    mock_cache.get_entities.return_value = []
    armors = [Armor.model_validate(armor_data[1])]
    mock_client.get_armor.return_value = armors
    mock_cache.store_entities.return_value = 1

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(item_type="armor", category="Light")

    assert len(results) == 1
    mock_client.get_armor.assert_called_once_with(category="Light")
    mock_cache.store_entities.assert_called_once()


@pytest.mark.asyncio
async def test_equipment_repository_search_empty_result(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search that returns no results."""
    mock_cache.get_entities.return_value = []
    mock_client.get_weapons.return_value = []

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(item_type="weapon", is_improvised=True)

    assert results == []
    mock_client.get_weapons.assert_called_once_with(is_improvised=True)


@pytest.mark.asyncio
async def test_equipment_repository_get_all_weapons_and_armor(
    mock_cache: MagicMock,
    mock_client: MagicMock,
    weapon_data: list[dict[str, Any]],
    armor_data: list[dict[str, Any]],
) -> None:
    """Test get_all retrieves weapons, armor, and magic items."""
    # Setup cache hits for all three types
    mock_cache.get_entities.side_effect = [weapon_data, armor_data, []]
    mock_client.get_weapons.return_value = []
    mock_client.get_armor.return_value = []
    mock_client.get_magic_items.return_value = []

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    # Should combine weapons and armor (no magic items in cache)
    assert len(results) == 4
    # First two should be weapons
    assert all(isinstance(r, Weapon) for r in results[:2])
    # Last two should be armor
    assert all(isinstance(r, Armor) for r in results[2:])


@pytest.mark.asyncio
async def test_equipment_repository_get_all_mixed_cache(
    mock_cache: MagicMock,
    mock_client: MagicMock,
    weapon_data: list[dict[str, Any]],
    armor_data: list[dict[str, Any]],
) -> None:
    """Test get_all handles partial cache hits (weapon hit, armor miss, no magic items)."""
    armors = [Armor.model_validate(data) for data in armor_data]
    # Weapons from cache, armor from API, no magic items
    mock_cache.get_entities.side_effect = [weapon_data, [], []]
    mock_client.get_armor.return_value = armors
    mock_client.get_magic_items.return_value = []
    mock_cache.store_entities.return_value = 2

    repo = EquipmentRepository(client=mock_client, cache=mock_cache)
    results = await repo.get_all()

    assert len(results) == 4
    # API should be called for armor miss
    mock_client.get_armor.assert_called_once()
    # Armor should be stored in cache (and possibly magic-items too)
    assert mock_cache.store_entities.call_count >= 1
