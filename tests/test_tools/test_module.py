"""Test tool module structure."""

from lorekeeper_mcp import tools
from lorekeeper_mcp.tools import (
    search_all,
    search_character_option,
    search_creature,
    search_equipment,
    search_rule,
    search_spell,
)


def test_tools_module_exists():
    """Verify tools module can be imported."""

    assert tools is not None


def test_tools_init_exports():
    """Verify __init__ exports all tool functions."""

    assert callable(search_all)
    assert callable(search_spell)
    assert callable(search_creature)
    assert callable(search_character_option)
    assert callable(search_equipment)
    assert callable(search_rule)
