"""Tests for rule lookup tool."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_lookup_condition(mock_open5e_v2_client):
    """Test looking up a condition."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_open5e_v2_client.get_conditions.return_value = [
        {"name": "Grappled", "desc": "A grappled creature's speed..."}
    ]

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_rule(rule_type="condition", name="Grappled")

    assert len(result) == 1
    assert result[0]["name"] == "Grappled"
    mock_open5e_v2_client.get_conditions.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_damage_type(mock_dnd5e_client):
    """Test looking up a damage type."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_dnd5e_client.get_damage_types.return_value = [
        {"name": "Radiant", "desc": "Radiant damage..."}
    ]

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Dnd5eApiClient",
        return_value=mock_dnd5e_client,
    ):
        result = await lookup_rule(rule_type="damage-type", name="Radiant")

    assert len(result) == 1
    assert result[0]["name"] == "Radiant"
    mock_dnd5e_client.get_damage_types.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_skill(mock_dnd5e_client):
    """Test looking up a skill."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_dnd5e_client.get_skills.return_value = [{"name": "Stealth", "ability_score": "dexterity"}]

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Dnd5eApiClient",
        return_value=mock_dnd5e_client,
    ):
        result = await lookup_rule(rule_type="skill", name="Stealth")

    assert len(result) == 1
    mock_dnd5e_client.get_skills.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_rules_with_section(mock_dnd5e_client):
    """Test looking up rules with section filter."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_dnd5e_client.get_rules.return_value = [{"name": "Combat", "desc": "Combat rules..."}]

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Dnd5eApiClient",
        return_value=mock_dnd5e_client,
    ):
        await lookup_rule(rule_type="rule", section="combat")

    call_kwargs = mock_dnd5e_client.get_rules.call_args[1]
    assert call_kwargs["section"] == "combat"


@pytest.mark.asyncio
async def test_lookup_all_reference_types(mock_dnd5e_client):
    """Test all valid reference types."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    mock_response = []

    # Configure all mock methods
    mock_dnd5e_client.get_weapon_properties.return_value = mock_response
    mock_dnd5e_client.get_ability_scores.return_value = mock_response
    mock_dnd5e_client.get_magic_schools.return_value = mock_response
    mock_dnd5e_client.get_languages.return_value = mock_response
    mock_dnd5e_client.get_proficiencies.return_value = mock_response
    mock_dnd5e_client.get_alignments.return_value = mock_response

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Dnd5eApiClient",
        return_value=mock_dnd5e_client,
    ):
        # Test each type
        await lookup_rule(rule_type="weapon-property")
        await lookup_rule(rule_type="ability-score")
        await lookup_rule(rule_type="magic-school")
        await lookup_rule(rule_type="language")
        await lookup_rule(rule_type="proficiency")
        await lookup_rule(rule_type="alignment")

    # Verify all were called
    mock_dnd5e_client.get_weapon_properties.assert_awaited_once()
    mock_dnd5e_client.get_ability_scores.assert_awaited_once()
    mock_dnd5e_client.get_magic_schools.assert_awaited_once()
    mock_dnd5e_client.get_languages.assert_awaited_once()
    mock_dnd5e_client.get_proficiencies.assert_awaited_once()
    mock_dnd5e_client.get_alignments.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_invalid_rule_type():
    """Test invalid rule type raises ValueError."""
    from lorekeeper_mcp.tools.rule_lookup import lookup_rule

    with pytest.raises(ValueError, match="Invalid type"):
        await lookup_rule(rule_type="invalid-rule-type")
