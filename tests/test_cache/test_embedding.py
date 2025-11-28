"""Tests for EmbeddingService."""

from lorekeeper_mcp.cache.embedding import EmbeddingService


class TestEmbeddingServiceInit:
    """Tests for EmbeddingService initialization."""

    def test_embedding_service_can_be_instantiated(self) -> None:
        """Test that EmbeddingService can be created."""
        service = EmbeddingService()
        assert service is not None

    def test_embedding_service_model_not_loaded_on_init(self) -> None:
        """Test that model is not loaded until first use (lazy loading)."""
        service = EmbeddingService()
        # Access internal state - model should be None until used
        assert service._model is None

    def test_embedding_service_default_model_name(self) -> None:
        """Test that default model name is all-MiniLM-L6-v2."""
        service = EmbeddingService()
        assert service.model_name == "all-MiniLM-L6-v2"

    def test_embedding_service_custom_model_name(self) -> None:
        """Test that custom model name can be provided."""
        service = EmbeddingService(model_name="custom-model")
        assert service.model_name == "custom-model"


class TestEmbeddingServiceEncode:
    """Tests for EmbeddingService.encode method."""

    def test_encode_returns_list_of_floats(self) -> None:
        """Test that encode returns a list of floats."""
        service = EmbeddingService()
        result = service.encode("test text")

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_encode_returns_384_dimensions(self) -> None:
        """Test that encode returns 384-dimensional vector."""
        service = EmbeddingService()
        result = service.encode("test text")

        assert len(result) == 384

    def test_encode_loads_model_on_first_call(self) -> None:
        """Test that model is loaded on first encode call."""
        service = EmbeddingService()
        assert service._model is None

        service.encode("test text")

        assert service._model is not None

    def test_encode_reuses_loaded_model(self) -> None:
        """Test that subsequent encode calls reuse the same model."""
        service = EmbeddingService()
        service.encode("first call")
        model_after_first = service._model

        service.encode("second call")
        model_after_second = service._model

        assert model_after_first is model_after_second

    def test_encode_different_texts_produce_different_embeddings(self) -> None:
        """Test that different texts produce different embeddings."""
        service = EmbeddingService()
        embedding1 = service.encode("fireball spell")
        embedding2 = service.encode("healing potion")

        # Embeddings should be different (not exactly equal)
        assert embedding1 != embedding2

    def test_encode_empty_string(self) -> None:
        """Test that encode handles empty string without error."""
        service = EmbeddingService()
        result = service.encode("")

        assert isinstance(result, list)
        assert len(result) == 384


class TestEmbeddingServiceEncodeBatch:
    """Tests for EmbeddingService.encode_batch method."""

    def test_encode_batch_returns_list_of_embeddings(self) -> None:
        """Test that encode_batch returns list of embedding lists."""
        service = EmbeddingService()
        texts = ["fireball", "ice storm", "lightning bolt"]
        result = service.encode_batch(texts)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(emb, list) for emb in result)
        assert all(len(emb) == 384 for emb in result)

    def test_encode_batch_empty_list(self) -> None:
        """Test that encode_batch handles empty list."""
        service = EmbeddingService()
        result = service.encode_batch([])

        assert result == []

    def test_encode_batch_single_item(self) -> None:
        """Test that encode_batch handles single item list."""
        service = EmbeddingService()
        result = service.encode_batch(["single text"])

        assert len(result) == 1
        assert len(result[0]) == 384

    def test_encode_batch_matches_individual_encode(self) -> None:
        """Test that batch encoding produces same results as individual encoding."""
        service = EmbeddingService()
        texts = ["fireball", "ice storm"]

        batch_result = service.encode_batch(texts)
        individual_results = [service.encode(t) for t in texts]

        # Results should be very close (floating point comparison)
        for batch_emb, ind_emb in zip(batch_result, individual_results, strict=True):
            for b, i in zip(batch_emb, ind_emb, strict=True):
                assert abs(b - i) < 1e-6


class TestEmbeddingServiceGetSearchableText:
    """Tests for EmbeddingService.get_searchable_text method."""

    def test_get_searchable_text_spell(self) -> None:
        """Test searchable text extraction for spells."""
        service = EmbeddingService()
        entity = {
            "name": "Fireball",
            "desc": "A bright streak flashes from your pointing finger.",
            "higher_level": "When cast at 4th level, damage increases.",
        }

        result = service.get_searchable_text(entity, "spells")

        assert "Fireball" in result
        assert "bright streak flashes" in result
        assert "4th level" in result

    def test_get_searchable_text_creature(self) -> None:
        """Test searchable text extraction for creatures."""
        service = EmbeddingService()
        entity = {
            "name": "Ancient Red Dragon",
            "desc": "A legendary creature of immense power.",
            "type": "dragon",
            "actions": [
                {"name": "Multiattack"},
                {"name": "Fire Breath"},
            ],
            "special_abilities": [
                {"name": "Legendary Resistance"},
            ],
        }

        result = service.get_searchable_text(entity, "creatures")

        assert "Ancient Red Dragon" in result
        assert "legendary creature" in result
        assert "dragon" in result
        assert "Multiattack" in result
        assert "Fire Breath" in result
        assert "Legendary Resistance" in result

    def test_get_searchable_text_equipment(self) -> None:
        """Test searchable text extraction for equipment."""
        service = EmbeddingService()
        entity = {
            "name": "Longsword",
            "desc": "A versatile slashing weapon.",
            "type": "Martial Melee Weapon",
            "properties": ["Versatile"],
        }

        result = service.get_searchable_text(entity, "equipment")

        assert "Longsword" in result
        assert "versatile slashing" in result
        assert "Martial Melee Weapon" in result
        assert "Versatile" in result

    def test_get_searchable_text_character_option(self) -> None:
        """Test searchable text extraction for character options."""
        service = EmbeddingService()
        entity = {
            "name": "Fighter",
            "desc": "A master of martial combat.",
        }

        # Character options include classes, races, backgrounds, feats
        result = service.get_searchable_text(entity, "classes")

        assert "Fighter" in result
        assert "martial combat" in result

    def test_get_searchable_text_rules(self) -> None:
        """Test searchable text extraction for rules."""
        service = EmbeddingService()
        entity = {
            "name": "Conditions",
            "desc": "Conditions alter a creature's capabilities.",
            "content": "Blinded: A blinded creature can't see.",
        }

        result = service.get_searchable_text(entity, "rules")

        assert "Conditions" in result
        assert "alter a creature" in result
        assert "blinded creature" in result.lower()

    def test_get_searchable_text_minimal_entity(self) -> None:
        """Test searchable text with only name field."""
        service = EmbeddingService()
        entity = {"name": "Unknown Item"}

        result = service.get_searchable_text(entity, "equipment")

        assert result == "Unknown Item"

    def test_get_searchable_text_empty_fields_skipped(self) -> None:
        """Test that empty/None fields are skipped."""
        service = EmbeddingService()
        entity = {
            "name": "Test Spell",
            "desc": None,
            "higher_level": "",
        }

        result = service.get_searchable_text(entity, "spells")

        # Should only contain name, no extra whitespace from None/empty
        assert result.strip() == "Test Spell"

    def test_get_searchable_text_unknown_entity_type(self) -> None:
        """Test fallback for unknown entity types."""
        service = EmbeddingService()
        entity = {
            "name": "Custom Entity",
            "desc": "Some description.",
        }

        result = service.get_searchable_text(entity, "unknown_type")

        # Should fall back to name + desc
        assert "Custom Entity" in result
        assert "Some description" in result
