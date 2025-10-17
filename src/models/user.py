"""User data models for Behance users."""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, HttpUrl


class UserStats(BaseModel):
    """Statistics for a Behance user."""

    followers: int = Field(ge=0, description="Number of followers")
    following: int = Field(ge=0, description="Number of users being followed")
    appreciations: int = Field(ge=0, description="Total appreciations received")
    views: int = Field(ge=0, description="Total profile views")
    project_views: int = Field(ge=0, description="Total project views")


class User(BaseModel):
    """Behance user model."""

    id: int = Field(..., description="Unique user ID from Behance")
    username: str = Field(..., description="Username")
    display_name: str = Field(..., description="Display name")
    url: HttpUrl = Field(..., description="Profile URL")
    location: Optional[str] = Field(None, description="User location")
    company: Optional[str] = Field(None, description="Company name")
    occupation: Optional[str] = Field(None, description="Job title/occupation")
    stats: UserStats = Field(..., description="User statistics")
    social_links: list[str] = Field(default_factory=list, description="Social media links")
    fields: list[str] = Field(default_factory=list, description="Creative fields")

    @field_validator("social_links")
    @classmethod
    def validate_social_links(cls, v: list[str]) -> list[str]:
        """Validate that social links are valid URLs."""
        for link in v:
            if not (link.startswith("http://") or link.startswith("https://")):
                raise ValueError(f"Social link must be a valid URL: {link}")
        return v

    def to_mongo_dict(self) -> dict[str, Any]:
        """Convert user to MongoDB document format."""
        data = self.model_dump()
        # Convert HttpUrl to string for MongoDB storage
        data["url"] = str(data["url"])
        return data

    @classmethod
    def from_mongo_dict(cls, data: dict[str, Any]) -> "User":
        """Reconstruct user from MongoDB document."""
        # Handle both _id and id fields from MongoDB
        if "_id" in data and "id" not in data:
            data["id"] = data["_id"]
        return cls(**data)
