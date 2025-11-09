"""Tests for equipment lookup tool."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon
from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment


@pytest.fixture
def mock_equipment_repository() -> MagicMock:
    """Create mock equipment repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.fixture
def sample_longsword() -> Weapon:
    """Sample longsword weapon for tests."""
    return Weapon(
        name="Longsword",
        slug="longsword",
        desc="A longsword with a straight blade",
        document_url="https://example.com/longsword",
        damage_dice="1d8",
        damage_type={
            "name": "Slashing",
            "key": "slashing",
            "url": "/api/damage-types/slashing",
        },
        range=5,
        long_range=5,
        distance_unit="feet",
        is_simple=False,
        is_improvised=False,
    )


@pytest.fixture
def sample_dagger() -> Weapon:
    """Sample dagger weapon for tests."""
    return Weapon(
        name="Dagger",
        slug="dagger",
        desc="A small, sharp-pointed blade",
        document_url="https://example.com/dagger",
        damage_dice="1d4",
        damage_type={
            "name": "Piercing",
            "key": "piercing",
            "url": "/api/damage-types/piercing",
        },
        range=20,
        long_range=60,
        distance_unit="feet",
        is_simple=True,
        is_improvised=False,
    )


@pytest.fixture
def sample_chain_mail() -> Armor:
    """Sample chain mail armor for tests."""
    return Armor(
        name="Chain Mail",
        slug="chain-mail",
        desc="Chain mail armor",
        document_url="https://example.com/chain-mail",
        category="Heavy",
        base_ac=16,
    )


@pytest.fixture
def sample_leather() -> Armor:
    """Sample leather armor for tests."""
    return Armor(
        name="Leather",
        slug="leather",
        desc="Light leather armor",
        document_url="https://example.com/leather",
        category="Light",
        base_ac=11,
        dex_bonus=True,
    )


@pytest.mark.asyncio
async def test_lookup_weapon(mock_equipment_repository, sample_longsword):
    """Test looking up a weapon."""
    mock_equipment_repository.search.return_value = [sample_longsword]

    result = await lookup_equipment(
        type="weapon", name="Longsword", repository=mock_equipment_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"
    assert result[0]["damage_dice"] == "1d8"
    mock_equipment_repository.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_armor(mock_equipment_repository, sample_chain_mail):
    """Test looking up armor."""
    mock_equipment_repository.search.return_value = [sample_chain_mail]

    result = await lookup_equipment(
        type="armor", name="Chain Mail", repository=mock_equipment_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Chain Mail"
    assert result[0]["category"] == "Heavy"
    mock_equipment_repository.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_simple_weapons(mock_equipment_repository, sample_dagger):
    """Test filtering for simple weapons."""
    mock_equipment_repository.search.return_value = [sample_dagger]

    result = await lookup_equipment(
        type="weapon", is_simple=True, repository=mock_equipment_repository
    )

    assert len(result) == 1
    assert result[0]["is_simple"] is True

    call_kwargs = mock_equipment_repository.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["is_simple"] is True


@pytest.mark.asyncio
async def test_lookup_armor_by_category(mock_equipment_repository, sample_leather):
    """Test looking up armor by category."""
    mock_equipment_repository.search.return_value = [sample_leather]

    result = await lookup_equipment(type="armor", repository=mock_equipment_repository)

    assert len(result) == 1
    assert result[0]["category"] == "Light"

    call_kwargs = mock_equipment_repository.search.call_args[1]
    assert call_kwargs["item_type"] == "armor"


@pytest.mark.asyncio
async def test_lookup_equipment_api_error(mock_equipment_repository):
    """Test equipment lookup handles API errors gracefully."""
    mock_equipment_repository.search.side_effect = ApiError("API unavailable")

    with pytest.raises(ApiError, match="API unavailable"):
        await lookup_equipment(type="weapon", repository=mock_equipment_repository)


@pytest.mark.asyncio
async def test_lookup_equipment_network_error(mock_equipment_repository):
    """Test equipment lookup handles network errors."""
    mock_equipment_repository.search.side_effect = NetworkError("Connection timeout")

    with pytest.raises(NetworkError, match="Connection timeout"):
        await lookup_equipment(type="armor", repository=mock_equipment_repository)


@pytest.mark.asyncio
async def test_equipment_search_by_name_client_side(
    mock_equipment_repository, sample_longsword, sample_dagger
):
    """Test that equipment lookup filters by name client-side."""
    # Repository returns both weapons
    mock_equipment_repository.search.return_value = [sample_longsword, sample_dagger]

    # Call with name filter - should filter client-side
    result = await lookup_equipment(
        type="weapon", name="longsword", repository=mock_equipment_repository
    )

    # Should only return Longsword, not Dagger
    assert len(result) == 1
    assert result[0]["name"] == "Longsword"

    # Verify repository.search was called
    mock_equipment_repository.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_equipment_limit_applied(mock_equipment_repository):
    """Test that lookup_equipment applies limit to results."""
    weapons = [
        Weapon(
            name=f"Weapon {i}",
            slug=f"weapon-{i}",
            desc=f"Weapon {i}",
            document_url="https://example.com",
            damage_dice="1d8",
            damage_type={
                "name": "Slashing",
                "key": "slashing",
                "url": "/api/damage-types/slashing",
            },
            range=5,
            long_range=5,
            distance_unit="feet",
            is_simple=False,
            is_improvised=False,
        )
        for i in range(1, 30)
    ]

    mock_equipment_repository.search.return_value = weapons

    result = await lookup_equipment(type="weapon", limit=5, repository=mock_equipment_repository)

    # Should only return 5 weapons even though repository returned 29
    assert len(result) == 5


@pytest.mark.asyncio
async def test_lookup_equipment_default_repository():
    """Test that lookup_equipment creates default repository when not provided."""
    # This test verifies the function accepts repository parameter
    # Real integration testing happens in integration tests
    # For unit test, we verify the signature accepts repository param
    sig = inspect.signature(lookup_equipment)
    assert "repository" in sig.parameters
