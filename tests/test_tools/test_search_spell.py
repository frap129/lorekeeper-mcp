"""Tests for spell search tool."""

import importlib
import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError
from lorekeeper_mcp.models import Spell
from lorekeeper_mcp.tools.search_spell import search_spell

search_spell_module = importlib.import_module("lorekeeper_mcp.tools.search_spell")


@pytest.fixture
def mock_spell_repository() -> MagicMock:
    """Create mock spell repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.fixture
def repository_context(mock_spell_repository):
    """Fixture to inject mock repository via context for tests."""
    search_spell_module._repository_context["repository"] = mock_spell_repository
    yield mock_spell_repository
    # Clean up after test
    if "repository" in search_spell_module._repository_context:
        del search_spell_module._repository_context["repository"]


@pytest.mark.asyncio
async def test_search_spell_by_name(repository_context):
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
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    result = await search_spell(name="Fireball")

    assert len(result) == 1
    assert result[0]["name"] == "Fireball"
    assert result[0]["level"] == 3
    assert result[0]["school"] == "evocation"
    repository_context.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_spell_with_filters(repository_context):
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
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    await search_spell(
        level=3,
        school="evocation",
        concentration=False,
        limit=10,
    )

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["level"] == 3
    assert call_kwargs["school"] == "evocation"
    assert call_kwargs["concentration"] is False


@pytest.mark.asyncio
async def test_search_spell_empty_results(repository_context):
    """Test spell lookup with no results."""
    repository_context.search.return_value = []

    result = await search_spell(name="NonexistentSpell")

    assert result == []


@pytest.mark.asyncio
async def test_search_spell_api_error(repository_context):
    """Test spell lookup handles API errors gracefully."""
    repository_context.search.side_effect = ApiError("API unavailable")

    with pytest.raises(ApiError, match="API unavailable"):
        await search_spell(name="Fireball")


@pytest.mark.asyncio
async def test_search_spell_network_error(repository_context):
    """Test spell lookup handles network errors."""
    repository_context.search.side_effect = NetworkError("Connection timeout")

    with pytest.raises(NetworkError, match="Connection timeout"):
        await search_spell(name="Fireball")


@pytest.mark.asyncio
async def test_spell_search_by_name_server_side(repository_context):
    """Test that spell lookup passes name filter to repository for server-side filtering."""
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
        document=None,
    )

    # Repository returns only matching spells (server-side filtered)
    repository_context.search.return_value = [spell_fireball]

    # Call with name filter - should pass to repository
    result = await search_spell(name="fireball")

    # Should return Fireball
    assert len(result) == 1
    assert result[0]["name"] == "Fireball"

    # Verify repository.search was called WITH name parameter (server-side filtering)
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["name"] == "fireball"


@pytest.mark.asyncio
async def test_search_spell_limit_applied(repository_context):
    """Test that search_spell applies limit to results."""
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
            document=None,
        )
        for i in range(1, 30)
    ]

    repository_context.search.return_value = spells

    result = await search_spell(limit=5)

    # Should only return 5 spells even though repository returned 29
    assert len(result) == 5


@pytest.mark.asyncio
async def test_search_spell_default_repository():
    """Test that search_spell creates default repository when not provided."""
    # This test verifies the function no longer accepts repository parameter
    # and instead uses context-based injection
    sig = inspect.signature(search_spell)
    assert "repository" not in sig.parameters


@pytest.mark.asyncio
async def test_search_spell_by_class_key(repository_context):
    """Test filtering spells by character class."""
    wizard_spell = Spell(
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
        classes=["wizard", "sorcerer"],
        document=None,
    )

    # Repository filters by class (server-side) and returns only wizard spells
    repository_context.search.return_value = [wizard_spell]

    results = await search_spell(class_key="wizard", limit=10)

    # Should return wizard spells
    assert len(results) == 1
    assert results[0]["name"] == "Fireball"
    assert "wizard" in results[0]["classes"]
    # Verify repository.search was called with class_key parameter
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["class_key"] == "wizard"


@pytest.mark.asyncio
async def test_search_spell_with_level_min(repository_context):
    """Test filtering spells by minimum level."""
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
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    result = await search_spell(level_min=3)

    assert len(result) == 1
    assert result[0]["level"] == 3
    # Verify repository.search was called with level_min parameter
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["level_min"] == 3


@pytest.mark.asyncio
async def test_search_spell_with_level_max(repository_context):
    """Test filtering spells by maximum level."""
    spell_obj = Spell(
        name="Magic Missile",
        slug="magic-missile",
        level=1,
        school="evocation",
        casting_time="1 action",
        range="120 feet",
        components="V,S",
        material=None,
        duration="Instantaneous",
        concentration=False,
        ritual=False,
        desc="A missile of magical force...",
        document_url="https://example.com/magic-missile",
        higher_level="When you cast this spell...",
        damage_type=None,
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    result = await search_spell(level_max=3)

    assert len(result) == 1
    assert result[0]["level"] == 1
    # Verify repository.search was called with level_max parameter
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["level_max"] == 3


@pytest.mark.asyncio
async def test_search_spell_with_level_range(repository_context):
    """Test filtering spells by level range using both min and max."""
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
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    result = await search_spell(level_min=1, level_max=5)

    assert len(result) == 1
    assert result[0]["level"] == 3
    # Verify both parameters were passed to repository
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["level_min"] == 1
    assert call_kwargs["level_max"] == 5


@pytest.mark.asyncio
async def test_search_spell_with_damage_type(repository_context):
    """Test filtering spells by damage type."""
    fire_spell = Spell(
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
        damage_type=["fire"],
        document=None,
    )

    repository_context.search.return_value = [fire_spell]

    result = await search_spell(damage_type="fire")

    assert len(result) == 1
    assert result[0]["name"] == "Fireball"
    # Verify repository.search was called with damage_type parameter
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["damage_type"] == "fire"


@pytest.mark.asyncio
async def test_search_spell_backward_compatibility(repository_context):
    """Test that search_spell is backward compatible without new parameters."""
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
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    # Call without new parameters - should work as before
    result = await search_spell(name="Fireball")

    assert len(result) == 1
    assert result[0]["name"] == "Fireball"
    # Verify only name parameter was passed (not level_min, level_max, damage_type)
    call_kwargs = repository_context.search.call_args[1]
    assert "name" in call_kwargs
    assert "level_min" not in call_kwargs
    assert "level_max" not in call_kwargs
    assert "damage_type" not in call_kwargs


@pytest.mark.asyncio
async def test_search_spell_with_document_filter(repository_context):
    """Test looking up spells filtered by document name."""
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
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    results = await search_spell(documents=["System Reference Document 5.1"], level=3)

    # Verify repository was called with document filter
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["document"] == ["System Reference Document 5.1"]

    # Verify results include spell data
    assert len(results) == 1
    assert results[0]["name"] == "Fireball"
    assert results[0]["level"] == 3


@pytest.mark.asyncio
async def test_search_spell_with_documents(repository_context):
    """Test search_spell with documents filter."""
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
        document="srd-5e",
    )

    repository_context.search.return_value = [spell_obj]

    results = await search_spell(name="fireball", documents=["srd-5e"])

    assert len(results) == 1
    assert results[0]["document"] == "srd-5e"

    # Verify repository was called with document parameter (not documents)
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["document"] == ["srd-5e"]


@pytest.mark.asyncio
async def test_search_spell_with_semantic_query(repository_context):
    """Test spell lookup with semantic_query parameter."""
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
        damage_type=["fire"],
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    result = await search_spell(semantic_query="fire damage explosion")

    assert len(result) == 1
    assert result[0]["name"] == "Fireball"

    # Verify repository.search was called with semantic_query parameter
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["semantic_query"] == "fire damage explosion"


@pytest.mark.asyncio
async def test_search_spell_semantic_query_with_filters(repository_context):
    """Test spell lookup combining semantic_query with traditional filters."""
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
        damage_type=["fire"],
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    result = await search_spell(semantic_query="fire explosion", level=3, school="evocation")

    assert len(result) == 1

    # Verify all parameters were passed to repository
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["semantic_query"] == "fire explosion"
    assert call_kwargs["level"] == 3
    assert call_kwargs["school"] == "evocation"


@pytest.mark.asyncio
async def test_search_spell_semantic_query_none_not_passed(repository_context):
    """Test that semantic_query=None is not passed to repository."""
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
        document=None,
    )

    repository_context.search.return_value = [spell_obj]

    # Call without semantic_query (default is None)
    await search_spell(name="Fireball")

    call_kwargs = repository_context.search.call_args[1]
    # semantic_query should not be in the params when None
    assert "semantic_query" not in call_kwargs
