"""Tests for search_dnd_content tool."""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.tools.search_dnd_content import search_dnd_content


@pytest.fixture
def mock_open5e_v2_client_for_search():
    """Mock Open5eV2Client for unified search testing."""
    client = MagicMock()
    client.unified_search = AsyncMock()
    return client


@pytest.fixture
def mock_client_factory(mock_open5e_v2_client_for_search, monkeypatch):
    """Mock the client factory to return mock client."""

    def mock_factory():
        return mock_open5e_v2_client_for_search

    # Get the actual module, not the function from __init__.py
    search_module = sys.modules.get("lorekeeper_mcp.tools.search_dnd_content")
    if search_module is None:
        search_module = sys.modules["lorekeeper_mcp.tools.search_dnd_content"]

    # Patch the module-level function
    monkeypatch.setattr(search_module, "_get_open5e_client", mock_factory)
    return mock_open5e_v2_client_for_search

    # Patch at module level using string path
    monkeypatch.setattr("lorekeeper_mcp.tools.search_dnd_content._get_open5e_client", mock_factory)
    return mock_open5e_v2_client_for_search


@pytest.mark.asyncio
async def test_search_dnd_content_tool(mock_client_factory):
    """Test search_dnd_content tool basic functionality."""

    # Mock search results
    mock_results = [
        {
            "object_name": "Fireball",
            "object_model": "Spell",
            "match_type": "exact",
            "match_score": 1.0,
        }
    ]
    mock_client_factory.unified_search.return_value = mock_results

    result = await search_dnd_content(query="fireball")

    assert len(result) == 1
    assert result[0]["object_name"] == "Fireball"
    assert result[0]["object_model"] == "Spell"
    mock_client_factory.unified_search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_dnd_content_with_fuzzy(mock_client_factory):
    """Test search_dnd_content tool with fuzzy matching enabled."""

    mock_results = [
        {
            "object_name": "Fireball",
            "object_model": "Spell",
            "match_type": "fuzzy",
            "match_score": 0.95,
        }
    ]
    mock_client_factory.unified_search.return_value = mock_results

    result = await search_dnd_content(query="firbal", enable_fuzzy=True)

    assert len(result) == 1
    call_kwargs = mock_client_factory.unified_search.call_args[1]
    assert call_kwargs["fuzzy"] is True


@pytest.mark.asyncio
async def test_search_dnd_content_with_semantic(mock_client_factory):
    """Test search_dnd_content tool with semantic search enabled."""

    mock_results = [
        {
            "object_name": "Cure Wounds",
            "object_model": "Spell",
            "match_type": "vector",
            "match_score": 0.85,
        }
    ]
    mock_client_factory.unified_search.return_value = mock_results

    result = await search_dnd_content(query="healing magic", enable_semantic=True)

    assert len(result) == 1
    call_kwargs = mock_client_factory.unified_search.call_args[1]
    assert call_kwargs["vector"] is True


@pytest.mark.asyncio
async def test_cross_entity_search(mock_client_factory):
    """Test searching across multiple content types."""

    # Mock results with different entity types
    mock_results = [
        {
            "object_name": "Red Dragon",
            "object_model": "Creature",
            "match_score": 1.0,
        },
        {
            "object_name": "Tiamat",
            "object_model": "Creature",
            "match_score": 0.95,
        },
        {
            "object_name": "Dragon Scales",
            "object_model": "Item",
            "match_score": 0.9,
        },
    ]
    mock_client_factory.unified_search.return_value = mock_results

    result = await search_dnd_content(query="dragon")

    assert len(result) == 3
    # Verify we got different entity types
    object_models = {r["object_model"] for r in result}
    assert "Creature" in object_models
    assert "Item" in object_models


@pytest.mark.asyncio
async def test_content_type_filtering(mock_client_factory):
    """Test filtering results by content type."""

    # First call for "Spell"
    spell_results = [
        {
            "object_name": "Fireball",
            "object_model": "Spell",
            "match_score": 1.0,
        }
    ]

    # Second call for "Creature"
    creature_results = [
        {
            "object_name": "Fire Elemental",
            "object_model": "Creature",
            "match_score": 0.9,
        }
    ]

    # Setup side effect to return different results for each call
    mock_client_factory.unified_search.side_effect = [
        spell_results,
        creature_results,
    ]

    result = await search_dnd_content(query="fire", content_types=["Spell", "Creature"])

    # Should have results from both searches
    assert len(result) == 2
    object_models = [r["object_model"] for r in result]
    assert "Spell" in object_models
    assert "Creature" in object_models

    # Verify unified_search was called twice, once per content type
    assert mock_client_factory.unified_search.await_count == 2


