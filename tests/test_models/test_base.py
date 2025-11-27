"""Tests for canonical base models."""

import pytest

from lorekeeper_mcp.models.base import BaseEntity


class TestBaseEntity:
    """Tests for BaseEntity model."""

    def test_base_entity_required_fields(self) -> None:
        """Test that BaseEntity validates required fields."""
        entity = BaseEntity(name="Test Item", slug="test-item")
        assert entity.name == "Test Item"
        assert entity.slug == "test-item"

    def test_base_entity_normalizes_key_to_slug(self) -> None:
        """Test that 'key' field is normalized to 'slug'."""
        entity = BaseEntity(name="Test", key="test-key")
        assert entity.slug == "test-key"

    def test_base_entity_slug_takes_precedence_over_key(self) -> None:
        """Test that explicit slug takes precedence over key."""
        entity = BaseEntity(name="Test", slug="explicit-slug", key="key-value")
        assert entity.slug == "explicit-slug"

    def test_base_entity_normalizes_description_to_desc(self) -> None:
        """Test that 'description' field is normalized to 'desc'."""
        entity = BaseEntity(name="Test", slug="test", description="A description")
        assert entity.desc == "A description"

    def test_base_entity_desc_takes_precedence_over_description(self) -> None:
        """Test that explicit desc takes precedence over description."""
        entity = BaseEntity(name="Test", slug="test", desc="explicit", description="ignored")
        assert entity.desc == "explicit"

    def test_base_entity_missing_slug_and_key_raises_error(self) -> None:
        """Test that missing both slug and key raises validation error."""
        with pytest.raises(ValueError):
            BaseEntity(name="Test")
