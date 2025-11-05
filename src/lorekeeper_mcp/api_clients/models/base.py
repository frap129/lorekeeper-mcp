"""Base Pydantic models for API responses."""

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field


class BaseModel(PydanticBaseModel):
    """Base model with common fields for API responses."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    name: str = Field(..., description="Name of the item")
    slug: str = Field(..., description="URL-safe identifier")
    desc: str | None = Field(None, description="Description text")
    document_url: str | None = Field(None, description="Source document URL")
