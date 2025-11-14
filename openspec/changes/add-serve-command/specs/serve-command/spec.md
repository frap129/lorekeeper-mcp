# serve-command Specification Delta

## ADDED Requirements

### Requirement: Serve Command
The CLI SHALL provide a `serve` command that starts the MCP server.

#### Scenario: User starts server with serve command
**Given** the lorekeeper package is installed
**When** the user runs `lorekeeper serve`
**Then** the MCP server starts and listens for connections
**And** the server lifecycle (startup, ready, shutdown) follows FastMCP conventions

#### Scenario: User requests help for serve command
**Given** the lorekeeper package is installed
**When** the user runs `lorekeeper serve --help`
**Then** the CLI displays help text describing the serve command
**And** help text indicates this command starts the MCP server

#### Scenario: User runs serve with verbose logging
**Given** the lorekeeper package is installed
**When** the user runs `lorekeeper -v serve`
**Then** the MCP server starts with DEBUG log level
**And** server initialization details are logged to stderr

---

### Requirement: Backward Compatibility
The package SHALL maintain existing behavior when invoked without CLI commands.

#### Scenario: User runs module directly without arguments
**Given** the lorekeeper package is installed
**When** the user runs `python -m lorekeeper_mcp` with no arguments
**Then** the MCP server starts (backward compatible behavior)
**And** server operates identically to `lorekeeper serve`

#### Scenario: User runs module with CLI arguments
**Given** the lorekeeper package is installed
**When** the user runs `python -m lorekeeper_mcp import file.orcbrew`
**Then** the CLI processes the import command
**And** behavior is identical to `lorekeeper import file.orcbrew`

---

### Requirement: Help Text Integration
The main CLI help SHALL list the serve command alongside other commands.

#### Scenario: User views main CLI help
**Given** the lorekeeper package is installed
**When** the user runs `lorekeeper --help`
**Then** the help text lists available commands including:
- `import` - Import D&D content from OrcBrew files
- `serve` - Start the MCP server
**And** both commands are presented with equal visibility

---

### Requirement: Server Lifecycle Integration
The serve command SHALL properly initialize and manage the MCP server lifecycle.

#### Scenario: Server initializes database on startup
**Given** the lorekeeper package is installed
**And** no database exists at the configured path
**When** the user runs `lorekeeper serve`
**Then** the server initializes the database during lifespan startup
**And** the server becomes ready to handle requests

#### Scenario: Server respects database path configuration
**Given** the user wants to use a custom database path
**When** the user runs `lorekeeper --db-path /custom/path.db serve`
**Then** the server uses `/custom/path.db` for all database operations
**And** the custom path is respected by the lifespan initialization

---

### Requirement: Error Handling
The serve command SHALL provide clear error messages when startup fails.

#### Scenario: Server startup fails due to configuration error
**Given** the lorekeeper package is installed
**And** an invalid configuration exists (e.g., read-only database directory)
**When** the user runs `lorekeeper serve`
**Then** the CLI displays a clear error message describing the failure
**And** exits with a non-zero status code

#### Scenario: User interrupts server with Ctrl+C
**Given** the MCP server is running via `lorekeeper serve`
**When** the user presses Ctrl+C
**Then** the server shuts down gracefully
**And** the lifespan cleanup executes
**And** the process exits with status code 0
