"""User data extraction from Behance."""

from typing import Dict, Any, List
from bs4 import BeautifulSoup
from playwright.async_api import Page

from src.models.user import User, UserStats


class UserExtractor:
    """Extract user data from Behance pages and API responses."""

    def __init__(self):
        """Initialize user extractor."""
        pass

    async def extract_from_page(self, page: Page) -> User:
        """Extract user data from HTML page using BeautifulSoup.

        Args:
            page: Playwright page object with user profile loaded

        Returns:
            User: Extracted user model
        """
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract username from URL
        current_url = page.url
        username = current_url.rstrip('/').split('/')[-1].split('?')[0]

        # Extract display name - try multiple selectors
        display_name = "Unknown User"
        name_selectors = [
            "#profile-display-name a",  # ID selector (most stable)
            ".team-name a",              # Class selector for teams
            "#profile-display-name",     # Fallback to container
        ]
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem and name_elem.text.strip():
                display_name = name_elem.text.strip()
                break

        # Extract location - use dynamic class matching
        location = None
        location_selectors = [
            "div[class*='location']",
            "span[class*='location']",
            ".profile-location"
        ]
        for selector in location_selectors:
            location_elem = soup.select_one(selector)
            if location_elem and location_elem.text.strip():
                location = location_elem.text.strip()
                break

        # Extract stats from HTML (note: actual numbers may be in JSON data)
        stats_data = {}

        # Try to extract follower count
        # Note: May only find text " FOLLOWERS" without number
        followers_elem = soup.select_one("div[class*='follower']")
        if followers_elem:
            text = followers_elem.text.strip()
            # Try to extract number from text
            import re
            numbers = re.findall(r'\d+', text.replace(',', ''))
            stats_data["followers"] = int(numbers[0]) if numbers else 0
        else:
            stats_data["followers"] = 0

        # Try to extract following count
        following_elem = soup.select_one("div[class*='following']")
        if following_elem:
            text = following_elem.text.strip()
            import re
            numbers = re.findall(r'\d+', text.replace(',', ''))
            stats_data["following"] = int(numbers[0]) if numbers else 0
        else:
            stats_data["following"] = 0

        # Set default values for other stats
        stats_data.setdefault("appreciations", 0)
        stats_data.setdefault("views", 0)
        stats_data.setdefault("project_views", 0)

        stats = await self.extract_stats(stats_data)

        # Generate user ID from username hash (since real ID is in JSON)
        user_id = hash(username) % (10 ** 8)

        return User(
            id=user_id,
            username=username,
            display_name=display_name,
            url=current_url.split('?')[0],  # Clean URL without query params
            location=location,
            company=None,
            occupation=None,
            stats=stats,
            social_links=[],
            fields=[]
        )

    async def extract_from_json(self, data: Dict[str, Any]) -> User:
        """Extract user data from JSON API response.

        Args:
            data: JSON dictionary from Behance API

        Returns:
            User: Extracted user model
        """
        # Extract stats
        stats_data = data.get("stats", {})
        stats = await self.extract_stats(stats_data)

        # Extract social links
        social_links = await self.extract_social_links(data)

        # Extract professional fields
        fields = await self.extract_fields(data)

        return User(
            id=data["id"],
            username=data["username"],
            display_name=data["display_name"],
            url=data["url"],
            location=data.get("location"),
            company=data.get("company"),
            occupation=data.get("occupation"),
            stats=stats,
            social_links=social_links,
            fields=fields
        )

    async def extract_stats(self, data: Dict[str, Any]) -> UserStats:
        """Extract user statistics from data.

        Args:
            data: Dictionary containing stats data

        Returns:
            UserStats: Extracted statistics
        """
        return UserStats(
            followers=data.get("followers", 0),
            following=data.get("following", 0),
            appreciations=data.get("appreciations", 0),
            views=data.get("views", 0),
            project_views=data.get("project_views", 0)
        )

    async def extract_social_links(self, data: Dict[str, Any]) -> List[str]:
        """Extract user social media links from data.

        Args:
            data: Dictionary containing user data

        Returns:
            List of social media URLs
        """
        social_links = data.get("social_links", [])
        return social_links

    async def extract_fields(self, data: Dict[str, Any]) -> List[str]:
        """Extract user professional fields from data.

        Args:
            data: Dictionary containing user data

        Returns:
            List of professional field names
        """
        fields = data.get("fields", [])
        return fields
