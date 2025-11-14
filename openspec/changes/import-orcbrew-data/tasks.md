# Tasks: Import OrcBrew Data

## Prerequisites
- [ ] Review `entity-cache` spec to understand cache interface
- [ ] Review .orcbrew file format (MegaPak_-_WotC_Books.orcbrew)
- [ ] Verify `edn-format` and `click` libraries are compatible

## Phase 1: Dependencies and Setup
- [x] Add `edn-format` to pyproject.toml dependencies
- [x] Add `click` to pyproject.toml dependencies
- [x] Run `uv sync` to install new dependencies
- [x] Verify imports work: `import edn_format`, `import click`

## Phase 2: Core Parser Implementation
- [x] Create `src/lorekeeper_mcp/parsers/__init__.py`
- [x] Create `src/lorekeeper_mcp/parsers/orcbrew.py` with `OrcBrewParser` class
- [x] Implement `parse_file()` method to read and parse EDN
- [x] Handle EDN data type conversions (keywords to strings, etc.)
- [x] Add error handling for malformed EDN files

## Phase 3: Entity Mapping
- [ ] Create `src/lorekeeper_mcp/parsers/entity_mapper.py`
- [ ] Define `ORCBREW_TO_LOREKEEPER` mapping dictionary
- [ ] Implement `map_entity_type()` function
- [ ] Implement `normalize_entity()` function
- [ ] Handle field transformations (`:key` → `slug`, `:option-pack` → `source`)
- [ ] Extract indexed fields based on entity type
- [ ] Add slug generation for entities missing `:key`

## Phase 4: CLI Framework
- [ ] Create `src/lorekeeper_mcp/cli.py` with Click decorators
- [ ] Implement main `cli()` group with --version and --help
- [ ] Add global option: `--db-path` for custom database location
- [ ] Add global option: `-v/--verbose` for detailed logging
- [ ] Update `src/lorekeeper_mcp/__main__.py` to support CLI mode
- [ ] Add CLI entry point in pyproject.toml: `[project.scripts]` section

## Phase 5: Import Command
- [ ] Implement `import` command in cli.py
- [ ] Add command option: `--dry-run` for parse-only mode
- [ ] Add command option: `--force` to overwrite existing data
- [ ] Integrate parser to read .orcbrew file
- [ ] Call entity mapper to normalize entities
- [ ] Use `bulk_cache_entities()` to store in cache
- [ ] Handle file not found errors gracefully
- [ ] Handle parse errors gracefully

## Phase 6: Progress Reporting and Logging
- [ ] Configure logging with INFO and DEBUG levels
- [ ] Log file parsing start and completion
- [ ] Log entity type processing with counts
- [ ] Report skipped entities with reasons
- [ ] Display final summary (total imported, skipped, time)
- [ ] Add verbose mode logging for individual entities

## Phase 7: Testing - Unit Tests
- [ ] Create `tests/test_parsers/__init__.py`
- [ ] Create `tests/test_parsers/test_orcbrew.py`
  - [ ] Test parsing valid EDN file
  - [ ] Test handling malformed EDN
  - [ ] Test entity extraction
  - [ ] Test missing required fields
- [ ] Create `tests/test_parsers/test_entity_mapper.py`
  - [ ] Test entity type mapping for all known types
  - [ ] Test field transformations
  - [ ] Test indexed field extraction
  - [ ] Test slug generation
- [ ] Create `tests/test_cli.py`
  - [ ] Test CLI invocation with Click's CliRunner
  - [ ] Test --help output
  - [ ] Test --version output
  - [ ] Test import command with missing file
  - [ ] Test --dry-run option

## Phase 8: Testing - Integration Tests
- [ ] Create sample .orcbrew file in `tests/fixtures/sample.orcbrew`
  - [ ] Include 2-3 spells
  - [ ] Include 1-2 monsters
  - [ ] Include 1 class with subclass
- [ ] Create `tests/test_cli/test_import_integration.py`
  - [ ] Test end-to-end import of sample file
  - [ ] Verify entities in cache after import
  - [ ] Test import with existing data (update scenario)
  - [ ] Test --force flag behavior
- [ ] Create performance test with larger dataset
  - [ ] Measure import time for 1000+ entities
  - [ ] Verify performance < 30 seconds for MegaPak

## Phase 9: Cache Enhancements
- [ ] Review `bulk_cache_entities()` for batch support
- [ ] Add validation for required fields in cache layer
- [ ] Ensure upsert behavior (insert or update on conflict)
- [ ] Add source API tracking ("orcbrew" value)
- [ ] Test batch import with 500+ entities

## Phase 10: Documentation
- [ ] Add docstrings to all parser functions and classes
- [ ] Add docstrings to CLI commands with usage examples
- [ ] Create user documentation in `docs/cli-usage.md`
  - [ ] Installation instructions
  - [ ] Basic usage examples
  - [ ] Common use cases
  - [ ] Troubleshooting section
- [ ] Update project README.md with CLI usage
- [ ] Add inline comments for complex parsing logic

## Phase 11: Error Handling and Edge Cases
- [ ] Test with empty .orcbrew file
- [ ] Test with file containing only unsupported entity types
- [ ] Test with entities missing all optional fields
- [ ] Test with very large file (> 50K lines)
- [ ] Test with Unicode characters in entity names
- [ ] Test concurrent imports (if applicable)

## Phase 12: Code Quality
- [ ] Run `just lint` and fix all issues
- [ ] Run `just format` to format code
- [ ] Run `just type-check` and fix type errors
- [ ] Ensure all tests pass: `just test`
- [ ] Verify test coverage > 90% for new code

## Phase 13: Live Testing
- [ ] Import MegaPak_-_WotC_Books.orcbrew into test database
- [ ] Verify entity counts match expectations
- [ ] Spot-check 5-10 entities for data accuracy
- [ ] Query imported entities via MCP tools
- [ ] Test search functionality with imported data
- [ ] Measure and document import performance

## Phase 14: Final Review
- [ ] Review all specs are satisfied
- [ ] Check all scenarios have corresponding tests
- [ ] Verify error messages are user-friendly
- [ ] Ensure logging is appropriate (not too verbose, not too quiet)
- [ ] Update CHANGELOG with new CLI command
- [ ] Tag release or create PR

## Dependencies Between Tasks
- Phase 2 (Parser) must complete before Phase 3 (Mapper)
- Phase 4 (CLI Framework) can be parallel with Phase 2-3
- Phase 5 (Import Command) depends on Phases 2, 3, and 4
- Phase 7-8 (Testing) can begin after Phase 5
- Phase 9 (Cache) can be parallel with Phases 2-5
- Phase 12-14 (Quality/Review) must be last

## Parallelizable Work
These tasks can be done concurrently:
- Phase 2 (Parser) + Phase 4 (CLI Framework)
- Phase 3 (Mapper) + Phase 9 (Cache enhancements)
- Phase 7 (Unit Tests) while Phase 6 (Logging) is in progress
- Documentation (Phase 10) while testing (Phases 7-8) is in progress
