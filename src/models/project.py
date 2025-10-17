"""Project data models for Behance projects."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, HttpUrl


class ProjectStats(BaseModel):
    """Statistics for a Behance project."""

    views: int = Field(ge=0, description="Number of views")
    appreciations: int = Field(ge=0, description="Number of appreciations")
    comments: int = Field(ge=0, description="Number of comments")


class Project(BaseModel):
    """Behance project model."""

    id: int = Field(..., description="Unique project ID from Behance")
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description")
    url: HttpUrl = Field(..., description="Project URL")
    published_on: datetime = Field(..., description="Publication timestamp")
    created_on: datetime = Field(..., description="Creation timestamp")
    modified_on: datetime = Field(..., description="Last modification timestamp")
    stats: ProjectStats = Field(..., description="Project statistics")
    tags: list[str] = Field(default_factory=list, description="Project tags")
    covers: dict[str, str] = Field(default_factory=dict, description="Cover images")
    owner_id: int = Field(..., description="Owner user ID")
    owner_username: str = Field(..., description="Owner username")

    @field_validator("tags")
    @classmethod
    def deduplicate_tags(cls, v: list[str]) -> list[str]:
        """Remove duplicate tags while preserving order."""
        seen = set()
        result = []
        for tag in v:
            if tag not in seen:
                seen.add(tag)
                result.append(tag)
        return result

    def to_mongo_dict(self) -> dict[str, Any]:
        """Convert project to MongoDB document format."""
        data = self.model_dump()
        # Convert HttpUrl to string for MongoDB storage
        data["url"] = str(data["url"])
        return data

    @classmethod
    def from_mongo_dict(cls, data: dict[str, Any]) -> "Project":
        """Reconstruct project from MongoDB document."""
        # Handle both _id and id fields from MongoDB
        if "_id" in data and "id" not in data:
            data["id"] = data["_id"]
        return cls(**data)
