# Proposal: Implement MCP Tools

## Overview
Implement the five core MCP tools that enable AI assistants to query D&D 5e game data through the LoreKeeper server, leveraging the existing API clients and cache infrastructure.

## Problem Statement
The LoreKeeper MCP server currently has:
- ✅ API clients implemented (Open5e v1, v2, and D&D 5e API)
- ✅ SQLite cache layer with TTL support
- ✅ FastMCP server framework configured
- ❌ No MCP tool implementations

Without the tool implementations, the server cannot expose any D&D 5e lookup functionality to AI assistants. The tools must bridge the gap between the MCP protocol and the underlying API clients.

## Proposed Solution
Implement five MCP tools as defined in `docs/tools.md`:

1. **`lookup_spell`**: Search and retrieve spell information using Open5e v2 API
2. **`lookup_creature`**: Search and retrieve monster/creature stat blocks using Open5e v1 API
3. **`lookup_character_option`**: Get character creation options (classes, races, backgrounds, feats) using Open5e APIs
4. **`lookup_equipment`**: Search for weapons, armor, and magic items using Open5e APIs
5. **`lookup_rule`**: Look up game rules, conditions, and reference information using D&D 5e API and Open5e v2 API

Each tool will:
- Accept typed parameters matching the tool specifications
- Use the appropriate API client(s) to fetch data
- Return structured, AI-friendly responses with source attribution
- Automatically leverage the existing cache layer for performance
- Handle errors gracefully with user-friendly messages

## Benefits
- **Complete MCP Server**: Enables the full D&D 5e lookup functionality promised in README
- **AI Assistant Integration**: Allows AI assistants to help players with character building, combat, and rules questions
- **Performance**: Leverages existing cache to minimize API calls
- **Type Safety**: FastMCP provides automatic parameter validation and schema generation
- **Maintainability**: Clear separation between tool handlers and API client logic

## Scope
**In Scope:**
- Implementation of 5 MCP tool handlers in `src/lorekeeper_mcp/tools/`
- Tool registration with FastMCP server
- Parameter parsing and validation
- Response formatting for AI consumption
- Error handling and user-friendly error messages
- Unit tests for each tool handler
- Integration tests with mocked API responses

**Out of Scope:**
- Modifications to existing API clients (already implemented)
- Changes to cache layer (already implemented)
- Advanced search features beyond tool specifications
- Custom data transformations or aggregations
- WebSocket or streaming responses
- Authentication/authorization

## Dependencies
- Existing API clients: `Open5eV1Client`, `Open5eV2Client`, `Dnd5eApiClient`
- Existing cache layer: `lorekeeper_mcp.cache.db`
- FastMCP framework for tool registration
- Tool specifications in `docs/tools.md`

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| API response schema changes | Use defensive parsing with try/except, log warnings for unexpected fields |
| Tool parameter complexity | Leverage FastMCP's automatic validation, provide clear error messages |
| Performance with large result sets | Enforce `limit` parameter, default to 20 results max |
| Inconsistent API responses | Normalize responses in API clients (already done), handle missing fields gracefully |

## Success Criteria
- [ ] All 5 tools are registered with FastMCP and visible in MCP client
- [ ] Each tool correctly queries the appropriate API client(s)
- [ ] Responses are formatted as structured data suitable for AI consumption
- [ ] All tools respect the `limit` parameter and return reasonable result sizes
- [ ] Error cases return user-friendly messages (not stack traces)
- [ ] Unit tests achieve >90% coverage for tool handlers
- [ ] Integration tests verify end-to-end functionality with mocked APIs
- [ ] Documentation in README accurately reflects implemented functionality

## Related Changes
- Depends on: `scaffold-project-setup` (provides FastMCP server, API clients, cache)
- Blocks: Future enhancements like advanced search, custom aggregations

## Validation
```bash
# Verify tools are registered
uv run python -c "from lorekeeper_mcp.server import mcp; print([t.name for t in mcp.tools])"

# Run tool tests
pytest tests/test_tools/ -v

# Test tool invocation (requires MCP client)
# Example: Call lookup_spell with name="fireball"

# Verify code quality
ruff check src/lorekeeper_mcp/tools/
uv format --check src/lorekeeper_mcp/tools/
```
