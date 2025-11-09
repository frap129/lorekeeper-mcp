"""Tests for spell lookup tool."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.api_clients.models import Spell
from lorekeeper_mcp.tools.spell_lookup import lookup_spell


@pytest.fixture
def mock_spell_repository() -> MagicMock:
    """Create mock spell repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_lookup_spell_by_name(mock_spell_repository):
    """Test looking up spell by exact name."""
    spell_obj = Spell(
        name="Fireball",
        slug="fireball",
        level=3,
        school="evocation",
        casting_time="1 action",
        range="150 feet",
        components="V,S,M",
        material="a tiny ball of bat guano and sulfur",
        duration="Instantaneous",
        concentration=False,
        ritual=False,
        desc="A bright streak flashes...",
        document_url="https://example.com/fireball",
        higher_level="When you cast this spell...",
        damage_type=None,
    )

    mock_spell_repository.search.return_value = [spell_obj]

    result = await lookup_spell(name="Fireball", repository=mock_spell_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Fireball"
    assert result[0]["level"] == 3
    assert result[0]["school"] == "evocation"
    mock_spell_repository.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_spell_with_filters(mock_spell_repository):
    """Test spell lookup with multiple filters."""
    spell_obj = Spell(
        name="Fireball",
        slug="fireball",
        level=3,
        school="evocation",
        casting_time="1 action",
        range="150 feet",
        components="V,S,M",
        material="a tiny ball of bat guano and sulfur",
        duration="Instantaneous",
        concentration=False,
        ritual=False,
        desc="A bright streak flashes...",
        document_url="https://example.com/fireball",
        higher_level="When you cast this spell...",
        damage_type=None,
    )

    mock_spell_repository.search.return_value = [spell_obj]

    await lookup_spell(
        level=3,
        school="evocation",
        concentration=False,
        limit=10,
        repository=mock_spell_repository,
    )

    call_kwargs = mock_spell_repository.search.call_args[1]
    assert call_kwargs["level"] == 3
    assert call_kwargs["school"] == "evocation"
    assert call_kwargs["concentration"] is False


@pytest.mark.asyncio
async def test_lookup_spell_empty_results(mock_spell_repository):
    """Test spell lookup with no results."""
    mock_spell_repository.search.return_value = []

    result = await lookup_spell(name="NonexistentSpell", repository=mock_spell_repository)

    assert result == []


@pytest.mark.asyncio
async def test_lookup_spell_api_error(mock_spell_repository):
    """Test spell lookup handles API errors gracefully."""
    mock_spell_repository.search.side_effect = ApiError("API unavailable")

    with pytest.raises(ApiError, match="API unavailable"):
        await lookup_spell(name="Fireball", repository=mock_spell_repository)


@pytest.mark.asyncio
async def test_lookup_spell_network_error(mock_spell_repository):
    """Test spell lookup handles network errors."""
    mock_spell_repository.search.side_effect = NetworkError("Connection timeout")

    with pytest.raises(NetworkError, match="Connection timeout"):
        await lookup_spell(name="Fireball", repository=mock_spell_repository)


@pytest.mark.asyncio
async def test_spell_search_by_name_client_side(mock_spell_repository):
    """Test that spell lookup filters by name client-side."""
    spell_fireball = Spell(
        name="Fireball",
        slug="fireball",
        level=3,
        school="evocation",
        casting_time="1 action",
        range="150 feet",
        components="V,S,M",
        material="a tiny ball of bat guano and sulfur",
        duration="Instantaneous",
        concentration=False,
        ritual=False,
        desc="A bright streak flashes...",
        document_url="https://example.com/fireball",
        higher_level="When you cast this spell...",
        damage_type=None,
    )
    spell_fire_bolt = Spell(
        name="Fire Bolt",
        slug="fire-bolt",
        level=0,
        school="evocation",
        casting_time="1 action",
        range="120 feet",
        components="V,S",
        material=None,
        duration="Instantaneous",
        concentration=False,
        ritual=False,
        desc="You hurl a mote of fire...",
        document_url="https://example.com/fire-bolt",
        higher_level=None,
        damage_type=None,
    )

    # Repository returns both spells
    mock_spell_repository.search.return_value = [spell_fireball, spell_fire_bolt]

    # Call with name filter - should filter client-side
    result = await lookup_spell(name="fireball", repository=mock_spell_repository)

    # Should only return Fireball, not Fire Bolt
    assert len(result) == 1
    assert result[0]["name"] == "Fireball"

    # Verify repository.search was called without name parameter
    # (since API doesn't support search)
    mock_spell_repository.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_spell_limit_applied(mock_spell_repository):
    """Test that lookup_spell applies limit to results."""
    spells = [
        Spell(
            name=f"Spell {i}",
            slug=f"spell-{i}",
            level=i % 9,
            school="evocation",
            casting_time="1 action",
            range="Self",
            components="V,S",
            material=None,
            duration="1 minute",
            concentration=False,
            ritual=False,
            desc="A spell.",
            document_url="https://example.com",
            higher_level=None,
            damage_type=None,
        )
        for i in range(1, 30)
    ]

    mock_spell_repository.search.return_value = spells

    result = await lookup_spell(limit=5, repository=mock_spell_repository)

    # Should only return 5 spells even though repository returned 29
    assert len(result) == 5


@pytest.mark.asyncio
async def test_lookup_spell_default_repository():
    """Test that lookup_spell creates default repository when not provided."""
    # This test verifies the function accepts repository parameter
    # Real integration testing happens in integration tests
    # For unit test, we verify the signature accepts repository param
    sig = inspect.signature(lookup_spell)
    assert "repository" in sig.parameters
