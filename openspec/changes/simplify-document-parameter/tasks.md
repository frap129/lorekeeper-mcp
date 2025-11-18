# Implementation Tasks

## Task 1: Update lookup_spell Tool

- [ ] Update test `test_lookup_spell_with_document_keys` to use `documents` parameter
- [ ] Run test to verify it fails
- [ ] Update `lookup_spell` function signature: remove `document` and `document_keys`, add `documents`
- [ ] Update docstring examples and Args section
- [ ] Update internal parameter handling
- [ ] Run test to verify it passes
- [ ] Run all spell_lookup tests
- [ ] Commit

## Task 2: Update lookup_creature Tool

- [ ] Update test `test_lookup_creature_with_document_keys` to use `documents` parameter
- [ ] Run test to verify it fails
- [ ] Update `lookup_creature` function signature: remove `document` and `document_keys`, add `documents`
- [ ] Update docstring examples and Args section
- [ ] Update internal parameter handling
- [ ] Run test to verify it passes
- [ ] Run all creature_lookup tests
- [ ] Commit

## Task 3: Update lookup_equipment Tool

- [ ] Update test `test_lookup_equipment_with_document_keys` to use `documents` parameter
- [ ] Run test to verify it fails
- [ ] Update `lookup_equipment` function signature: remove `document` and `document_keys`, add `documents`
- [ ] Update docstring Args section
- [ ] Update internal parameter handling (3 places: weapons, armor, magic items)
- [ ] Run test to verify it passes
- [ ] Run all equipment_lookup tests
- [ ] Commit

## Task 4: Update lookup_character_option Tool

- [ ] Update test `test_lookup_character_option_with_document_keys` to use `documents` parameter
- [ ] Run test to verify it fails
- [ ] Update `lookup_character_option` function signature: rename `document_keys` to `documents`
- [ ] Update docstring Args section
- [ ] Update internal parameter handling
- [ ] Run test to verify it passes
- [ ] Run all character_option_lookup tests
- [ ] Commit

## Task 5: Update lookup_rule Tool

- [ ] Update test `test_lookup_rule_with_document_keys` to use `documents` parameter
- [ ] Run test to verify it fails
- [ ] Update `lookup_rule` function signature: rename `document_keys` to `documents`
- [ ] Update docstring examples and Args section
- [ ] Update internal parameter handling
- [ ] Run test to verify it passes
- [ ] Run all rule_lookup tests
- [ ] Commit

## Task 6: Update search_dnd_content Tool

- [ ] Update 3 tests to use `documents` parameter
- [ ] Run tests to verify they fail
- [ ] Update `search_dnd_content` function signature: rename `document_keys` to `documents`
- [ ] Update docstring examples and Args section
- [ ] Update internal parameter handling (4 places)
- [ ] Run tests to verify they pass
- [ ] Run all search_dnd_content tests
- [ ] Commit

## Task 7: Update Integration Tests

- [ ] Update `test_document_filtering.py` to use `documents` parameter
- [ ] Update `test_live_mcp.py` to use `documents` parameter
- [ ] Run integration tests
- [ ] Commit

## Task 8: Update list_documents Docstring

- [ ] Update docstring references from `document_keys` to `documents`
- [ ] Run list_documents tests
- [ ] Commit

## Task 9: Update Documentation

- [ ] Update `docs/document-filtering.md`
- [ ] Update `docs/tools.md`
- [ ] Update `README.md`
- [ ] Commit

## Task 10: Run Full Test Suite and Quality Checks

- [ ] Run all unit tests: `uv run pytest tests/ -v -m "not live"`
- [ ] Run type checking: `just type-check`
- [ ] Run linting: `just lint`
- [ ] Run formatting: `just format`
- [ ] Run all quality checks: `just check`
- [ ] Commit any formatting fixes

## Validation Checklist

- [ ] All 6 tools use `documents: list[str] | None = None` parameter
- [ ] No tools have `document` or `document_keys` parameters
- [ ] All tool docstrings updated with new parameter name and examples
- [ ] All tests renamed and updated to use `documents`
- [ ] Integration tests updated
- [ ] list_documents docstring references updated
- [ ] Documentation files updated
- [ ] All unit tests pass
- [ ] Type checking passes
- [ ] Linting passes
- [ ] No regressions in existing functionality
