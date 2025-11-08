# cache-builder-progress Specification

**Spec ID**: `cache-builder-progress`
**Change**: `implement-build-cache-flag`
**Status**: Proposed

## Purpose

Provide clear, actionable progress reporting during cache build operations to give visibility into fetch/index status, errors, and completion.

## ADDED Requirements

### Requirement: Progress logging for each entity type

The system SHALL log progress as each entity type is fetched and indexed.

**Rationale**: Long-running cache builds need visibility; users should know the process is working and see which entity types are being processed.

#### Scenario: Log progress during fetch phase

**Given** cache building starts
**When** each entity type is being fetched
**Then** a log message is emitted: `"[INFO] Fetching {entity_type} from {client_name}..."`
**And** when fetch completes: `"[INFO] Fetched {count} {entity_type}"`

**Example Output**:
```
[INFO] Fetching spells from Open5e v2...
[INFO] Fetched 520 spells
```

#### Scenario: Log progress during index phase

**Given** entities have been fetched
**When** indexing to Marqo begins
**Then** a log message is emitted: `"[INFO] Indexing {count} {entity_type} to Marqo..."`
**And** when indexing completes: `"[INFO] ✓ Indexed {count} {entity_type}"`

**Example Output**:
```
[INFO] Indexing 520 spells to Marqo...
[INFO] ✓ Indexed 520 spells
```

---

### Requirement: Build summary report

The system SHALL log a comprehensive summary after cache build completes.

**Rationale**: Summary provides at-a-glance view of what was built, time taken, and any failures.

#### Scenario: Log successful build summary

**Given** cache build completes successfully
**When** all entity types have been processed
**Then** a summary log is emitted containing:
- Total entity count across all types
- Number of entity types successfully built
- Total build duration in seconds
- Timestamp of completion

**Example Output**:
```
[INFO] ==========================================
[INFO] Cache Build Complete
[INFO] ==========================================
[INFO] Total Entities: 3427
[INFO] Entity Types Built: 11/11
[INFO] Build Duration: 147.3s
[INFO] Status: SUCCESS
[INFO] ==========================================
```

#### Scenario: Log partial build summary

**Given** some entity types failed to build
**And** at least one entity type succeeded
**When** cache build completes
**Then** a summary log is emitted containing:
- Total entities indexed (successful only)
- Number of successful entity types vs total
- List of failed entity types
- Warning about partial build

**Example Output**:
```
[WARN] ==========================================
[WARN] Cache Build Completed with Warnings
[WARN] ==========================================
[INFO] Total Entities: 2384 (partial)
[WARN] Entity Types Built: 9/11
[WARN] Failed Types: monsters, rules
[INFO] Build Duration: 98.2s
[WARN] Status: PARTIAL SUCCESS
[WARN] ==========================================
```

---

### Requirement: Error logging with context

The system SHALL log errors with sufficient context for debugging.

**Rationale**: When builds fail, users need actionable error messages to diagnose and fix issues.

#### Scenario: Log fetch error with context

**Given** fetching monsters fails with a network timeout
**When** the error occurs
**Then** an error log is emitted: `"[ERROR] Failed to fetch {entity_type} from {client}: {error_message}"`
**And** a stack trace is included if debug logging is enabled

**Example Output**:
```
[ERROR] Failed to fetch monsters from Open5e v1: Connection timeout after 30s
```

#### Scenario: Log indexing error with context

**Given** indexing fails due to Marqo unavailable
**When** the error occurs
**Then** an error log is emitted: `"[ERROR] Failed to index {entity_type}: {error_message}"`
**And** suggestion to check Marqo service is included

**Example Output**:
```
[ERROR] Failed to index spells: Marqo connection refused
[ERROR] Ensure Marqo is running at http://localhost:8882
```

---

### Requirement: Start and end markers

The system SHALL log clear start and end markers for the cache build process.

**Rationale**: Helps identify build boundaries in logs, especially when multiple builds occur consecutively.

#### Scenario: Log build start

**Given** cache builder starts
**When** initialization completes
**Then** a start marker is logged with timestamp
**And** configuration summary is included (Marqo URL, batch size, etc.)

**Example Output**:
```
[INFO] ==========================================
[INFO] Starting Cache Build
[INFO] ==========================================
[INFO] Marqo URL: http://localhost:8882
[INFO] Batch Size: 100
[INFO] Clients: Open5eV2, Open5eV1, DnD5eAPI
[INFO] Time: 2025-11-08 14:32:15 UTC
[INFO] ==========================================
```

#### Scenario: Log build end

**Given** cache build completes (success or failure)
**When** the process exits
**Then** an end marker is logged with final status

**Example Output**:
```
[INFO] ==========================================
[INFO] Cache Build Ended
[INFO] Exit Code: 0
[INFO] ==========================================
```

---

### Requirement: Per-entity-type statistics

The system SHALL track and log statistics for each entity type built.

**Rationale**: Detailed breakdown helps identify slow or problematic entity types.

#### Scenario: Log entity type build statistics

**Given** cache build completes
**When** summary is generated
**Then** statistics per entity type are logged in a table format including:
- Entity type name
- Count of entities fetched
- Fetch duration
- Index duration
- Status (success/failed)

**Example Output**:
```
[INFO] Entity Type Statistics:
[INFO] ┌──────────────┬───────┬────────┬────────┬─────────┐
[INFO] │ Type         │ Count │ Fetch  │ Index  │ Status  │
[INFO] ├──────────────┼───────┼────────┼────────┼─────────┤
[INFO] │ spells       │   520 │  8.2s  │  3.1s  │ SUCCESS │
[INFO] │ monsters     │  1043 │ 19.8s  │  6.4s  │ SUCCESS │
[INFO] │ weapons      │    50 │  2.1s  │  0.8s  │ SUCCESS │
[INFO] │ armor        │    30 │  1.9s  │  0.7s  │ SUCCESS │
[INFO] │ classes      │    13 │  1.8s  │  0.5s  │ SUCCESS │
[INFO] │ races        │     9 │  1.2s  │  0.4s  │ SUCCESS │
[INFO] │ backgrounds  │    13 │  1.7s  │  0.5s  │ SUCCESS │
[INFO] │ feats        │    50 │  2.8s  │  0.9s  │ SUCCESS │
[INFO] │ conditions   │    15 │  1.5s  │  0.6s  │ SUCCESS │
[INFO] │ rules        │    20 │  2.3s  │  0.7s  │ SUCCESS │
[INFO] │ rule_sections│   100 │  4.9s  │  1.8s  │ SUCCESS │
[INFO] └──────────────┴───────┴────────┴────────┴─────────┘
```

---

## MODIFIED Requirements

None - progress logging is a new feature.

---

## REMOVED Requirements

None - no existing functionality is removed.

---

## Cross-References

- Related Spec: `cache-builder-cli` - CLI interface that users interact with
- Related Spec: `cache-builder-orchestration` - Orchestration logic that generates progress events

---

## Notes

- All logs use standard Python `logging` module with INFO, WARN, ERROR levels
- Log format includes timestamp, level, and message (configured in logging setup)
- Progress statistics use simple string formatting (no external table libraries)
- Build duration measured using `time.perf_counter()` for high precision
- Entity counts are actual counts from API responses, not estimates
