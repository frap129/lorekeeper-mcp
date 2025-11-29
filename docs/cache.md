# Database Cache Documentation

This document provides detailed information about LoreKeeper MCP's caching system using **Milvus Lite** with semantic/vector search capabilities.

## Table of Contents

- [Overview](#overview)
- [Milvus Lite Backend](#milvus-lite-backend)
- [Semantic Search](#semantic-search)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Overview

The cache layer provides persistent storage for D&D entity data with semantic search capabilities, reducing external API calls and improving response times.

### Key Features

- **Entity-Based Storage**: Separate collections for spells, creatures, equipment, etc.
- **Semantic Search**: Natural language queries find related content
- **Hybrid Search**: Combine semantic search with structured filters (level, school, CR, etc.)
- **Infinite TTL**: Valid entity data never expires; only explicitly updated
- **Indexed Filtering**: Fast queries on type-specific fields
- **Source Tracking**: Records which API provided cached data
- **Zero Configuration**: Works out of the box with sensible defaults

### Cache Strategy

The system uses a **cache-aside pattern** with semantic search:

1. **Entity Cache First**: Check entity-based cache for D&D content
2. **Entity Hit**: Return cached entity data (no expiration)
3. **Entity Miss**: Fetch from API, generate embeddings, cache, return data
4. **Offline Fallback**: Serve cached entities when API is unavailable

## Milvus Lite Backend

Milvus Lite is an embedded vector database that runs in-process. It stores both entity data and embedding vectors for semantic search.

### How It Works

1. **Entity Storage**: When entities are cached, searchable text is extracted
2. **Embedding Generation**: Text is converted to 384-dimensional vectors using `all-MiniLM-L6-v2`
3. **Vector Index**: Embeddings are indexed for fast similarity search
4. **Hybrid Queries**: Semantic search can be combined with scalar filters

### Collection Schema

Each entity type has its own Milvus collection with the following structure:

**Base Fields (all collections):**
| Field | Type | Description |
|-------|------|-------------|
| `slug` | VARCHAR(256) | Primary key, unique identifier |
| `name` | VARCHAR(256) | Entity display name |
| `embedding` | FLOAT_VECTOR(384) | Semantic embedding vector |
| `source_api` | VARCHAR(64) | Source API (open5e, orcbrew) |
| `document` | VARCHAR(128) | Source document/book |

**Type-Specific Indexed Fields:**

| Collection | Indexed Fields |
|------------|----------------|
| `spells` | `level` (INT64), `school` (VARCHAR), `concentration` (BOOL), `ritual` (BOOL) |
| `creatures` | `challenge_rating` (VARCHAR), `type` (VARCHAR), `size` (VARCHAR) |
| `equipment` | `item_type` (VARCHAR), `rarity` (VARCHAR) |
| `weapons` | `category` (VARCHAR), `damage_type` (VARCHAR) |
| `armor` | `category` (VARCHAR), `armor_class` (INT64) |
| `magicitems` | `type` (VARCHAR), `rarity` (VARCHAR), `requires_attunement` (BOOL) |
| `classes` | `hit_die` (INT64) |
| `races` | `size` (VARCHAR) |
| `rules` | `parent` (VARCHAR) |

### Usage Examples

```python
from lorekeeper_mcp.cache import MilvusCache

# Create cache instance
cache = MilvusCache("~/.lorekeeper/milvus.db")

# Store entities (embeddings generated automatically)
spells = [
    {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation", ...},
    {"slug": "lightning-bolt", "name": "Lightning Bolt", "level": 3, "school": "Evocation", ...},
]
count = await cache.store_entities(spells, "spells")

# Structured query
evocation_spells = await cache.get_entities("spells", level=3, school="Evocation")

# Semantic search - find spells similar to "explosive fire damage"
fire_spells = await cache.semantic_search(
    "spells",
    query="explosive fire damage",
    limit=10
)

# Hybrid search - semantic + filters
fire_evocation = await cache.semantic_search(
    "spells",
    query="area fire damage",
    level=3,
    school="Evocation",
    limit=10
)

# Always close when done
cache.close()
```

### Context Manager Usage

```python
async with MilvusCache("~/.lorekeeper/milvus.db") as cache:
    results = await cache.semantic_search("spells", "healing magic")
    # Cache automatically closed on exit
```

## Semantic Search

Semantic search uses embedding vectors to find entities by meaning rather than exact text matches. This enables natural language queries like "find defensive buff spells" or "creatures that can fly and breathe fire".

### How Semantic Search Works

1. **Query Embedding**: Your search query is converted to a 384-dimensional vector
2. **Vector Similarity**: The query vector is compared against all entity embeddings
3. **Ranked Results**: Entities are returned ranked by cosine similarity
4. **Optional Filters**: Results can be filtered by scalar fields (level, type, etc.)

### Embedding Model

LoreKeeper uses the `all-MiniLM-L6-v2` sentence-transformers model:

- **Dimensions**: 384 floating-point values per embedding
- **Size**: ~80MB download (cached after first use)
- **Speed**: <10ms per text encoding
- **Quality**: Good balance of speed and semantic understanding

### Entity Text Extraction

Different entity types have different text fields extracted for embedding:

| Entity Type | Fields Extracted |
|-------------|------------------|
| **Spells** | name, description, higher_level |
| **Creatures** | name, description, type, action names, ability names |
| **Equipment** | name, description, type, properties |
| **Rules** | name, description, content |
| **Other** | name, description |

### Semantic Search Examples

```python
# Find spells by concept
healing = await cache.semantic_search("spells", "restore health and cure wounds")
fire = await cache.semantic_search("spells", "burn enemies with fire")
control = await cache.semantic_search("spells", "stop enemies from moving")

# Find creatures by behavior
flyers = await cache.semantic_search("creatures", "flying creatures with ranged attacks")
undead = await cache.semantic_search("creatures", "risen dead that drain life")

# Hybrid search: semantic + filters
low_level_fire = await cache.semantic_search(
    "spells",
    query="fire damage",
    level=1,
    limit=5
)

# Multi-document search
srd_healing = await cache.semantic_search(
    "spells",
    query="healing magic",
    document=["srd-5e"]
)
```

### Similarity Scores

Semantic search results include a `_score` field (0.0 to 1.0) indicating similarity:

```python
results = await cache.semantic_search("spells", "fire explosion")
for spell in results:
    print(f"{spell['name']}: {spell['_score']:.3f}")
# Output:
# Fireball: 0.892
# Fire Storm: 0.834
# Flame Strike: 0.789
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOREKEEPER_MILVUS_DB_PATH` | Path to Milvus database file | `~/.lorekeeper/milvus.db` |
| `LOREKEEPER_EMBEDDING_MODEL` | Sentence-transformers model name | `all-MiniLM-L6-v2` |

### Configuration Examples

```bash
# .env file

# Path to Milvus database (supports ~ expansion)
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db

# Custom embedding model (advanced)
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Programmatic Configuration

```python
from lorekeeper_mcp.cache import create_cache, get_cache_from_config

# Create cache from config/environment
cache = get_cache_from_config()

# Or create directly with explicit settings
from lorekeeper_mcp.cache import MilvusCache

cache = MilvusCache("/path/to/milvus.db")

# Factory function
cache = create_cache(db_path="/custom/path.db")
```

## Troubleshooting

### Model Download Fails

**Symptoms**: Error downloading `all-MiniLM-L6-v2` on first run

**Solutions**:
```bash
# Pre-download the model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Or use a different model
LOREKEEPER_EMBEDDING_MODEL=paraphrase-MiniLM-L3-v2
```

### Slow First Query

**Symptoms**: First query takes 2-3 seconds

**Cause**: Embedding model lazy-loads on first use

**Solutions**:
- This is expected behavior; subsequent queries are fast
- Pre-warm the cache by running a dummy query at startup

### Large Database Size

**Symptoms**: Milvus database file is larger than expected

**Cause**: Embedding vectors (384 floats × 4 bytes = 1.5KB per entity)

**Solutions**:
- This is expected; vectors enable semantic search
- For 10,000 entities, expect ~15-20MB for vectors alone

### Entity Not Found After Caching

**Solutions**:
```python
# Ensure entity has required fields
def validate_entity(entity):
    return "slug" in entity and "name" in entity

# Check entity type matches
await cache.get_entities("spells", ...)  # Not "spell"
```

### Filter Returns No Results

**Solutions**:
```python
# Check available indexed fields for entity type
# Spells: level, school, concentration, ritual, document
# Creatures: challenge_rating, type, size, document

# Verify field values match exactly (case-sensitive)
await cache.get_entities("spells", school="Evocation")  # Not "evocation"
```

### Cache Statistics

Get cache statistics for debugging:

```python
stats = await cache.get_cache_stats()
print(f"Collections: {stats['collections']}")
print(f"Total entities: {stats['total_entities']}")
print(f"Database: {stats['db_path']}")
```

## API Reference

### MilvusCache

```python
class MilvusCache:
    """Milvus Lite-backed cache with semantic search support."""

    def __init__(self, db_path: str) -> None:
        """Initialize with database path. Supports ~ expansion."""

    async def store_entities(
        self, entities: list[dict], entity_type: str
    ) -> int:
        """Store entities with auto-generated embeddings."""

    async def get_entities(
        self, entity_type: str, document: str | list[str] | None = None, **filters
    ) -> list[dict]:
        """Retrieve entities with structured filters."""

    async def semantic_search(
        self, entity_type: str, query: str, limit: int = 20,
        document: str | list[str] | None = None, **filters
    ) -> list[dict]:
        """Semantic search with optional hybrid filtering."""

    async def get_entity_count(self, entity_type: str) -> int:
        """Get count of entities in a collection."""

    async def get_available_documents(self) -> list[str]:
        """Get list of available document keys."""

    async def get_document_metadata(self, document_key: str) -> dict[str, int]:
        """Get entity counts per type for a document."""

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get overall cache statistics."""

    def close(self) -> None:
        """Close the database connection."""
```

### Factory Functions

```python
def create_cache(
    db_path: str | None = None
) -> CacheProtocol:
    """Create MilvusCache instance."""

def get_cache_from_config() -> CacheProtocol:
    """Create cache from environment configuration."""
```

### EmbeddingService

```python
class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize with model name. Lazy-loads model."""

    def encode(self, text: str) -> list[float]:
        """Encode single text to 384-dim vector."""

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Encode multiple texts efficiently."""

    def get_searchable_text(self, entity: dict, entity_type: str) -> str:
        """Extract searchable text from entity."""
```

## Summary

LoreKeeper's cache system provides efficient storage for D&D entities with powerful semantic search:

- **Milvus Lite**: Embedded vector database with semantic search capabilities
- **Semantic Search**: Find content by meaning with natural language queries
- **Hybrid Search**: Combine semantic queries with structured filters
- **Embedded Database**: No external services required
- **Zero Configuration**: Works out of the box with sensible defaults
