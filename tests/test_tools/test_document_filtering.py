"""Integration tests for document filtering across all tools."""

import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import patch

import pytest

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.db import bulk_cache_entities
from lorekeeper_mcp.cache.schema import init_entity_cache
from lorekeeper_mcp.cache.sqlite import SQLiteCache
from lorekeeper_mcp.config import settings
from lorekeeper_mcp.repositories.monster import MonsterRepository
from lorekeeper_mcp.repositories.spell import SpellRepository
from lorekeeper_mcp.tools.creature_lookup import (
    _repository_context as creature_context,
)
from lorekeeper_mcp.tools.creature_lookup import (
    lookup_creature,
)
from lorekeeper_mcp.tools.list_documents import list_documents
from lorekeeper_mcp.tools.spell_lookup import (
    _repository_context as spell_context,
)
from lorekeeper_mcp.tools.spell_lookup import (
    lookup_spell,
)


@pytest.fixture
async def populated_cache() -> AsyncGenerator[str, None]:
    """Fixture providing a cache populated with various entities."""
    # Create a temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_populated.db")
        await init_entity_cache(db_path)

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
            },
        ]
        await bulk_cache_entities(spells, "spells", db_path=db_path, source_api="open5e_v2")

        # Add monsters from different documents
        monsters = [
            {
                "slug": "goblin",
                "name": "Goblin",
                "type": "humanoid",
                "size": "Small",
                "challenge_rating": 0.25,
                "document": "mm",
            },
            {
                "slug": "dragon",
                "name": "Dragon",
                "type": "dragon",
                "size": "Huge",
                "challenge_rating": 24,
                "document": "mm",
            },
        ]
        await bulk_cache_entities(monsters, "monsters", db_path=db_path, source_api="dnd5e_api")

        yield db_path


@pytest.mark.asyncio
async def test_list_documents_integration(populated_cache: str) -> None:
    """Test list_documents with real cache data."""
    # Patch the settings to use the test database
    with patch.object(settings, "db_path", populated_cache):
        documents = await list_documents()

        assert isinstance(documents, list)
        # Should have at least some documents in populated cache
        assert len(documents) >= 2

        # Verify structure
        for doc in documents:
            assert "document" in doc
            assert "source_api" in doc
            assert "entity_count" in doc

        # Verify expected documents
        doc_names = [d["document"] for d in documents]
        assert "srd-5e" in doc_names or "tce" in doc_names


@pytest.mark.asyncio
async def test_spell_lookup_with_document_filter_integration(
    populated_cache: str,
) -> None:
    """Test spell lookup with document filtering end-to-end."""
    # Setup repository with test database
    cache = SQLiteCache(db_path=populated_cache)
    repo = SpellRepository(client=Open5eV2Client(), cache=cache)
    spell_context["repository"] = repo

    try:
        # First, get spells without filter
        all_spells = await lookup_spell(limit=50)

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
        filtered_spells = await lookup_spell(document_keys=[doc_to_filter], limit=50)

        # All filtered results should match the document
        for spell in filtered_spells:
            if spell.get("document"):
                assert spell["document"] == doc_to_filter

    finally:
        spell_context.clear()


@pytest.mark.asyncio
async def test_cross_tool_document_consistency(populated_cache: str) -> None:
    """Test that document filtering works consistently across all tools."""
    # Patch settings
    with patch.object(settings, "db_path", populated_cache):
        # Get available documents
        documents = await list_documents()

        if len(documents) == 0:
            pytest.skip("No documents in cache")

        # Setup repositories
        cache = SQLiteCache(db_path=populated_cache)
        spell_repo = SpellRepository(client=Open5eV2Client(), cache=cache)
        creature_repo = MonsterRepository(client=Open5eV1Client(), cache=cache)

        spell_context["repository"] = spell_repo
        creature_context["repository"] = creature_repo

        try:
            # Test filtering with each document
            for doc in documents[:2]:  # Test first 2 documents
                doc_key: str = doc["document"]
                source_api: str = doc.get("source_api", "")

                # Try filtering with each tool
                spells = await lookup_spell(document_keys=[doc_key], limit=5)
                creatures = await lookup_creature(document_keys=[doc_key], limit=5)

                # Should complete without errors
                assert isinstance(spells, list)
                assert isinstance(creatures, list)

                # Verify filtering worked if results exist
                # Only check filtering for matching source APIs
                if source_api == "open5e_v2":
                    for spell in spells:
                        if spell.get("document"):
                            assert spell["document"] == doc_key

                if source_api == "dnd5e_api":
                    for creature in creatures:
                        if creature.get("document"):
                            assert creature["document"] == doc_key

        finally:
            spell_context.clear()
            creature_context.clear()


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
    cache = SQLiteCache(db_path=db_path)
    repo = SpellRepository(client=Open5eV2Client(), cache=cache)

    # Inject repository into tool context
    spell_context["repository"] = repo

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
        spell_context.clear()


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
    cache = SQLiteCache(db_path=db_path)
    repo = SpellRepository(client=Open5eV2Client(), cache=cache)
    spell_context["repository"] = repo

    try:
        results = await lookup_spell(name="Test Spell")

        assert len(results) == 1
        result = results[0]

        # Verify document field is present
        assert result["document"] == "Test Document"

    finally:
        spell_context.clear()
