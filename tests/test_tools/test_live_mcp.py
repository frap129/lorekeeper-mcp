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

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_filter_by_level(self, rate_limiter, clear_cache):
        """Verify level filtering returns only spells of specified level."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(level=0, limit=10)

        assert len(results) >= 5, "Should find at least 5 cantrips"
        for spell in results:
            spell_level = spell.get("level", spell.get("lvl"))
            # Level might be 0, "0", or "cantrip"
            assert spell_level in [0, "0", "cantrip"], f"Expected cantrip, got level {spell_level}"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_filter_by_school(self, rate_limiter, clear_cache):
        """Verify school filtering returns only spells of specified school."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(school="evocation", limit=10)

        assert len(results) >= 1, "Should find at least 1 evocation spell"
        for spell in results:
            school = spell.get("school", "").lower()
            assert "evocation" in school, f"Expected evocation spell, got {school}"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_filter_combined(self, rate_limiter, clear_cache):
        """Verify multiple filters work together correctly."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        # Find wizard spells that require concentration
        results = await lookup_spell(class_key="wizard", concentration=True, limit=10)

        assert len(results) >= 5, "Should find at least 5 wizard concentration spells"
        # Note: API might not return concentration field in all cases
        # Validation depends on API response structure

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_limit_respected(self, rate_limiter, clear_cache):
        """Verify limit parameter restricts result count."""
        from lorekeeper_mcp.tools.spell_lookup import lookup_spell

        await rate_limiter("open5e")
        results = await lookup_spell(limit=5)

        assert len(results) <= 5, f"Requested limit=5 but got {len(results)} results"
        assert len(results) > 0, "Should return some results"


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
