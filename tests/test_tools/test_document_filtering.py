"""Integration tests for document filtering across the stack."""

import pytest

from lorekeeper_mcp.cache.db import bulk_cache_entities
from lorekeeper_mcp.cache.schema import init_entity_cache
from lorekeeper_mcp.tools.spell_lookup import lookup_spell


@pytest.mark.asyncio
async def test_end_to_end_document_filtering(tmp_path):
    """Test document filtering from tool through repository to cache."""
    # Setup test database
    db_path = str(tmp_path / "test.db")
    await init_entity_cache(db_path)

    # Populate cache with spells from different documents
    spells = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "level": 3,
            "school": "evocation",
            "casting_time": "1 action",
            "range": "150 feet",
            "duration": "Instantaneous",
            "document": "System Reference Document 5.1",
        },
        {
            "slug": "custom-blast",
            "name": "Custom Blast",
            "level": 3,
            "school": "evocation",
            "casting_time": "1 action",
            "range": "100 feet",
            "duration": "Instantaneous",
            "document": "Homebrew Grimoire",
        },
        {
            "slug": "advanced-spell",
            "name": "Advanced Spell",
            "level": 3,
            "casting_time": "1 bonus action",
            "range": "Self",
            "duration": "1 minute",
            "school": "transmutation",
            "document": "Adventurer's Guide",
        },
    ]

    await bulk_cache_entities(spells, "spells", db_path=db_path)

    # Create repository with test cache
    from lorekeeper_mcp.cache.sqlite import SQLiteCache

    cache = SQLiteCache(db_path=db_path)
    from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
    from lorekeeper_mcp.repositories.spell import SpellRepository

    repo = SpellRepository(client=Open5eV2Client(), cache=cache)

    # Inject repository into tool context
    from lorekeeper_mcp.tools.spell_lookup import _repository_context

    _repository_context["repository"] = repo

    try:
        # Test 1: Filter by SRD document
        srd_results = await lookup_spell(document="System Reference Document 5.1")
        assert len(srd_results) == 1
        assert srd_results[0]["slug"] == "fireball"

        # Test 2: Filter by homebrew document
        homebrew_results = await lookup_spell(document="Homebrew Grimoire")
        assert len(homebrew_results) == 1
        assert homebrew_results[0]["slug"] == "custom-blast"

        # Test 3: Combine document filter with other filters
        level3_srd = await lookup_spell(level=3, document="System Reference Document 5.1")
        assert len(level3_srd) == 1
        assert level3_srd[0]["slug"] == "fireball"

    finally:
        _repository_context.clear()


@pytest.mark.asyncio
async def test_document_in_tool_responses(tmp_path):
    """Test that tool responses include document name."""
    db_path = str(tmp_path / "test.db")
    await init_entity_cache(db_path)

    spell = {
        "slug": "test-spell",
        "name": "Test Spell",
        "level": 2,
        "school": "abjuration",
        "casting_time": "1 action",
        "range": "60 feet",
        "duration": "10 minutes",
        "document": "Test Document",
    }

    await bulk_cache_entities([spell], "spells", db_path=db_path)

    # Setup and query
    from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
    from lorekeeper_mcp.cache.sqlite import SQLiteCache
    from lorekeeper_mcp.repositories.spell import SpellRepository
    from lorekeeper_mcp.tools.spell_lookup import _repository_context, lookup_spell

    cache = SQLiteCache(db_path=db_path)
    repo = SpellRepository(client=Open5eV2Client(), cache=cache)
    _repository_context["repository"] = repo

    try:
        results = await lookup_spell(name="Test Spell")

        assert len(results) == 1
        result = results[0]

        # Verify document field is present
        assert result["document"] == "Test Document"

    finally:
        _repository_context.clear()