@pytest.mark.asyncio
async def test_content_type_filtering_respects_limit(mock_client_factory):
    """Test that limit is distributed across content types."""

    spell_results = [
        {
            "object_name": "Fireball",
            "object_model": "Spell",
            "match_score": 1.0,
        },
        {
            "object_name": "Fire Shield",
            "object_model": "Spell",
            "match_score": 0.95,
        },
    ]

    creature_results = [
        {
            "object_name": "Fire Elemental",
            "object_model": "Creature",
            "match_score": 0.9,
        }
    ]

    mock_client_factory.unified_search.side_effect = [
        spell_results,
        creature_results,
    ]

    await search_dnd_content(query="fire", content_types=["Spell", "Creature"], limit=10)

    # With limit=10 and 2 content types, each gets 5
    # Verify the distribution in the calls
    calls = mock_client_factory.unified_search.call_args_list
    assert len(calls) == 2
    # Each call should have limit=5 (10 / 2)
    assert calls[0][1]["limit"] == 5
    assert calls[1][1]["limit"] == 5


@pytest.mark.asyncio
async def test_search_with_limit(mock_client_factory):
    """Test search with custom limit parameter."""

    mock_results = [
        {"object_name": "Spell1", "object_model": "Spell"},
        {"object_name": "Spell2", "object_model": "Spell"},
        {"object_name": "Spell3", "object_model": "Spell"},
    ]
    mock_client_factory.unified_search.return_value = mock_results

    result = await search_dnd_content(query="spell", limit=3)

    call_kwargs = mock_client_factory.unified_search.call_args[1]
    assert call_kwargs["limit"] == 3
    assert len(result) <= 3


@pytest.mark.asyncio
async def test_search_combines_results_within_limit(mock_client_factory):
    """Test that combined results respect the overall limit."""

    spell_results = [{"object_name": f"Spell{i}", "object_model": "Spell"} for i in range(6)]

    creature_results = [
        {"object_name": f"Creature{i}", "object_model": "Creature"} for i in range(6)
    ]

    mock_client_factory.unified_search.side_effect = [
        spell_results,
        creature_results,
    ]

    result = await search_dnd_content(query="test", content_types=["Spell", "Creature"], limit=10)

    # Should not exceed limit even if searches return more results
    assert len(result) <= 10


@pytest.mark.asyncio
async def test_search_dnd_content_with_document_keys(mock_client_factory):
    """Test search_dnd_content with document_keys post-filtering."""
    # Mock search results with different documents
    mock_results = [
        {
            "object_name": "Fireball",
            "object_model": "Spell",
            "document": "srd-5e",
            "document__slug": "srd-5e",
        },
        {
            "object_name": "Fire Bolt",
            "object_model": "Spell",
            "document": "tce",
            "document__slug": "tce",
        },
        {
            "object_name": "Meteor Storm",
            "object_model": "Spell",
            "document": "srd-5e",
            "document__slug": "srd-5e",
        },
    ]
    mock_client_factory.unified_search.return_value = mock_results

    # Filter to only srd-5e
    result = await search_dnd_content(query="fire", document_keys=["srd-5e"], limit=10)

    # Should only have results from srd-5e document
    assert len(result) == 2
    for item in result:
        assert item.get("document") in ["srd-5e"]


@pytest.mark.asyncio
async def test_search_dnd_content_empty_document_keys(mock_client_factory):
    """Test search_dnd_content short-circuits on empty document_keys list."""
    # Should return empty list without calling unified_search
    result = await search_dnd_content(query="fire", document_keys=[], limit=10)

    assert result == []
    # Should not have called the API
    mock_client_factory.unified_search.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_dnd_content_document_keys_with_content_types(mock_client_factory):
    """Test document_keys post-filtering with content_types specified."""
    # First call for "Spell"
    spell_results = [
        {
            "object_name": "Fireball",
            "object_model": "Spell",
            "document": "srd-5e",
        },
        {
            "object_name": "Fire Bolt",
            "object_model": "Spell",
            "document": "tce",
        },
    ]

    # Second call for "Creature"
    creature_results = [
        {
            "object_name": "Fire Elemental",
            "object_model": "Creature",
            "document": "srd-5e",
        }
    ]

    mock_client_factory.unified_search.side_effect = [
        spell_results,
        creature_results,
    ]

    result = await search_dnd_content(
        query="fire", content_types=["Spell", "Creature"], document_keys=["srd-5e"], limit=10
    )

    # Should only have results from srd-5e
    assert len(result) == 2
    for item in result:
        assert item.get("document") == "srd-5e"
