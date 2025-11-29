"""Tests for list_documents tool."""

from unittest.mock import AsyncMock, patch

import pytest

from lorekeeper_mcp.tools.list_documents import list_documents


@pytest.mark.asyncio
async def test_list_documents() -> None:
    """Test list_documents returns document list."""
    # Mock the MilvusCache to return test data
    mock_cache = AsyncMock()
    mock_cache.get_available_documents = AsyncMock(return_value=["srd-5e"])
    mock_cache.get_document_metadata = AsyncMock(return_value={"spells": 50, "creatures": 50})

    with patch("lorekeeper_mcp.tools.list_documents.MilvusCache", return_value=mock_cache):
        result = await list_documents()
        assert isinstance(result, list)
        assert len(result) > 0
        assert "document" in result[0]
        assert result[0]["document"] == "srd-5e"
        assert result[0]["entity_count"] == 100
        assert result[0]["entity_types"] == {"spells": 50, "creatures": 50}


@pytest.mark.asyncio
async def test_list_documents_source_filter() -> None:
    """Test list_documents with source filter."""
    result = await list_documents(source="open5e_v2")

    assert isinstance(result, list)
    # All results should be from open5e_v2 or none if cache is empty
    for doc in result:
        if doc.get("source_api"):
            assert doc["source_api"] == "open5e_v2"


def test_list_documents_docstring_references() -> None:
    """Test that docstring references documents parameter, not document_keys."""
    docstring = list_documents.__doc__
    assert docstring is not None

    # Should reference "documents" parameter
    assert "documents parameter" in docstring
    # Should reference "use this in documents"
    assert "use this in documents" in docstring

    # Should NOT reference "document_keys"
    assert "document_keys" not in docstring
