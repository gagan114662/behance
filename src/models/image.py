"""Image data models for Behance project images."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, HttpUrl


class Image(BaseModel):
    """Behance project image model."""

    url: HttpUrl = Field(..., description="Image URL")
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
    size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Image format")
    project_id: int = Field(..., description="Associated project ID")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate image format is one of the supported types."""
        valid_formats = ["jpg", "jpeg", "png", "gif", "webp", "svg"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Image format must be one of {valid_formats}, got: {v}")
        return v.lower()

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio of the image."""
        return self.width / self.height
