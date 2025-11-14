# Tasks: Import OrcBrew Data

## Prerequisites
- [x] Review `entity-cache` spec to understand cache interface
- [x] Review .orcbrew file format (MegaPak_-_WotC_Books.orcbrew)
- [x] Verify `edn-format` and `click` libraries are compatible

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
- [x] Create `src/lorekeeper_mcp/parsers/entity_mapper.py`
- [x] Define `ORCBREW_TO_LOREKEEPER` mapping dictionary
- [x] Implement `map_entity_type()` function
- [x] Implement `normalize_entity()` function
- [x] Handle field transformations (`:key` → `slug`, `:option-pack` → `source`)
- [x] Extract indexed fields based on entity type
- [x] Add slug generation for entities missing `:key`

## Phase 4: CLI Framework
- [x] Create `src/lorekeeper_mcp/cli.py` with Click decorators
- [x] Implement main `cli()` group with --version and --help
- [x] Add global option: `--db-path` for custom database location
- [x] Add global option: `-v/--verbose` for detailed logging
- [x] Update `src/lorekeeper_mcp/__main__.py` to support CLI mode
- [x] Add CLI entry point in pyproject.toml: `[project.scripts]` section

## Phase 5: Import Command
- [x] Implement `import` command in cli.py
- [x] Add command option: `--dry-run` for parse-only mode
- [x] Add command option: `--force` to overwrite existing data
- [x] Integrate parser to read .orcbrew file
- [x] Call entity mapper to normalize entities
- [x] Use `bulk_cache_entities()` to store in cache
- [x] Handle file not found errors gracefully
- [x] Handle parse errors gracefully

## Phase 6: Progress Reporting and Logging
- [x] Configure logging with INFO and DEBUG levels
- [x] Log file parsing start and completion
- [x] Log entity type processing with counts
- [x] Report skipped entities with reasons
- [x] Display final summary (total imported, skipped, time)
- [x] Add verbose mode logging for individual entities

## Phase 7: Testing - Unit Tests
- [x] Create `tests/test_parsers/__init__.py`
- [x] Create `tests/test_parsers/test_orcbrew.py`
  - [x] Test parsing valid EDN file
  - [x] Test handling malformed EDN
  - [x] Test entity extraction
  - [x] Test missing required fields
- [x] Create `tests/test_parsers/test_entity_mapper.py`
  - [x] Test entity type mapping for all known types
  - [x] Test field transformations
  - [x] Test indexed field extraction
  - [x] Test slug generation
- [x] Create `tests/test_cli.py`
  - [x] Test CLI invocation with Click's CliRunner
  - [x] Test --help output
  - [x] Test --version output
  - [x] Test import command with missing file
  - [x] Test --dry-run option

## Phase 8: Testing - Integration Tests
- [x] Create sample .orcbrew file in `tests/fixtures/sample.orcbrew`
  - [x] Include 2-3 spells
  - [x] Include 1-2 monsters
  - [x] Include 1 class with subclass
- [x] Create `tests/test_cli/test_import_integration.py`
  - [x] Test end-to-end import of sample file
  - [x] Verify entities in cache after import
  - [x] Test import with existing data (update scenario)
  - [x] Test --force flag behavior
- [x] Create performance test with larger dataset
  - [x] Measure import time for 1000+ entities
  - [x] Verify performance < 30 seconds for MegaPak

## Phase 9: Cache Enhancements
- [x] Review `bulk_cache_entities()` for batch support
- [x] Add validation for required fields in cache layer
- [x] Ensure upsert behavior (insert or update on conflict)
- [x] Add source API tracking ("orcbrew" value)
- [x] Test batch import with 500+ entities

## Phase 10: Documentation
- [x] Add docstrings to all parser functions and classes
- [x] Add docstrings to CLI commands with usage examples
- [x] Create user documentation in `docs/cli-usage.md`
  - [x] Installation instructions
  - [x] Basic usage examples
  - [x] Common use cases
  - [x] Troubleshooting section
- [x] Update project README.md with CLI usage
- [x] Add inline comments for complex parsing logic

## Phase 11: Error Handling and Edge Cases
- [x] Test with empty .orcbrew file
- [x] Test with file containing only unsupported entity types
- [x] Test with entities missing all optional fields
- [x] Test with very large file (> 50K lines)
- [x] Test with Unicode characters in entity names
- [x] Test concurrent imports (if applicable)

## Phase 12: Code Quality
- [x] Run `just lint` and fix all issues
- [x] Run `just format` to format code
- [x] Run `just type-check` and fix type errors
- [x] Ensure all tests pass: `just test`
- [x] Verify test coverage > 90% for new code

## Phase 13: Live Testing
- [x] Import MegaPak_-_WotC_Books.orcbrew into test database (optional - skipped if file not available)
- [x] Verify entity counts match expectations
- [x] Spot-check 5-10 entities for data accuracy
- [x] Query imported entities via MCP tools
- [x] Test search functionality with imported data
- [x] Measure and document import performance

## Phase 14: Final Review
- [x] Review all specs are satisfied
- [x] Check all scenarios have corresponding tests
- [x] Verify error messages are user-friendly
- [x] Ensure logging is appropriate (not too verbose, not too quiet)
- [x] Update CHANGELOG with new CLI command
- [x] Tag release or create PR

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
