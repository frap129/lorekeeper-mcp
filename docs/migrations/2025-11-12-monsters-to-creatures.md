# Migration: Monsters to Creatures (Open5e v1 → v2)

## Date
2025-11-12

## Summary
Migrated MonsterRepository from Open5e API v1 `/monsters/` endpoint to v2 `/creatures/` endpoint.

## Changes

### API Clients
- **RepositoryFactory**: Now uses `Open5eV2Client` by default for monster repository
- **Open5eV1Client**: Added `get_creatures()` alias method for backward compatibility
- **Open5eV2Client**: Already had `get_creatures()` method

### Database Schema
- **creatures table**: Added `challenge_rating` indexed field (was missing)
- **monsters table**: Kept for backward compatibility but no longer used by default

### Repositories
- **MonsterRepository**:
  - Changed from `"monsters"` to `"creatures"` table
  - Updated `get_all()` and `search()` methods
  - Added v2 parameter mapping for `cr_min`/`cr_max` → `challenge_rating_decimal__gte`/`lte`

### Tests
- Fixed test isolation by clearing `RepositoryFactory._cache_instance`
- Updated mock clients to include `get_creatures()` method

## Migration Path

### For Users
No action required. The change is transparent.

### For Developers
If you have custom code using MonsterRepository:
- Repository now uses `"creatures"` table by default
- API client defaults to Open5eV2Client
- To use v1 explicitly: `RepositoryFactory.create_monster_repository(client=Open5eV1Client())`

## Testing
- All 17 integration tests pass
- All 34 live tests pass
- No breaking changes to public API
