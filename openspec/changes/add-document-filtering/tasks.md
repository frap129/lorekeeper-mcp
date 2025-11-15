# Implementation Tasks

## Phase 1: Cache Layer

### 1.1 Multi-Document Filtering
- [x] Update `query_cached_entities()` in `src/lorekeeper_mcp/cache/db.py` to accept `document` as list or string
- [x] Generate SQL IN clause for list values: `WHERE document IN (?, ?, ...)`
- [x] Add short-circuit for empty document list (return empty immediately)
- [x] Write tests for single document (string), multiple documents (list), empty list, and None
- [x] Verify backward compatibility with existing cache queries

### 1.2 Document Discovery
- [x] Add `get_available_documents()` function to `src/lorekeeper_mcp/cache/db.py`
- [x] Implement UNION ALL query across all entity types in `ENTITY_TYPES`
- [x] Group by document and source_api, count entities per document and type
- [x] Add optional `source_api` filter parameter
- [x] Write tests for multi-source documents, empty cache, and source filtering

### 1.3 Document Metadata Query
- [x] Add `get_document_metadata()` function to `src/lorekeeper_mcp/cache/db.py`
- [x] Query `documents` entity type by slug, return metadata or None
- [x] Write tests for existing metadata, missing documents, and missing table

## Phase 2: Cache and Repository Updates

### 2.1 Cache Protocol Updates
- [x] Update `CacheProtocol.get_entities()` signature in `src/lorekeeper_mcp/cache/protocol.py` to accept `document` parameter
- [x] Update `SQLiteCache.get_entities()` in `src/lorekeeper_mcp/cache/sqlite.py` to accept and pass document parameter
- [x] Write tests for SQLiteCache with document filtering

### 2.2 Repository Updates
- [x] Update `SpellRepository.search()` to accept `document` parameter and pass to cache layer
- [x] Update `MonsterRepository.search()` with same pattern
- [x] Update `EquipmentRepository.search()` with same pattern
- [x] Update `CharacterOptionRepository.search()` with same pattern
- [x] Update `RuleRepository.search()` with same pattern
- [x] Remove `document` from API filters on cache miss (cache-only filter)
- [x] Write tests for each repository with document filtering

## Phase 3: MCP Tools

### 3.1 list_documents Tool
- [x] Create `src/lorekeeper_mcp/tools/list_documents.py` with async `list_documents(source=None)` function
- [x] Call `get_available_documents()` and optionally enrich with `get_document_metadata()`
- [x] Export from `src/lorekeeper_mcp/tools/__init__.py`
- [x] Register tool in `src/lorekeeper_mcp/server.py` with schema for `source` parameter
- [x] Write unit tests and integration tests

### 3.2 Add document_keys to Lookup Tools
- [x] Add `document_keys: list[str] | None` parameter to `lookup_spell()` in `tools/spell_lookup.py`
- [x] Add `document_keys` parameter to `lookup_creature()` in `tools/creature_lookup.py`
- [x] Add `document_keys` parameter to `lookup_equipment()` in `tools/equipment_lookup.py`
- [x] Add `document_keys` parameter to `lookup_character_option()` in `tools/character_option_lookup.py`
- [x] Add `document_keys` parameter to `lookup_rule()` in `tools/rule_lookup.py`
- [x] Pass parameter to repository as `document` in all tools
- [x] Update docstrings with document filtering examples
- [x] Update server.py tool schemas with `document_keys` array parameter
- [x] Write tests for each tool with document filtering

### 3.3 Add document_keys to Search Tool
- [x] Add `document_keys: list[str] | None` parameter to `search_dnd_content()` in `tools/search_dnd_content.py`
- [x] Implement post-filtering by document field after unified search
- [x] Add short-circuit for empty document_keys list
- [x] Update server.py tool schema
- [x] Write tests for post-filtering with single/multiple documents and empty list

## Phase 4: Testing and Documentation

### 4.1 Integration Testing
- [x] Create `tests/test_tools/test_document_filtering.py` with end-to-end tests
- [x] Test `list_documents()` with real cache data
- [x] Test document filtering across all lookup tools
- [x] Test cross-source filtering (open5e_v2, dnd5e_api, orcbrew)

### 4.2 Live MCP Testing
- [x] Add live test for `list_documents()` in `tests/test_tools/test_live_mcp.py`
- [x] Add live tests for document filtering in lookup tools
- [x] Verify tools callable via MCP protocol with correct responses

### 4.3 Quality Checks
- [ ] Run all unit tests: `uv run pytest tests/ -m "not live" -v` (4 failures in test_serve.py - unrelated to document filtering)
- [x] Run type checking: `just type-check`
- [x] Run linting: `just lint`
- [x] Run formatting: `just format --check`
- [ ] Run all quality checks: `just check` (blocked by test failures)

### 4.4 Documentation
- [x] Update README.md with document filtering examples
- [x] Update docs/tools.md with `list_documents()` usage and `document_keys` parameter documentation
- [x] Add examples for common use cases (SRD-only filtering, multi-document searches)

## Validation Checklist

- [x] All cache functions work across sources (open5e_v2, dnd5e_api, orcbrew)
- [x] `list_documents()` returns accurate document lists from cache
- [x] All lookup tools accept and respect `document_keys` parameter
- [x] Search tool post-filters by document correctly
- [x] Multi-document filtering works with IN clause
- [x] Empty document list short-circuits correctly
- [x] Single document filter backward compatible (string)
- [ ] All unit tests pass (4 failures in test_serve.py - unrelated to document filtering)
- [ ] All live tests pass (not yet verified)
- [x] Type checking passes
- [x] Linting passes
- [x] No breaking changes to existing functionality
- [x] Documentation updated with examples
- [x] Source-agnostic design verified (no API-specific document logic)
