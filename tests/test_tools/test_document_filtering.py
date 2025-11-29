"""Integration tests for document filtering across all tools."""

import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import patch

import pytest

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.milvus import MilvusCache
from lorekeeper_mcp.repositories.creature import CreatureRepository
from lorekeeper_mcp.repositories.spell import SpellRepository
from lorekeeper_mcp.tools.list_documents import list_documents
from lorekeeper_mcp.tools.search_creature import (
    _repository_context as creature_context,
)
from lorekeeper_mcp.tools.search_creature import (
    search_creature,
)
from lorekeeper_mcp.tools.search_spell import (
    _repository_context as spell_context,
)
from lorekeeper_mcp.tools.search_spell import (
    search_spell,
)


@pytest.fixture
async def populated_cache() -> AsyncGenerator[MilvusCache, None]:
    """Fixture providing a cache populated with various entities."""
    # Create a temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_populated.db")
        cache = MilvusCache(db_path)

        # Add spells from different documents
        spells = [
            {
                "slug": "fireball",
                "name": "Fireball",
                "level": 3,
                "school": "evocation",
                "casting_time": "1 action",
                "range": "150 feet",
                "duration": "Instantaneous",
                "components": "V,S,M",
                "material": "a tiny ball of bat guano and sulfur",
                "document": "srd-5e",
                "source_api": "open5e_v2",
            },
            {
                "slug": "magic-missile",
                "name": "Magic Missile",
                "level": 1,
                "school": "evocation",
                "casting_time": "1 action",
                "range": "120 feet",
                "duration": "Instantaneous",
                "components": "V,S",
                "document": "srd-5e",
                "source_api": "open5e_v2",
            },
            {
                "slug": "tasha-spell",
                "name": "Tasha Spell",
                "level": 2,
                "school": "transmutation",
                "casting_time": "1 bonus action",
                "range": "Self",
                "duration": "1 minute",
                "components": "V",
                "document": "tce",
                "source_api": "open5e_v2",
            },
        ]
        await cache.store_entities(spells, "spells")

        # Add creatures from different documents
        creatures = [
            {
                "slug": "goblin",
                "name": "Goblin",
                "type": "humanoid",
                "size": "Small",
                "challenge_rating": "0.25",
                "alignment": "neutral evil",
                "armor_class": 15,
                "hit_points": 7,
                "hit_dice": "2d6",
                "document": "mm",
                "source_api": "open5e_v2",
            },
            {
                "slug": "dragon",
                "name": "Dragon",
                "type": "dragon",
                "size": "Huge",
                "challenge_rating": "24",
                "alignment": "chaotic evil",
                "armor_class": 22,
                "hit_points": 546,
                "hit_dice": "28d20+252",
                "document": "mm",
                "source_api": "open5e_v2",
            },
        ]
        await cache.store_entities(creatures, "creatures")

        yield cache

        cache.close()


@pytest.mark.asyncio
async def test_list_documents_integration(populated_cache: MilvusCache) -> None:
    """Test list_documents with real cache data."""
    # Patch the MilvusCache constructor to return our test cache
    with patch(
        "lorekeeper_mcp.tools.list_documents.MilvusCache",
        return_value=populated_cache,
    ):
        documents = await list_documents()

        assert isinstance(documents, list)
        # Should have at least some documents in populated cache
        assert len(documents) >= 2

        # Verify structure
        for doc in documents:
            assert "document" in doc
            assert "entity_count" in doc

        # Verify expected documents
        doc_names = [d["document"] for d in documents]
        assert "srd-5e" in doc_names or "tce" in doc_names


@pytest.mark.asyncio
async def test_spell_search_with_document_filter_integration(
    populated_cache: MilvusCache,
) -> None:
    """Test spell search with document filtering end-to-end."""
    # Setup repository with test cache
    repo = SpellRepository(client=Open5eV2Client(), cache=populated_cache)
    spell_context["repository"] = repo

    try:
        # First, get spells without filter
        all_spells = await search_spell(limit=50)

        if len(all_spells) == 0:
            pytest.skip("No spells in cache")

        # Get unique documents - properly typed
        documents_set: set[str] = set()
        for spell in all_spells:
            doc = spell.get("document")
            if isinstance(doc, str):
                documents_set.add(doc)

        if len(documents_set) == 0:
            pytest.skip("No documents in spell data")

        # Filter by first document
        doc_to_filter = next(iter(documents_set))
        filtered_spells = await search_spell(documents=[doc_to_filter], limit=50)

        # All filtered results should match the document
        for spell in filtered_spells:
            if spell.get("document"):
                assert spell["document"] == doc_to_filter

    finally:
        spell_context.clear()


