# Document List Command Specification

## Purpose
Enable users to discover and list all available source documents from the Open5e API via a CLI command, with filtering and formatting options.

## ADDED Requirements

### Requirement: List Documents CLI Command
The system SHALL provide a CLI command `lorekeeper-mcp list-documents` that fetches and displays all available source documents from the Open5e API.

#### Scenario:
When a user runs `lorekeeper-mcp list-documents`, the command should display all available documents with their metadata in a human-readable format.

**Acceptance Criteria:**
- `lorekeeper-mcp list-documents` command exists and is accessible
- Fetches documents from Open5e v2 API `/documents/` endpoint
- Displays document information in a formatted table by default
- Shows at minimum: document key, display name, publisher, and license information
- Returns proper exit codes (0 for success, 1 for errors)
- Displays all documents even if count is large (23+ documents available)
- Handles pagination if API response is paginated

### Requirement: JSON Output Format
The system SHALL support JSON output format for programmatic document discovery.

#### Scenario:
When a user runs `lorekeeper-mcp list-documents --format json`, the command should output structured JSON data suitable for parsing and processing.

**Acceptance Criteria:**
- `--format json` or `-f json` flag enables JSON output
- JSON includes all document metadata fields from API
- Output is valid JSON parseable by standard tools
- Each document entry includes: key, name, display_name, author, publisher, gamesystem, publication_date, description, licenses, permalink
- Can be piped to `jq` or other JSON processors

### Requirement: Filter Documents by Publisher
The system SHALL support filtering documents by publisher name.

#### Scenario:
When a user runs `lorekeeper-mcp list-documents --publisher "Kobold Press"`, only documents from that publisher should be displayed.

**Acceptance Criteria:**
- `--publisher <name>` or `-p <name>` flag filters documents
- Filter is case-insensitive partial match on publisher name
- Displays matching documents in same format as unfiltered list
- Returns empty list with appropriate message if no matches found
- Works with both table and JSON output formats

### Requirement: Filter Documents by Game System
The system SHALL support filtering documents by game system.

#### Scenario:
When a user runs `lorekeeper-mcp list-documents --game-system "5e"`, only documents for that game system should be displayed.

**Acceptance Criteria:**
- `--game-system <name>` or `-g <name>` flag filters documents
- Filter is case-insensitive partial match on game system name
- Displays matching documents in same format as unfiltered list
- Returns empty list with appropriate message if no matches found
- Works with both table and JSON output formats
- Example: "-g a5e" shows only Advanced 5th Edition documents

### Requirement: Help and Usage Information
The system SHALL provide clear help and usage information for the command.

#### Scenario:
When a user runs `lorekeeper-mcp list-documents --help`, they should see usage information.

**Acceptance Criteria:**
- `--help` or `-h` flag displays command usage
- Help text explains all available options
- Help text includes examples of common usage patterns
- Shows exit code 0 and doesn't perform the actual command

### Requirement: Error Handling and Messages
The system SHALL handle errors gracefully with informative messages.

#### Scenario:
When the Open5e API is unavailable or returns an error, the command should fail gracefully.

**Acceptance Criteria:**
- Network errors result in user-friendly error message
- API errors are caught and reported with context
- Command returns exit code 1 on any error
- Error messages explain what went wrong and potential solutions
- Examples: "Failed to fetch documents from Open5e API: Connection timeout (attempt 1/3)"

### Requirement: Performance and Caching
The system SHALL cache document list to reduce API calls.

#### Scenario:
When `list-documents` is called multiple times in succession, subsequent calls should be fast.

**Acceptance Criteria:**
- Document list is cached locally (expires after 7 days)
- Cache is stored in user's cache directory or database
- First call fetches from API, subsequent calls use cache
- Cache can be invalidated by `--refresh` or `--no-cache` flag
- Cache hits are noticeably faster than API calls

### Requirement: Output Formatting - Table View
The system SHALL format document lists as readable ASCII tables.

#### Scenario:
When documents are listed in table format (default), they should be easy to read and scan.

**Acceptance Criteria:**
- Default output format is a formatted ASCII table
- Columns include: Key, Display Name, Publisher, License
- Optional columns (if space allows): Author, Game System
- Column widths adapt to content and terminal width
- Long content is truncated with ellipsis (...) if needed
- All documents are visible without scrolling more than 30 lines (with headers)
- Table has clear header row and separator lines

### Requirement: Consistent Information Across Formats
The system SHALL provide consistent document information regardless of output format.

#### Scenario:
Whether a user views documents in table or JSON format, the underlying data should be identical.

**Acceptance Criteria:**
- Same document subset appears in table and JSON output for same filters
- All metadata fields present in JSON are represented in table (where space allows)
- Data values are identical between formats
- Key values are always included to enable configuration
