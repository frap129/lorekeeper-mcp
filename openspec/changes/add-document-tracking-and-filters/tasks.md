## 1. Entity Document Tracking
- [ ] 1.1 Review Open5e v2 and OrcBrew document semantics (document keys, names, publishers, and top-level book headings) and align on a normalized `document_key` / `document_name` shape for entities.
- [ ] 1.2 Update entity normalization logic (Open5e v2 clients and D&D 5e client normalizers) to attach document metadata to each entity where available (e.g., `document.key`, `document.name`, `document.publisher`).
- [ ] 1.3 Update OrcBrew parser normalization to treat the highest-level EDN book heading as the entity's source document, and propagate it into normalized entity metadata.
- [ ] 1.4 Extend the entity cache schema and helper functions so every cached entity can store and retrieve normalized document metadata alongside existing indexed fields.

## 2. Repository-Level Document Filtering
- [ ] 2.1 Extend repository interfaces (spell, creature, equipment, character option, rule) to accept optional document filter arguments without breaking existing call sites.
- [ ] 2.2 Implement repository-level filtering that can constrain queries to specific documents, SRD-only content, or OrcBrew-only content using the cached `document_key` / `source` metadata.
- [ ] 2.3 Ensure document filters interact correctly with existing enhanced filtering behavior (name, level, type, etc.) and do not reintroduce client-side over-fetching.

## 3. MCP Tool Surface and Configuration Integration
- [ ] 3.1 Decide how document filters are surfaced to tools (new optional parameters vs. relying solely on global configuration), ensuring backward-compatible MCP tool schemas.
- [ ] 3.2 Wire document filter options through MCP tools into repositories, honoring global document inclusion/exclusion configuration from `list-open5e-documents` where appropriate.
- [ ] 3.3 Confirm that tool responses continue to include source attribution that aligns with the new entity-level document metadata (e.g., document name, document key, and API/source).

## 4. Testing and Validation
- [ ] 4.1 Add unit tests for entity normalization to verify document metadata is correctly attached for Open5e v2, D&D 5e SRD, and OrcBrew entities.
- [ ] 4.2 Add repository tests that exercise document-based filtering in combination with existing filter parameters and limits.
- [ ] 4.3 Add MCP tool tests (or extend existing tests) that assert document filter behavior and verify source attribution fields reflect the correct document metadata.
- [ ] 4.4 Add targeted live or integration tests (flagged/marked appropriately) to validate document metadata and filtering against the real Open5e `/v2/documents/` semantics.
