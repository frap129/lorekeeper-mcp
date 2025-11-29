# Database Cache Documentation

This document provides detailed information about LoreKeeper MCP's caching system. The system supports two backends: **Milvus Lite** (default) with semantic/vector search, and **SQLite** (legacy) with structured filtering only.

## Table of Contents

- [Overview](#overview)
- [Cache Backends](#cache-backends)
- [Milvus Lite Backend](#milvus-lite-backend)
- [SQLite Backend (Legacy)](#sqlite-backend-legacy)
- [Semantic Search](#semantic-search)
- [Configuration](#configuration)
- [Migration Guide](#migration-guide)
- [Troubleshooting](#troubleshooting)

## Overview

The cache layer provides persistent storage for D&D entity data, reducing external API calls and improving response times. LoreKeeper supports two cache backends:

| Backend | Vector Search | Structured Filters | Embedded | Default |
|---------|---------------|-------------------|----------|---------|
| **Milvus Lite** | ✓ | ✓ | ✓ | Yes |
| **SQLite** | ✗ | ✓ | ✓ | No |

### Key Features

- **Entity-Based Storage**: Separate collections/tables for spells, creatures, equipment, etc.
- **Semantic Search**: Natural language queries find related content (Milvus only)
- **Hybrid Search**: Combine semantic search with filters (level, school, CR, etc.)
- **Infinite TTL**: Valid entity data never expires; only explicitly updated
- **Indexed Filtering**: Fast queries on type-specific fields
- **Source Tracking**: Records which API provided cached data
- **Zero Configuration**: Works out of the box with sensible defaults

### Cache Strategy

The system uses a **multi-layered caching strategy**:

1. **Entity Cache First**: Check entity-based cache for D&D content
2. **Entity Hit**: Return cached entity data (no expiration)
3. **Entity Miss**: Fetch from API, cache with embeddings, return data
4. **Offline Fallback**: Serve cached entities when API is unavailable

## Cache Backends

### Choosing a Backend

**Use Milvus Lite (default) when:**
- You want semantic search capabilities ("find spells like Fireball")
- Natural language queries are important for your use case
- You have ~100MB disk space for the embedding model

**Use SQLite when:**
- You only need exact/pattern matching
- Disk space is constrained
- You're migrating from an older version and want backward compatibility

### Backend Comparison

| Feature | Milvus Lite | SQLite |
|---------|-------------|--------|
| **Semantic Search** | ✓ Natural language queries | ✗ Pattern matching only |
| **Hybrid Search** | ✓ Vector + filters combined | ✗ Filters only |
| **First-Run Download** | ~80MB embedding model | None |
| **Database Size** | Larger (includes embeddings) | Smaller |
| **Query Speed** | Fast (indexed vectors) | Fast (indexed columns) |
| **Startup Time** | ~2s on first use (model load) | Instant |

## Milvus Lite Backend

Milvus Lite is an embedded vector database that runs in-process (like SQLite). It stores both entity data and embedding vectors for semantic search.

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

## SQLite Backend (Legacy)

SQLite provides a lightweight, file-based cache with structured filtering only. It does not support semantic search.

### Database Schema

```sql
CREATE TABLE {entity_type} (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,          -- Full entity as JSON
    source_api TEXT NOT NULL,
    document TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    -- Type-specific indexed fields
    [field1] [TYPE],
    [field2] [TYPE],
    ...
);
```

### Usage Examples

```python
from lorekeeper_mcp.cache import SQLiteCache

cache = SQLiteCache("./data/cache.db")

# Store entities
await cache.store_entities(spells, "spells")

# Query with filters
results = await cache.get_entities("spells", level=3, school="Evocation")

# Semantic search not supported
try:
    await cache.semantic_search("spells", "fire damage")
except NotImplementedError:
    print("SQLite does not support semantic search")
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
| `LOREKEEPER_CACHE_BACKEND` | Backend type: "milvus" or "sqlite" | `milvus` |
| `LOREKEEPER_MILVUS_DB_PATH` | Path to Milvus database file | `~/.lorekeeper/milvus.db` |
| `LOREKEEPER_SQLITE_DB_PATH` | Path to SQLite database file | `~/.lorekeeper/cache.db` |
| `LOREKEEPER_EMBEDDING_MODEL` | Sentence-transformers model name | `all-MiniLM-L6-v2` |

### Configuration Examples

```bash
# .env file

# Use Milvus (default)
LOREKEEPER_CACHE_BACKEND=milvus
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db

# Or use SQLite for legacy compatibility
LOREKEEPER_CACHE_BACKEND=sqlite
LOREKEEPER_DB_PATH=./data/cache.db

# Custom embedding model (advanced)
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Programmatic Configuration

```python
from lorekeeper_mcp.cache import create_cache, get_cache_from_config

# Create cache from config/environment
cache = get_cache_from_config()

# Or create directly with explicit settings
from lorekeeper_mcp.cache import MilvusCache, SQLiteCache

milvus_cache = MilvusCache("/path/to/milvus.db")
sqlite_cache = SQLiteCache("/path/to/sqlite.db")

# Factory function
cache = create_cache(backend="milvus", db_path="/custom/path.db")
```

## Migration Guide

### Migrating from SQLite to Milvus Lite

**Breaking Changes:**
- Cache data format is different between backends
- SQLite cache data cannot be automatically migrated to Milvus
- First Milvus startup downloads the embedding model (~80MB)

**Migration Steps:**

1. **Update Configuration**

   ```bash
   # .env
   LOREKEEPER_CACHE_BACKEND=milvus
   LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db
   ```

2. **Re-index Your Data**

   The Milvus cache will be empty on first use. Re-import your data:

   ```bash
   # Re-import from API or OrcBrew files
   lorekeeper import /path/to/content.orcbrew

   # Or let it repopulate from API on first query
   ```

3. **Verify Semantic Search Works**

   ```python
   # Test semantic search
   results = await cache.semantic_search("spells", "fire damage")
   assert len(results) > 0
   ```

**Data Re-indexing Note:** Switching to Milvus requires re-caching all entities because:
- Milvus needs embedding vectors that SQLite doesn't have
- Entity storage format differs between backends
- There's no automated migration tool (data comes from APIs)

### Rollback to SQLite

If you need to switch back to SQLite:

```bash
# .env
LOREKEEPER_CACHE_BACKEND=sqlite
LOREKEEPER_DB_PATH=./data/cache.db
```

**Important:** Your SQLite cache (if it still exists) will be used, but it won't have any data cached since switching to Milvus. Re-import or let it repopulate from APIs.

### Parallel Operation

You can run both backends for testing:

```bash
# Use separate database files
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db
LOREKEEPER_DB_PATH=~/.lorekeeper/sqlite.db

# Switch between them by changing LOREKEEPER_CACHE_BACKEND
```

## Troubleshooting

### Milvus-Specific Issues

#### Model Download Fails

**Symptoms**: Error downloading `all-MiniLM-L6-v2` on first run

**Solutions**:
```bash
# Pre-download the model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Or use a different model
LOREKEEPER_EMBEDDING_MODEL=paraphrase-MiniLM-L3-v2
```

#### Slow First Query

**Symptoms**: First query takes 2-3 seconds

**Cause**: Embedding model lazy-loads on first use

**Solutions**:
- This is expected behavior; subsequent queries are fast
- Pre-warm the cache by running a dummy query at startup

#### Large Database Size

**Symptoms**: Milvus database file is much larger than SQLite

**Cause**: Embedding vectors (384 floats × 4 bytes = 1.5KB per entity)

**Solutions**:
- This is expected; vectors enable semantic search
- For 10,000 entities, expect ~15-20MB for vectors alone
- Consider SQLite if disk space is critical

### SQLite-Specific Issues

#### Database Lock Errors

**Symptoms**: `sqlite3.OperationalError: database is locked`

**Solutions**:
```python
# Ensure WAL mode is enabled
async with aiosqlite.connect(db_path) as db:
    await db.execute("PRAGMA journal_mode=WAL")

# Use shorter transactions
# Add retry logic with exponential backoff
```

#### Semantic Search Not Supported

**Symptoms**: `NotImplementedError` when calling `semantic_search()`

**Cause**: SQLite backend doesn't support vector search

**Solutions**:
- Switch to Milvus backend for semantic search
- Use `get_entities()` with filters instead
- Use name pattern matching: `name="fire*"`

### Common Issues (Both Backends)

#### Entity Not Found After Caching

**Solutions**:
```python
# Ensure entity has required fields
def validate_entity(entity):
    return "slug" in entity and "name" in entity

# Check entity type matches
await cache.get_entities("spells", ...)  # Not "spell"
```

#### Filter Returns No Results

**Solutions**:
```python
# Check available indexed fields for entity type
# Spells: level, school, concentration, ritual, document
# Creatures: challenge_rating, type, size, document

# Verify field values match exactly (case-sensitive)
await cache.get_entities("spells", school="Evocation")  # Not "evocation"
```

#### Cache Statistics

Get cache statistics for debugging:

```python
# Milvus
stats = await cache.get_cache_stats()
print(f"Collections: {stats['collections']}")
print(f"Total entities: {stats['total_entities']}")
print(f"Database: {stats['db_path']}")

# SQLite
stats = await get_cache_stats()
print(f"Entity counts: {stats['entity_counts']}")
print(f"Database size: {stats['db_size_bytes'] / 1024 / 1024:.1f} MB")
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

### SQLiteCache

```python
class SQLiteCache:
    """SQLite-backed cache with structured filtering only."""

    # Same interface as MilvusCache except:
    # - semantic_search() raises NotImplementedError
    # - No embedding vectors stored
```

### Factory Functions

```python
def create_cache(
    backend: str = "milvus",
    db_path: str | None = None
) -> CacheProtocol:
    """Create cache instance by backend type."""

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

LoreKeeper's cache system provides flexible, efficient storage for D&D entities with two backend options:

- **Milvus Lite (default)**: Full semantic search capabilities with natural language queries
- **SQLite (legacy)**: Lightweight structured filtering without semantic search

Key benefits:
- **Zero Configuration**: Works out of the box with sensible defaults
- **Semantic Search**: Find content by meaning, not just keywords
- **Hybrid Search**: Combine semantic queries with structured filters
- **Embedded Database**: No external services required
- **Easy Migration**: Switch backends via environment variable
