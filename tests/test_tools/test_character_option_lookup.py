"""Tests for character option lookup tool."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.tools import character_option_lookup
from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option


@pytest.fixture
def mock_character_option_repository() -> MagicMock:
    """Create mock character option repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_lookup_class_with_repository(repository_context):
    """Test looking up a class using repository context."""
    repository_context.search.return_value = [{"name": "Paladin", "hit_dice": "1d10"}]

    result = await lookup_character_option(type="class", name="Paladin")

    assert len(result) == 1
    assert result[0]["name"] == "Paladin"
    # Verify repository.search was called with option_type
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["option_type"] == "class"


@pytest.mark.asyncio
async def test_lookup_race_with_repository(repository_context):
    """Test looking up a race using repository context."""
    repository_context.search.return_value = [{"name": "Elf", "speed": 30}]

    result = await lookup_character_option(type="race", name="Elf")

    assert len(result) == 1
    assert result[0]["name"] == "Elf"
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["option_type"] == "race"


@pytest.mark.asyncio
async def test_lookup_background_with_repository(repository_context):
    """Test looking up a background using repository context."""
    repository_context.search.return_value = [{"name": "Acolyte"}]

    result = await lookup_character_option(type="background", name="Acolyte")

    assert len(result) == 1
    assert result[0]["name"] == "Acolyte"
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["option_type"] == "background"


@pytest.mark.asyncio
async def test_lookup_feat_with_repository(repository_context):
    """Test looking up a feat using repository context."""
    repository_context.search.return_value = [{"name": "Sharpshooter"}]

    result = await lookup_character_option(type="feat", name="Sharpshooter")

    assert len(result) == 1
    assert result[0]["name"] == "Sharpshooter"
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["option_type"] == "feat"


@pytest.mark.asyncio
async def test_lookup_invalid_type():
    """Test invalid type parameter raises ValueError."""

    with pytest.raises(ValueError, match="Invalid type"):
        await lookup_character_option(type="invalid-type")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_lookup_character_option_with_limit(repository_context):
    """Test that limit parameter is passed to repository."""
    options = [{"name": f"Option {i}", "id": i} for i in range(5)]
    repository_context.search.return_value = options

    result = await lookup_character_option(type="class", limit=5)

    assert len(result) == 5
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["limit"] == 5


@pytest.mark.asyncio
async def test_lookup_character_option_empty_results(repository_context):
    """Test character option lookup with no results."""
    repository_context.search.return_value = []

    result = await lookup_character_option(type="class", name="NonexistentClass")

    assert result == []


@pytest.mark.asyncio
async def test_lookup_character_option_api_error(repository_context):
    """Test character option lookup handles API errors gracefully."""
    repository_context.search.side_effect = ApiError("API unavailable")

    with pytest.raises(ApiError, match="API unavailable"):
        await lookup_character_option(type="class")


@pytest.mark.asyncio
async def test_lookup_character_option_network_error(repository_context):
    """Test character option lookup handles network errors."""
    repository_context.search.side_effect = NetworkError("Connection timeout")

    with pytest.raises(NetworkError, match="Connection timeout"):
        await lookup_character_option(type="class")


@pytest.mark.asyncio
async def test_lookup_character_option_no_repository_parameter():
    """Test that lookup_character_option no longer accepts repository parameter."""
    # This test verifies the function does NOT accept repository parameter
    # and instead uses context-based injection like other tools
    sig = inspect.signature(lookup_character_option)
    assert "repository" not in sig.parameters


@pytest.mark.asyncio
async def test_lookup_character_option_with_documents(
    repository_context,
) -> None:
    """Test lookup_character_option with documents filter."""
    repository_context.search.return_value = [{"name": "Barbarian", "document": "srd-5e"}]

    result = await lookup_character_option(type="class", documents=["srd-5e"])

    assert len(result) == 1
    assert result[0]["name"] == "Barbarian"
    # Verify document parameter is passed to repository
    call_kwargs = repository_context.search.call_args[1]
    assert "document" in call_kwargs
    assert call_kwargs["document"] == ["srd-5e"]


@pytest.fixture
def repository_context(mock_character_option_repository):
    """Fixture to inject mock repository via context for tests."""
    character_option_lookup._repository_context["repository"] = mock_character_option_repository
    yield mock_character_option_repository
    # Clean up after test
    if "repository" in character_option_lookup._repository_context:
        del character_option_lookup._repository_context["repository"]
