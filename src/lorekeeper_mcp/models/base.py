"""Base canonical models with shared validators."""

from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, model_validator


class BaseEntity(PydanticBaseModel):
    """Base model for all canonical entities.

    Includes shared validators for:
    - Normalizing 'key' to 'slug'
    - Normalizing 'description' to 'desc'
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    name: str = Field(..., description="Name of the entity")
    slug: str = Field(..., description="URL-safe identifier")
    desc: str | None = Field(None, description="Description text")
    document: str | None = Field(None, description="Source document name")
    document_url: str | None = Field(None, description="Source document URL")
    source_api: str | None = Field(None, description="Source API (open5e, orcbrew)")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        """Normalize field names from various sources.

        - 'key' -> 'slug' (OrcBrew and Open5e v2 use 'key')
        - 'description' -> 'desc' (OrcBrew uses 'description')
        """
        if not isinstance(data, dict):
            return data

        # Normalize key -> slug
        if "key" in data and "slug" not in data:
            data["slug"] = data["key"]

        # Normalize description -> desc
        if "description" in data and "desc" not in data:
            data["desc"] = data["description"]

        return data
