# Document Filtering in LoreKeeper

## Overview

LoreKeeper tracks the source document for every cached entity, enabling filtering by document across all tools and repositories. This allows AI assistants to answer questions like "show me SRD-only spells" or "only use content from this homebrew book".

Every entity in LoreKeeper includes a `document` field containing the source document name, enabling precise control over which sources you query.

## Getting Started

### 1. Discover Available Documents

Use `list_documents()` to see what's available in your cache:

```python
# List all available documents across all sources
documents = await list_documents()

# Each document contains:
# - document: The document name/identifier (use in documents)
# - source_api: Where it came from (open5e_v2, orcbrew)
# - entity_count: Number of entities from this document
# - entity_types: Breakdown by type (spells, creatures, etc.)
# - publisher: Publisher name (Open5e only)
# - license: License type (Open5e only)
```

### 2. Use in Lookup Tools

All lookup tools accept `documents` parameter:

```python
# Single document filter
srd_spells = await lookup_spell(level=3, documents=["srd-5e"])

# Multiple documents
creatures = await lookup_creature(
    type="dragon",
    documents=["srd-5e", "tce", "phb"]
)
```

### 3. Use in Search Tool

The search tool also supports document filtering:

```python
# Search within specific documents
results = await search_dnd_content(
    query="fireball",
    documents=["srd-5e"]
)
```

## Document Names

Every entity includes a `document` field containing the document name:

### Open5e Documents

Documents from Open5e v1 and v2 APIs include the document name from the API metadata. Examples include:

- `"System Reference Document 5.1"` - Core SRD
- `"Adventurer's Guide"` - Adventurer's League
- `"Tome of Beasts"` - Kobold Press content
- `"Midgard Heroes Handbook"` - Midgard campaign setting



### OrcBrew Documents

When importing OrcBrew files, the top-level book name from the `.orcbrew` file becomes the document identifier. Examples:

- `"Homebrew Grimoire"` - Custom homebrew content
- `"My Campaign Setting"` - Campaign-specific content
- `"Community Compendium"` - Crowdsourced content

## Practical Usage Examples

### Query SRD-Only Content

Get only free, System Reference Document content (no purchased supplements):

```python
# All SRD spells
srd_spells = await lookup_spell(documents=["srd-5e"])

# SRD creatures up to CR 5
srd_creatures = await lookup_creature(
    cr_max=5,
    documents=["srd-5e"]
)

# All SRD equipment
srd_equipment = await lookup_equipment(
    documents=["srd-5e"]
)

# SRD character options
srd_classes = await lookup_character_option(
    type="class",
    documents=["srd-5e"]
)

# SRD rules and conditions
grappled = await lookup_rule(
    rule_type="condition",
    name="grappled",
    documents=["srd-5e"]
)
```

### Filter by Specific Book

Query a single published supplement:

```python
# Only Tasha's Cauldron of Everything
tasha_spells = await lookup_spell(documents=["tce"])

# Only Xanathar's Guide to Everything
xgte_creatures = await lookup_creature(documents=["xgte"])

# Only Player's Handbook classes
phb_classes = await lookup_character_option(
    type="class",
    documents=["phb"]
)
```

### Multi-Source Queries

Combine multiple documents in a single query:

```python
# Get spells from SRD and Tasha's
core_and_tasha = await lookup_spell(
    documents=["srd-5e", "tce"]
)

# Get creatures from multiple books
multi_source_creatures = await lookup_creature(
    cr_min=5,
    cr_max=10,
    documents=["srd-5e", "mm", "vrgr", "moot"]
)

# Search across multiple supplements
comprehensive_search = await search_dnd_content(
    query="magic item",
    documents=["srd-5e", "phb", "tce", "xgte", "dmg"]
)
```

### Complex Filtering

Combine document filters with other parameters:

```python
# Evocation spells from SRD and Tasha's
targeted_spells = await lookup_spell(
    school="evocation",
    level_min=3,
    level_max=5,
    damage_type="fire",
    documents=["srd-5e", "tce"]
)

# Ritual spells available to clerics
cleric_rituals = await lookup_spell(
    class_key="cleric",
    ritual=True,
    documents=["srd-5e"]
)

# Rare magic items from published books
rare_items = await lookup_equipment(
    type="magic-item",
    rarity="rare",
    documents=["srd-5e", "phb", "dmg", "tce"]
)
```

### Homebrew Filtering

Isolate imported homebrew content from official sources:

```python
# List all homebrew documents
homebrew_docs = await list_documents(source="orcbrew")

# Extract document names
homebrew_keys = [doc["document"] for doc in homebrew_docs]

# Query only homebrew
homebrew_creatures = await lookup_creature(
    documents=homebrew_keys
)

# Or work with a single homebrew document
custom_book = "My Custom Campaign"
custom_creatures = await lookup_creature(
    documents=[custom_book]
)
```

### Source-Specific Queries

Query by source API directly:

```python
# Get only Open5e v2 content (includes community content)
open5e_docs = await list_documents(source="open5e_v2")
open5e_keys = [doc["document"] for doc in open5e_docs]
open5e_spells = await lookup_spell(documents=open5e_keys)

# Get all available Open5e content
open5e_all = await list_documents(source="open5e_v2")
```

## Integration Patterns

### AI Assistant Discovery Workflow

When an AI assistant needs to know available options:

