"""Tests for equipment lookup tool."""

import inspect
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.models import Armor, MagicItem, Weapon
from lorekeeper_mcp.tools import equipment_lookup
from lorekeeper_mcp.tools.equipment_lookup import (
    _repository_context,
    lookup_equipment,
)


@pytest.fixture
def mock_equipment_repository() -> MagicMock:
    """Create mock equipment repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.fixture
def repository_context(mock_equipment_repository):
    """Fixture to inject mock repository via context for tests."""
    equipment_lookup._repository_context["repository"] = mock_equipment_repository
    yield mock_equipment_repository
    # Clean up after test
    if "repository" in equipment_lookup._repository_context:
        del equipment_lookup._repository_context["repository"]


@pytest.fixture
def sample_longsword() -> Weapon:
    """Sample longsword weapon for tests."""
    return Weapon(
        name="Longsword",
        slug="longsword",
        desc="A longsword with a straight blade",
        document_url="https://example.com/longsword",
        damage_dice="1d8",
        damage_type="Slashing",
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
        damage_type="Piercing",
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
    )


@pytest.mark.asyncio
async def test_lookup_weapon(repository_context, sample_longsword):
    """Test looking up a weapon."""
    repository_context.search.return_value = [sample_longsword]

    result = await lookup_equipment(type="weapon", name="Longsword")

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"
    assert result[0]["damage_dice"] == "1d8"
    repository_context.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_armor(repository_context, sample_chain_mail):
    """Test looking up armor."""
    repository_context.search.return_value = [sample_chain_mail]

    result = await lookup_equipment(type="armor", name="Chain Mail")

    assert len(result) == 1
    assert result[0]["name"] == "Chain Mail"
    assert result[0]["category"] == "Heavy"
    repository_context.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_simple_weapons(repository_context, sample_dagger):
    """Test filtering for simple weapons."""
    repository_context.search.return_value = [sample_dagger]

    result = await lookup_equipment(type="weapon", is_simple=True)

    assert len(result) == 1
    assert result[0]["is_simple"] is True

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["is_simple"] is True


@pytest.mark.asyncio
async def test_lookup_armor_by_category(repository_context, sample_leather):
    """Test looking up armor by category."""
    repository_context.search.return_value = [sample_leather]

    result = await lookup_equipment(type="armor")

    assert len(result) == 1
    assert result[0]["category"] == "Light"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "armor"


@pytest.mark.asyncio
async def test_lookup_equipment_api_error(repository_context):
    """Test equipment lookup handles API errors gracefully."""
    repository_context.search.side_effect = ApiError("API unavailable")

    with pytest.raises(ApiError, match="API unavailable"):
        await lookup_equipment(type="weapon")


@pytest.mark.asyncio
async def test_lookup_equipment_network_error(repository_context):
    """Test equipment lookup handles network errors."""
    repository_context.search.side_effect = NetworkError("Connection timeout")

    with pytest.raises(NetworkError, match="Connection timeout"):
        await lookup_equipment(type="armor")


@pytest.mark.asyncio
async def test_equipment_search_by_name_client_side(
    repository_context, sample_longsword, sample_dagger
):
    """Test that equipment lookup passes name filter to repository for server-side filtering."""
    # Repository returns only matching weapon when called with name filter
    repository_context.search.return_value = [sample_longsword]

    # Call with name filter - should pass to repository
    result = await lookup_equipment(type="weapon", name="longsword")

    # Should only return Longsword
    assert len(result) == 1
    assert result[0]["name"] == "Longsword"

    # Verify repository.search was called with name parameter
    repository_context.search.assert_awaited_once_with(
        limit=20, item_type="weapon", name="longsword"
    )


@pytest.mark.asyncio
async def test_lookup_equipment_limit_applied(repository_context):
    """Test that lookup_equipment passes limit to repository for server-side limiting."""
    weapons = [
        Weapon(
            name=f"Weapon {i}",
            slug=f"weapon-{i}",
            desc=f"Weapon {i}",
            document_url="https://example.com",
            damage_dice="1d8",
            damage_type="Slashing",
            range=5,
            long_range=5,
            distance_unit="feet",
            is_simple=False,
            is_improvised=False,
        )
        for i in range(1, 6)  # Only 5 weapons since limit=5
    ]

    repository_context.search.return_value = weapons

    result = await lookup_equipment(type="weapon", limit=5)

    # Should return 5 weapons from repository (server-side limit)
    assert len(result) == 5
    # Verify repository was called with limit parameter
    repository_context.search.assert_awaited_once_with(limit=5, item_type="weapon")


@pytest.mark.asyncio
async def test_lookup_equipment_default_repository():
    """Test that lookup_equipment does NOT have repository parameter in signature."""
    sig = inspect.signature(lookup_equipment)
    assert "repository" not in sig.parameters


@pytest.mark.asyncio
async def test_lookup_magic_items(repository_context):
    """Test looking up magic items."""
    sample_bag = MagicItem(
        name="Bag of Holding",
        key="bag-of-holding",
        desc="This bag holds much more than it appears",
        rarity="uncommon",
        requires_attunement=False,
    )

    repository_context.search.return_value = [sample_bag]

    result = await lookup_equipment(type="magic-item", name="Bag")

    assert len(result) == 1
    assert result[0]["name"] == "Bag of Holding"
    assert result[0]["rarity"] == "uncommon"
    repository_context.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_magic_items_by_rarity(repository_context):
    """Test filtering magic items by rarity."""
    sample_rare = MagicItem(
        name="Wand of Fireballs",
        key="wand-of-fireballs",
        desc="This wand has 7 charges",
        rarity="rare",
        requires_attunement=True,
    )

    repository_context.search.return_value = [sample_rare]

    result = await lookup_equipment(type="magic-item", rarity="rare")

    assert len(result) == 1
    assert result[0]["rarity"] == "rare"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "magic-item"
    assert call_kwargs["rarity"] == "rare"


@pytest.mark.asyncio
async def test_lookup_magic_items_by_attunement(repository_context):
    """Test filtering magic items by attunement requirement."""
    sample_attune = MagicItem(
        name="Ring of Protection",
        key="ring-of-protection",
        desc="This ring offers protection",
        rarity="rare",
        requires_attunement=True,
    )

    repository_context.search.return_value = [sample_attune]

    result = await lookup_equipment(
        type="magic-item",
        requires_attunement="yes",
    )

    assert len(result) == 1
    assert result[0]["requires_attunement"] is True

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "magic-item"
    assert call_kwargs["requires_attunement"] is True


@pytest.mark.asyncio
async def test_lookup_all_equipment_types(repository_context):
    """Test searching all equipment types together."""
    sample_longsword = Weapon(
        name="Longsword",
        slug="longsword",
        desc="A longsword",
        document_url="https://example.com/longsword",
        damage_dice="1d8",
        damage_type="Slashing",
        range=5,
        long_range=5,
        distance_unit="feet",
        is_simple=False,
        is_improvised=False,
    )

    sample_armor = Armor(
        name="Plate",
        slug="plate",
        desc="Plate armor",
        document_url="https://example.com/plate",
        category="Heavy",
    )

    sample_magic = MagicItem(
        name="Cloak of Invisibility",
        slug="cloak-of-invisibility",
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

    repository_context.search.side_effect = search_side_effect

    result = await lookup_equipment(type="all", limit=20)

    # Should get one of each type
    assert len(result) == 3
    names = {item["name"] for item in result}
    assert names == {"Longsword", "Plate", "Cloak of Invisibility"}


@pytest.mark.asyncio
async def test_lookup_magic_items_empty_results(repository_context):
    """Test magic item lookup when no results are found."""
    repository_context.search.return_value = []

    result = await lookup_equipment(type="magic-item", name="NonExistent")

    assert len(result) == 0


@pytest.mark.asyncio
async def test_lookup_weapon_by_cost_min(repository_context, sample_longsword):
    """Test filtering weapons by minimum cost."""
    repository_context.search.return_value = [sample_longsword]

    result = await lookup_equipment(type="weapon", cost_min=10)

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["cost_min"] == 10


@pytest.mark.asyncio
async def test_lookup_weapon_by_cost_max(repository_context, sample_dagger):
    """Test filtering weapons by maximum cost."""
    repository_context.search.return_value = [sample_dagger]

    result = await lookup_equipment(type="weapon", cost_max=5)

    assert len(result) == 1
    assert result[0]["name"] == "Dagger"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["cost_max"] == 5


@pytest.mark.asyncio
async def test_lookup_armor_by_cost_max(repository_context, sample_leather):
    """Test filtering armor by maximum cost."""
    repository_context.search.return_value = [sample_leather]

    result = await lookup_equipment(type="armor", cost_max=10)

    assert len(result) == 1
    assert result[0]["name"] == "Leather"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "armor"
    assert call_kwargs["cost_max"] == 10


@pytest.mark.asyncio
async def test_lookup_weapon_by_weight_max(repository_context, sample_dagger):
    """Test filtering weapons by maximum weight."""
    repository_context.search.return_value = [sample_dagger]

    result = await lookup_equipment(type="weapon", weight_max=3)

    assert len(result) == 1
    assert result[0]["name"] == "Dagger"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["weight_max"] == 3


@pytest.mark.asyncio
async def test_lookup_weapon_by_is_finesse(repository_context, sample_dagger):
    """Test filtering weapons by finesse property."""
    repository_context.search.return_value = [sample_dagger]

    result = await lookup_equipment(type="weapon", is_finesse=True)

    assert len(result) == 1
    assert result[0]["name"] == "Dagger"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["is_finesse"] is True


@pytest.mark.asyncio
async def test_lookup_weapon_by_is_light(repository_context, sample_dagger):
    """Test filtering weapons by light property."""
    repository_context.search.return_value = [sample_dagger]

    result = await lookup_equipment(type="weapon", is_light=True)

    assert len(result) == 1
    assert result[0]["name"] == "Dagger"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["is_light"] is True


@pytest.mark.asyncio
async def test_lookup_weapon_by_is_magic(repository_context, sample_longsword):
    """Test filtering weapons by magic property."""
    repository_context.search.return_value = [sample_longsword]

    result = await lookup_equipment(type="weapon", is_magic=True)

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["is_magic"] is True


@pytest.mark.asyncio
async def test_lookup_weapon_multiple_new_filters(repository_context, sample_longsword):
    """Test filtering weapons with multiple new parameters."""
    repository_context.search.return_value = [sample_longsword]

    result = await lookup_equipment(
        type="weapon",
        cost_min=5,
        cost_max=25,
        weight_max=4,
        is_finesse=True,
    )

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["cost_min"] == 5
    assert call_kwargs["cost_max"] == 25
    assert call_kwargs["weight_max"] == 4
    assert call_kwargs["is_finesse"] is True


@pytest.mark.asyncio
async def test_lookup_equipment_backward_compatibility_no_new_params(
    repository_context, sample_longsword
):
    """Test backward compatibility when new parameters are not used."""
    repository_context.search.return_value = [sample_longsword]

    # Old-style call without new parameters should still work
    result = await lookup_equipment(type="weapon", name="longsword", limit=20)

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["name"] == "longsword"
    assert call_kwargs["limit"] == 20
    # New parameters should not be present
    assert "cost_min" not in call_kwargs
    assert "cost_max" not in call_kwargs
    assert "weight_max" not in call_kwargs
    assert "is_finesse" not in call_kwargs
    assert "is_light" not in call_kwargs
    assert "is_magic" not in call_kwargs


@pytest.mark.asyncio
async def test_lookup_weapon_with_document_filter(repository_context, sample_longsword):
    """Test filtering weapons by document name."""
    repository_context.search.return_value = [sample_longsword]

    result = await lookup_equipment(type="weapon", documents=["System Reference Document 5.1"])

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "weapon"
    assert call_kwargs["document"] == ["System Reference Document 5.1"]


@pytest.mark.asyncio
async def test_lookup_armor_with_document_filter(repository_context, sample_chain_mail):
    """Test filtering armor by document name."""
    repository_context.search.return_value = [sample_chain_mail]

    result = await lookup_equipment(type="armor", documents=["System Reference Document 5.1"])

    assert len(result) == 1
    assert result[0]["name"] == "Chain Mail"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "armor"
    assert call_kwargs["document"] == ["System Reference Document 5.1"]


@pytest.mark.asyncio
async def test_lookup_magic_item_with_document_filter(repository_context, sample_bag_of_holding):
    """Test filtering magic items by document name."""
    repository_context.search.return_value = [sample_bag_of_holding]

    result = await lookup_equipment(type="magic-item", documents=["System Reference Document 5.1"])

    assert len(result) == 1
    assert result[0]["name"] == "Bag of Holding"

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["item_type"] == "magic-item"
    assert call_kwargs["document"] == ["System Reference Document 5.1"]


@pytest.mark.asyncio
async def test_lookup_equipment_with_documents() -> None:
    """Test lookup_equipment with documents filter."""

    # Mock repository
    class MockRepository:
        async def search(self, **kwargs: Any) -> list[Any]:
            # Verify document parameter is passed
            assert "document" in kwargs
            assert kwargs["document"] == ["srd-5e"]
            return [
                Weapon(
                    name="Longsword",
                    slug="longsword",
                    desc="A longsword with a straight blade",
                    document_url="https://example.com/longsword",
                    damage_dice="1d8",
                    damage_type="Slashing",
                    range=5,
                    long_range=5,
                    distance_unit="feet",
                    is_simple=False,
                    is_improvised=False,
                )
            ]

    _repository_context["repository"] = MockRepository()

    try:
        results = await lookup_equipment(type="weapon", name="longsword", documents=["srd-5e"])
        assert len(results) == 1
        assert results[0]["name"] == "Longsword"
    finally:
        _repository_context.clear()
