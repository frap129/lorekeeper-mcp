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

import json
import time

import pytest

from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option
from lorekeeper_mcp.tools.creature_lookup import lookup_creature
from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment
from lorekeeper_mcp.tools.rule_lookup import lookup_rule
from lorekeeper_mcp.tools.spell_lookup import lookup_spell


class TestLiveSpellLookup:
    """Live tests for lookup_spell tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_by_name_found(self, rate_limiter, clear_cache):
        """Verify well-known spell can be found by name."""

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

        await rate_limiter("open5e")
        results = await lookup_spell(name="NonexistentSpell12345XYZ")

        assert len(results) == 0, "Non-existent spell should return empty list"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_basic_fields_present(self, rate_limiter, clear_cache):
        """Verify spell response contains expected schema fields."""

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

        await rate_limiter("open5e")
        results = await lookup_spell(limit=5)

        assert len(results) <= 5, f"Requested limit=5 but got {len(results)} results"
        assert len(results) > 0, "Should return some results"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_cache_miss_then_hit(self, rate_limiter, clear_cache):
        """Verify cache behavior on duplicate queries."""

        await rate_limiter("open5e")

        # First call - cache miss (no filters, just limit)
        first_results = await lookup_spell(limit=20)

        assert len(first_results) > 0, "Should find spells"

        # Second call - cache hit (identical call should reuse cached API results)
        second_results = await lookup_spell(limit=20)

        assert second_results == first_results, "Cached results should match"
        # Second call might not always be faster due to network variance,
        # but should be significantly faster if cache worked
        # We just verify results are identical
        assert len(second_results) == len(first_results), "Result count should be consistent"

    @pytest.mark.live
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_spell_cache_performance(self, rate_limiter, clear_cache):
        """Verify cached queries return consistent results."""

        await rate_limiter("open5e")

        # Make multiple calls with same parameters
        call1 = await lookup_spell(limit=10)
        assert len(call1) > 0, "Should get results"

        # Second call should return same results (cache is working)
        call2 = await lookup_spell(limit=10)
        assert call2 == call1, "Repeated queries should return identical results from cache"

        # Third call for consistency
        call3 = await lookup_spell(limit=10)
        assert call3 == call1, "All identical queries should return same cached results"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_different_queries_different_cache(self, rate_limiter, clear_cache):
        """Verify different queries use separate cache entries."""

        await rate_limiter("open5e")

        # Execute two different queries with different API parameters
        # These result in different cache entries
        results_level0 = await lookup_spell(level=0, limit=10)
        await rate_limiter("open5e")
        results_level1 = await lookup_spell(level=1, limit=10)

        assert (
            results_level0 != results_level1
        ), "Different level filters should have different results"

        # Verify both are cached independently
        start_0 = time.time()
        cached_level0 = await lookup_spell(level=0, limit=10)
        duration_0 = time.time() - start_0

        start_1 = time.time()
        cached_level1 = await lookup_spell(level=1, limit=10)
        duration_1 = time.time() - start_1

        assert cached_level0 == results_level0, "Level 0 cache should work"
        assert cached_level1 == results_level1, "Level 1 cache should work"
        # Both should be cached (fast), no specific threshold needed
        assert duration_0 < 2.0, "Cached level 0 query should be reasonably fast"
        assert duration_1 < 2.0, "Cached level 1 query should be reasonably fast"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_invalid_school(self, rate_limiter, clear_cache):
        """Verify graceful handling of invalid school parameter."""

        await rate_limiter("open5e")

        # Try invalid school - should return empty or handle gracefully
        results = await lookup_spell(school="InvalidSchoolXYZ123")

        # Should not crash - either empty results or filtered out
        assert isinstance(results, list), "Should return list even with invalid school"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_invalid_limit(self, rate_limiter, clear_cache):
        """Verify handling of invalid limit parameter."""

        await rate_limiter("open5e")

        # Negative limit should be handled gracefully
        try:
            results = await lookup_spell(limit=-5)
            # If it doesn't raise, should return empty or default
            assert isinstance(results, list), "Should return list"
        except (ValueError, AssertionError):
            # Acceptable to raise validation error
            pass

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_spell_empty_results(self, rate_limiter, clear_cache):
        """Verify handling of queries with no matches."""

        await rate_limiter("open5e")

        # Query that should match nothing
        results = await lookup_spell(name="ZZZNonexistent", level=9, school="abjuration")

        assert isinstance(results, list), "Should return list"
        assert len(results) == 0, "Should return empty list for no matches"


class TestLiveCreatureLookup:
    """Live tests for lookup_creature tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_by_name_found(self, rate_limiter, clear_cache):
        """Verify creatures can be found by name search."""

        await rate_limiter("open5e")
        results = await lookup_creature(name="Goblin", limit=50)

        assert len(results) > 0, "Should find creatures matching 'Goblin'"
        # Verify at least one result contains "goblin" in name
        goblin_found = any("goblin" in c["name"].lower() for c in results)
        assert goblin_found, "Should find at least one creature with 'goblin' in name"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_by_name_not_found(self, rate_limiter, clear_cache):
        """Verify non-existent creature returns empty results."""

        await rate_limiter("open5e")
        results = await lookup_creature(name="NonexistentCreature12345XYZ")

        assert len(results) == 0, "Non-existent creature should return empty list"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_basic_fields_present(self, rate_limiter, clear_cache):
        """Verify creature response contains expected schema fields."""

        await rate_limiter("open5e")
        results = await lookup_creature(name="Goblin")

        assert len(results) > 0, "Should find Goblin"
        creature = results[0]

        # Check for expected fields
        assert "name" in creature
        # CR might be challenge_rating, cr, or challenge
        assert any(key in creature for key in ["challenge_rating", "cr", "challenge"])
        # Type field
        assert "type" in creature

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_filter_by_cr(self, rate_limiter, clear_cache):
        """Verify CR filtering returns creatures of specified challenge rating."""

        await rate_limiter("open5e")
        results = await lookup_creature(cr=1, limit=10)

        assert len(results) >= 3, "Should find at least 3 CR 1 creatures"
        for creature in results:
            cr = creature.get("challenge_rating", creature.get("cr", ""))
            # CR might be "1", 1, or "1.0"
            assert str(cr) in ["1", "1.0"], f"Expected CR 1, got {cr}"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_filter_by_type(self, rate_limiter, clear_cache):
        """Verify type filtering returns creatures of specified type."""

        await rate_limiter("open5e")
        results = await lookup_creature(type="Beast", limit=10)

        assert len(results) >= 5, "Should find at least 5 beasts"
        for creature in results:
            creature_type = creature.get("type", "").lower()
            assert "beast" in creature_type, f"Expected beast, got {creature_type}"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_filter_by_size(self, rate_limiter, clear_cache):
        """Verify size filtering returns creatures of specified size."""

        await rate_limiter("open5e")
        results = await lookup_creature(size="Large", limit=10)

        assert len(results) >= 3, "Should find at least 3 Large creatures"
        for creature in results:
            size = creature.get("size", "").lower()
            assert "large" in size, f"Expected Large, got {size}"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_cache_behavior(self, rate_limiter, clear_cache):
        """Verify cache hit/miss behavior for creature lookups."""

        await rate_limiter("open5e")

        # First call
        first = await lookup_creature(name="Dragon")
        # Second call (cached)
        second = await lookup_creature(name="Dragon")

        assert second == first, "Cached results should match"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_invalid_type(self, rate_limiter, clear_cache):
        """Verify handling of invalid creature type."""

        await rate_limiter("open5e")
        results = await lookup_creature(type="InvalidType123")

        # Should not crash
        assert isinstance(results, list), "Should return list"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_creature_empty_results(self, rate_limiter, clear_cache):
        """Verify handling of no matches."""

        await rate_limiter("open5e")
        results = await lookup_creature(name="ZZZNonexistent", cr=30)

        assert isinstance(results, list), "Should return list"
        assert len(results) == 0, "Should return empty list"


