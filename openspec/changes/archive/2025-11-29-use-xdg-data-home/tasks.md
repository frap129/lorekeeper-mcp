# Implementation Tasks

## 1. Update Configuration
- [x] 1.1 Add XDG_DATA_HOME detection logic to config.py
- [x] 1.2 Update default milvus_db_path to use XDG path with fallback
- [x] 1.3 Add backward compatibility check for existing database at old location
- [x] 1.4 Add logging when using legacy path for backward compatibility
- [x] 1.5 Add warning log when both legacy and XDG locations have databases

## 2. Update Cache Factory
- [x] 2.1 Update DEFAULT_MILVUS_DB_PATH in cache/factory.py to use XDG path
- [x] 2.2 Consider importing path logic from config.py to avoid duplication

## 3. Update Tests
- [x] 3.1 Update test_config.py to verify XDG_DATA_HOME path resolution
- [x] 3.2 Update test_config_milvus.py to test fallback behavior
- [x] 3.3 Add test for backward compatibility (old path exists, new doesn't)
- [x] 3.4 Add test for both locations exist (should prefer XDG, warn about legacy)
- [x] 3.5 Update tests that hardcode ~/.lorekeeper paths

## 4. Update Documentation
- [x] 4.1 Update README.md default path references (lines ~121, ~193)
- [x] 4.2 Update docs/cache.md default path references
- [x] 4.3 Update docs/architecture.md config example

## 5. Update Specs
- [x] 5.1 Update openspec/specs/database-setup/spec.md to use XDG paths
- [x] 5.2 Update openspec/specs/entity-cache/spec.md to use XDG paths

## 6. Validation
- [x] 6.1 Run all tests and ensure they pass
- [x] 6.2 Test manual scenarios:
  - [x] Fresh install (no existing database)
  - [x] Existing database at old location only
  - [x] Existing database at XDG location only
  - [x] Databases exist at both locations
  - [x] XDG_DATA_HOME set
  - [x] XDG_DATA_HOME not set
  - [x] Environment variable override
  - [x] CLI flag override
- [x] 6.3 Verify no breaking changes for existing users
