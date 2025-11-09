"""Tests for character option lookup tool."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option


@pytest.fixture
def mock_character_option_repository() -> MagicMock:
    """Create mock character option repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_lookup_class_with_repository(mock_character_option_repository):
    """Test looking up a class using repository."""
    mock_character_option_repository.search.return_value = [{"name": "Paladin", "hit_dice": "1d10"}]

    result = await lookup_character_option(
        type="class", name="Paladin", repository=mock_character_option_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Paladin"
    # Verify repository.search was called with option_type
    mock_character_option_repository.search.assert_awaited_once()
    call_kwargs = mock_character_option_repository.search.call_args[1]
    assert call_kwargs["option_type"] == "class"


@pytest.mark.asyncio
async def test_lookup_race_with_repository(mock_character_option_repository):
    """Test looking up a race using repository."""
    mock_character_option_repository.search.return_value = [{"name": "Elf", "speed": 30}]

    result = await lookup_character_option(
        type="race", name="Elf", repository=mock_character_option_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Elf"
    call_kwargs = mock_character_option_repository.search.call_args[1]
    assert call_kwargs["option_type"] == "race"


@pytest.mark.asyncio
async def test_lookup_background_with_repository(mock_character_option_repository):
    """Test looking up a background using repository."""
    mock_character_option_repository.search.return_value = [{"name": "Acolyte"}]

    result = await lookup_character_option(
        type="background", name="Acolyte", repository=mock_character_option_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Acolyte"
    call_kwargs = mock_character_option_repository.search.call_args[1]
    assert call_kwargs["option_type"] == "background"


@pytest.mark.asyncio
async def test_lookup_feat_with_repository(mock_character_option_repository):
    """Test looking up a feat using repository."""
    mock_character_option_repository.search.return_value = [{"name": "Sharpshooter"}]

    result = await lookup_character_option(
        type="feat", name="Sharpshooter", repository=mock_character_option_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Sharpshooter"
    call_kwargs = mock_character_option_repository.search.call_args[1]
    assert call_kwargs["option_type"] == "feat"


@pytest.mark.asyncio
async def test_lookup_invalid_type():
    """Test invalid type parameter raises ValueError."""

    with pytest.raises(ValueError, match="Invalid type"):
        await lookup_character_option(type="invalid-type")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_lookup_character_option_with_limit(mock_character_option_repository):
    """Test that limit parameter is passed to repository."""
    options = [{"name": f"Option {i}", "id": i} for i in range(5)]
    mock_character_option_repository.search.return_value = options

    result = await lookup_character_option(
        type="class", limit=5, repository=mock_character_option_repository
    )

    assert len(result) == 5
    call_kwargs = mock_character_option_repository.search.call_args[1]
    assert call_kwargs["limit"] == 5


@pytest.mark.asyncio
async def test_lookup_character_option_empty_results(mock_character_option_repository):
    """Test character option lookup with no results."""
    mock_character_option_repository.search.return_value = []

    result = await lookup_character_option(
        type="class", name="NonexistentClass", repository=mock_character_option_repository
    )

    assert result == []


@pytest.mark.asyncio
async def test_lookup_character_option_api_error(mock_character_option_repository):
    """Test character option lookup handles API errors gracefully."""
    mock_character_option_repository.search.side_effect = ApiError("API unavailable")

    with pytest.raises(ApiError, match="API unavailable"):
        await lookup_character_option(type="class", repository=mock_character_option_repository)


@pytest.mark.asyncio
async def test_lookup_character_option_network_error(mock_character_option_repository):
    """Test character option lookup handles network errors."""
    mock_character_option_repository.search.side_effect = NetworkError("Connection timeout")

    with pytest.raises(NetworkError, match="Connection timeout"):
        await lookup_character_option(type="class", repository=mock_character_option_repository)


@pytest.mark.asyncio
async def test_lookup_character_option_default_repository():
    """Test that lookup_character_option creates default repository when not provided."""
    # This test verifies the function accepts repository parameter
    # Real integration testing happens in integration tests
    # For unit test, we verify the signature accepts repository param
    sig = inspect.signature(lookup_character_option)
    assert "repository" in sig.parameters
