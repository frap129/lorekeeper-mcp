"""Tool for listing available D&D content documents across all sources.

This module provides document discovery functionality that shows all documents
available in the cache across all sources (Open5e, D&D 5e API, OrcBrew).
"""

from typing import Any

from lorekeeper_mcp.cache.db import get_available_documents, get_document_metadata


async def list_documents(
    source: str | None = None,
) -> list[dict[str, Any]]:
    """
    List all available D&D content documents in the cache.

    This tool queries the cache to discover which source documents are available
    across all data sources (Open5e API, D&D 5e API, OrcBrew imports). Use this
    to see which books, supplements, and homebrew content you have access to,
    then use the document_keys parameter in other tools to filter content.

    IMPORTANT: This shows only documents currently in your cache. Run the build
    command to populate your cache with content from configured sources.

    Examples:
        # List all available documents
        docs = await list_documents()

        # List only Open5e documents
        docs = await list_documents(source="open5e_v2")

        # List only OrcBrew homebrew
        docs = await list_documents(source="orcbrew")

    Args:
        source: Optional source filter. Valid values:
            - "open5e_v2": Open5e API documents (SRD, Kobold Press, etc.)
            - "dnd5e_api": Official D&D 5e API (SRD only)
            - "orcbrew": Imported OrcBrew homebrew files
            - None (default): Show documents from all sources

    Returns:
        List of document dictionaries, each containing:
            - document: Document name/identifier (use this in document_keys)
            - source_api: Which API/source this came from
            - entity_count: Total number of entities from this document
            - entity_types: Breakdown of entities by type (spells, creatures, etc.)
            - publisher: Publisher name (if available, Open5e only)
            - license: License type (if available, Open5e only)

        Documents are sorted by entity count (highest first).

    Note:
        This queries only the cache and does not make API calls. You must
        populate your cache first using the build command.
    """
    # Get documents from cache
    documents = await get_available_documents(source_api=source)

    # Optionally enrich with metadata
    enriched_documents = []
    for doc in documents:
        enriched = dict(doc)

        # Try to get metadata for this document
        metadata = await get_document_metadata(doc["document"])
        if metadata:
            # Add useful metadata fields
            for field in ["publisher", "license", "description"]:
                if field in metadata:
                    enriched[field] = metadata[field]

        enriched_documents.append(enriched)

    return enriched_documents
