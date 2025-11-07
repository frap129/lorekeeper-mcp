"""
Live integration tests for MCP tools against real APIs.

These tests validate functionality against live Open5e and D&D 5e APIs.
They are marked with @pytest.mark.live and can be skipped with:
    pytest -m "not live"

Run only live tests with:
    pytest -m live

Requirements:
- Internet connection
- Working Open5e and D&D 5e API endpoints
- Reasonable API rate limits

Performance expectations:
- Uncached queries: < 3 seconds
- Cached queries: < 50ms
"""

import pytest


class TestLiveSpellLookup:
    """Live tests for lookup_spell tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_by_name_found(self, rate_limiter, clear_cache):
        """Verify well-known spell can be found by name."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(name="Magic Missile")

        assert len(results) > 0, "Should find at least one 'Magic Missile' spell"
        first_result = results[0]
        assert "magic missile" in first_result["name"].lower()
        assert "level" in first_result
        assert "school" in first_result
        assert "description" in first_result or "desc" in first_result

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_by_name_not_found(self, rate_limiter, clear_cache):
        """Verify non-existent spell returns empty results."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(name="NonexistentSpell12345XYZ")

        assert len(results) == 0, "Non-existent spell should return empty list"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_basic_fields_present(self, rate_limiter, clear_cache):
        """Verify spell response contains expected schema fields."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(name="Fireball")

        assert len(results) > 0, "Should find Fireball spell"
        spell = results[0]

        # Required fields
        assert "name" in spell
        assert "level" in spell
        assert "school" in spell

        # Check level is correct type
        assert isinstance(spell["level"], int | str)
        if isinstance(spell["level"], str):
            assert spell["level"].isdigit() or spell["level"] == "cantrip"


class TestLiveCreatureLookup:
    """Live tests for lookup_creature tool."""


class TestLiveEquipmentLookup:
    """Live tests for lookup_equipment tool."""


class TestLiveCharacterOptionLookup:
    """Live tests for lookup_character_option tool."""


class TestLiveRuleLookup:
    """Live tests for lookup_rule tool."""


class TestLiveCacheValidation:
    """Cross-cutting cache behavior validation."""


class TestLivePerformance:
    """Performance benchmarks for live API calls."""
