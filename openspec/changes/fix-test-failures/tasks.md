# Fix Test Failures - Tasks

##Phase 1: Fix Monster Repository Parameter Mapping (Critical)

- [x] Update `MonsterRepository._map_to_api_params` to map `type` → `type__key` with lowercase
- [x] Update `MonsterRepository._map_to_api_params` to map `size` → `size__key` with lowercase
- [x] Add mapping for exact `cr` → `challenge_rating_decimal` in `MonsterRepository._map_to_api_params`
- [x] Run monster repository unit tests to verify parameter mapping
- [x] Run integration tests for creature lookup to verify fixes

## Phase 2: Fix Spell Repository Parameter Mapping (Critical)

- [x] Update `SpellRepository._map_to_api_params` to map `class_key` → `classes__key` with lowercase
- [x] Update `SpellRepository._map_to_api_params` to map `school` → `school__key` with lowercase
- [x] Ensure `concentration` parameter is passed through correctly
- [x] Run spell repository unit tests to verify parameter mapping
- [x] Run integration tests for spell lookup to verify fixes

## Phase 3: Add Graceful Error Handling

- [x] Update `BaseApiClient.make_request` to catch 400 validation errors
- [x] Add logging for 400 errors with API response details
- [x] Return empty result set `{"results": [], "count": 0}` for 400 errors
- [x] Add unit tests for 400 error handling behavior
- [x] Verify invalid type/size/school parameters return empty results instead of crashing

## Phase 4: Fix Feat Lookup

- [x] Update `CharacterOptionRepository._search_feats` to default `api_limit = 100` when no limit specified
- [x] Verify `Open5eV2Client.get_feats` accepts and uses `limit` parameter correctly
- [x] Add unit test for feat lookup with no limit specified
- [x] Add unit test for feat lookup with explicit limit
- [x] Run live test for feat lookup to verify >= 20 results

## Phase 5: Fix Integration Test Mocks

- [ ] Update `test_creature_lookup_basic` mock to use `/v2/creatures/?limit=220`
- [ ] Update `test_creature_lookup_by_cr` mock to use `/v2/creatures/?limit=20&challenge_rating_decimal=21.0`
- [ ] Add mock for `/v2/creatures/?type__key=<type>&limit=<n>` pattern
- [ ] Add mock for `/v2/creatures/?size__key=<size>&limit=<n>` pattern
- [ ] Run integration tests to verify mocks work correctly

## Phase 6: Debug Goblin Search (Investigation)

- [ ] Add logging to `MonsterRepository._map_to_api_params` to verify `name__icontains` param
- [ ] Add logging to creature lookup tool to verify client-side filtering
- [ ] Run live test for goblin search with debug logging
- [ ] Identify root cause of empty results
- [ ] Implement fix based on root cause
- [ ] Verify goblin search returns results

## Phase 7: Validation & Testing

- [ ] Run full test suite to verify all 9 failures are fixed
- [ ] Run `just test` to verify no regressions
- [ ] Run live tests multiple times to ensure consistency
- [ ] Run `just lint` and `just type-check` to verify code quality
- [ ] Document any changes to API parameter conventions

## Phase 8: Documentation

- [ ] Update `docs/apis/open5e-api.md` with correct parameter conventions
- [ ] Add examples of filter parameter mapping
- [ ] Document error handling behavior for invalid parameters
- [ ] Update repository layer documentation with parameter mapping rules
