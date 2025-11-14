# Change Proposal: Remove Repository Parameter from MCP Tools

## Overview
Remove the `repository` parameter from all MCP tool function signatures. This parameter was erroneously added during the repository pattern implementation and exposes internal implementation details to external MCP clients.

## Motivation
The `implement-repository-pattern` change incorrectly added a `repository` parameter to all five MCP tool functions (`lookup_spell`, `lookup_creature`, `lookup_equipment`, `lookup_character_option`, `lookup_rule`). This creates several problems:

1. **Leaky Abstraction**: External MCP clients (AI assistants) see an internal implementation detail they shouldn't need to know about
2. **Poor UX**: AI assistants must understand repository objects when they should only care about domain parameters (spell name, level, etc.)
3. **API Pollution**: The MCP tool interface is cluttered with parameters that serve no purpose for external callers
4. **Violates Spec**: The `mcp-tools` specification defines tool parameters without any `repository` field
5. **Confusing Documentation**: Tool docstrings must explain a parameter that users should never touch

The repository parameter was intended for dependency injection during testing, but exposing it as a public API parameter was a design mistake.

## Goals
1. **Clean MCP Interface**: Remove `repository` parameter from all tool function signatures
2. **Maintain Testability**: Preserve ability to inject mock repositories for unit testing
3. **Update Specs**: Remove any spec requirements that added the repository parameter
4. **Backward Compatibility**: Tools continue to work identically for external callers (they never used this parameter anyway)

## Success Criteria
- [ ] All 5 tools (`lookup_spell`, `lookup_creature`, `lookup_equipment`, `lookup_character_option`, `lookup_rule`) have `repository` parameter removed from signatures
- [ ] MCP tool interface no longer exposes `repository` field to clients
- [ ] Unit tests can still inject mock repositories for testing
- [ ] All existing tests pass (54 tool tests + integration tests)
- [ ] `implement-repository-pattern` specs updated to remove repository parameter requirements
- [ ] Tool docstrings updated to remove repository parameter documentation

## Impact Assessment

### Benefits
- **Cleaner API**: MCP clients see only domain-relevant parameters
- **Better Documentation**: Tool signatures are self-documenting without internal details
- **Spec Compliance**: Tools match their specification exactly
- **Less Confusion**: New developers don't see mysterious parameters
- **Better Encapsulation**: Implementation details stay internal

### Risks
- **Test Refactoring**: Unit tests need new mechanism for repository injection
- **Breaking Internal Changes**: If any internal code uses `repository` parameter (unlikely, as tools are leaf nodes)

### Mitigation Strategies
- Use module-level context variables or factory overrides for test injection
- Comprehensive testing after refactor to ensure no regressions
- Keep changes minimal and focused on parameter removal

## Alternatives Considered

### Alternative 1: Keep Repository Parameter but Mark as Internal
**Pros**: Less refactoring needed
**Cons**: FastMCP has no mechanism to hide parameters; still visible to clients

**Decision**: Rejected - doesn't solve the core problem

### Alternative 2: Wrap Functions with Separate MCP-Facing Functions
**Pros**: Could keep both internal and external signatures
**Cons**: Code duplication, maintenance burden, overly complex

**Decision**: Rejected - unnecessarily complex solution

### Alternative 3: Use Dependency Injection Container
**Pros**: Professional DI pattern, very flexible
**Cons**: Overkill for this use case, adds significant complexity

**Decision**: Rejected - too much complexity for a small project

## Proposed Solution
Use module-level context variable for test injection:

```python
# Global context for test injection
_repository_context: dict[str, Any] = {}

def _get_spell_repository() -> SpellRepository:
    """Get spell repository, respecting test context."""
    if "spell_repository" in _repository_context:
        return _repository_context["spell_repository"]
    return RepositoryFactory.create_spell_repository()

async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    # ... other domain parameters
    limit: int = 20,
    # NO repository parameter!
) -> list[dict[str, Any]]:
    """Search and retrieve D&D 5e spells."""
    repository = _get_spell_repository()  # Internal
    # ... rest of implementation
```

For testing:
```python
# In test setup
from lorekeeper_mcp.tools import spell_lookup
spell_lookup._repository_context["spell_repository"] = mock_repo

# Run test
result = await lookup_spell(name="Fireball")

# In test teardown
spell_lookup._repository_context.clear()
```

## Dependencies
This change depends on:
- Completed repository pattern implementation (`implement-repository-pattern` change)

This change is a prerequisite for:
- Future MCP tool additions (they'll follow the corrected pattern)

## References
- Current tool implementations: `src/lorekeeper_mcp/tools/`
- MCP Tools Spec: `openspec/specs/mcp-tools/spec.md`
- Repository Pattern Implementation: `openspec/changes/implement-repository-pattern/`
- FastMCP Documentation: https://github.com/jlowin/fastmcp
