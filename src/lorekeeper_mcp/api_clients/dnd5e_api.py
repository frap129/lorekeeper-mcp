"""Client for D&D 5e API (rules, reference data)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon

# All D&D 5e API content is from the SRD - same document as Open5e's srd-2014
SRD_DOCUMENT_NAME = "System Reference Document 5.1"


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

        if "results" in response and isinstance(response["results"], list):
            entities = response["results"]
        elif "slug" in response or "index" in response:
            entities = [response]
        else:
            return []
        for entity in entities:
            if isinstance(entity, dict) and "index" in entity and "slug" not in entity:
                entity["slug"] = entity["index"]

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
        endpoint = f"/rules/{section}" if section else "/rules/"

        params = {k: v for k, v in filters.items() if v is not None}

        result = await self.make_request(endpoint, params=params)

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
        # Normalize index to slug and add SRD document name
        for item in results:
            if isinstance(item, dict):
                if "index" in item and "slug" not in item:
                    item["slug"] = item["index"]
                # Add SRD document name (D&D 5e API is all SRD content)
                item["document"] = SRD_DOCUMENT_NAME
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
        # Normalize index to slug and add SRD document name
        for item in results:
            if isinstance(item, dict):
                if "index" in item and "slug" not in item:
                    item["slug"] = item["index"]
                # Add SRD document name (D&D 5e API is all SRD content)
                item["document"] = SRD_DOCUMENT_NAME
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
        # Normalize index to slug and add SRD document name
        for item in results:
            if isinstance(item, dict):
                if "index" in item and "slug" not in item:
                    item["slug"] = item["index"]
                # Add SRD document name (D&D 5e API is all SRD content)
                item["document"] = SRD_DOCUMENT_NAME
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
        # Normalize index to slug and add SRD document name
        for item in results:
            if isinstance(item, dict):
                if "index" in item and "slug" not in item:
                    item["slug"] = item["index"]
                # Add SRD document name (D&D 5e API is all SRD content)
                item["document"] = SRD_DOCUMENT_NAME
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

    def _transform_weapon(self, weapon_dict: dict[str, Any]) -> Weapon:
        """Transform D&D 5e API weapon data to Weapon model format.

        Args:
            weapon_dict: Raw weapon data from D&D 5e API

        Returns:
            Weapon model instance
        """
        # Transform the data to match Weapon model expectations
        transformed = dict(weapon_dict)

        # Handle desc field - API returns as list, model expects string
        if "desc" in transformed and isinstance(transformed["desc"], list):
            transformed["desc"] = " ".join(transformed["desc"])

        # Add key field from index
        transformed["key"] = weapon_dict.get("index", weapon_dict.get("slug", ""))

        # Extract damage_dice from nested damage object
        if "damage" in weapon_dict and isinstance(weapon_dict["damage"], dict):
            transformed["damage_dice"] = weapon_dict["damage"].get("damage_dice", "")

            # Create damage_type object
            damage_type_index = weapon_dict["damage"].get("damage_type", {}).get("index", "")
            transformed["damage_type"] = {
                "name": damage_type_index.title(),
                "key": damage_type_index,
                "url": f"https://www.dnd5eapi.co/api/damage-types/{damage_type_index}",
            }

        # Transform properties
        if "properties" in weapon_dict and isinstance(weapon_dict["properties"], list):
            transformed["properties"] = []
            for prop in weapon_dict["properties"]:
                if isinstance(prop, dict) and "index" in prop:
                    transformed["properties"].append(
                        {
                            "property": {
                                "name": prop["index"].replace("-", " ").title(),
                                "type": None,
                                "url": f"https://www.dnd5eapi.co/api/weapon-properties/{prop['index']}",
                            }
                        }
                    )

        # Extract range values
        if "range" in weapon_dict and isinstance(weapon_dict["range"], dict):
            transformed["range"] = weapon_dict["range"].get("normal", 0)
            transformed["long_range"] = weapon_dict["range"].get("long", 0) or weapon_dict[
                "range"
            ].get("normal", 0)
            transformed["distance_unit"] = "feet"
        else:
            transformed["range"] = 0
            transformed["long_range"] = 0
            transformed["distance_unit"] = "feet"

        # Set default values for required fields
        transformed.setdefault(
            "is_simple", "simple" in weapon_dict.get("weapon_category", "").lower()
        )
        transformed.setdefault("is_improvised", False)

        # Transform cost
        if "cost" in weapon_dict and isinstance(weapon_dict["cost"], dict):
            quantity = weapon_dict["cost"].get("quantity", 0)
            unit = weapon_dict["cost"].get("unit", "gp")
            transformed["cost"] = f"{quantity} {unit}"
        return Weapon.model_validate(transformed)

    def _transform_armor(self, armor_dict: dict[str, Any]) -> Armor:
        """Transform D&D 5e API armor data to Armor model format.

        Args:
            armor_dict: Raw armor data from D&D 5e API

        Returns:
            Armor model instance
        """
        # Transform the data to match Armor model expectations
        transformed = dict(armor_dict)

        # Handle desc field - API returns as list, model expects string
        if "desc" in transformed and isinstance(transformed["desc"], list):
            transformed["desc"] = " ".join(transformed["desc"])

        # Add key field from index
        transformed["key"] = armor_dict.get("index", armor_dict.get("slug", ""))

        # Set default values for required fields
        transformed["category"] = armor_dict.get("armor_category", "")
        transformed.setdefault("base_ac", armor_dict.get("armor_class", {}).get("base", 0))
        transformed.setdefault(
            "dex_bonus", armor_dict.get("armor_class", {}).get("dex_bonus", False)
        )
        transformed.setdefault("max_dex_bonus", armor_dict.get("armor_class", {}).get("max_bonus"))
        transformed.setdefault("strength_required", armor_dict.get("str_minimum", 0))
        transformed.setdefault(
            "stealth_disadvantage", armor_dict.get("stealth_disadvantage", False)
        )

        # Transform cost
        if "cost" in armor_dict and isinstance(armor_dict["cost"], dict):
            quantity = armor_dict["cost"].get("quantity", 0)
            unit = armor_dict["cost"].get("unit", "gp")
            transformed["cost"] = f"{quantity} {unit}"
        return Armor.model_validate(transformed)

    async def get_weapons(self, **filters: Any) -> list[Weapon]:
        """Get weapons from D&D 5e API.

        Fetches weapons from the weapon category endpoint. Equipment category
        endpoint returns minimal data, so fetch full details from each item's
        individual endpoint.

        Args:
            limit: Maximum number of weapons to return
            **filters: Additional filter parameters

        Returns:
            List of Weapon model instances

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        weapons_list: list[dict[str, Any]] = []

        # Fetch from weapon category
        result = await self.make_request("/equipment-categories/weapon")
        if isinstance(result, dict) and "equipment" in result:
            weapons_list = result.get("equipment", [])

        # Fetch full details for each weapon from its individual endpoint
        full_weapons: list[dict[str, Any]] = []
        for weapon_ref in weapons_list:
            if isinstance(weapon_ref, dict) and "index" in weapon_ref:
                try:
                    # Fetch full weapon details from /equipment/{index}
                    full_weapon = await self.make_request(f"/equipment/{weapon_ref['index']}")
                    if isinstance(full_weapon, dict):
                        full_weapons.append(full_weapon)
                except Exception:
                    # If individual fetch fails, skip this weapon
                    continue

        # Normalize index to slug and add SRD document name for all weapons
        for weapon in full_weapons:
            if isinstance(weapon, dict):
                if "index" in weapon and "slug" not in weapon:
                    weapon["slug"] = weapon["index"]
                # Add SRD document name
                weapon["document"] = SRD_DOCUMENT_NAME

        # Apply limit if specified
        limit = filters.get("limit")
        if limit is not None:
            full_weapons = full_weapons[:limit]

        return [self._transform_weapon(weapon) for weapon in full_weapons]

    async def get_armor(self, **filters: Any) -> list[Armor]:
        """Get armor from D&D 5e API.

        Fetches armor from the armor equipment category. Equipment category
        endpoint returns minimal data, so fetch full details from each item's
        individual endpoint.

        Args:
            limit: Maximum number of armor items to return
            **filters: Additional filter parameters

        Returns:
            List of Armor model instances

        Raises:
            NetworkError: Network request failed
            ApiError: API returned error response
        """
        armor_list: list[dict[str, Any]] = []

        # Fetch from armor category
        result = await self.make_request("/equipment-categories/armor")
        if isinstance(result, dict) and "equipment" in result:
            armor_list = result.get("equipment", [])

        # Fetch full details for each armor item from its individual endpoint
        full_armor: list[dict[str, Any]] = []
        for armor_ref in armor_list:
            if isinstance(armor_ref, dict) and "index" in armor_ref:
                try:
                    # Fetch full armor details from /equipment/{index}
                    full_item = await self.make_request(f"/equipment/{armor_ref['index']}")
                    if isinstance(full_item, dict):
                        full_armor.append(full_item)
                except Exception:
                    # If individual fetch fails, skip this armor
                    continue

        # Normalize index to slug and add SRD document name for all armor
        for armor in full_armor:
            if isinstance(armor, dict):
                if "index" in armor and "slug" not in armor:
                    armor["slug"] = armor["index"]
                # Add SRD document name
                armor["document"] = SRD_DOCUMENT_NAME

        # Apply limit if specified
        limit = filters.get("limit")
        if limit is not None:
            full_armor = full_armor[:limit]

        return [self._transform_armor(item) for item in full_armor]

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
        # Normalize index to slug and add SRD document name
        for item in results:
            if isinstance(item, dict):
                if "index" in item and "slug" not in item:
                    item["slug"] = item["index"]
                # Add SRD document name
                item["document"] = SRD_DOCUMENT_NAME
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
        # Normalize index to slug and add SRD document name
        for item in results:
            if isinstance(item, dict):
                if "index" in item and "slug" not in item:
                    item["slug"] = item["index"]
                # Add SRD document name
                item["document"] = SRD_DOCUMENT_NAME
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