@pytest.mark.asyncio
async def test_cross_tool_document_consistency(populated_cache: MilvusCache) -> None:
    """Test that document filtering works consistently across all tools.

    This test verifies that when filtering by a document that has cached entities
    of a specific type, the results correctly match that document. It only tests
    filtering for entity types that actually exist in each document to avoid
    triggering API fallback on cache miss.
    """
    # Patch to return our test cache for list_documents
    with patch(
        "lorekeeper_mcp.tools.list_documents.MilvusCache",
        return_value=populated_cache,
    ):
        # Get available documents
        documents = await list_documents()

        if len(documents) == 0:
            pytest.skip("No documents in cache")

        # Setup repositories
        spell_repo = SpellRepository(client=Open5eV2Client(), cache=populated_cache)
        creature_repo = CreatureRepository(client=Open5eV1Client(), cache=populated_cache)

        spell_context["repository"] = spell_repo
        creature_context["repository"] = creature_repo

        try:
            # Test filtering with each document
            for doc in documents[:2]:  # Test first 2 documents
                doc_key: str = doc["document"]
                entity_types: dict[str, int] = doc.get("entity_types", {})

                # Only test spells if this document has spells in cache
                # Otherwise cache-aside pattern would fetch from API
                if entity_types.get("spells", 0) > 0:
                    spells = await search_spell(documents=[doc_key], limit=5)
                    assert isinstance(spells, list)
                    # Verify all returned spells match the document filter
                    for spell in spells:
                        if spell.get("document"):
                            assert spell["document"] == doc_key

                # Only test creatures if this document has them in cache
                if entity_types.get("creatures", 0) > 0:
                    creatures = await search_creature(documents=[doc_key], limit=5)
                    assert isinstance(creatures, list)
                    # Verify all returned creatures match the document filter
                    for creature in creatures:
                        if creature.get("document"):
                            assert creature["document"] == doc_key

        finally:
            spell_context.clear()
            creature_context.clear()


@pytest.mark.asyncio
async def test_end_to_end_document_filtering(tmp_path: Path) -> None:
    """Test document filtering from tool through repository to cache."""
    # Setup test database
    db_path = str(tmp_path / "test.db")
    cache = MilvusCache(db_path)

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
            "source_api": "open5e_v2",
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
            "source_api": "open5e_v2",
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
            "source_api": "open5e_v2",
        },
    ]

    await cache.store_entities(spells, "spells")

    # Create repository with test cache
    repo = SpellRepository(client=Open5eV2Client(), cache=cache)

    # Inject repository into tool context
    spell_context["repository"] = repo

    try:
        # Test 1: Filter by SRD document
        srd_results = await search_spell(documents=["System Reference Document 5.1"])
        assert len(srd_results) == 1
        assert srd_results[0]["slug"] == "fireball"

        # Test 2: Filter by homebrew document
        homebrew_results = await search_spell(documents=["Homebrew Grimoire"])
        assert len(homebrew_results) == 1
        assert homebrew_results[0]["slug"] == "custom-blast"

        # Test 3: Combine document filter with other filters
        level3_srd = await search_spell(level=3, documents=["System Reference Document 5.1"])
        assert len(level3_srd) == 1
        assert level3_srd[0]["slug"] == "fireball"

    finally:
        spell_context.clear()
        cache.close()


@pytest.mark.asyncio
async def test_document_in_tool_responses(tmp_path: Path) -> None:
    """Test that tool responses include document name."""
    db_path = str(tmp_path / "test.db")
    cache = MilvusCache(db_path)

    spell = {
        "slug": "test-spell",
        "name": "Test Spell",
        "level": 2,
        "school": "abjuration",
        "casting_time": "1 action",
        "range": "60 feet",
        "duration": "10 minutes",
        "document": "Test Document",
        "source_api": "open5e_v2",
    }

    await cache.store_entities([spell], "spells")

    # Setup and query
    repo = SpellRepository(client=Open5eV2Client(), cache=cache)
    spell_context["repository"] = repo

    try:
        results = await search_spell(search="Test Spell")

        assert len(results) == 1
        result = results[0]

        # Verify document field is present
        assert result["document"] == "Test Document"

    finally:
        spell_context.clear()
        cache.close()
