"""Tests for creature lookup tool."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.api_clients.models import Monster
from lorekeeper_mcp.tools.creature_lookup import lookup_creature


@pytest.fixture
def mock_monster_repository() -> MagicMock:
    """Create mock monster repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_lookup_creature_by_name(mock_monster_repository):
    """Test looking up creature by exact name."""
    creature_obj = Monster(
        name="Ancient Red Dragon",
        slug="ancient-red-dragon",
        size="Gargantuan",
        type="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+280",
        strength=30,
        dexterity=10,
        constitution=29,
        intelligence=18,
        wisdom=15,
        charisma=23,
        challenge_rating="24",
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/ancient-red-dragon",
    )

    mock_monster_repository.search.return_value = [creature_obj]

    result = await lookup_creature(name="Ancient Red Dragon", repository=mock_monster_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Ancient Red Dragon"
    assert result[0]["challenge_rating"] == "24"
    mock_monster_repository.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_creature_by_cr_and_type(mock_monster_repository):
    """Test creature lookup with CR and type filters."""
    creature_obj = Monster(
        name="Zombie",
        slug="zombie",
        size="Medium",
        type="undead",
        alignment="neutral evil",
        armor_class=8,
        hit_points=22,
        hit_dice="5d8",
        strength=13,
        dexterity=6,
        constitution=16,
        intelligence=3,
        wisdom=6,
        charisma=5,
        challenge_rating="1/4",
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/zombie",
    )

    mock_monster_repository.search.return_value = [creature_obj]

    await lookup_creature(cr=5, type="undead", limit=15, repository=mock_monster_repository)

    call_kwargs = mock_monster_repository.search.call_args[1]
    assert call_kwargs["challenge_rating"] == 5  # Maps cr -> challenge_rating
    assert call_kwargs["type"] == "undead"
    assert call_kwargs["limit"] == 15


@pytest.mark.asyncio
async def test_lookup_creature_fractional_cr(mock_monster_repository):
    """Test creature lookup with fractional CR."""
    creature_obj = Monster(
        name="Goblin",
        slug="goblin",
        size="Small",
        type="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        strength=8,
        dexterity=14,
        constitution=10,
        intelligence=10,
        wisdom=8,
        charisma=8,
        challenge_rating="1/4",
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/goblin",
    )

    mock_monster_repository.search.return_value = [creature_obj]

    await lookup_creature(cr=0.25, repository=mock_monster_repository)

    call_kwargs = mock_monster_repository.search.call_args[1]
    assert call_kwargs["challenge_rating"] == 0.25  # Maps cr -> challenge_rating


@pytest.mark.asyncio
async def test_lookup_creature_cr_range(mock_monster_repository):
    """Test creature lookup with CR range."""
    creatures = [
        Monster(
            name=f"Creature {i}",
            slug=f"creature-{i}",
            size="Medium",
            type="humanoid",
            alignment="neutral",
            armor_class=10,
            hit_points=10,
            hit_dice="1d8",
            strength=10,
            dexterity=10,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            challenge_rating=str(i),
            actions=None,
            legendary_actions=None,
            special_abilities=None,
            desc=None,
            speed=None,
            document_url="https://example.com",
        )
        for i in range(1, 4)
    ]

    mock_monster_repository.search.return_value = creatures

    await lookup_creature(cr_min=1, cr_max=3, repository=mock_monster_repository)

    call_kwargs = mock_monster_repository.search.call_args[1]
    assert call_kwargs["cr_min"] == 1
    assert call_kwargs["cr_max"] == 3


@pytest.mark.asyncio
async def test_lookup_creature_empty_results(mock_monster_repository):
    """Test creature lookup with no results."""
    mock_monster_repository.search.return_value = []

    result = await lookup_creature(name="Nonexistent", repository=mock_monster_repository)

    assert result == []


@pytest.mark.asyncio
async def test_lookup_creature_api_error(mock_monster_repository):
    """Test creature lookup handles API errors gracefully."""
    mock_monster_repository.search.side_effect = ApiError("API unavailable")

    with pytest.raises(ApiError, match="API unavailable"):
        await lookup_creature(name="Dragon", repository=mock_monster_repository)


@pytest.mark.asyncio
async def test_lookup_creature_network_error(mock_monster_repository):
    """Test creature lookup handles network errors."""
    mock_monster_repository.search.side_effect = NetworkError("Connection timeout")

    with pytest.raises(NetworkError, match="Connection timeout"):
        await lookup_creature(name="Dragon", repository=mock_monster_repository)


@pytest.mark.asyncio
async def test_creature_search_by_name_client_side(mock_monster_repository):
    """Test that creature lookup filters by name client-side."""
    creature_red_dragon = Monster(
        name="Ancient Red Dragon",
        slug="ancient-red-dragon",
        size="Gargantuan",
        type="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+280",
        strength=30,
        dexterity=10,
        constitution=29,
        intelligence=18,
        wisdom=15,
        charisma=23,
        challenge_rating="24",
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/ancient-red-dragon",
    )
    creature_bronze_dragon = Monster(
        name="Ancient Bronze Dragon",
        slug="ancient-bronze-dragon",
        size="Gargantuan",
        type="dragon",
        alignment="chaotic good",
        armor_class=22,
        hit_points=491,
        hit_dice="26d20+182",
        strength=29,
        dexterity=10,
        constitution=25,
        intelligence=18,
        wisdom=17,
        charisma=21,
        challenge_rating="23",
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/ancient-bronze-dragon",
    )

    # Repository returns both dragons
    mock_monster_repository.search.return_value = [
        creature_red_dragon,
        creature_bronze_dragon,
    ]

    # Call with name filter - should filter client-side
    result = await lookup_creature(name="red", repository=mock_monster_repository)

    # Should only return Ancient Red Dragon, not Ancient Bronze Dragon
    assert len(result) == 1
    assert result[0]["name"] == "Ancient Red Dragon"

    # Verify repository.search was called
    mock_monster_repository.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_creature_limit_applied(mock_monster_repository):
    """Test that lookup_creature applies limit to results."""
    creatures = [
        Monster(
            name=f"Creature {i}",
            slug=f"creature-{i}",
            size="Medium",
            type="humanoid",
            alignment="neutral",
            armor_class=10,
            hit_points=10,
            hit_dice="1d8",
            strength=10,
            dexterity=10,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            challenge_rating="1",
            actions=None,
            legendary_actions=None,
            special_abilities=None,
            desc=None,
            speed=None,
            document_url="https://example.com",
        )
        for i in range(1, 30)
    ]

    mock_monster_repository.search.return_value = creatures

    result = await lookup_creature(limit=5, repository=mock_monster_repository)

    # Should only return 5 creatures even though repository returned 29
    assert len(result) == 5


@pytest.mark.asyncio
async def test_lookup_creature_default_repository():
    """Test that lookup_creature creates default repository when not provided."""
    # This test verifies the function accepts repository parameter
    # Real integration testing happens in integration tests
    # For unit test, we verify the signature accepts repository param
    sig = inspect.signature(lookup_creature)
    assert "repository" in sig.parameters