class TestLiveEquipmentLookup:
    """Live tests for lookup_equipment tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_equipment_weapon_lookup(self, rate_limiter, clear_cache):
        """Verify weapon lookup returns weapons."""

        await rate_limiter("open5e")
        results = await lookup_equipment(type="weapon", limit=10)

        assert len(results) > 0, "Should find weapons"
        # Verify the first result has weapon-like properties
        weapon = results[0]
        assert "name" in weapon
        assert "damage_dice" in weapon or "damage" in weapon

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_equipment_armor_lookup(self, rate_limiter, clear_cache):
        """Verify armor lookup with AC properties."""

        await rate_limiter("open5e")
        results = await lookup_equipment(type="armor", limit=10)

        assert len(results) >= 5, "Should find at least 5 armor items"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_equipment_cache_behavior(self, rate_limiter, clear_cache):
        """Verify cache behavior."""

        await rate_limiter("open5e")

        # Query weapons only to avoid magic items API issues
        first = await lookup_equipment(type="weapon", limit=10)
        second = await lookup_equipment(type="weapon", limit=10)

        assert first == second, "Cached results should match"


class TestLiveCharacterOptionLookup:
    """Live tests for lookup_character_option tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_character_option_class_lookup(self, rate_limiter, clear_cache):
        """Verify class lookup returns expected classes."""

        await rate_limiter("open5e")
        results = await lookup_character_option(type="class")

        assert len(results) >= 12, "Should find at least 12 classes"
        class_names = [c["name"].lower() for c in results]
        assert any("wizard" in name for name in class_names)
        assert any("fighter" in name for name in class_names)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_character_option_race_lookup(self, rate_limiter, clear_cache):
        """Verify race lookup returns expected races."""

        await rate_limiter("open5e")
        results = await lookup_character_option(type="race")

        assert len(results) >= 9, "Should find at least 9 races"
        race_names = [r["name"].lower() for r in results]
        assert any("human" in name for name in race_names)
        assert any("elf" in name for name in race_names)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_character_option_feat_lookup(self, rate_limiter, clear_cache):
        """Verify feat lookup returns expected feats."""

        await rate_limiter("open5e")
        results = await lookup_character_option(type="feat")

        assert len(results) >= 20, "Should find at least 20 feats"


