"""Tool for listing available D&D content documents across all sources.

This module provides document discovery functionality that shows all documents
available in the cache across all sources (Open5e, OrcBrew).
"""

from typing import Any

from lorekeeper_mcp.cache.milvus import MilvusCache
from lorekeeper_mcp.config import settings


async def list_documents(
    source: str | None = None,
) -> list[dict[str, Any]]:
    """
    List all available D&D content documents in the cache.

    This tool queries the cache to discover which source documents are available
    across all data sources (Open5e API, D&D 5e API, OrcBrew imports). Use this
    to see which books, supplements, and homebrew content you have access to,
    then use the documents parameter in other tools to filter content.

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
            - "orcbrew": Imported OrcBrew homebrew files
            - None (default): Show documents from all sources

    Returns:
        List of document dictionaries, each containing:
            - document: Document name/identifier (use this in documents)
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
    # Get cache instance - MilvusCache is the only supported backend
    cache = MilvusCache(str(settings.milvus_db_path))

    # Get list of available documents from cache
    document_keys = await cache.get_available_documents()

    # Build result with metadata for each document
    enriched_documents: list[dict[str, Any]] = []
    for doc_key in document_keys:
        # Get entity counts per type for this document
        metadata = await cache.get_document_metadata(doc_key)

        # Calculate total entity count
        total_count = sum(metadata.values())

        enriched: dict[str, Any] = {
            "document": doc_key,
            "entity_count": total_count,
            "entity_types": metadata,
        }

        enriched_documents.append(enriched)

    # Sort by entity count (highest first)
    enriched_documents.sort(key=lambda x: x["entity_count"], reverse=True)

    return enriched_documents
