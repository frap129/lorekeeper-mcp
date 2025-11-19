"""Search tool for unified D&D content search across multiple types.

This module provides a search tool that exposes the Open5e unified search
endpoint with fuzzy and semantic matching capabilities for cross-entity searches.

Architecture:
    - Uses Open5eV2Client.unified_search() for fuzzy and semantic search
    - Supports searching across multiple content types
    - Handles limit distribution when searching multiple types

Examples:
    Basic search:
        results = await search_dnd_content(query="fireball")

    Fuzzy search for typos:
        results = await search_dnd_content(query="firbal", enable_fuzzy=True)

    Semantic search for related content:
        results = await search_dnd_content(query="healing magic", enable_semantic=True)

    Filter by content type:
        spells = await search_dnd_content(query="fire", content_types=["Spell"])
"""

from typing import Any

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


def _get_open5e_client() -> Open5eV2Client:
    """Get Open5eV2Client instance.

    Returns:
        Open5eV2Client for unified search
    """
    return Open5eV2Client()


async def search_dnd_content(
    query: str,
    content_types: list[str] | None = None,
    documents: list[str] | None = None,
    enable_fuzzy: bool = True,
    enable_semantic: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search across all D&D content with advanced fuzzy and semantic matching.

    This tool uses Open5e's unified search endpoint to find content across
    multiple types (spells, creatures, items, etc.) with typo tolerance and
    conceptual matching. Perfect for exploratory searches like "find anything
    related to fire" or when you're not sure of exact spelling.

    Examples:
        # Cross-entity search
        search_dnd_content(query="dragon")  # Finds dragons, dragon spells, etc.

        # Typo-tolerant search
        search_dnd_content(query="firbal")  # Finds "Fireball" despite typo

        # Concept-based search
        search_dnd_content(query="healing magic")  # Finds healing spells

        # Type-filtered search
        search_dnd_content(query="fire", content_types=["Spell"])  # Only spells

        # Document-filtered search
        search_dnd_content(query="fireball", documents=["srd-5e"])
        search_dnd_content(query="spell", documents=["srd-5e", "tce"])

    Args:
        query: Search term (handles typos and concepts automatically)
        content_types: Limit to specific types: ["Spell", "Creature", "Item",
            "Background", "Feat"]. Default None searches all content types.
        documents: Filter results to specific documents. Provide list of
            document names from list_documents() tool. Post-filters search
            results by document field. Examples: ["srd-5e"], ["srd-5e", "tce"].
        enable_fuzzy: Enable fuzzy matching for typo tolerance (default True)
        enable_semantic: Enable semantic/vector search for conceptual
            matching (default True)
        limit: Maximum number of results to return (default 20)

    Returns:
        List of content dictionaries with varied structure based on content
        type. Each result includes a 'type' or 'model' field indicating
        content type.

    Raises:
        ApiError: If the API request fails due to network issues or errors
    """
    # Short-circuit for empty document list
    if documents is not None and len(documents) == 0:
        return []

    client = _get_open5e_client()

    if content_types:
        # Multiple searches, one per content type
        all_results: list[dict[str, Any]] = []
        per_type_limit = limit // len(content_types)

        for content_type in content_types:
            results = await client.unified_search(
                query=query,
                fuzzy=enable_fuzzy,
                vector=enable_semantic,
                object_model=content_type,
                limit=per_type_limit,
            )
            all_results.extend(results)

        # Post-filter by document if specified
        if documents:
            all_results = [
                r
                for r in all_results
                if r.get("document") in documents or r.get("document__slug") in documents
            ]

        return all_results[:limit]

    # Single unified search across all types
    results = await client.unified_search(
        query=query,
        fuzzy=enable_fuzzy,
        vector=enable_semantic,
        limit=limit,
    )

    # Post-filter by document if specified
    if documents:
        results = [
            r
            for r in results
            if r.get("document") in documents or r.get("document__slug") in documents
        ]

    return results[:limit]
