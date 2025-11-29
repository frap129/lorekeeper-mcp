# Use XDG_DATA_HOME for Database Storage

## Why

The application currently stores the Milvus database at `~/.lorekeeper/milvus.db`, which does not follow the XDG Base Directory Specification. This violates Linux/Unix best practices and clutters the user's home directory. The XDG specification provides a standard way to organize application data files, making it easier for users to locate, backup, and manage application data.

## What Changes

- Change default database path from `~/.lorekeeper/milvus.db` to `$XDG_DATA_HOME/lorekeeper/milvus.db`
- Fall back to `~/.local/share/lorekeeper/milvus.db` when `XDG_DATA_HOME` is not set
- Maintain backward compatibility by checking for existing database at old location
- Keep existing override mechanisms (environment variable and CLI flag) working
- Update configuration, documentation, and tests to reflect new default path

## Impact

- **Affected specs:** `database-setup`
- **Affected code:**
  - `src/lorekeeper_mcp/config.py` - Update default path logic
  - `src/lorekeeper_mcp/cache/factory.py` - Update DEFAULT_MILVUS_DB_PATH constant
  - Tests that verify default paths
- **Affected docs:**
  - `README.md` - Update default path references
  - `docs/cache.md` - Update default path references
  - `docs/architecture.md` - Update config example
- **Migration:** Automatic - if database exists at old location and new location doesn't exist, continue using old location with informational log message. If both exist, prefer new XDG location and log warning about orphaned legacy database.
- **Breaking:** No - existing users with databases will continue to work; new installations use XDG path
