# Document Filtering in LoreKeeper

## Overview

LoreKeeper tracks the source document for every cached entity, enabling filtering by document across all tools and repositories. This allows AI assistants to answer questions like "show me SRD-only spells" or "only use content from this homebrew book".

## Document Names

Every entity includes a `document` field containing the document name:

### Open5e v2

Documents from Open5e include the document name from the API (e.g., "System Reference Document 5.1", "Adventurer's Guide", "Tome of Beasts").

### D&D 5e API

All content from the D&D 5e API is SRD content, normalized to **"System Reference Document 5.1"** (the same document name as Open5e's SRD).

### OrcBrew

The top-level book name from the .orcbrew file becomes the document (e.g., "Homebrew Grimoire", "Test Content Pack").

## Using Document Filters

### In Tools

All lookup tools accept a `document` parameter:

```python
# Filter spells from the SRD
spells = await lookup_spell(document="System Reference Document 5.1", level=3)

# Filter creatures from a specific book
creatures = await lookup_creature(document="Adventurer's Guide")

# Filter weapons from homebrew
weapons = await lookup_weapon(document="Homebrew Grimoire", category="martial")
```

### In Repositories

Repositories support document filtering through the search method:

```python
repository = RepositoryFactory.create_spell_repository()
spells = await repository.search(document="System Reference Document 5.1", level=3)
```

### In Cache Queries

Direct cache queries support document filtering:

```python
from lorekeeper_mcp.cache.db import query_cached_entities

spells = await query_cached_entities(
    "spells",
    document="System Reference Document 5.1",
    level=3
)
```

## SRD Content from Multiple APIs

Both Open5e and the D&D 5e API provide SRD content. LoreKeeper normalizes both to use the same document name: **"System Reference Document 5.1"**.

This means filtering by `document="System Reference Document 5.1"` returns SRD content from **both** APIs (whichever LoreKeeper has cached). Users don't need to know which API provided the data.

## Performance

Document filtering uses indexed database queries for optimal performance:
- `document` has a database index on all entity tables
- Filters are applied at the database level (no client-side filtering when cache hits)
- Combines efficiently with other indexed fields (level, type, etc.)

## Backward Compatibility

Document filtering is fully backward compatible:
- The `document` parameter is optional on all tools
- Existing tool calls work unchanged
- The `source_api` field remains for internal tracking but is not exposed as a user-facing filter
