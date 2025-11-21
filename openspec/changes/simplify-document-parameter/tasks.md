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

- [x] Update test `test_lookup_rule_with_document_keys` to use `documents` parameter
- [x] Run test to verify it fails
- [x] Update `lookup_rule` function signature: rename `document_keys` to `documents`
- [x] Update docstring examples and Args section
- [x] Update internal parameter handling
- [x] Run test to verify it passes
- [x] Run all rule_lookup tests
- [x] Commit

## Task 6: Update search_dnd_content Tool

- [x] Update 3 tests to use `documents` parameter
- [x] Run tests to verify they fail
- [x] Update `search_dnd_content` function signature: rename `document_keys` to `documents`
- [x] Update docstring examples and Args section
- [x] Update internal parameter handling (4 places)
- [x] Run tests to verify they pass
- [x] Run all search_dnd_content tests
- [x] Commit

## Task 7: Update Integration Tests

- [x] Update `test_document_filtering.py` to use `documents` parameter
- [x] Update `test_live_mcp.py` to use `documents` parameter
- [x] Run integration tests
- [x] Commit

## Task 8: Update list_documents Docstring

- [x] Update docstring references from `document_keys` to `documents`
- [x] Run list_documents tests
- [x] Commit

## Task 9: Update Documentation

- [x] Update `docs/document-filtering.md`
- [x] Update `docs/tools.md`
- [x] Update `README.md`
- [x] Commit

## Task 10: Run Full Test Suite and Quality Checks

- [x] Run all unit tests: `uv run pytest tests/ -v -m "not live"`
- [x] Run type checking: `just type-check`
- [x] Run linting: `just lint`
- [x] Run formatting: `just format`
- [x] Run all quality checks: `just check`
- [x] Commit any formatting fixes

## Validation Checklist

- [x] All 6 tools use `documents: list[str] | None = None` parameter
- [x] No tools have `document` or `document_keys` parameters
- [x] All tool docstrings updated with new parameter name and examples
- [x] All tests renamed and updated to use `documents`
- [x] Integration tests updated
- [x] list_documents docstring references updated
- [x] Documentation files updated
- [x] All unit tests pass
- [x] Type checking passes
- [x] Linting passes
- [x] No regressions in existing functionality
