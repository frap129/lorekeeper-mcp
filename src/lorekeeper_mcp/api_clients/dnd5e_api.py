"""Client for D&D 5e API (rules, reference data)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient


class Dnd5eApiClient(BaseHttpClient):
    """Client for D&D 5e API endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize D&D 5e API client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(
            base_url="https://www.dnd5eapi.co/api/2014",
            source_api="dnd5e_api",
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

        # Make request
        result = await self.make_request(endpoint, params=params)

        # Extract and normalize entities
        response = result if isinstance(result, dict) else {"results": result}
        return self._extract_entities(response, "rules")

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

        # Make request
        result = await self.make_request(endpoint, params=params)

        # Extract and normalize entities
        response = result if isinstance(result, dict) else {"results": result}
        return self._extract_entities(response, "rule_sections")

    async def get_damage_types(self, **filters: Any) -> list[dict[str, Any]]:
        """Get damage types from D&D 5e API.

        Returns:
            List of damage type dictionaries (13 types)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request("/damage-types/", params=params)
        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_weapon_properties(self, **filters: Any) -> list[dict[str, Any]]:
        """Get weapon properties from D&D 5e API.

        Returns:
            List of weapon property dictionaries (11 properties)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/weapon-properties/",
            params=params,
        )
        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_skills(self, **filters: Any) -> list[dict[str, Any]]:
        """Get skills from D&D 5e API.

        Returns:
            List of skill dictionaries (18 skills)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/skills/",
            params=params,
        )
        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_ability_scores(self, **filters: Any) -> list[dict[str, Any]]:
        """Get ability scores from D&D 5e API.

        Returns:
            List of ability score dictionaries (6 scores)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/ability-scores/",
            params=params,
        )
        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_magic_schools(self, **filters: Any) -> list[dict[str, Any]]:
        """Get magic schools from D&D 5e API.

        Returns:
            List of magic school dictionaries (8 schools)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/magic-schools/",
            params=params,
        )
        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_languages(self, **filters: Any) -> list[dict[str, Any]]:
        """Get languages from D&D 5e API.

        Returns:
            List of language dictionaries (16 languages)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/languages/",
            params=params,
        )
        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_proficiencies(self, **filters: Any) -> list[dict[str, Any]]:
        """Get proficiencies from D&D 5e API.

        Returns:
            List of proficiency dictionaries (117 proficiencies)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/proficiencies/",
            params=params,
        )
        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_alignments(self, **filters: Any) -> list[dict[str, Any]]:
        """Get alignments from D&D 5e API.

        Returns:
            List of alignment dictionaries (9 alignments)

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/alignments/",
            params=params,
        )
        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    # Task 1.12: Character option methods
    async def get_backgrounds_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Get backgrounds from D&D 5e API.

        Returns:
            List of background dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/backgrounds/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_classes_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Get classes from D&D 5e API.

        Returns:
            List of class dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/classes/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_subclasses(self, **filters: Any) -> list[dict[str, Any]]:
        """Get subclasses from D&D 5e API.

        Returns:
            List of subclass dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/subclasses/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_races_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Get races from D&D 5e API.

        Returns:
            List of race dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/races/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_subraces(self, **filters: Any) -> list[dict[str, Any]]:
        """Get subraces from D&D 5e API.

        Returns:
            List of subrace dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/subraces/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_feats_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Get feats from D&D 5e API.

        Returns:
            List of feat dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/feats/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_traits(self, **filters: Any) -> list[dict[str, Any]]:
        """Get traits from D&D 5e API.

        Returns:
            List of trait dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/traits/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    # Task 1.13: Equipment methods
    async def get_equipment(self, **filters: Any) -> list[dict[str, Any]]:
        """Get equipment from D&D 5e API.

        Returns:
            List of equipment dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/equipment/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_weapons(self, **filters: Any) -> list[dict[str, Any]]:
        """Get weapons from D&D 5e API by filtering equipment results.

        Returns:
            List of weapon dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        all_equipment = await self.get_equipment(**filters)
        # Filter for weapons (equipment with weapon_category or melee/ranged in category)
        weapons: list[dict[str, Any]] = []
        for item in all_equipment:
            # Check if it's a weapon
            if "weapon_category" in item:
                weapons.append(item)
            elif "equipment_category" in item and isinstance(item["equipment_category"], dict):
                category_index = item["equipment_category"].get("index", "").lower()
                if (
                    "weapon" in category_index
                    or "melee" in category_index
                    or "ranged" in category_index
                ):
                    weapons.append(item)
        return weapons

    async def get_armor(self, **filters: Any) -> list[dict[str, Any]]:
        """Get armor from D&D 5e API by filtering equipment results.

        Returns:
            List of armor dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        all_equipment = await self.get_equipment(**filters)
        # Filter for armor (equipment with armor_category)
        armor: list[dict[str, Any]] = []
        for item in all_equipment:
            # Check if it's armor
            if "armor_category" in item:
                armor.append(item)
            elif "equipment_category" in item and isinstance(item["equipment_category"], dict):
                category_index = item["equipment_category"].get("index", "").lower()
                if "armor" in category_index:
                    armor.append(item)
        return armor

    async def get_equipment_categories(self, **filters: Any) -> list[dict[str, Any]]:
        """Get equipment categories from D&D 5e API.

        Returns:
            List of equipment category dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/equipment-categories/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_magic_items_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Get magic items from D&D 5e API.

        Returns:
            List of magic item dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/magic-items/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    # Task 1.14: Spell and monster methods
    async def get_spells_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Get spells from D&D 5e API.

        Returns:
            List of spell dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/spells/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_monsters_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Get monsters from D&D 5e API.

        Returns:
            List of monster dictionaries with Monster model compatibility

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/monsters/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    # Task 1.15: Conditions and features methods
    async def get_conditions_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Get conditions from D&D 5e API.

        Returns:
            List of condition dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/conditions/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    async def get_features(self, **filters: Any) -> list[dict[str, Any]]:
        """Get features from D&D 5e API.

        Returns:
            List of feature dictionaries

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(
            "/features/",
            params=params,
        )

        results = result if isinstance(result, list) else result.get("results", [])
        # Normalize index to slug
        for item in results:
            if isinstance(item, dict) and "index" in item and "slug" not in item:
                item["slug"] = item["index"]
        return results

    # Wrapper methods for CharacterOption and Equipment repositories
    # These delegate to the _dnd5e versions for compatibility with repository interfaces

    async def get_classes(self, **filters: Any) -> list[dict[str, Any]]:
        """Wrapper for get_classes_dnd5e for repository compatibility."""
        return await self.get_classes_dnd5e(**filters)

    async def get_races(self, **filters: Any) -> list[dict[str, Any]]:
        """Wrapper for get_races_dnd5e for repository compatibility."""
        return await self.get_races_dnd5e(**filters)

    async def get_backgrounds(self, **filters: Any) -> list[dict[str, Any]]:
        """Wrapper for get_backgrounds_dnd5e for repository compatibility."""
        return await self.get_backgrounds_dnd5e(**filters)

    async def get_feats(self, **filters: Any) -> list[dict[str, Any]]:
        """Wrapper for get_feats_dnd5e for repository compatibility."""
        return await self.get_feats_dnd5e(**filters)

    async def get_conditions(self, **filters: Any) -> list[dict[str, Any]]:
        """Wrapper for get_conditions_dnd5e for repository compatibility."""
        return await self.get_conditions_dnd5e(**filters)
