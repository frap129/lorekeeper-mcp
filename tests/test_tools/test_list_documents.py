"""Tests for list_documents tool."""

import sys
from typing import Any

import pytest

from lorekeeper_mcp.tools.list_documents import list_documents


@pytest.mark.asyncio
async def test_list_documents() -> None:
    """Test list_documents returns document list."""
    # Get the module from sys.modules to avoid shadowing
    list_docs_module = sys.modules["lorekeeper_mcp.tools.list_documents"]

    original_get_docs = list_docs_module.get_available_documents
    original_get_metadata = list_docs_module.get_document_metadata

    async def mock_get_docs(**kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "document": "srd-5e",
                "source_api": "open5e_v2",
                "entity_count": 100,
                "entity_types": {"spells": 50, "creatures": 50},
            }
        ]

    async def mock_get_metadata(doc_key: str) -> dict[str, Any] | None:
        return None

    list_docs_module.get_available_documents = mock_get_docs
    list_docs_module.get_document_metadata = mock_get_metadata

    try:
        result = await list_documents()
        assert isinstance(result, list)
        assert len(result) > 0
        assert "document" in result[0]
    finally:
        list_docs_module.get_available_documents = original_get_docs
        list_docs_module.get_document_metadata = original_get_metadata


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
