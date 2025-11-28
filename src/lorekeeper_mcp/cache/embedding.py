"""Embedding service for generating text embeddings using sentence-transformers.

This module provides the EmbeddingService class that generates 384-dimensional
embedding vectors for semantic search. The model is loaded lazily on first use
to avoid startup delays when the cache is not needed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Default embedding model - lightweight, fast, 384 dimensions
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers.

    Uses lazy model loading to avoid ~2s startup delay when cache is not needed.
    The model is loaded on first encode() or encode_batch() call.

    Attributes:
        model_name: Name of the sentence-transformers model to use.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        """Initialize EmbeddingService with model name.

        Args:
            model_name: Name of sentence-transformers model. Defaults to
                all-MiniLM-L6-v2 which produces 384-dimensional vectors.
        """
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load and return the embedding model.

        Returns:
            Loaded SentenceTransformer model instance.
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        return self._model

    def encode(self, text: str) -> list[float]:
        """Encode single text to embedding vector.

        Args:
            text: Text to encode.

        Returns:
            List of floats representing the 384-dimensional embedding.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        result: list[float] = embedding.tolist()
        return result

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Encode multiple texts efficiently in batches.

        Args:
            texts: List of texts to encode.
            batch_size: Number of texts to encode per batch. Defaults to 32.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        result: list[list[float]] = embeddings.tolist()
        return result

    def get_searchable_text(self, entity: dict[str, Any], entity_type: str) -> str:
        """Extract searchable text from entity for embedding generation.

        Extracts entity-type-specific text fields and concatenates them
        for semantic embedding. Different entity types have different
        relevant fields for search.

        Args:
            entity: Entity dictionary with fields to extract.
            entity_type: Type of entity (spells, creatures, equipment, etc.)

        Returns:
            Concatenated searchable text string.
        """
        text_parts: list[str] = []

        # Always include name
        name = entity.get("name")
        if name:
            text_parts.append(str(name))

        if entity_type == "spells":
            self._extract_spell_text(entity, text_parts)
        elif entity_type in ("creatures", "monsters"):
            self._extract_creature_text(entity, text_parts)
        elif entity_type in ("equipment", "weapons", "armor", "magicitems", "items"):
            self._extract_equipment_text(entity, text_parts)
        elif entity_type in ("rules", "rule_sections", "conditions"):
            self._extract_rule_text(entity, text_parts)
        else:
            # Default: include description
            desc = entity.get("desc")
            if desc:
                text_parts.append(str(desc))

        return " ".join(filter(None, text_parts))

    def _extract_spell_text(self, entity: dict[str, Any], text_parts: list[str]) -> None:
        """Extract spell-specific text fields."""
        desc = entity.get("desc")
        if desc:
            text_parts.append(str(desc))

        higher_level = entity.get("higher_level")
        if higher_level:
            text_parts.append(str(higher_level))

    def _extract_creature_text(self, entity: dict[str, Any], text_parts: list[str]) -> None:
        """Extract creature-specific text fields."""
        desc = entity.get("desc")
        if desc:
            text_parts.append(str(desc))

        creature_type = entity.get("type")
        if creature_type:
            text_parts.append(str(creature_type))

        # Extract action names
        actions = entity.get("actions", [])
        if actions:
            action_names = [a.get("name", "") for a in actions if isinstance(a, dict)]
            text_parts.extend(filter(None, action_names))

        # Extract special ability names
        abilities = entity.get("special_abilities", [])
        if abilities:
            ability_names = [a.get("name", "") for a in abilities if isinstance(a, dict)]
            text_parts.extend(filter(None, ability_names))

    def _extract_equipment_text(self, entity: dict[str, Any], text_parts: list[str]) -> None:
        """Extract equipment-specific text fields."""
        desc = entity.get("desc")
        if desc:
            text_parts.append(str(desc))

        item_type = entity.get("type")
        if item_type:
            text_parts.append(str(item_type))

        properties = entity.get("properties", [])
        if properties and isinstance(properties, list):
            text_parts.extend(str(p) for p in properties if p)

    def _extract_rule_text(self, entity: dict[str, Any], text_parts: list[str]) -> None:
        """Extract rule-specific text fields."""
        desc = entity.get("desc")
        if desc:
            text_parts.append(str(desc))

        content = entity.get("content")
        if content:
            text_parts.append(str(content))