```python
# 1. Show user what documents are available
available = await list_documents()
print(f"Available sources: {[d['document'] for d in available]}")

# 2. Suggest appropriate filters
print("SRD-only: use documents=['srd-5e']")
print(f"Published books: use documents={[d for d in available if 'homebrew' not in d.lower()]}")

# 3. Execute filtered query
srd_results = await lookup_spell(documents=["srd-5e"])
```

### Respecting Licensing

When ensuring only licensed content is used:

```python
# Get non-SRD documents
all_docs = await list_documents()
srd_docs = [d for d in all_docs if "srd" in d["document"].lower()]
non_srd_docs = [d for d in all_docs if d not in srd_docs]

# Query only SRD
licensed_only = await lookup_spell(
    documents=[d["document"] for d in srd_docs]
)
```

### Campaign-Specific Content

When running a campaign with specific content restrictions:

```python
# Campaign allows: SRD + Player's Handbook + Tasha's
campaign_sources = ["srd-5e", "phb", "tce"]

# All character options for the campaign
campaign_classes = await lookup_character_option(
    type="class",
    documents=campaign_sources
)

# Campaign-legal spells
campaign_spells = await lookup_spell(
    documents=campaign_sources
)

# All equipment available in campaign
campaign_equipment = await lookup_equipment(
    documents=campaign_sources
)
```

## Document Names

Every entity includes a `document` field containing the document name:

### Open5e v2

Documents from Open5e include the document name from the API (e.g., "System Reference Document 5.1", "Adventurer's Guide", "Tome of Beasts").



### OrcBrew

The top-level book name from the .orcbrew file becomes the document (e.g., "Homebrew Grimoire", "Test Content Pack").

## Using Document Filters

### In Tools

All lookup tools accept a `documents` parameter:

```python
# Filter spells from the SRD
spells = await lookup_spell(documents=["srd-5e"], level=3)

# Filter creatures from a specific book
creatures = await lookup_creature(documents=["Adventurer's Guide"])

# Filter equipment from multiple sources
weapons = await lookup_equipment(
    documents=["srd-5e", "phb"],
    type="weapon"
)
```

### In Search Tool

The search tool also filters by document:

```python
# Search within SRD only
results = await search_dnd_content(
    query="fireball",
    documents=["srd-5e"]
)

# Search across multiple books
comprehensive = await search_dnd_content(
    query="dragon",
    documents=["srd-5e", "mm", "vrgr"]
)
```

### In Repositories (Advanced)

For direct repository access, use the search method:

```python
from lorekeeper_mcp.repositories.factory import RepositoryFactory

repository = RepositoryFactory.create_spell_repository()
spells = await repository.search(
    document=["srd-5e"],
    level=3
)
```

### In Cache Queries (Advanced)

For direct cache queries:

```python
from lorekeeper_mcp.cache.db import query_cached_entities

spells = await query_cached_entities(
    "spells",
    document=["srd-5e"],
    level=3
)
```

## SRD Content from Multiple APIs

Both Open5e and the D&D 5e API provide SRD content. LoreKeeper normalizes both to use the same document name: **"System Reference Document 5.1"**.

This means filtering by `documents=["srd-5e"]` returns SRD content from **both** APIs (whichever LoreKeeper has cached). Users don't need to know which API provided the data—it's transparent.

### Why This Matters

- **Consistency**: Same filter returns SRD content regardless of which API cached it
- **Transparency**: Users don't need to understand API internals
- **Flexibility**: If one API is slow, users get results from the other
- **Completeness**: Filtering by SRD ensures all free content is searched

## Performance Characteristics

### Indexed Queries

Document filtering uses indexed database queries for optimal performance:
- The `document` field has a database index on all entity tables
- Filters are applied at the database level (no client-side filtering)
- Combines efficiently with other indexed fields (level, type, cr, etc.)

### Query Performance

```python
# Fast - indexed field
fast = await lookup_spell(documents=["srd-5e"])

# Still fast - combined indexed filters
indexed = await lookup_spell(
    level=3,
    school="evocation",
    documents=["srd-5e"]
)

# Efficient - text search is slower but works
slow = await search_dnd_content(
    query="fireball",
    documents=["srd-5e"]
)
```

## Backward Compatibility

Document filtering is fully backward compatible:
- The `documents` parameter is optional on all tools
- Existing tool calls work unchanged
- Omitting the parameter queries all available documents
- The `document` field remains for internal tracking

## Troubleshooting

### No Results from Filter

If a document filter returns no results:

```python
# 1. Check if the document exists
docs = await list_documents()
available_docs = [d["document"] for d in docs]
print(f"Available: {available_docs}")

# 2. Verify exact spelling and case
# Document names are case-sensitive
print(f"Looking for: ['srd-5e']")

# 3. Check how many entities are in that document
for doc in docs:
    if "srd" in doc["document"].lower():
        print(f"{doc['document']}: {doc['entity_count']} entities")
```

### Unexpected Results

If you get results from unexpected documents:

```python
# Always check the returned document field
results = await lookup_spell(level=3)
documents_in_results = set(r["document"] for r in results)
print(f"Results came from: {documents_in_results}")

# Use strict filtering to verify
filtered = await lookup_spell(
    level=3,
    documents=["srd-5e"]
)
# All results should have document="srd-5e"
```
