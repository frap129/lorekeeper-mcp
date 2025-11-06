"""Client for D&D 5e API (rules, reference data)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient


class Dnd5eApiClient(BaseHttpClient):
    """Client for D&D 5e API endpoints."""

    # Reference data TTL: 30 days (static data)
    REFERENCE_DATA_TTL = 2592000

    def __init__(
        self,
        base_url: str = "https://www.dnd5eapi.co/api/2014",
        cache_ttl: int = 604800,  # 7 days default
        source_api: str = "dnd5e_api",
        **kwargs: Any,
    ) -> None:
        """Initialize D&D 5e API client.

        Args:
            base_url: Base URL for API requests (includes version)
            cache_ttl: Cache time-to-live in seconds (default 7 days)
            source_api: Source API identifier for cache metadata
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(
            base_url=base_url,
            cache_ttl=cache_ttl,
            source_api=source_api,
            **kwargs,
        )

    def _extract_entities(
        self,
        response: dict[str, Any],
        entity_type: str,
    ) -> list[dict[str, Any]]:
        """Extract entities from API response.

        Handles both paginated responses with 'results' and direct entities.
        Normalizes 'index' field to 'slug' for D&D5e API compatibility.

        Args:
            response: API response dictionary
            entity_type: Type of entities

        Returns:
            List of entity dictionaries with 'slug' field
        """
        entities: list[dict[str, Any]] = []

        # Check if paginated response
        if "results" in response and isinstance(response["results"], list):
            entities = response["results"]
        # Check if direct entity (has slug or index)
        elif "slug" in response or "index" in response:
            entities = [response]
        # Unknown format
        else:
            return []

        # Normalize 'index' field to 'slug' for D&D5e API entities
        for entity in entities:
            if isinstance(entity, dict) and "index" in entity and "slug" not in entity:
                entity["slug"] = entity["index"]

        # Filter out entities without slug
        return [e for e in entities if isinstance(e, dict) and "slug" in e]

    async def get_rules(
        self,
        section: str | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Get rules from D&D 5e API.

        Args:
            section: Filter by rule section (adventuring, combat, equipment,
                     spellcasting, using-ability-scores, appendix)
            **filters: Additional API parameters

        Returns:
            List of rule dictionaries with hierarchical organization

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        # Build endpoint
        endpoint = f"/rules/{section}" if section else "/rules/"

        params = {k: v for k, v in filters.items() if v is not None}

        # Make request with entity cache
        result = await self.make_request(
            endpoint,
            use_entity_cache=True,
            entity_type="rules",
            cache_filters={},
            params=params,
        )

        # Result is already a list due to entity caching extraction
        return result if isinstance(result, list) else [result]

    async def get_rule_sections(
        self,
        name: str | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Get rule sections from D&D 5e API.

        Args:
            name: Filter by rule section name (index)
            **filters: Additional API parameters

        Returns:
            List of rule section dictionaries with detailed mechanics

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        # Build endpoint
        endpoint = f"/rule-sections/{name}" if name else "/rule-sections/"

        params = {k: v for k, v in filters.items() if v is not None}

        # Make request with entity cache
        result = await self.make_request(
            endpoint,
            use_entity_cache=True,
            entity_type="rule_sections",
            cache_filters={},
            params=params,
        )

        # Result is already a list due to entity caching extraction
        return result if isinstance(result, list) else [result]

    async def get_damage_types(self, **filters: Any) -> list[dict[str, Any]]:
        """Get damage types from D&D 5e API.

        Returns:
            List of damage type dictionaries (13 types)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        # Override cache TTL for reference data
        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/damage-types/",
                use_entity_cache=True,
                entity_type="damage_types",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_weapon_properties(self, **filters: Any) -> list[dict[str, Any]]:
        """Get weapon properties from D&D 5e API.

        Returns:
            List of weapon property dictionaries (11 properties)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        # Override cache TTL for reference data
        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/weapon-properties/",
                use_entity_cache=True,
                entity_type="weapon_properties",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_skills(self, **filters: Any) -> list[dict[str, Any]]:
        """Get skills from D&D 5e API.

        Returns:
            List of skill dictionaries (18 skills)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/skills/",
                use_entity_cache=True,
                entity_type="skills",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_ability_scores(self, **filters: Any) -> list[dict[str, Any]]:
        """Get ability scores from D&D 5e API.

        Returns:
            List of ability score dictionaries (6 scores)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/ability-scores/",
                use_entity_cache=True,
                entity_type="ability_scores",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_magic_schools(self, **filters: Any) -> list[dict[str, Any]]:
        """Get magic schools from D&D 5e API.

        Returns:
            List of magic school dictionaries (8 schools)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/magic-schools/",
                use_entity_cache=True,
                entity_type="magic_schools",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_languages(self, **filters: Any) -> list[dict[str, Any]]:
        """Get languages from D&D 5e API.

        Returns:
            List of language dictionaries (16 languages)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/languages/",
                use_entity_cache=True,
                entity_type="languages",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_proficiencies(self, **filters: Any) -> list[dict[str, Any]]:
        """Get proficiencies from D&D 5e API.

        Returns:
            List of proficiency dictionaries (117 proficiencies)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/proficiencies/",
                use_entity_cache=True,
                entity_type="proficiencies",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl

    async def get_alignments(self, **filters: Any) -> list[dict[str, Any]]:
        """Get alignments from D&D 5e API.

        Returns:
            List of alignment dictionaries (9 alignments)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        original_ttl = self.cache_ttl
        self.cache_ttl = self.REFERENCE_DATA_TTL

        try:
            result = await self.make_request(
                "/alignments/",
                use_entity_cache=True,
                entity_type="alignments",
                params=params,
            )
            return result if isinstance(result, list) else result.get("results", [])
        finally:
            self.cache_ttl = original_ttl
