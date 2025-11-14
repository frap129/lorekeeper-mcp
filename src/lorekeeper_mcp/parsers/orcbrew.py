"""OrcBrew (.orcbrew) file parser for D&D 5e content.

OrcBrew files are EDN (Extensible Data Notation) files used by OrcPub
and DungeonMastersVault for exporting D&D content.
"""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import edn_format

logger = logging.getLogger(__name__)


class OrcBrewParser:
    """Parser for OrcBrew (.orcbrew) EDN files."""

    def parse_file(self, file_path: Path) -> dict[str, Any]:
        """Parse an OrcBrew file and return structured data.

        Args:
            file_path: Path to .orcbrew file

        Returns:
            Dictionary mapping book names to entity collections

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed as EDN
        """
        if not file_path.exists():
            raise FileNotFoundError(f"OrcBrew file not found: {file_path}")

        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
                parsed = edn_format.loads(content)

            # Convert EDN data structure to plain Python dicts/lists
            result = self._edn_to_python(parsed)
            return result if isinstance(result, dict) else {}
        except Exception as e:
            raise ValueError(f"Failed to parse EDN file: {e}") from e

    def _edn_to_python(self, obj: Any) -> Any:
        """Convert EDN data types to Python equivalents.

        Args:
            obj: EDN object (can be nested)

        Returns:
            Python equivalent (dict, list, str, int, etc.)
        """
        # Handle keywords first
        if hasattr(obj, "__class__") and obj.__class__.__name__ == "Keyword":
            return self._keyword_to_string(obj)
        # Handle dicts and ImmutableDict (Mapping protocol)
        if isinstance(obj, Mapping):
            return {self._keyword_to_string(k): self._edn_to_python(v) for k, v in obj.items()}
        # Handle lists, tuples, sets
        if isinstance(obj, list | tuple | set):
            return [self._edn_to_python(item) for item in obj]
        return obj

    def _keyword_to_string(self, keyword: Any) -> str:
        """Convert EDN keyword to string.

        Args:
            keyword: EDN keyword or string

        Returns:
            String representation
        """
        if isinstance(keyword, str):
            return keyword
        # EDN keywords have a 'name' attribute
        if hasattr(keyword, "name"):
            return cast(str, keyword.name)
        return str(keyword)

    def extract_entities(self, parsed_data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        """Extract entities by type from parsed OrcBrew data.

        Args:
            parsed_data: Parsed OrcBrew data (book → entity types → entities)

        Returns:
            Dictionary mapping entity type strings to lists of entity dicts
        """
        entities_by_type: dict[str, list[dict[str, Any]]] = {}

        # Iterate through books
        for book_name, book_data in parsed_data.items():
            if not isinstance(book_data, dict):
                logger.warning(f"Skipping non-dict book data for '{book_name}'")
                continue

            # Iterate through entity type collections
            for entity_type_key, entities_dict in book_data.items():
                if not isinstance(entities_dict, dict):
                    continue

                # Initialize list for this entity type
                if entity_type_key not in entities_by_type:
                    entities_by_type[entity_type_key] = []

                # Extract individual entities
                for entity_key, entity_data in entities_dict.items():
                    if not isinstance(entity_data, dict):
                        continue

                    # Add source book and entity key
                    entity_with_meta = {
                        **entity_data,
                        "_source_book": book_name,
                        "_entity_key": entity_key,
                    }
                    entities_by_type[entity_type_key].append(entity_with_meta)

        return entities_by_type
