# Design: Import OrcBrew Data

## Architecture Overview

```
┌─────────────────┐
│   CLI Entry     │
│  (lorekeeper)   │
└────────┬────────┘
         │
         │ commands
         ▼
┌─────────────────┐
│  CLI Commands   │
│  - import       │
└────────┬────────┘
         │
         │ parse file
         ▼
┌─────────────────┐      ┌──────────────────┐
│  OrcBrew Parser │─────▶│  Entity Mapper   │
│  (EDN reader)   │      │  (type mapping)  │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  │ normalized entities
                                  ▼
                         ┌─────────────────┐
                         │  Cache Writer   │
                         │ (bulk import)   │
                         └────────┬────────┘
                                  │
                                  │ store
                                  ▼
                         ┌─────────────────┐
                         │  SQLite Cache   │
                         │  (existing)     │
                         └─────────────────┘
```

## Component Details

### 1. CLI Entry Point (`src/lorekeeper_mcp/cli.py`)
- Uses Click framework for command definition
- Entry point via `__main__.py` or direct module execution
- Handles global options (--verbose, --db-path)

**Key Functions**:
- `cli()` - Main CLI group
- `import_cmd()` - Import command handler

### 2. OrcBrew Parser (`src/lorekeeper_mcp/parsers/orcbrew.py`)
Responsibilities:
- Read .orcbrew files (EDN format)
- Parse top-level structure (book → entity types → entities)
- Extract entity data with metadata

**Key Classes**:
- `OrcBrewParser` - Main parser class
  - `parse_file(file_path: Path) -> dict[str, list[dict]]`
  - `_extract_entities(book_name: str, data: dict) -> list[dict]`
  - `_normalize_entity(entity: dict, entity_type: str, book: str) -> dict`

**Data Flow**:
```
.orcbrew file
  └─▶ EDN parse
      └─▶ {"Book Name": {":orcpub.dnd.e5/spells": {...}}}
          └─▶ Extract by entity type
              └─▶ List of normalized entities
```

### 3. Entity Type Mapper (`src/lorekeeper_mcp/parsers/entity_mapper.py`)
Maps OrcBrew entity types to LoreKeeper entity types.

**Mappings**:
```python
ORCBREW_TO_LOREKEEPER = {
    "orcpub.dnd.e5/spells": "spells",
    "orcpub.dnd.e5/monsters": "creatures",  # Use 'creatures' not 'monsters'
    "orcpub.dnd.e5/subclasses": "subclasses",
    "orcpub.dnd.e5/races": "species",  # Map to 'species'
    "orcpub.dnd.e5/subraces": "subraces",
    "orcpub.dnd.e5/classes": "classes",
    "orcpub.dnd.e5/feats": "feats",
    "orcpub.dnd.e5/backgrounds": "backgrounds",
    "orcpub.dnd.e5/languages": "languages",
    # Skip unsupported types initially
    "orcpub.dnd.e5/invocations": None,
    "orcpub.dnd.e5/selections": None,
}
```

**Field Transformations**:
- `:key` → `slug` (entity identifier)
- `:name` → `name` (display name)
- `:option-pack` → `source` (source book name)
- `:description` → `desc` (for consistency with API data)
- Full entity data → `data` (JSON field)

### 4. Batch Cache Writer
Reuses existing `bulk_cache_entities()` from `cache.db` module.

**Features**:
- Async batch writes for performance
- Transaction support (all-or-nothing per entity type)
- Progress reporting via logging

### 5. Error Handling Strategy

**Levels**:
1. **File-level errors** (Fatal):
   - File not found
   - Invalid EDN syntax
   - Unreadable file
   → Abort import, show error

2. **Entity-type errors** (Warning):
   - Unsupported entity type
   - Empty entity list
   → Log warning, skip type, continue

3. **Entity-level errors** (Warning):
   - Missing required field (slug, name)
   - Invalid data format
   → Log warning, skip entity, continue

**Logging**:
```
INFO: Starting import of 'MegaPak.orcbrew'...
INFO: Found 5 entity types to import
INFO: Importing spells... (1234 entities)
INFO: ✓ Imported 1230 spells (4 skipped)
WARN: Skipped 4 entities due to missing 'slug' field
INFO: Importing creatures... (567 entities)
INFO: ✓ Imported 567 creatures
INFO: Import complete! Imported 1797 total entities
```

## Data Normalization

### Entity Structure
Every imported entity is normalized to:
```python
{
    "slug": str,           # Required: unique identifier
    "name": str,           # Required: display name
    "source": str,         # Source book/pack
    "source_api": "orcbrew",  # Mark as imported from OrcBrew
    "data": dict,          # Full original entity data (JSON)
    # Type-specific indexed fields extracted from data
}
```

### Indexed Field Extraction
For entity types with indexed fields, extract from `data`:

**Spells**:
- `level` → `data.level`
- `school` → `data.school`
- `concentration` → `data.concentration` (boolean)
- `ritual` → `data.ritual` (boolean)

**Creatures/Monsters**:
- `challenge_rating` → `data.challenge` (float)
- `type` → `data.type` (string)
- `size` → `data.size` (string)

## Performance Considerations

1. **Streaming**: Read file once, process in chunks
2. **Batch writes**: Use SQLite transactions for groups of 500 entities
3. **Progress**: Report every 100 entities
4. **Memory**: Avoid loading entire file into memory at once

**Estimated Performance** (MegaPak file, 43K lines):
- Parse time: ~2-5 seconds
- Import time: ~10-20 seconds
- Total time: <30 seconds

## CLI Usage Examples

```bash
# Basic import
lorekeeper import MegaPak_-_WotC_Books.orcbrew

# Import with custom database path
lorekeeper --db-path ./custom.db import data.orcbrew

# Verbose output with progress
lorekeeper -v import homebrew.orcbrew

# Dry run (parse only, don't import)
lorekeeper import --dry-run test.orcbrew

# Force overwrite existing entries
lorekeeper import --force MegaPak.orcbrew
```

## Testing Strategy

### Unit Tests
1. **Parser tests** (`tests/test_parsers/test_orcbrew.py`):
   - Parse valid EDN
   - Handle malformed EDN
   - Extract entities correctly
   - Handle missing fields

2. **Mapper tests** (`tests/test_parsers/test_entity_mapper.py`):
   - Map all known entity types
   - Handle unknown types gracefully
   - Transform fields correctly

3. **CLI tests** (`tests/test_cli.py`):
   - Command invocation
   - Option handling
   - Error messages

### Integration Tests
1. **End-to-end import** (`tests/test_cli/test_import_e2e.py`):
   - Import sample .orcbrew file
   - Verify entities in cache
   - Check indexed fields
   - Validate data integrity

2. **Large file test**:
   - Import MegaPak file
   - Measure performance
   - Verify all entity types imported

## Security Considerations

1. **File access**: Only read files, never execute code
2. **Input validation**: Validate EDN structure before processing
3. **SQL injection**: Use parameterized queries (already handled by aiosqlite)
4. **Resource limits**: Limit file size to prevent DoS (e.g., max 100MB)

## Future Enhancements (Out of Scope)

1. **Export command**: Export cache to .orcbrew format
2. **Merge strategy**: Smart merging of conflicting data
3. **Validation schemas**: Strict schema validation for entity data
4. **Progress bar**: Visual progress indicator (via `rich` library)
5. **Parallel imports**: Import multiple files simultaneously
6. **Incremental updates**: Only import changed entities
