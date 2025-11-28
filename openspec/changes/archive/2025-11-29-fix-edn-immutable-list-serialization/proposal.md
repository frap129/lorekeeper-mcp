## Why

The OrcBrew parser fails when importing files containing EDN arrays (lists) and sets because `edn_format.ImmutableList` and `frozenset` objects are not converted to Python lists. This causes JSON serialization to fail during cache storage with errors like: "Object of type ImmutableList is not JSON serializable" and "Object of type frozenset is not JSON serializable".

This is a bug in the `_edn_to_python` method which checks for `list | tuple | set` but `ImmutableList` is a `collections.abc.Sequence`, not one of those concrete types. Similarly, EDN sets are parsed as `frozenset` which also needs explicit handling.

## What Changes

- Fix `_edn_to_python` method to use `collections.abc.Sequence` protocol instead of concrete `list | tuple | set` types
- Add `collections.abc.Set` handling for frozenset conversion
- Add unit tests to verify EDN arrays and sets are converted to Python lists and can be JSON serialized

## Impact

- Affected specs: `orcbrew-parser` (restores existing "Handle EDN collections" scenario)
- Affected code: `src/lorekeeper_mcp/parsers/orcbrew.py:84-90`
- No breaking changes - this fix restores intended behavior defined in spec
