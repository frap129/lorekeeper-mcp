"""Factory for creating repository instances with dependency injection."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.sqlite import SQLiteCache
from lorekeeper_mcp.config import settings
from lorekeeper_mcp.repositories.character_option import CharacterOptionRepository
from lorekeeper_mcp.repositories.equipment import EquipmentRepository
from lorekeeper_mcp.repositories.monster import MonsterRepository
from lorekeeper_mcp.repositories.rule import RuleRepository
from lorekeeper_mcp.repositories.spell import SpellRepository


class _CacheProtocol(Protocol):
    """Protocol for cache implementations used by factory."""

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache."""
        ...

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        ...


class RepositoryFactory:
    """Factory for creating repository instances with dependency injection.

    Provides static factory methods for creating properly configured repository
    instances. Supports optional client and cache overrides for testing.
    """

    _cache_instance: _CacheProtocol | None = None

    @staticmethod
    def _get_cache() -> _CacheProtocol:
        """Get or create the shared cache instance.

        Returns:
            A cache instance implementing the CacheProtocol.
        """
        if RepositoryFactory._cache_instance is None:
            db_path = str(settings.db_path)
            RepositoryFactory._cache_instance = SQLiteCache(db_path=db_path)
        assert RepositoryFactory._cache_instance is not None
        return RepositoryFactory._cache_instance

    @staticmethod
    def create_spell_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> SpellRepository:
        """Create a SpellRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to shared SQLiteCache.

        Returns:
            A configured SpellRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return SpellRepository(client=client, cache=cache)

    @staticmethod
    def create_monster_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> MonsterRepository:
        """Create a MonsterRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to shared SQLiteCache.

        Returns:
            A configured MonsterRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return MonsterRepository(client=client, cache=cache)

    @staticmethod
    def create_equipment_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> EquipmentRepository:
        """Create an EquipmentRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to shared SQLiteCache.

        Returns:
            A configured EquipmentRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return EquipmentRepository(client=client, cache=cache)  # type: ignore[arg-type]

    @staticmethod
    def create_character_option_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> CharacterOptionRepository:
        """Create a CharacterOptionRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to shared SQLiteCache.

        Returns:
            A configured CharacterOptionRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return CharacterOptionRepository(client=client, cache=cache)

    @staticmethod
    def create_rule_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> RuleRepository:
        """Create a RuleRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to shared SQLiteCache.

        Returns:
            A configured RuleRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return RuleRepository(client=client, cache=cache)
