"""Tests for rule lookup tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.tools.rule_lookup import lookup_rule


@pytest.mark.asyncio
async def test_lookup_invalid_rule_type():
    """Test invalid rule type raises ValueError."""

    with pytest.raises(ValueError, match="Invalid type"):
        await lookup_rule(rule_type="invalid-rule-type")  # type: ignore[arg-type]


@pytest.fixture
def mock_rule_repository() -> MagicMock:
    """Create mock rule repository for testing."""
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_lookup_rule_with_repository(mock_rule_repository):
    """Test looking up a rule using repository."""
    mock_rule_repository.search.return_value = [
        {"name": "Combat", "desc": "Combat rules...", "index": "combat"}
    ]

    result = await lookup_rule(rule_type="rule", repository=mock_rule_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Combat"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "rule"


@pytest.mark.asyncio
async def test_lookup_condition_with_repository(mock_rule_repository):
    """Test looking up a condition using repository."""
    mock_rule_repository.search.return_value = [
        {"name": "Grappled", "desc": "A grappled creature's speed..."}
    ]

    result = await lookup_rule(
        rule_type="condition", name="Grappled", repository=mock_rule_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Grappled"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "condition"


@pytest.mark.asyncio
async def test_lookup_damage_type_with_repository(mock_rule_repository):
    """Test looking up a damage type using repository."""
    mock_rule_repository.search.return_value = [{"name": "Radiant", "desc": "Radiant damage..."}]

    result = await lookup_rule(
        rule_type="damage-type", name="Radiant", repository=mock_rule_repository
    )

    assert len(result) == 1
    assert result[0]["name"] == "Radiant"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "damage-type"


@pytest.mark.asyncio
async def test_lookup_weapon_property_with_repository(mock_rule_repository):
    """Test looking up a weapon property using repository."""
    mock_rule_repository.search.return_value = [
        {"name": "Finesse", "desc": "When making an attack..."}
    ]

    result = await lookup_rule(rule_type="weapon-property", repository=mock_rule_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Finesse"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "weapon-property"


@pytest.mark.asyncio
async def test_lookup_skill_with_repository(mock_rule_repository):
    """Test looking up a skill using repository."""
    mock_rule_repository.search.return_value = [{"name": "Stealth", "ability_score": "dexterity"}]

    result = await lookup_rule(rule_type="skill", name="Stealth", repository=mock_rule_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Stealth"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "skill"


@pytest.mark.asyncio
async def test_lookup_ability_score_with_repository(mock_rule_repository):
    """Test looking up ability scores using repository."""
    mock_rule_repository.search.return_value = [{"name": "Strength", "desc": "Strength ability..."}]

    result = await lookup_rule(rule_type="ability-score", repository=mock_rule_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Strength"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "ability-score"


@pytest.mark.asyncio
async def test_lookup_magic_school_with_repository(mock_rule_repository):
    """Test looking up magic schools using repository."""
    mock_rule_repository.search.return_value = [
        {"name": "Evocation", "desc": "Evocation school..."}
    ]

    result = await lookup_rule(rule_type="magic-school", repository=mock_rule_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Evocation"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "magic-school"


@pytest.mark.asyncio
async def test_lookup_language_with_repository(mock_rule_repository):
    """Test looking up languages using repository."""
    mock_rule_repository.search.return_value = [{"name": "Common", "type": "common"}]

    result = await lookup_rule(rule_type="language", repository=mock_rule_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Common"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "language"


@pytest.mark.asyncio
async def test_lookup_proficiency_with_repository(mock_rule_repository):
    """Test looking up proficiencies using repository."""
    mock_rule_repository.search.return_value = [{"name": "Armor", "class": "armor"}]

    result = await lookup_rule(rule_type="proficiency", repository=mock_rule_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Armor"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "proficiency"


@pytest.mark.asyncio
async def test_lookup_alignment_with_repository(mock_rule_repository):
    """Test looking up alignments using repository."""
    mock_rule_repository.search.return_value = [
        {"name": "Lawful Good", "desc": "Alignment description..."}
    ]

    result = await lookup_rule(rule_type="alignment", repository=mock_rule_repository)

    assert len(result) == 1
    assert result[0]["name"] == "Lawful Good"
    mock_rule_repository.search.assert_awaited_once()
    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("rule_type") == "alignment"


@pytest.mark.asyncio
async def test_lookup_rule_with_section_and_repository(mock_rule_repository):
    """Test looking up rules with section filter using repository."""
    mock_rule_repository.search.return_value = [
        {"name": "Combat", "desc": "Combat rules...", "section": "combat"}
    ]

    await lookup_rule(rule_type="rule", section="combat", repository=mock_rule_repository)

    call_kwargs = mock_rule_repository.search.call_args[1]
    assert call_kwargs.get("section") == "combat"
    assert call_kwargs.get("rule_type") == "rule"
