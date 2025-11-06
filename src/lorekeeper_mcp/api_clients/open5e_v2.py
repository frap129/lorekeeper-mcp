"""Client for Open5e API v2 (spells, weapons, armor, etc.)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient


class Open5eV2Client(BaseHttpClient):
    """Client for Open5e API v2 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v2 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v2", **kwargs)

    async def get_spells(
        self,
        level: int | None = None,
        school: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Get spells from Open5e API v2.

        Args:
            level: Filter by spell level
            school: Filter by spell school
            **kwargs: Additional API parameters

        Returns:
            List of spell dictionaries
        """
        cache_filters: dict[str, Any] = {}
        params: dict[str, Any] = {}

        if level is not None:
            cache_filters["level"] = level
            params["level"] = level
        if school:
            cache_filters["school"] = school
            params["school"] = school

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/spells/",
            use_entity_cache=True,
            entity_type="spells",
            cache_filters=cache_filters,
            params=params,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_weapons(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get weapons from Open5e API v2."""
        result = await self.make_request(
            "/weapons/",
            use_entity_cache=True,
            entity_type="weapons",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_armor(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get armor from Open5e API v2."""
        result = await self.make_request(
            "/armor/",
            use_entity_cache=True,
            entity_type="armor",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_backgrounds(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character backgrounds."""
        result = await self.make_request(
            "/backgrounds/",
            use_entity_cache=True,
            entity_type="backgrounds",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_feats(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character feats."""
        result = await self.make_request(
            "/feats/",
            use_entity_cache=True,
            entity_type="feats",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_conditions(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game conditions."""
        result = await self.make_request(
            "/conditions/",
            use_entity_cache=True,
            entity_type="conditions",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]
