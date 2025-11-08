"""Integration tests for MCP tool registration."""

from lorekeeper_mcp.server import mcp


def test_all_tools_registered():
    """Verify all 5 tools are registered with FastMCP."""

    # Get all registered tools from the tool manager
    tools = mcp._tool_manager._tools
    tool_names = set(tools.keys())

    expected_tools = {
        "lookup_spell",
        "lookup_creature",
        "lookup_character_option",
        "lookup_equipment",
        "lookup_rule",
    }

    assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"


def test_tool_schemas_valid():
    """Verify tool schemas are properly defined."""

    tools = mcp._tool_manager._tools

    # Check lookup_spell schema
    spell_tool = tools.get("lookup_spell")
    assert spell_tool is not None
    assert "name" in spell_tool.parameters["properties"]
    assert "level" in spell_tool.parameters["properties"]
    assert "limit" in spell_tool.parameters["properties"]

    # Check lookup_creature schema
    creature_tool = tools.get("lookup_creature")
    assert creature_tool is not None
    assert "cr" in creature_tool.parameters["properties"]

    # Check lookup_character_option schema
    char_tool = tools.get("lookup_character_option")
    assert char_tool is not None
    assert "type" in char_tool.parameters["required"]

    # Check lookup_equipment schema
    equip_tool = tools.get("lookup_equipment")
    assert equip_tool is not None

    # Check lookup_rule schema
    rule_tool = tools.get("lookup_rule")
    assert rule_tool is not None
    assert "rule_type" in rule_tool.parameters["required"]
