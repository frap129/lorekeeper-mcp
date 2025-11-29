"""Tests for repository factory."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.repositories.character_option import CharacterOptionRepository
from lorekeeper_mcp.repositories.creature import CreatureRepository
from lorekeeper_mcp.repositories.equipment import EquipmentRepository
from lorekeeper_mcp.repositories.factory import RepositoryFactory
from lorekeeper_mcp.repositories.rule import RuleRepository
from lorekeeper_mcp.repositories.spell import SpellRepository


@pytest.mark.asyncio
async def test_factory_create_spell_repository():
    """Test creating SpellRepository via factory."""
    repo = RepositoryFactory.create_spell_repository()
    assert isinstance(repo, SpellRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_spell_repository_with_overrides():
    """Test creating SpellRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_spell_repository(client=mock_client, cache=mock_cache)

    assert isinstance(repo, SpellRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_create_creature_repository():
    """Test creating CreatureRepository via factory."""
    repo = RepositoryFactory.create_creature_repository()
    assert isinstance(repo, CreatureRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_creature_repository_with_overrides():
    """Test creating CreatureRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_creature_repository(client=mock_client, cache=mock_cache)

    assert isinstance(repo, CreatureRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_create_equipment_repository():
    """Test creating EquipmentRepository via factory."""
    repo = RepositoryFactory.create_equipment_repository()
    assert isinstance(repo, EquipmentRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_equipment_repository_with_overrides():
    """Test creating EquipmentRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_equipment_repository(client=mock_client, cache=mock_cache)

    assert isinstance(repo, EquipmentRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_create_character_option_repository():
    """Test creating CharacterOptionRepository via factory."""
    repo = RepositoryFactory.create_character_option_repository()
    assert isinstance(repo, CharacterOptionRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_character_option_repository_with_overrides():
    """Test creating CharacterOptionRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_character_option_repository(
        client=mock_client, cache=mock_cache
    )

    assert isinstance(repo, CharacterOptionRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_create_rule_repository():
    """Test creating RuleRepository via factory."""
    repo = RepositoryFactory.create_rule_repository()
    assert isinstance(repo, RuleRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_rule_repository_with_overrides():
    """Test creating RuleRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_rule_repository(client=mock_client, cache=mock_cache)

    assert isinstance(repo, RuleRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_creates_shared_cache_by_default():
    """Test that factory uses shared cache instance by default."""
    # Create multiple repositories
    spell_repo = RepositoryFactory.create_spell_repository()
    creature_repo = RepositoryFactory.create_creature_repository()
    equipment_repo = RepositoryFactory.create_equipment_repository()

    # Cache instances should be the same (singleton pattern)
    assert spell_repo.cache is creature_repo.cache
    assert creature_repo.cache is equipment_repo.cache


@pytest.mark.asyncio
async def test_factory_all_repositories_created_successfully():
    """Test that all repositories can be created successfully."""
    repos = {
        "spell": RepositoryFactory.create_spell_repository(),
        "creature": RepositoryFactory.create_creature_repository(),
        "equipment": RepositoryFactory.create_equipment_repository(),
        "character_option": RepositoryFactory.create_character_option_repository(),
        "rule": RepositoryFactory.create_rule_repository(),
    }

    for name, repo in repos.items():
        assert repo is not None, f"{name} repository is None"
        assert hasattr(repo, "get_all"), f"{name} repository missing get_all"
        assert hasattr(repo, "search"), f"{name} repository missing search"
        assert hasattr(repo, "client"), f"{name} repository missing client"
        assert hasattr(repo, "cache"), f"{name} repository missing cache"


def test_create_creature_repository_default_uses_v2():
    """Test that create_creature_repository uses Open5eV2Client by default."""
    # Clear any cached instance
    RepositoryFactory._cache_instance = None

    repo = RepositoryFactory.create_creature_repository()

    assert isinstance(repo.client, Open5eV2Client)


class TestRepositoryFactoryCacheIntegration:
    """Tests for repository factory cache backend integration."""

    def test_factory_uses_cache_factory_default(
        self, tmp_path: "Path", monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        """Test that factory uses cache factory with default backend."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        # Set Milvus path to tmp_path
        db_path = tmp_path / "milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")

        # Clear cached instance
        RepositoryFactory._cache_instance = None

        # Create a repository
        RepositoryFactory.create_spell_repository()

        # Cache should be MilvusCache
        assert isinstance(RepositoryFactory._cache_instance, MilvusCache)

    def test_factory_uses_milvus_backend(
        self, tmp_path: "Path", monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        """Test that factory uses Milvus as the only backend."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        # Set Milvus path to tmp_path
        db_path = tmp_path / "milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))

        # Clear cached instance
        RepositoryFactory._cache_instance = None

        # Create a repository
        RepositoryFactory.create_spell_repository()

        # Cache should be MilvusCache
        assert isinstance(RepositoryFactory._cache_instance, MilvusCache)

    def test_factory_reuses_cache_instance(
        self, tmp_path: "Path", monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        """Test that factory reuses the same cache instance."""
        db_path = tmp_path / "milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")

        # Clear cached instance
        RepositoryFactory._cache_instance = None

        # Create multiple repositories
        spell_repo = RepositoryFactory.create_spell_repository()
        creature_repo = RepositoryFactory.create_creature_repository()

        # Should use same cache instance
        assert spell_repo.cache is creature_repo.cache

    def test_factory_reset_cache(self, tmp_path: "Path", monkeypatch: "pytest.MonkeyPatch") -> None:
        """Test that factory cache can be reset."""
        db_path = tmp_path / "milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")

        # Clear cached instance
        RepositoryFactory._cache_instance = None

        # Create a repository
        RepositoryFactory.create_spell_repository()
        first_cache = RepositoryFactory._cache_instance

        # Reset cache
        RepositoryFactory.reset_cache()

        # Create another repository
        RepositoryFactory.create_spell_repository()
        second_cache = RepositoryFactory._cache_instance

        # Should be different instances
        assert first_cache is not second_cache
