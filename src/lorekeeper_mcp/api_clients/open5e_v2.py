"""Client for Open5e API v2 (spells, weapons, armor, etc.)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.models import Armor, Creature, Spell, Weapon


def _extract_document_name(entity: dict[str, Any]) -> str | None:
    """Extract document name from Open5e v2 entity.

    Args:
        entity: Raw entity data from Open5e v2 API

    Returns:
        Document name or None if not available
    """
    if isinstance(entity.get("document"), dict):
        doc_name = entity["document"].get("name")
        if isinstance(doc_name, str):
            return doc_name
    return None


class Open5eV2Client(BaseHttpClient):
    """Client for Open5e API v2 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v2 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v2", **kwargs)

    def _transform_creature_response(self, creature: dict[str, Any]) -> dict[str, Any] | None:
        """Transform Open5e v2 creature response to Creature model format.

        Args:
            creature: Raw creature data from Open5e v2 API

        Returns:
            Transformed creature data compatible with Creature model,
            or None if creature should be filtered out (missing required fields)
        """
        # Skip creatures with missing required fields (e.g., hit_dice: None)
        if creature.get("hit_dice") is None:
            return None

        transformed = creature.copy()

        # 1. API `key` → Monster `slug`
        if "key" in creature and "slug" not in creature:
            transformed["slug"] = creature["key"]

        # 2. API `type` object → Monster string
        if isinstance(creature.get("type"), dict):
            transformed["type"] = creature["type"].get("name", "")

        # 3. API `size` object → Monster string
        if isinstance(creature.get("size"), dict):
            transformed["size"] = creature["size"].get("name", "")

        # 4. API `challenge_rating_text` → Monster `challenge_rating`
        if "challenge_rating_text" in creature and "challenge_rating" not in creature:
            transformed["challenge_rating"] = creature["challenge_rating_text"]

        # 5. API `challenge_rating_decimal` string → Monster float
        if isinstance(creature.get("challenge_rating_decimal"), str):
            try:
                transformed["challenge_rating_decimal"] = float(
                    creature["challenge_rating_decimal"]
                )
            except ValueError:
                # If conversion fails, set to None
                transformed["challenge_rating_decimal"] = None

        # 6. API `speed` with `unit` → Monster speed dict without unit
        if isinstance(creature.get("speed"), dict):
            speed = creature["speed"].copy()
            # Remove unit field as Monster model expects only speed values
            speed.pop("unit", None)
            # Convert float values to int for Monster model compatibility
            for key, value in speed.items():
                if isinstance(value, float) and value.is_integer():
                    speed[key] = int(value)
            transformed["speed"] = speed

        # 7. API `ability_scores` nested → Monster flat ability fields
        if isinstance(creature.get("ability_scores"), dict):
            ability_scores = creature["ability_scores"]
            for ability, score in ability_scores.items():
                if ability in [
                    "strength",
                    "dexterity",
                    "constitution",
                    "intelligence",
                    "wisdom",
                    "charisma",
                ]:
                    transformed[ability] = score

        # 8. API `traits` → Monster `special_abilities`
        if "traits" in creature and "special_abilities" not in creature:
            transformed["special_abilities"] = creature["traits"]

        # 9. API nested `document` → Monster `document_url` and `document` name
        if isinstance(creature.get("document"), dict):
            document_url = creature["document"].get("url", "")
            if document_url:
                transformed["document_url"] = document_url
            # Extract document name
            document_name = _extract_document_name(creature)
            if document_name:
                transformed["document"] = document_name

        # 10. API `armor_class` array → Monster integer (take first value)
        if isinstance(creature.get("armor_class"), list) and creature["armor_class"]:
            first_ac = creature["armor_class"][0]
            if isinstance(first_ac, dict) and "value" in first_ac:
                transformed["armor_class"] = first_ac["value"]

        return transformed

    async def get_spells(
        self,
        level: int | None = None,
        school: str | None = None,
        name: str | None = None,
        level_gte: int | None = None,
        level_lte: int | None = None,
        **kwargs: Any,
    ) -> list[Spell]:
        """Get spells from Open5e API v2.

        Args:
            level: Filter by spell level
            school: Filter by spell school (server-side filtering via school__key)
            name: Filter by spell name (server-side filtering via name__icontains)
            level_gte: Filter spells with level >= this value (level__gte)
            level_lte: Filter spells with level <= this value (level__lte)
            **kwargs: Additional API parameters

        Returns:
            List of Spell models
        """
        params: dict[str, Any] = {}

        if level is not None:
            params["level"] = level

        # Use server-side range operators for level filtering
        if level_gte is not None:
            params["level__gte"] = level_gte
        if level_lte is not None:
            params["level__lte"] = level_lte

        # Use server-side school__key parameter for filtering
        if school:
            params["school__key"] = school.lower()

        # Use server-side name__icontains parameter for partial name matching
        if name:
            params["name__icontains"] = name

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/spells/",
            params=params,
        )

        spell_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        # Extract document name for each spell
        for spell in spell_dicts:
            document_name = _extract_document_name(spell)
            if document_name:
                spell["document"] = document_name

        return [Spell.model_validate(spell) for spell in spell_dicts]

    async def get_weapons(
        self,
        name: str | None = None,
        cost_gte: int | float | None = None,
        cost_lte: int | float | None = None,
        **kwargs: Any,
    ) -> list[Weapon]:
        """Get weapons from Open5e API v2.

        Args:
            name: Filter by weapon name (server-side filtering via name__icontains)
            cost_gte: Filter weapons with cost >= this value (cost__gte)
            cost_lte: Filter weapons with cost <= this value (cost__lte)
            **kwargs: Additional API parameters

        Returns:
            List of Weapon models
        """
        params: dict[str, Any] = {}

        # Use server-side name__icontains parameter for partial name matching
        if name:
            params["name__icontains"] = name

        # Use server-side range operators for cost filtering
        if cost_gte is not None:
            params["cost__gte"] = cost_gte
        if cost_lte is not None:
            params["cost__lte"] = cost_lte

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/weapons/",
            params=params,
        )

        weapon_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        # Extract document name for each weapon
        for weapon in weapon_dicts:
            document_name = _extract_document_name(weapon)
            if document_name:
                weapon["document"] = document_name

        return [Weapon.model_validate(weapon) for weapon in weapon_dicts]

    async def get_armor(
        self,
        name: str | None = None,
        cost_gte: int | float | None = None,
        cost_lte: int | float | None = None,
        **kwargs: Any,
    ) -> list[Armor]:
        """Get armor from Open5e API v2.

        Args:
            name: Filter by armor name (server-side filtering via name__icontains)
            cost_gte: Filter armor with cost >= this value (cost__gte)
            cost_lte: Filter armor with cost <= this value (cost__lte)
            **kwargs: Additional API parameters

        Returns:
            List of Armor models
        """
        params: dict[str, Any] = {}

        # Use server-side name__icontains parameter for partial name matching
        if name:
            params["name__icontains"] = name

        # Use server-side range operators for cost filtering
        if cost_gte is not None:
            params["cost__gte"] = cost_gte
        if cost_lte is not None:
            params["cost__lte"] = cost_lte

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/armor/",
            params=params,
        )

        armor_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        # Extract document name for each armor
        for armor_item in armor_dicts:
            document_name = _extract_document_name(armor_item)
            if document_name:
                armor_item["document"] = document_name

        return [Armor.model_validate(armor) for armor in armor_dicts]

    async def get_backgrounds(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character backgrounds."""
        result = await self.make_request(
            "/backgrounds/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_feats(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character feats."""
        result = await self.make_request(
            "/feats/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_conditions(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game conditions."""
        result = await self.make_request(
            "/conditions/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.6: Item-related methods
    async def get_items(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get items from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of item dictionaries
        """
        result = await self.make_request(
            "/items/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_item_sets(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get item sets from Open5e API v2.

        Item sets are collections of items (e.g., core rulebook items).
        Uses 30-day cache TTL for reference data.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of item set dictionaries
        """
        result = await self.make_request(
            "/itemsets/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_item_categories(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get item categories from Open5e API v2.

        Item categories describe types of items (e.g., Wondrous Item, Potion).
        Uses 30-day cache TTL for reference data.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of item category dictionaries
        """
        result = await self.make_request(
            "/itemcategories/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.7: Creature methods
    async def get_creatures(
        self,
        challenge_rating_decimal_gte: float | None = None,
        challenge_rating_decimal_lte: float | None = None,
        **kwargs: Any,
    ) -> list[Creature]:
        """Get creatures from Open5e API v2.

        Creatures are returned as Creature models compatible with v1.

        Args:
            challenge_rating_decimal_gte: Filter creatures with CR >= this value
                (challenge_rating_decimal__gte)
            challenge_rating_decimal_lte: Filter creatures with CR <= this value
                (challenge_rating_decimal__lte)
            **kwargs: Additional API parameters

        Returns:
            List of Creature models
        """
        params: dict[str, Any] = {}

        # Use server-side range operators for challenge rating filtering
        if challenge_rating_decimal_gte is not None:
            params["challenge_rating_decimal__gte"] = challenge_rating_decimal_gte
        if challenge_rating_decimal_lte is not None:
            params["challenge_rating_decimal__lte"] = challenge_rating_decimal_lte

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/creatures/",
            params=params,
        )

        creature_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        # Transform each creature response to match Monster model format
        transformed_creatures = []
        for creature in creature_dicts:
            transformed = self._transform_creature_response(creature)
            # Skip creatures with missing required fields (e.g., hit_dice: None)
            if transformed is not None:
                transformed_creatures.append(transformed)

        return [Creature.model_validate(creature) for creature in transformed_creatures]

    async def get_creature_types(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get creature type definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of creature type dictionaries
        """
        result = await self.make_request(
            "/creaturetypes/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_creature_sets(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get creature sets from Open5e API v2.

        Creature sets are collections of creatures (e.g., SRD, Monster Manual).

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of creature set dictionaries
        """
        result = await self.make_request(
            "/creaturesets/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.8: Reference data methods (30-day TTL for all)
    async def get_damage_types_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get damage type definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of damage type dictionaries
        """
        result = await self.make_request(
            "/damagetypes/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_languages_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get language definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of language dictionaries
        """
        result = await self.make_request(
            "/languages/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_alignments_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get alignment definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of alignment dictionaries
        """
        result = await self.make_request(
            "/alignments/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_spell_schools_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get spell school definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of spell school dictionaries
        """
        result = await self.make_request(
            "/spellschools/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_sizes(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get creature size definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of size dictionaries
        """
        result = await self.make_request(
            "/sizes/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_item_rarities(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get item rarity level definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of rarity dictionaries
        """
        result = await self.make_request(
            "/itemrarities/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_environments(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get encounter environment definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of environment dictionaries
        """
        result = await self.make_request(
            "/environments/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_abilities(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get ability score definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of ability dictionaries
        """
        result = await self.make_request(
            "/abilities/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_skills_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get skill definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of skill dictionaries
        """
        result = await self.make_request(
            "/skills/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.9: Character option methods (7-day TTL)
    async def get_species(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character species/races from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of species dictionaries
        """
        result = await self.make_request(
            "/species/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_classes_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character classes from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of class dictionaries
        """
        result = await self.make_request(
            "/classes/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.10: Rules and metadata methods
    async def get_rules_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game rules from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of rule dictionaries
        """
        result = await self.make_request(
            "/rules/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_rulesets(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get ruleset definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of ruleset dictionaries
        """
        result = await self.make_request(
            "/rulesets/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_documents(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game document definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of document dictionaries
        """
        result = await self.make_request(
            "/documents/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_licenses(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get license information from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of license dictionaries
        """
        result = await self.make_request(
            "/licenses/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_publishers(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get publisher information from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of publisher dictionaries
        """
        result = await self.make_request(
            "/publishers/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_game_systems(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game system information from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of game system dictionaries
        """
        result = await self.make_request(
            "/gamesystems/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.11: Additional content methods
    async def get_images(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get image resources from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of image dictionaries
        """
        result = await self.make_request(
            "/images/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_weapon_properties_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get weapon property definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of weapon property dictionaries
        """
        result = await self.make_request(
            "/weaponproperties/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_services(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get service information from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of service dictionaries
        """
        result = await self.make_request(
            "/services/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 2.2: Unified Search Implementation
    DEFAULT_SEARCH_LIMIT = 50

    async def unified_search(
        self,
        query: str,
        fuzzy: bool = False,
        vector: bool = False,
        object_model: str | None = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
    ) -> list[dict[str, Any]]:
        """Search across all D&D content using the unified search endpoint.

        This method provides cross-entity search across spells, creatures,
        items, and other D&D content with support for fuzzy matching and
        semantic/vector search.

        Args:
            query: Search term (required)
            fuzzy: Enable typo-tolerant matching (default: False)
            vector: Enable semantic/concept-based matching (default: False)
            object_model: Filter to specific content type
                (e.g., "Spell", "Creature", "Item")
            limit: Max results to return (default: 50)

        Returns:
            List of search results with fields:
                - document: Dict with key and name
                - object_pk: Primary key of the result
                - object_name: Name of the result
                - object: Entity-specific data
                - object_model: Content type (Spell, Creature, Item, etc.)
                - schema_version: API version (v2)
                - route: API route for the result
                - text: Full description text
                - highlighted: Text excerpt with match highlighted
                - match_type: Type of match (exact, fuzzy, vector)
                - matched_term: The term that matched
                - match_score: Relevance score (0.0-1.0)
        """
        params: dict[str, Any] = {"query": query}

        # Add optional parameters if provided
        if fuzzy:
            params["fuzzy"] = "true"
        if vector:
            params["vector"] = "true"
        if object_model:
            params["object_model"] = object_model
        if limit != self.DEFAULT_SEARCH_LIMIT:
            params["limit"] = limit

        result = await self.make_request(
            "/search/",
            params=params,
        )

        # The search endpoint returns a list directly
        if isinstance(result, list):
            return result

        # Fallback in case the API returns a dict with results
        return result.get("results", [])  # type: ignore[no-any-return]
