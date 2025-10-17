"""Pinterest data models."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class PinterestBoard(BaseModel):
    """Pinterest board model."""

    id: str = Field(..., description="Board ID")
    name: str = Field(..., description="Board name")
    description: Optional[str] = Field(None, description="Board description")
    url: str = Field(..., description="Board URL")
    pin_count: int = Field(0, description="Number of pins in board")
    follower_count: int = Field(0, description="Number of followers")
    image_url: Optional[str] = Field(None, description="Board cover image URL")
    owner_username: str = Field(..., description="Board owner username")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When this was scraped")


class PinterestPin(BaseModel):
    """Pinterest pin model."""

    id: str = Field(..., description="Pin ID")
    title: Optional[str] = Field(None, description="Pin title")
    description: Optional[str] = Field(None, description="Pin description")
    url: str = Field(..., description="Pin URL")
    image_url: str = Field(..., description="Pin image URL")
    image_width: Optional[int] = Field(None, description="Image width")
    image_height: Optional[int] = Field(None, description="Image height")
    board_id: Optional[str] = Field(None, description="Associated board ID")
    board_name: Optional[str] = Field(None, description="Board name")
    repin_count: int = Field(0, description="Number of repins")
    reaction_count: int = Field(0, description="Number of reactions")
    comment_count: int = Field(0, description="Number of comments")
    link: Optional[str] = Field(None, description="External link if any")
    owner_username: str = Field(..., description="Pin owner username")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When this was scraped")


class PinterestProfile(BaseModel):
    """Pinterest profile model."""

    username: str = Field(..., description="Pinterest username")
    display_name: str = Field(..., description="Display name")
    bio: Optional[str] = Field(None, description="Profile bio")
    profile_image: Optional[str] = Field(None, description="Profile image URL")
    follower_count: int = Field(0, description="Number of followers")
    following_count: int = Field(0, description="Number of following")
    board_count: int = Field(0, description="Number of boards")
    pin_count: int = Field(0, description="Number of pins")
    website: Optional[str] = Field(None, description="Website URL")
    location: Optional[str] = Field(None, description="Location")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When this was scraped")
