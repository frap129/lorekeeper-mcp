# Change Proposal: Implement Repository Pattern

## Overview
Implement complete API clients for all three D&D APIs (Open5e v1, Open5e v2, and D&D 5e API) with full endpoint coverage, and introduce a repository pattern layer to decouple tools and cache from direct API client usage.

## Motivation
Currently, the MCP tools are tightly coupled to API clients and cache implementations. This creates several issues:

1. **Incomplete API Coverage**: Clients only implement endpoints needed by current tools, missing many available endpoints
2. **Tight Coupling**: Tools directly instantiate and call API clients, making them difficult to test and modify
3. **Mixed Concerns**: Caching logic is embedded in the base client, violating separation of concerns
4. **Limited Extensibility**: Adding new data sources or changing caching strategies requires modifying multiple tool files
5. **Testing Complexity**: Unit testing tools requires mocking HTTP clients rather than simple data access interfaces

## Goals
1. **Complete API Client Coverage**: Implement every endpoint available in all three APIs
2. **Repository Pattern**: Introduce a repository layer that provides a clean data access interface
3. **Separation of Concerns**: Decouple data fetching, caching, and business logic
4. **Improved Testability**: Enable easy unit testing with mock repositories
5. **Future-Proofing**: Make it trivial to add new data sources or change caching strategies

## Success Criteria
- [ ] All Open5e v1 endpoints have corresponding client methods
- [ ] All Open5e v2 endpoints have corresponding client methods
- [ ] All D&D 5e API endpoints have corresponding client methods
- [ ] Repository interfaces defined for all entity types
- [ ] Repository implementations handle caching transparently
- [ ] All tools refactored to use repositories instead of direct client access
- [ ] All existing tests pass with repository implementation
- [ ] Repository pattern enables easy mock-based unit testing

## Impact Assessment

### Benefits
- **Maintainability**: Clear separation between data access and business logic
- **Testability**: Easier to write and maintain tests with repository mocks
- **Flexibility**: Swap data sources or caching strategies without touching tools
- **Completeness**: Access to all API data, not just what current tools need
- **Consistency**: Uniform data access patterns across all tools

### Risks
- **Migration Effort**: Requires refactoring all existing tools
- **Breaking Changes**: May require updates to tool interfaces
- **Performance**: Additional abstraction layer (mitigated by proper caching)

### Mitigation Strategies
- Implement repository pattern incrementally, starting with one tool
- Maintain backward compatibility during transition
- Comprehensive testing at each migration step
- Monitor performance and optimize caching strategies

## Alternatives Considered

### Alternative 1: Keep Current Architecture
**Pros**: No migration effort, no breaking changes
**Cons**: Continues to have tight coupling, incomplete API coverage, testing difficulties

**Decision**: Rejected - technical debt will compound over time

### Alternative 2: Direct Cache Abstraction (No Repository)
**Pros**: Simpler than full repository pattern
**Cons**: Still tightly couples tools to client implementation details

**Decision**: Rejected - doesn't fully address testability and flexibility concerns

### Alternative 3: Service Layer Pattern
**Pros**: Similar benefits to repository pattern
**Cons**: More complex, less focused on data access

**Decision**: Rejected - repository pattern is more focused and appropriate for this use case

## Dependencies
This change depends on:
- Existing API client implementations (base, Open5e v1, Open5e v2, DnD5e API)
- Current cache implementation (SQLite with entity caching)
- Pydantic models for entity types

This change is a prerequisite for:
- Future data source additions (e.g., local JSON files, other APIs)
- Advanced caching strategies (e.g., semantic search with Marqo)
- Tool composition and chaining

## References
- Current API client implementations: `src/lorekeeper_mcp/api_clients/`
- Current tool implementations: `src/lorekeeper_mcp/tools/`
- Repository Pattern: https://martinfowler.com/eaaCatalog/repository.html
- Open5e v1 API: https://api.open5e.com/v1/
- Open5e v2 API: https://api.open5e.com/v2/
- D&D 5e API: https://www.dnd5eapi.co/api/2014/
