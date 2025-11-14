"""Tests for creature lookup tool."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.api_clients.models import Monster
from lorekeeper_mcp.tools import creature_lookup
from lorekeeper_mcp.tools.creature_lookup import lookup_creature


@pytest.fixture
def mock_monster_repository() -> MagicMock:
    """Create mock monster repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.fixture
def repository_context(mock_monster_repository):
    """Fixture to inject mock repository via context for tests."""
    creature_lookup._repository_context["repository"] = mock_monster_repository
    yield mock_monster_repository
    # Clean up after test
    if "repository" in creature_lookup._repository_context:
        del creature_lookup._repository_context["repository"]


@pytest.mark.asyncio
async def test_lookup_creature_by_name(repository_context):
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
        challenge_rating_decimal=24.0,
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/ancient-red-dragon",
        document=None,
    )

    repository_context.search.return_value = [creature_obj]

    result = await lookup_creature(name="Ancient Red Dragon")

    assert len(result) == 1
    assert result[0]["name"] == "Ancient Red Dragon"
    assert result[0]["challenge_rating"] == "24"
    repository_context.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_creature_by_cr_and_type(repository_context):
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

    repository_context.search.return_value = [creature_obj]

    await lookup_creature(cr=5, type="undead", limit=15)

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["challenge_rating"] == 5.0  # Maps cr -> challenge_rating
    assert call_kwargs["type"] == "undead"
    assert call_kwargs["limit"] == 15


@pytest.mark.asyncio
async def test_lookup_creature_fractional_cr(repository_context):
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

    repository_context.search.return_value = [creature_obj]

    await lookup_creature(cr=0.25)

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["challenge_rating"] == 0.25  # Maps cr -> challenge_rating


@pytest.mark.asyncio
async def test_lookup_creature_cr_range(repository_context):
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

    repository_context.search.return_value = creatures

    await lookup_creature(cr_min=1, cr_max=3)

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["cr_min"] == 1
    assert call_kwargs["cr_max"] == 3


@pytest.mark.asyncio
async def test_lookup_creature_empty_results(repository_context):
    """Test creature lookup with no results."""
    repository_context.search.return_value = []

    result = await lookup_creature(name="Nonexistent")

    assert result == []


@pytest.mark.asyncio
async def test_lookup_creature_api_error(repository_context):
    """Test creature lookup handles API errors gracefully."""
    repository_context.search.side_effect = ApiError("API unavailable")

    with pytest.raises(ApiError, match="API unavailable"):
        await lookup_creature(name="Dragon")


@pytest.mark.asyncio
async def test_lookup_creature_network_error(repository_context):
    """Test creature lookup handles network errors."""
    repository_context.search.side_effect = NetworkError("Connection timeout")

    with pytest.raises(NetworkError, match="Connection timeout"):
        await lookup_creature(name="Dragon")


@pytest.mark.asyncio
async def test_creature_search_by_name_client_side(repository_context):
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
        document=None,
    )

    # Repository returns only the red dragon (server-side filtering)
    repository_context.search.return_value = [
        creature_red_dragon,
    ]

    # Call with name filter - repository does server-side filtering
    result = await lookup_creature(name="red")

    # Should only return Ancient Red Dragon
    assert len(result) == 1
    assert result[0]["name"] == "Ancient Red Dragon"

    # Verify repository.search was called with name parameter
    repository_context.search.assert_awaited_once_with(name="red", limit=20)


@pytest.mark.asyncio
async def test_lookup_creature_limit_applied(repository_context):
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

    repository_context.search.return_value = creatures

    result = await lookup_creature(limit=5)

    # Should only return 5 creatures even though repository returned 29
    assert len(result) == 5


@pytest.mark.asyncio
async def test_lookup_creature_default_repository():
    """Test that lookup_creature creates default repository when not provided."""
    # This test verifies the function no longer accepts repository parameter
    # and instead uses context-based injection
    sig = inspect.signature(lookup_creature)
    assert "repository" not in sig.parameters


@pytest.mark.asyncio
async def test_lookup_creature_armor_class_min(repository_context):
    """Test creature lookup with armor_class_min filter."""
    creature_obj = Monster(
        name="Ancient Red Dragon",
        slug="ancient-red-dragon",
        size="Gargantuan",
        type="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+280",
        challenge_rating="24",
        challenge_rating_decimal=24.0,
        strength=30,
        dexterity=10,
        constitution=29,
        intelligence=18,
        wisdom=15,
        charisma=23,
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/ancient-red-dragon",
        document=None,
    )

    repository_context.search.return_value = [creature_obj]

    await lookup_creature(armor_class_min=20)

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["armor_class_min"] == 20
    assert call_kwargs["limit"] == 20


