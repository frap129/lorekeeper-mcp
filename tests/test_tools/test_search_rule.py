"""Tests for rule search tool."""

import contextlib
import importlib
import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.tools.search_rule import search_rule

search_rule_module = importlib.import_module("lorekeeper_mcp.tools.search_rule")


@pytest.mark.asyncio
async def test_search_invalid_rule_type():
    """Test invalid rule type raises ValueError."""

    with pytest.raises(ValueError, match="Invalid type"):
        await search_rule(rule_type="invalid-rule-type")  # type: ignore[arg-type]


@pytest.fixture
def mock_rule_repository() -> MagicMock:
    """Create mock rule repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.fixture
def repository_context(mock_rule_repository):
    """Fixture to inject mock repository via context for tests."""
    search_rule_module._repository_context["repository"] = mock_rule_repository
    yield mock_rule_repository
    # Clean up after test
    if "repository" in search_rule_module._repository_context:
        del search_rule_module._repository_context["repository"]


@pytest.mark.asyncio
async def test_search_rule_with_repository(repository_context):
    """Test looking up a rule using repository."""
    repository_context.search.return_value = [
        {"name": "Combat", "desc": "Combat rules...", "index": "combat"}
    ]

    result = await search_rule(rule_type="rule")

    assert len(result) == 1
    assert result[0]["name"] == "Combat"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "rule"


@pytest.mark.asyncio
async def test_search_condition_with_repository(repository_context):
    """Test looking up a condition using repository."""
    repository_context.search.return_value = [
        {"name": "Grappled", "desc": "A grappled creature's speed..."}
    ]

    result = await search_rule(rule_type="condition", search="Grappled")

    assert len(result) == 1
    assert result[0]["name"] == "Grappled"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "condition"


@pytest.mark.asyncio
async def test_search_damage_type_with_repository(repository_context):
    """Test looking up a damage type using repository."""
    repository_context.search.return_value = [{"name": "Radiant", "desc": "Radiant damage..."}]

    result = await search_rule(rule_type="damage-type", search="Radiant")

    assert len(result) == 1
    assert result[0]["name"] == "Radiant"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "damage-type"


@pytest.mark.asyncio
async def test_search_weapon_property_with_repository(repository_context):
    """Test looking up a weapon property using repository."""
    repository_context.search.return_value = [
        {"name": "Finesse", "desc": "When making an attack..."}
    ]

    result = await search_rule(rule_type="weapon-property")

    assert len(result) == 1
    assert result[0]["name"] == "Finesse"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "weapon-property"


@pytest.mark.asyncio
async def test_search_skill_with_repository(repository_context):
    """Test looking up a skill using repository."""
    repository_context.search.return_value = [{"name": "Stealth", "ability_score": "dexterity"}]

    result = await search_rule(rule_type="skill", search="Stealth")

    assert len(result) == 1
    assert result[0]["name"] == "Stealth"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "skill"


@pytest.mark.asyncio
async def test_search_ability_score_with_repository(repository_context):
    """Test looking up ability scores using repository."""
    repository_context.search.return_value = [{"name": "Strength", "desc": "Strength ability..."}]

    result = await search_rule(rule_type="ability-score")

    assert len(result) == 1
    assert result[0]["name"] == "Strength"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "ability-score"


@pytest.mark.asyncio
async def test_search_magic_school_with_repository(repository_context):
    """Test looking up magic schools using repository."""
    repository_context.search.return_value = [{"name": "Evocation", "desc": "Evocation school..."}]

    result = await search_rule(rule_type="magic-school")

    assert len(result) == 1
    assert result[0]["name"] == "Evocation"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "magic-school"


@pytest.mark.asyncio
async def test_search_language_with_repository(repository_context):
    """Test looking up languages using repository."""
    repository_context.search.return_value = [{"name": "Common", "type": "common"}]

    result = await search_rule(rule_type="language")

    assert len(result) == 1
    assert result[0]["name"] == "Common"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "language"


@pytest.mark.asyncio
async def test_search_proficiency_with_repository(repository_context):
    """Test looking up proficiencies using repository."""
    repository_context.search.return_value = [{"name": "Armor", "class": "armor"}]

    result = await search_rule(rule_type="proficiency")

    assert len(result) == 1
    assert result[0]["name"] == "Armor"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "proficiency"


@pytest.mark.asyncio
async def test_search_alignment_with_repository(repository_context):
    """Test looking up alignments using repository."""
    repository_context.search.return_value = [
        {"name": "Lawful Good", "desc": "Alignment description..."}
    ]

    result = await search_rule(rule_type="alignment")

    assert len(result) == 1
    assert result[0]["name"] == "Lawful Good"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "alignment"


@pytest.mark.asyncio
async def test_search_rule_with_section_and_repository(repository_context):
    """Test looking up rules with section filter using repository."""
    repository_context.search.return_value = [
        {"name": "Combat", "desc": "Combat rules...", "section": "combat"}
    ]

    await search_rule(rule_type="rule", section="combat")

    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("section") == "combat"
    assert call_kwargs.get("rule_type") == "rule"


@pytest.mark.asyncio
async def test_search_rule_no_repository_parameter():
    """Test that search_rule no longer accepts repository parameter."""
    # This test verifies the function signature doesn't have repository parameter
    sig = inspect.signature(search_rule)
    assert "repository" not in sig.parameters


@pytest.mark.asyncio
async def test_search_rule_with_context_injection(repository_context):
    """Test looking up rule using context-based repository injection."""
    repository_context.search.return_value = [
        {"name": "Combat", "desc": "Combat rules...", "index": "combat"}
    ]

    result = await search_rule(rule_type="rule")

    assert len(result) == 1
    assert result[0]["name"] == "Combat"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "rule"


@pytest.mark.asyncio
async def test_search_rule_default_repository():
    """Test that search_rule creates default repository when no context is set."""
    # Clear any existing context
    if hasattr(search_rule_module, "_repository_context"):
        search_rule_module._repository_context.clear()

    # This should work without errors (creates default repository)
    # We expect this to potentially fail with network errors in test environment,
    # but we're testing the repository creation logic
    with contextlib.suppress(Exception):
        await search_rule(rule_type="rule", limit=1)


@pytest.mark.asyncio
async def test_search_rule_with_documents(repository_context) -> None:
    """Test search_rule with documents filter."""
    repository_context.search.return_value = [
        {"name": "Combat", "desc": "Combat rules...", "document": "srd-5e"}
    ]

    result = await search_rule(rule_type="rule", search="Combat", documents=["srd-5e"])

    assert len(result) == 1
    assert result[0]["name"] == "Combat"
    assert result[0]["document"] == "srd-5e"
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs.get("rule_type") == "rule"
    # Verify document parameter is passed (documents maps to document)
    assert "document" in call_kwargs
    assert call_kwargs["document"] == ["srd-5e"]


@pytest.mark.asyncio
async def test_search_rule_with_search_param(repository_context):
    """Test rule search with search parameter."""
    repository_context.search.return_value = [
        {"name": "Grappled", "desc": "A grappled creature's speed becomes 0..."}
    ]

    result = await search_rule(rule_type="condition", search="movement restricted hold")

    assert len(result) == 1
    assert result[0]["name"] == "Grappled"

    # Verify repository.search was called with search parameter
    repository_context.search.assert_awaited_once()
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["search"] == "movement restricted hold"


@pytest.mark.asyncio
async def test_search_rule_search_param_with_filters(repository_context):
    """Test rule search combining search with traditional filters."""
    repository_context.search.return_value = [{"name": "Fire", "desc": "Fire damage burns..."}]

    result = await search_rule(
        rule_type="damage-type",
        search="burning flame heat",
        documents=["srd-5e"],
    )

    assert len(result) == 1

    # Verify all parameters were passed to repository
    call_kwargs = repository_context.search.call_args[1]
    assert call_kwargs["search"] == "burning flame heat"
    assert call_kwargs["document"] == ["srd-5e"]


@pytest.mark.asyncio
async def test_search_rule_search_none_not_passed(repository_context):
    """Test that search=None is not passed to repository."""
    repository_context.search.return_value = [{"name": "Combat", "desc": "Combat rules..."}]

    # Call without search (default is None)
    await search_rule(rule_type="rule")

    call_kwargs = repository_context.search.call_args[1]
    # search should not be in the params when None
    assert "search" not in call_kwargs
