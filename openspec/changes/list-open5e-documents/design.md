# Design Document: List and Filter Open5e Documents

## Problem Statement
The LoreKeeper MCP server currently ingests D&D 5e data from the Open5e API without visibility into the source documents (published books, supplements, etc.). The Open5e v2 API provides a `/documents/` endpoint that exposes metadata about all available documents, but this information is not surfaced to users or configurable.

## Solution Overview

### Architecture

```
┌──────────────────────────┐
│   User                   │
└────────────┬─────────────┘
             │
             │ CLI command
             ▼
┌──────────────────────────────────────────┐
│   Document Management CLI                │
│  (list-documents command)                │
│  Calls Open5e v2 API → /documents/       │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│   Open5eV2Client.get_documents()         │
│   (already exists in codebase)           │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│   Open5e API v2 /documents/ endpoint     │
│   Returns JSON with all available docs   │
└──────────────────────────────────────────┘
```

### Phase 1: Document Listing (This Proposal)

**Deliverables:**
1. CLI command: `lorekeeper-mcp list-documents`
2. Configuration option: `included_documents` and `excluded_documents`
3. Server startup logging indicating configured documents

**Implementation Details:**

#### CLI Command Structure
- Command: `lorekeeper-mcp list-documents`
- Options:
  - `--format json` or `--format table` (default: table)
  - `--publisher <name>` (filter by publisher)
  - `--game-system <name>` (filter by game system)

Example output (table):
```
Key              Display Name              Publisher         License
─────────────────────────────────────────────────────────────────────
a5e-ag           Adventurer's Guide        EN Publishing     CC-BY-4.0
a5e-ddg          Dungeon Delver's Guide    EN Publishing     CC-BY-4.0
srd-5e           Player's Handbook (SRD)   Wizards of Coast  OGL-1.0a
tce              Tasha's Cauldron of E...  Wizards of Coast  OGL-1.0a
...
```

#### Configuration Options
Add to `config.py` Settings class:
```python
included_documents: list[str] | None = Field(
    default=None,
    description="List of document keys to include. If set, only these documents are used."
)
excluded_documents: list[str] | None = Field(
    default=None,
    description="List of document keys to exclude from all lookups."
)
```

Environment variable support:
```
INCLUDED_DOCUMENTS="srd-5e,tce,phb"
EXCLUDED_DOCUMENTS="ogl-content"
```

#### Server Startup
On server initialization, log:
```
[INFO] Documents configured:
  - Included: 3 documents (srd-5e, tce, phb)
  - Excluded: 0 documents
  - Mode: Inclusive (only listed documents used)
```

### Phase 2: Document Filtering (Future Enhancement)
- Filter API results to only include items with `document` field matching configured documents
- Update repositories to accept document filter parameter
- Add filtering to all lookup tools

## Implementation Approach

### 1. CLI Implementation (minimal approach)
Since the codebase doesn't currently use Click or Typer, we have two options:

**Option A: Use Python's built-in argparse** (minimal dependencies)
- Add basic argparse-based CLI to `__main__.py`
- Supports subcommands: `list-documents`, `run` (default)
- Minimal additional dependencies

**Option B: Add Click library** (more flexible)
- Better CLI structure and options
- More maintainable for future CLI commands
- Single new dependency

**Recommendation**: Option A first (use argparse), upgrade to Click if needed.

### 2. Configuration Management
- Extend existing `Settings` class in `config.py`
- Support both CLI arguments and environment variables
- Validate document keys against API before accepting configuration

### 3. Document Discovery
- Implement `list_documents()` function in `repositories/` or new `documents.py` module
- Cache document list (expires after 7 days)
- Handle API failures gracefully

### 4. Server Logging
- Add startup logging to show configured documents
- Include in server initialization sequence

## Data Model

### Document Metadata Structure
```python
@dataclass
class DocumentMetadata:
    key: str                           # Unique identifier (e.g., "srd-5e")
    name: str                          # Display name
    display_name: str                  # User-friendly name
    author: str                        # Author/creator
    publisher: str                     # Publisher name
    gamesystem: str                    # Game system (e.g., "5e", "a5e")
    publication_date: str              # ISO 8601 date
    description: str                   # Brief description
    licenses: list[dict[str, str]]    # License information
    permalink: str                     # Link to source
```

## Testing Strategy
1. Unit tests for document list command
2. Integration tests with Open5e API
3. Configuration validation tests
4. Startup logging verification tests

## Future Enhancements (Phase 2)

### Document Filtering in Lookups
Add optional document filtering to all lookup tools:
```python
async def lookup_spell(
    name: str | None = None,
    ...
    document_keys: list[str] | None = None,  # New parameter
    ...
) -> list[Spell]:
    # Filter results to only include spells from specified documents
```

### Repository-Level Filtering
```python
class SpellRepository:
    async def search(
        self,
        name: str | None = None,
        document_keys: list[str] | None = None,  # Apply filter
        ...
    ) -> list[Spell]:
```

## Configuration Examples

### Include Specific Documents Only
```bash
# Via environment variables
export INCLUDED_DOCUMENTS="srd-5e,tce,phb"

# Via .env file
INCLUDED_DOCUMENTS=srd-5e,tce,phb

# Via CLI (future)
lorekeeper-mcp run --included-documents srd-5e,tce,phb
```

### Exclude Certain Documents
```bash
export EXCLUDED_DOCUMENTS="experimental,preview"
```

### List Available Documents
```bash
lorekeeper-mcp list-documents
lorekeeper-mcp list-documents --format json | jq '.[].key'
lorekeeper-mcp list-documents --publisher "Kobold Press"
```

## Edge Cases & Error Handling

1. **Invalid document key in config**: Log warning, ignore invalid key
2. **API unavailable when listing**: Return cached list or error message
3. **Both included and excluded specified**: Included takes precedence, log warning
4. **Empty document list**: Allow, just note in startup logs
5. **Network timeout on first startup**: Use empty cache, warn user

## Backward Compatibility
- All changes are additive
- Default behavior (no configuration) = all documents included
- Existing users unaffected unless they set configuration
- No breaking changes to tools or repositories

## Success Metrics
- Users can discover available documents via CLI
- Users can configure document filtering via environment
- Server startup clearly indicates configured documents
- No increase in server startup time
- No new external dependencies (use argparse)