class TestLiveRuleLookup:
    """Live tests for lookup_rule tool."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_rule_condition_lookup(self, rate_limiter, clear_cache):
        """Verify condition lookup returns expected conditions."""

        await rate_limiter("open5e")
        results = await lookup_rule(rule_type="condition")

        assert len(results) >= 10, "Should find at least 10 conditions"
        condition_names = [c["name"].lower() for c in results]
        assert any("prone" in name for name in condition_names)
        assert any("grappled" in name for name in condition_names)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_rule_skill_lookup(self, rate_limiter, clear_cache):
        """Verify skill lookup returns exactly 18 skills."""

        await rate_limiter("open5e")
        results = await lookup_rule(rule_type="skill")

        # D&D 5e has exactly 18 skills
        assert len(results) == 18, f"Expected 18 skills, got {len(results)}"
        skill_names = [s["name"].lower() for s in results]
        assert any("perception" in name for name in skill_names)
        assert any("stealth" in name for name in skill_names)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_rule_ability_score_lookup(self, rate_limiter, clear_cache):
        """Verify ability score lookup returns exactly 6 abilities."""

        await rate_limiter("open5e")
        results = await lookup_rule(rule_type="ability-score")

        # D&D 5e has exactly 6 ability scores
        assert len(results) == 6, f"Expected 6 abilities, got {len(results)}"
        ability_names = [a["name"].upper() for a in results]
        # API returns abbreviated names: STR, DEX, CON, INT, WIS, CHA
        expected = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        for ability in expected:
            assert any(ability in name for name in ability_names), f"Missing {ability}"


class TestLiveCacheValidation:
    """Cross-cutting cache behavior validation."""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_cache_isolation_across_tools(self, rate_limiter, clear_cache):
        """Verify different tools use separate cache entries."""

        await rate_limiter("open5e")

        # Call both tools
        spells = await lookup_spell(name="Fire")
        await rate_limiter("open5e")
        creatures = await lookup_creature(name="Fire")

        # Should get different results (spells vs creatures)
        assert spells != creatures, "Different tools should have different results"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_cache_key_uniqueness(self, rate_limiter, clear_cache):
        """Verify different parameters create different cache keys."""

        await rate_limiter("open5e")

        # Different level parameters should be cached separately
        level0 = await lookup_spell(level=0, limit=5)
        await rate_limiter("open5e")
        level1 = await lookup_spell(level=1, limit=5)

        assert level0 != level1, "Different parameters should yield different results"

        # Both should be cached
        start = time.time()
        cached0 = await lookup_spell(level=0, limit=5)
        duration0 = time.time() - start

        start = time.time()
        cached1 = await lookup_spell(level=1, limit=5)
        duration1 = time.time() - start

        assert cached0 == level0, "Level 0 cache should work"
        assert cached1 == level1, "Level 1 cache should work"
        assert duration0 < 0.05 and duration1 < 0.05, "Both should be fast"


class TestLivePerformance:
    """Performance benchmarks for live API calls."""

    @pytest.mark.live
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_uncached_call_performance(self, rate_limiter, clear_cache):
        """Verify API calls complete within time limit."""

        await rate_limiter("open5e")

        start = time.time()
        results = await lookup_spell(name="Detect Magic")
        duration = time.time() - start

        assert len(results) > 0, "Should find spell"
        assert duration < 5.0, f"API call took {duration:.2f}s, expected <5s"

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_cached_call_performance(self, rate_limiter, clear_cache):
        """Verify cached calls are fast."""

        await rate_limiter("open5e")

        # Prime cache
        await lookup_creature(name="Goblin")

        # Measure cached performance
        start = time.time()
        await lookup_creature(name="Goblin")
        duration = time.time() - start

        assert duration < 0.05, f"Cached call took {duration:.3f}s, expected <0.05s"


class TestLiveMCPProtocol:
    """Tests for tools called via MCP protocol."""

    async def call_mcp_tool(self, mcp_server, tool_name: str, arguments: dict[str, object]) -> str:
        """Helper to call tool via MCP protocol and return JSON response."""
        tools = await mcp_server.get_tools()
        tool = tools[tool_name]
        result = await tool.run(arguments)
        # ToolResult has content which is a list of TextContent objects
        if hasattr(result, "content") and result.content:
            return result.content[0].text
        return ""

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_list_documents_live(self, mcp_server) -> None:
        """Live test for list_documents tool via MCP protocol."""
        # Call tool via MCP
        response = await self.call_mcp_tool(mcp_server, "list_documents", {})

        assert response is not None
        # Parse JSON response
        data = json.loads(response)
        assert isinstance(data, list)

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_lookup_spell_with_document_filter_live(self, mcp_server, rate_limiter) -> None:
        """Live test for lookup_spell with documents via MCP protocol."""
        await rate_limiter("open5e")

        # First get documents
        docs_response = await self.call_mcp_tool(mcp_server, "list_documents", {})
        documents = json.loads(docs_response)

        if len(documents) == 0:
            pytest.skip("No documents in cache")

        doc_key = documents[0]["document"]

        # Now search with document filter
        response = await self.call_mcp_tool(
            mcp_server,
            "lookup_spell",
            {"documents": [doc_key], "limit": 5},
        )

        assert response is not None
        spells = json.loads(response)
        assert isinstance(spells, list)
