# Implementation Tasks

## Phase 1: Cache Layer

### 1.1 Multi-Document Filtering
- [ ] Update `query_cached_entities()` in `src/lorekeeper_mcp/cache/db.py` to accept `document` as list or string
- [ ] Generate SQL IN clause for list values: `WHERE document IN (?, ?, ...)`
- [ ] Add short-circuit for empty document list (return empty immediately)
- [ ] Write tests for single document (string), multiple documents (list), empty list, and None
- [ ] Verify backward compatibility with existing cache queries

### 1.2 Document Discovery
- [ ] Add `get_available_documents()` function to `src/lorekeeper_mcp/cache/db.py`
- [ ] Implement UNION ALL query across all entity types in `ENTITY_TYPES`
- [ ] Group by document and source_api, count entities per document and type
- [ ] Add optional `source_api` filter parameter
- [ ] Write tests for multi-source documents, empty cache, and source filtering

### 1.3 Document Metadata Query
- [ ] Add `get_document_metadata()` function to `src/lorekeeper_mcp/cache/db.py`
- [ ] Query `documents` entity type by slug, return metadata or None
- [ ] Write tests for existing metadata, missing documents, and missing table

## Phase 2: Cache and Repository Updates

### 2.1 Cache Protocol Updates
- [ ] Update `CacheProtocol.get_entities()` signature in `src/lorekeeper_mcp/cache/protocol.py` to accept `document` parameter
- [ ] Update `SQLiteCache.get_entities()` in `src/lorekeeper_mcp/cache/sqlite.py` to accept and pass document parameter
- [ ] Write tests for SQLiteCache with document filtering

### 2.2 Repository Updates
- [ ] Update `SpellRepository.search()` to accept `document` parameter and pass to cache layer
- [ ] Update `MonsterRepository.search()` with same pattern
- [ ] Update `EquipmentRepository.search()` with same pattern
- [ ] Update `CharacterOptionRepository.search()` with same pattern
- [ ] Update `RuleRepository.search()` with same pattern
- [ ] Remove `document` from API filters on cache miss (cache-only filter)
- [ ] Write tests for each repository with document filtering

## Phase 3: MCP Tools

### 3.1 list_documents Tool
- [ ] Create `src/lorekeeper_mcp/tools/list_documents.py` with async `list_documents(source=None)` function
- [ ] Call `get_available_documents()` and optionally enrich with `get_document_metadata()`
- [ ] Export from `src/lorekeeper_mcp/tools/__init__.py`
- [ ] Register tool in `src/lorekeeper_mcp/server.py` with schema for `source` parameter
- [ ] Write unit tests and integration tests

### 3.2 Add document_keys to Lookup Tools
- [x] Add `document_keys: list[str] | None` parameter to `lookup_spell()` in `tools/spell_lookup.py`
- [x] Add `document_keys` parameter to `lookup_creature()` in `tools/creature_lookup.py`
- [ ] Add `document_keys` parameter to `lookup_equipment()` in `tools/equipment_lookup.py`
- [ ] Add `document_keys` parameter to `lookup_character_option()` in `tools/character_option_lookup.py`
- [ ] Add `document_keys` parameter to `lookup_rule()` in `tools/rule_lookup.py`
- [ ] Pass parameter to repository as `document` in all tools
- [ ] Update docstrings with document filtering examples
- [ ] Update server.py tool schemas with `document_keys` array parameter
- [ ] Write tests for each tool with document filtering

### 3.3 Add document_keys to Search Tool
- [ ] Add `document_keys: list[str] | None` parameter to `search_dnd_content()` in `tools/search_dnd_content.py`
- [ ] Implement post-filtering by document field after unified search
- [ ] Add short-circuit for empty document_keys list
- [ ] Update server.py tool schema
- [ ] Write tests for post-filtering with single/multiple documents and empty list

## Phase 4: Testing and Documentation

### 4.1 Integration Testing
- [ ] Create `tests/test_tools/test_document_filtering.py` with end-to-end tests
- [ ] Test `list_documents()` with real cache data
- [ ] Test document filtering across all lookup tools
- [ ] Test cross-source filtering (open5e_v2, dnd5e_api, orcbrew)

### 4.2 Live MCP Testing
- [ ] Add live test for `list_documents()` in `tests/test_tools/test_live_mcp.py`
- [ ] Add live tests for document filtering in lookup tools
- [ ] Verify tools callable via MCP protocol with correct responses

### 4.3 Quality Checks
- [ ] Run all unit tests: `uv run pytest tests/ -m "not live" -v`
- [ ] Run type checking: `just type-check`
- [ ] Run linting: `just lint`
- [ ] Run formatting: `just format --check`
- [ ] Run all quality checks: `just check`

### 4.4 Documentation
- [ ] Update README.md with document filtering examples
- [ ] Update docs/tools.md with `list_documents()` usage and `document_keys` parameter documentation
- [ ] Add examples for common use cases (SRD-only filtering, multi-document searches)

## Validation Checklist

- [ ] All cache functions work across sources (open5e_v2, dnd5e_api, orcbrew)
- [ ] `list_documents()` returns accurate document lists from cache
- [ ] All lookup tools accept and respect `document_keys` parameter
- [ ] Search tool post-filters by document correctly
- [ ] Multi-document filtering works with IN clause
- [ ] Empty document list short-circuits correctly
- [ ] Single document filter backward compatible (string)
- [ ] All unit tests pass
- [ ] All live tests pass
- [ ] Type checking passes
- [ ] Linting passes
- [ ] No breaking changes to existing functionality
- [ ] Documentation updated with examples
- [ ] Source-agnostic design verified (no API-specific document logic)
