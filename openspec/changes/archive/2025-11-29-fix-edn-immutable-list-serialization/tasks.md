## 1. Fix ImmutableList Handling
- [x] 1.1 Update `_edn_to_python` method in `src/lorekeeper_mcp/parsers/orcbrew.py` to use `collections.abc.Sequence` instead of `list | tuple | set`
- [x] 1.2 Add string exclusion since `str` is also a `Sequence` but should not be converted to list
- [x] 1.3 Add `collections.abc.Set` handling for frozenset conversion (discovered during live testing)

## 2. Add Test Coverage
- [x] 2.1 Add unit test for parsing EDN with arrays (lists) to verify Python list conversion
- [x] 2.2 Add test to verify parsed result can be JSON serialized
- [x] 2.3 Add unit test for parsing EDN with sets to verify frozenset conversion
- [x] 2.4 Add test to verify sets can be JSON serialized

## 3. Verification
- [x] 3.1 Run existing orcbrew parser tests to ensure no regression
- [x] 3.2 Run live MegaPak import test if file is available (`lorekeeper import MegaPak_-_WotC_Books.orcbrew`)