@pytest.mark.asyncio
async def test_lookup_creature_hit_points_min(repository_context):
    """Test creature lookup with hit_points_min filter."""
    creature_obj = Monster(
        name="Ancient Red Dragon",
        slug="ancient-red-dragon",
        size="Gargantuan",
        type="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+280",
        challenge_rating="24",
        challenge_rating_decimal=24.0,
        strength=30,
        dexterity=10,
        constitution=29,
        intelligence=18,
        wisdom=15,
        charisma=23,
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/ancient-red-dragon",
        document=None,
    )

    repository_context.search.return_value = [creature_obj]

    await lookup_creature(hit_points_min=500)

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["hit_points_min"] == 500
    assert call_kwargs["limit"] == 20


@pytest.mark.asyncio
async def test_lookup_creature_combined_filters(repository_context):
    """Test creature lookup with armor_class_min and hit_points_min together."""
    creature_obj = Monster(
        name="Ancient Red Dragon",
        slug="ancient-red-dragon",
        size="Gargantuan",
        type="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+280",
        challenge_rating="24",
        challenge_rating_decimal=24.0,
        strength=30,
        dexterity=10,
        constitution=29,
        intelligence=18,
        wisdom=15,
        charisma=23,
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/ancient-red-dragon",
        document=None,
    )

    repository_context.search.return_value = [creature_obj]

    await lookup_creature(armor_class_min=20, hit_points_min=500, cr=10)

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["armor_class_min"] == 20
    assert call_kwargs["hit_points_min"] == 500
    assert call_kwargs["challenge_rating"] == 10.0
    assert call_kwargs["limit"] == 20


@pytest.mark.asyncio
async def test_lookup_creature_backward_compatible(repository_context):
    """Test that existing calls without new parameters still work."""
    creature_obj = Monster(
        name="Goblin",
        slug="goblin",
        size="Small",
        type="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        challenge_rating="1/4",
        challenge_rating_decimal=0.25,
        strength=8,
        dexterity=14,
        constitution=10,
        intelligence=10,
        wisdom=8,
        charisma=8,
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/goblin",
    )

    repository_context.search.return_value = [creature_obj]

    # Call without new parameters - should work unchanged
    result = await lookup_creature(name="goblin")

    assert len(result) == 1
    assert result[0]["name"] == "Goblin"

    # Verify new parameters were not passed to repository
    call_kwargs = repository_context.search.call_args[1]
    assert "armor_class_min" not in call_kwargs
    assert "hit_points_min" not in call_kwargs


@pytest.mark.asyncio
async def test_lookup_creature_with_document_filter(repository_context):
    """Test looking up creatures filtered by document name."""
    creature_obj = Monster(
        name="Goblin",
        slug="goblin",
        size="Small",
        type="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        challenge_rating="1/4",
        challenge_rating_decimal=0.25,
        strength=8,
        dexterity=14,
        constitution=10,
        intelligence=10,
        wisdom=8,
        charisma=8,
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/goblin",
    )

    repository_context.search.return_value = [creature_obj]

    results = await lookup_creature(document="System Reference Document 5.1")

    # Verify repository was called with document filter
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["document"] == "System Reference Document 5.1"

    # Verify results are returned
    assert len(results) == 1
    assert results[0]["name"] == "Goblin"


@pytest.mark.asyncio
async def test_lookup_creature_with_document_keys(repository_context):
    """Test lookup_creature with document_keys filter."""
    creature_obj = Monster(
        name="Fireball",
        slug="fireball",
        size="Small",
        type="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        challenge_rating="1/4",
        challenge_rating_decimal=0.25,
        strength=8,
        dexterity=14,
        constitution=10,
        intelligence=10,
        wisdom=8,
        charisma=8,
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        desc=None,
        speed=None,
        document_url="https://example.com/fireball",
        document="srd-5e",
    )

    repository_context.search.return_value = [creature_obj]

    results = await lookup_creature(name="fireball", document_keys=["srd-5e"])

    # Verify repository was called with document as document_keys
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["document"] == ["srd-5e"]

    # Verify results are returned
    assert len(results) == 1
    assert results[0]["document"] == "srd-5e"
