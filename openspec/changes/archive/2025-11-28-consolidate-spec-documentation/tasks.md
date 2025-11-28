## 1. Analysis and Planning

- [x] 1.1 Review all 26 specs and document exact overlap/duplication
- [x] 1.2 Document merge strategy for each consolidation group
- [x] 1.3 Identify requirements that may conflict between specs

## 2. API Client Spec Consolidation

### 2.1 Open5e v1 Client
- [x] 2.1.1 Merge `open5e-v1-client/spec.md` into `complete-open5e-v1-client/spec.md`
- [x] 2.1.2 Update purpose section with clear description
- [x] 2.1.3 Remove duplicate requirements
- [x] 2.1.4 Delete `open5e-v1-client` directory

### 2.2 Open5e v2 Client
- [x] 2.2.1 Merge `open5e-v2-client/spec.md` into `complete-open5e-v2-client/spec.md`
- [x] 2.2.2 Update purpose section with clear description
- [x] 2.2.3 Remove duplicate requirements
- [x] 2.2.4 Delete `open5e-v2-client` directory

## 3. Search/Filter Spec Consolidation

- [x] 3.1 Merge `filter-enhancement/spec.md` into `enhanced-search/spec.md`
- [x] 3.2 Merge `search-parameter-correction/spec.md` into `enhanced-search/spec.md`
- [x] 3.3 Merge `api-parameter-usage/spec.md` into `enhanced-search/spec.md`
- [x] 3.4 Update purpose section for enhanced-search
- [x] 3.5 Remove duplicate requirements
- [x] 3.6 Delete merged spec directories

## 4. Narrow Fix Specs Absorption

- [x] 4.1 Absorb `spell-school-filtering` into `complete-open5e-v2-client`
- [x] 4.2 Absorb `weapon-model-correction` into `complete-open5e-v2-client`
- [x] 4.3 Delete absorbed spec directories

## 5. Repository/MCP Spec Consolidation

- [x] 5.1 Absorb `tool-repository-migration` into `repository-infrastructure`
- [x] 5.2 Absorb `mcp-tool-cleanup` into `mcp-tools`
- [x] 5.3 Delete absorbed spec directories

## 6. Purpose Section Updates

Update TBD purpose sections for the 17 remaining specs (after consolidation):
- [x] 6.1 `base-client`
- [x] 6.2 `canonical-models`
- [x] 6.3 `cli-interface`
- [x] 6.4 `code-quality`
- [x] 6.5 `complete-open5e-v1-client`
- [x] 6.6 `complete-open5e-v2-client`
- [x] 6.7 `database-setup`
- [x] 6.8 `dev-environment`
- [x] 6.9 `enhanced-search`
- [x] 6.10 `entity-cache`
- [x] 6.11 `mcp-live-testing`
- [x] 6.12 `mcp-tools`
- [x] 6.13 `orcbrew-parser`
- [x] 6.14 `project-structure`
- [x] 6.15 `repository-infrastructure`
- [x] 6.16 `serve-command`
- [x] 6.17 `testing-infrastructure`

## 7. Validation

- [x] 7.1 Verify all specs still accurately describe implemented behavior
- [x] 7.2 Run `openspec validate --strict` on consolidated specs
- [x] 7.3 Update any cross-references between specs

## Expected Outcome

| Before | After |
|--------|-------|
| 26 specs | 17 specs |
| 26 specs with "TBD" purpose | 0 specs with "TBD" purpose |
| Overlapping requirements | Deduplicated, clear requirements |

## Consolidation Summary

| Action | Source Specs | Target Spec |
|--------|--------------|-------------|
| Merge | `open5e-v1-client` | `complete-open5e-v1-client` |
| Merge | `open5e-v2-client` | `complete-open5e-v2-client` |
| Merge | `filter-enhancement`, `search-parameter-correction`, `api-parameter-usage` | `enhanced-search` |
| Absorb | `spell-school-filtering`, `weapon-model-correction` | `complete-open5e-v2-client` |
| Absorb | `tool-repository-migration` | `repository-infrastructure` |
| Absorb | `mcp-tool-cleanup` | `mcp-tools` |
