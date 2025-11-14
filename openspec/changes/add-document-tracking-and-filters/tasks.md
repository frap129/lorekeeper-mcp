## Task 1: Add Document Column to Cache Schema

- [x] Add document TEXT column to entity cache schema
- [x] Add document field to INDEXED_FIELDS for all entity types
- [x] Create database indexes on document column
- [x] Write tests for document field in schema
- [x] Write tests for document indexing
- [x] Run cache schema tests
- [x] Commit changes

**Status:** COMPLETE (commit bece438)

## Task 2: Update Cache DB Layer for Document Field

- [x] Write tests for storing entities with document name
- [x] Write tests for querying entities by document
- [x] Verify bulk_cache_entities handles document field automatically
- [x] Run all cache DB tests
- [x] Commit tests

**Status:** COMPLETE (commit bece438)

## Task 3: Normalize Open5e V2 Document Names

- [x] Add \_extract_document_name() helper function
- [x] Update get_spells to extract document name
- [x] Update Spell model to include document field
- [x] Update get_creatures to extract document name
- [x] Update Monster model to include document field
- [x] Update get_weapons to extract document name
- [x] Update Weapon model to include document field
- [x] Update get_armor to extract document name
- [x] Update Armor model to include document field
- [x] Write tests for document name extraction
- [x] Run all Open5e v2 tests
- [x] Commit changes

**Status:** COMPLETE (commit f2300e1)

## Task 4: Add SRD Document Name to D&D 5e API Entities

- [x] Add SRD_DOCUMENT_NAME constant
- [x] Update get_spells to add "System Reference Document 5.1"
- [x] Update get_monsters to add "System Reference Document 5.1"
- [x] Update other D&D 5e API methods
- [x] Write tests for SRD document name
- [x] Run all D&D 5e API tests
- [x] Commit changes

**Status:** COMPLETE (commit ab1a958)

## Task 5: Extract OrcBrew Book Name as Document

- [x] Update normalize_entity to extract document from option-pack or \_source_book
- [x] Write tests for OrcBrew document extraction
- [x] Write tests for option-pack override
- [x] Run all entity mapper tests
- [x] Commit changes

**Status:** COMPLETE (commits included in earlier work)

## Task 6: Add Document Filtering to Repositories

- [x] Update SpellRepository.search to support document filter
- [x] Update MonsterRepository.search to support document filter
- [x] Update EquipmentRepository.search to support document filter
- [x] Write test for SpellRepository document filtering
- [x] Write test for MonsterRepository document filtering
- [x] Write test for EquipmentRepository document filtering (weapons)
- [x] Write test for EquipmentRepository document filtering (armor)
- [x] Run all repository tests (79 tests pass)
- [x] Commit test additions

**Status:** COMPLETE (implementation in 088de43, tests in fb0ed03)

## Task 7: Add Document Filtering to MCP Tools

- [x] Add document parameter to lookup_spell
- [x] Add document parameter to lookup_creature
- [x] Add document parameter to lookup_weapon
- [x] Add document parameter to lookup_armor
- [x] Write tests for tool document filtering
- [x] Run all tool tests
- [x] Commit changes

**Status:** COMPLETE (commit 088de43)

## Task 8: Add Integration Tests for Document Filtering
- [x] Create tests/test_tools/test_document_filtering.py
- [x] Write test_end_to_end_document_filtering
- [x] Write test_document_in_tool_responses
- [x] Run integration tests (2 tests pass)
- [x] Commit integration tests

**Status:** COMPLETE (commit 9708991)

## Task 9: Update Documentation

- [ ] Create docs/document-filtering.md
- [ ] Document how document names are assigned per API
- [ ] Document how to use document filters in tools
- [ ] Document how to use document filters in repositories
- [ ] Document SRD content normalization
- [ ] Document performance considerations
- [ ] Commit documentation

**Status:** INCOMPLETE - Documentation missing

## Task 10: Run Full Test Suite and Fix Failures

- [ ] Run full test suite (just test)
- [ ] Fix any test failures
- [ ] Commit any fixes if needed

**Status:** MOSTLY COMPLETE - 468 tests pass, but linting issues exist

## Task 11: Run Live Tests

- [ ] Run live MCP tests (pytest -m live)
- [ ] Verify document names in live responses
- [ ] Fix any live test failures
- [ ] Commit any fixes

**Status:** INCOMPLETE - Not yet verified

## Task 12: Run Quality Checks

- [ ] Run type checking (just type-check)
- [ ] Run linting (just lint) - 40 PLC0415 errors to fix
- [ ] Run formatting (just format)
- [ ] Run all quality checks (just check)
- [ ] Commit formatting/linting fixes

**Status:** INCOMPLETE - 40 linting warnings exist
