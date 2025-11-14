# Add Serve Command

## Why

The LoreKeeper CLI provides an `import` command but lacks a discoverable way to start the MCP server. Users must run `python -m lorekeeper_mcp` with no arguments, which is undocumented and unintuitive. This creates a poor user experience for those trying to start the server for the first time.

## What Changes

- Add `serve` CLI command to explicitly start the MCP server
- Update `__main__.py` to maintain backward compatibility (running `python -m lorekeeper_mcp` without args still works)
- Integrate serve command with existing global options (--db-path, --verbose)
- Add unit tests for the serve command and routing logic
- Update documentation (README.md and docs/cli-usage.md) to reference the new command

## Impact

**Affected specs:**
- `cli-interface` (modified capability - adds new serve command requirement)

**Affected code:**
- `src/lorekeeper_mcp/cli.py` - Add serve command function
- `src/lorekeeper_mcp/__main__.py` - Update routing logic for backward compatibility
- `tests/test_cli/test_serve.py` - New test file for serve command
- `tests/test_cli_basic.py` - Update backward compatibility tests
- `README.md` - Update "Running the Server" section
- `docs/cli-usage.md` - Add serve command documentation

## Additional Context

### Motivation
1. **Discoverability**: New users running `lorekeeper --help` cannot see how to start the server; the current approach relies on undocumented behavior (`python -m lorekeeper_mcp` with no args)
2. **Consistency**: Modern CLI tools provide explicit commands for all operations; having `import` but no `serve` creates an inconsistent interface
3. **Clarity**: `lorekeeper serve` is more intuitive than `python -m lorekeeper_mcp` or `uv run python -m lorekeeper_mcp`
4. **Documentation**: An explicit command is easier to document and search for in help text

## Scope
This change adds a new CLI command and modifies the package entry point behavior.

### In Scope
- Add `serve` CLI command to start the MCP server
- Update `__main__.py` to route `serve` command appropriately
- Maintain backward compatibility: running `python -m lorekeeper_mcp` with no args still starts the server
- Update CLI help text to include the new command

### Out of Scope
- Server configuration options (host, port, etc.) - FastMCP handles this
- Daemon mode or background process management
- Process monitoring or health checks
- Changes to server implementation itself

## Impact
- **Users**: Gain an explicit, documented command to start the server
- **Documentation**: README and CLI docs need minor updates to reference `lorekeeper serve`
- **Compatibility**: Fully backward compatible; existing usage patterns continue to work

## Dependencies
- None - uses existing Click CLI framework
- No new external dependencies required

## Related Work
- Existing CLI interface: `openspec/specs/cli-interface/spec.md`
- Server implementation: `src/lorekeeper_mcp/server.py`
- CLI entry point: `src/lorekeeper_mcp/cli.py`

## Risks
- **Minimal**: This is a straightforward additive change
- **Backward compatibility**: Carefully maintain existing `__main__.py` behavior for users who run `python -m lorekeeper_mcp` directly
