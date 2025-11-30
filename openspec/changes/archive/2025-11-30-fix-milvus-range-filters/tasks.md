## 1. Implementation

- [x] 1.1 Update `_build_filter_expression()` in `milvus.py` to detect `_min`/`_max` suffixes and convert to range operators (`>=`/`<=`)
- [x] 1.2 Add unit tests for range filter expression building
- [x] 1.3 Add integration test for `semantic_search` with range filters

## 2. Validation

- [x] 2.1 Run existing test suite to ensure no regressions
- [x] 2.2 Run live tests to verify fix works end-to-end
- [x] 2.3 Manual verification: `search_spell(search="fire", level_min=4)` returns expected results
