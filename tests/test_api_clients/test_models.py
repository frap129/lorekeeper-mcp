"""Tests for Pydantic response models."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.api_clients.models.base import BaseModel


def test_base_model_required_fields() -> None:
    """Test that BaseModel validates required fields."""
    model = BaseModel(name="Test Item", slug="test-item")
    assert model.name == "Test Item"
    assert model.slug == "test-item"


def test_base_model_optional_fields() -> None:
    """Test that BaseModel handles optional fields."""
    model = BaseModel(
        name="Test Item",
        slug="test-item",
        desc="Test description",
        document_url="https://example.com",
    )
    assert model.desc == "Test description"
    assert model.document_url == "https://example.com"


def test_base_model_missing_required_field() -> None:
    """Test that BaseModel raises error for missing required fields."""
    with pytest.raises(ValidationError):
        BaseModel(name="Test")  # Missing slug


def test_base_model_to_dict() -> None:
    """Test model serialization to dict."""
    model = BaseModel(name="Test", slug="test", desc="Description")
    data = model.model_dump()

    assert data["name"] == "Test"
    assert data["slug"] == "test"
    assert data["desc"] == "Description"
