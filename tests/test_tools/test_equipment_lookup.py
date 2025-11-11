"""Tests for equipment lookup tool."""

import inspect
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.api_clients.models.equipment import Armor, MagicItem, Weapon
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


@pytest.fixture
def sample_bag_of_holding() -> MagicItem:
    """Sample magic item for tests."""
    return MagicItem(
        name="Bag of Holding",
        slug="bag-of-holding",
        desc="This bag holds much more than it appears to hold",
        document_url="https://example.com/bag-of-holding",
        rarity="uncommon",
        requires_attunement=False,
        wondrous=True,
        weight=15.0,
    )


@pytest.fixture
def sample_wand_of_fireballs() -> MagicItem:
    """Sample wand magic item for tests."""
    return MagicItem(
        name="Wand of Fireballs",
        slug="wand-of-fireballs",
        desc="This wand has 7 charges and regains 1d6+1 charges daily at dawn",
        document_url="https://example.com/wand-of-fireballs",
        rarity="rare",
        requires_attunement=True,
        type="wand",
        damage="8d6 fire",
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


@pytest.mark.asyncio
async def test_lookup_magic_items(mock_equipment_repository):
    """Test looking up magic items."""
    sample_bag = MagicItem(
        name="Bag of Holding",
        key="bag-of-holding",
        desc="This bag holds much more than it appears",
        rarity="uncommon",
        requires_attunement=False,
    )

    mock_equipment_repository.search.return_value = [sample_bag]

    result = await lookup_equipment(
        type="magic-item", name="Bag", repository=mock_equipment_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Bag of Holding"
    assert result[0]["rarity"] == "uncommon"
    mock_equipment_repository.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_magic_items_by_rarity(mock_equipment_repository):
    """Test filtering magic items by rarity."""
    sample_rare = MagicItem(
        name="Wand of Fireballs",
        key="wand-of-fireballs",
        desc="This wand has 7 charges",
        rarity="rare",
        requires_attunement=True,
    )

    mock_equipment_repository.search.return_value = [sample_rare]

    result = await lookup_equipment(
        type="magic-item", rarity="rare", repository=mock_equipment_repository
    )

    assert len(result) == 1
    assert result[0]["rarity"] == "rare"

    call_kwargs = mock_equipment_repository.search.call_args[1]
    assert call_kwargs["item_type"] == "magic-item"
    assert call_kwargs["rarity"] == "rare"


@pytest.mark.asyncio
async def test_lookup_magic_items_by_attunement(mock_equipment_repository):
    """Test filtering magic items by attunement requirement."""
    sample_attune = MagicItem(
        name="Ring of Protection",
        key="ring-of-protection",
        desc="This ring offers protection",
        rarity="rare",
        requires_attunement=True,
    )

    mock_equipment_repository.search.return_value = [sample_attune]

    result = await lookup_equipment(
        type="magic-item",
        requires_attunement="yes",
        repository=mock_equipment_repository,
    )

    assert len(result) == 1
    assert result[0]["requires_attunement"] is True

    call_kwargs = mock_equipment_repository.search.call_args[1]
    assert call_kwargs["item_type"] == "magic-item"
    assert call_kwargs["requires_attunement"] is True


@pytest.mark.asyncio
async def test_lookup_all_equipment_types(mock_equipment_repository):
    """Test searching all equipment types together."""
    sample_longsword = Weapon(
        name="Longsword",
        key="longsword",
        desc="A longsword",
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

    sample_armor = Armor(
        name="Plate",
        key="plate",
        desc="Plate armor",
        document_url="https://example.com/plate",
        category="Heavy",
        base_ac=18,
    )

    sample_magic = MagicItem(
        name="Cloak of Invisibility",
        key="cloak-of-invisibility",
        desc="While wearing this cloak you are invisible",
        rarity="legendary",
        requires_attunement=False,
    )

    # Mock returns different items based on item_type filter
    def search_side_effect(**kwargs: Any) -> list[Any]:
        """Return different results based on item_type."""
        item_type = kwargs.get("item_type")
        if item_type == "weapon":
            return [sample_longsword]
        if item_type == "armor":
            return [sample_armor]
        if item_type == "magic-item":
            return [sample_magic]
        return []

    mock_equipment_repository.search.side_effect = search_side_effect

    result = await lookup_equipment(type="all", limit=20, repository=mock_equipment_repository)

    # Should get one of each type
    assert len(result) == 3
    names = {item["name"] for item in result}
    assert names == {"Longsword", "Plate", "Cloak of Invisibility"}


@pytest.mark.asyncio
async def test_lookup_magic_items_empty_results(mock_equipment_repository):
    """Test magic item lookup when no results are found."""
    mock_equipment_repository.search.return_value = []

    result = await lookup_equipment(
        type="magic-item", name="NonExistent", repository=mock_equipment_repository
    )

    assert len(result) == 0
