## Why
LoreKeeper currently allows users to discover and configure Open5e source documents (via the `list-open5e-documents` change), but it does not actually track which document each cached entity comes from or expose document-aware filtering across tools. Open5e and OrcBrew both have a strong notion of "documents" or "books" as top-level sources, while the official D&D 5e API (2014) effectively maps to the SRD. Without first-class document tracking and filtering, AI assistants cannot answer questions like "show me SRD-only spells" or "only use content from this third-party book".

## What Changes
- Add explicit document name to all cached entities so every item in the cache knows which document or book it originated from (Open5e v2 document name, OrcBrew book name, or "System Reference Document 5.1" for SRD content).
- Extend repository and tool behavior so lookups can filter entities by document name (e.g., "System Reference Document 5.1", "Adventurer's Guide", "Tome of Beasts", or OrcBrew book names).
- Clarify how document configuration (included/excluded document lists from the `list-open5e-documents` change) interacts with per-item document tracking and filtering.
- Ensure all MCP tool responses continue to include clear source attribution (document name), backed by consistent, queryable document metadata.

## Impact
- Affected specs: `mcp-tools`, `repository-infrastructure`, `entity-cache`, `orcbrew-parser`.
- Affected code (expected): cache schema and normalization (`src/lorekeeper_mcp/cache/schema.py`, `src/lorekeeper_mcp/cache/db.py`), OrcBrew parser and entity mapper (`src/lorekeeper_mcp/parsers/orcbrew.py`, `src/lorekeeper_mcp/parsers/entity_mapper.py`), Open5e and D&D API client normalization (`src/lorekeeper_mcp/api_clients/*`), repositories (`src/lorekeeper_mcp/repositories/*.py`), and MCP tools (`src/lorekeeper_mcp/tools/*.py`).
- Backward compatibility: Additive behavior only; existing tool parameters remain unchanged. New document filter options will be additive, and existing configuration from `list-open5e-documents` continues to work as documented.
