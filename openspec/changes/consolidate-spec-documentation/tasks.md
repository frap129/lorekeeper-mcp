## 1. Analysis and Planning

- [ ] 1.1 Review all 28 specs and identify exact overlap/duplication
- [ ] 1.2 Document merge strategy for each consolidation group
- [ ] 1.3 Identify requirements that may conflict between specs

## 2. API Client Spec Consolidation

### 2.1 D&D 5e API Client
- [ ] 2.1.1 Merge `dnd5e-api-client/spec.md` into `complete-dnd5e-client/spec.md`
- [ ] 2.1.2 Update purpose section with clear description
- [ ] 2.1.3 Remove duplicate requirements
- [ ] 2.1.4 Archive/delete `dnd5e-api-client` directory

### 2.2 Open5e v1 Client
- [ ] 2.2.1 Merge `open5e-v1-client/spec.md` into `complete-open5e-v1-client/spec.md`
- [ ] 2.2.2 Update purpose section with clear description
- [ ] 2.2.3 Remove duplicate requirements
- [ ] 2.2.4 Archive/delete `open5e-v1-client` directory

### 2.3 Open5e v2 Client
- [ ] 2.3.1 Merge `open5e-v2-client/spec.md` into `complete-open5e-v2-client/spec.md`
- [ ] 2.3.2 Update purpose section with clear description
- [ ] 2.3.3 Remove duplicate requirements
- [ ] 2.3.4 Archive/delete `open5e-v2-client` directory

## 3. Search/Filter Spec Consolidation

- [ ] 3.1 Merge `filter-enhancement/spec.md` into `enhanced-search/spec.md`
- [ ] 3.2 Merge `search-parameter-correction/spec.md` into `enhanced-search/spec.md`
- [ ] 3.3 Update purpose section for enhanced-search
- [ ] 3.4 Remove duplicate requirements
- [ ] 3.5 Archive/delete merged spec directories

## 4. Narrow Fix Specs

- [ ] 4.1 Absorb `spell-school-filtering` into `enhanced-search` or `complete-open5e-v2-client`
- [ ] 4.2 Absorb `weapon-model-correction` into `complete-open5e-v2-client`
- [ ] 4.3 Archive/delete absorbed spec directories

## 5. Purpose Section Updates

- [ ] 5.1 Update all remaining "TBD" purpose sections with clear descriptions
- [ ] 5.2 Ensure all specs follow consistent format

## 6. Validation

- [ ] 6.1 Verify all specs still accurately describe implemented behavior
- [ ] 6.2 Run `openspec validate --strict` on consolidated specs
- [ ] 6.3 Update any cross-references between specs

## Expected Outcome

| Before | After |
|--------|-------|
| 28 specs | ~16-18 specs |
| 6 specs with "TBD" purpose | 0 specs with "TBD" purpose |
| Overlapping requirements | Deduplicated, clear requirements |
