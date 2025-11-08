"""Test tool module structure."""

from lorekeeper_mcp import tools
from lorekeeper_mcp.tools import (
    lookup_character_option,
    lookup_creature,
    lookup_equipment,
    lookup_rule,
    lookup_spell,
)


def test_tools_module_exists():
    """Verify tools module can be imported."""

    assert tools is not None


def test_tools_init_exports():
    """Verify __init__ exports all tool functions."""

    assert callable(lookup_spell)
    assert callable(lookup_creature)
    assert callable(lookup_character_option)
    assert callable(lookup_equipment)
    assert callable(lookup_rule)
