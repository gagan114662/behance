"""Project data extraction from Behance."""

from typing import Dict, Any, List
from bs4 import BeautifulSoup
from playwright.async_api import Page

from src.models.project import Project, ProjectStats


class ProjectExtractor:
    """Extract project data from Behance pages and API responses."""

    def __init__(self):
        """Initialize project extractor."""
        pass

    async def extract_from_page(self, page: Page) -> Project:
        """Extract project data from HTML page using BeautifulSoup.

        Args:
            page: Playwright page object with project page loaded

        Returns:
            Project: Extracted project model
        """
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract project ID and slug from URL
        # URL pattern: https://www.behance.net/gallery/{id}/{slug}
        import re
        current_url = page.url
        url_match = re.search(r'/gallery/(\d+)/([^/?]+)', current_url)
        project_id = int(url_match.group(1)) if url_match else hash(current_url) % (10 ** 8)

        # Extract title - try multiple selectors
        title = "Untitled Project"
        title_selectors = [
            "h1",                        # Most common: single h1 on page
            "div[class*='title'] h1",    # Alternative with title container
            ".project-title"             # Legacy selector
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.text.strip():
                title = title_elem.text.strip()
                break

        # Extract description
        description = ""
        desc_selectors = [
            "div[class*='description']",
            ".project-description",
            "div[class*='ProjectDescription']"
        ]
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem and desc_elem.text.strip():
                description = desc_elem.text.strip()
                break

        # Extract owner information
        owner_username = "unknown"
        owner_selectors = [
            "a[class*='Owner']",         # Discovered selector
            "div[class*='owner'] a",     # Alternative
            ".project-owner a"           # Legacy
        ]
        for selector in owner_selectors:
            owner_elem = soup.select_one(selector)
            if owner_elem and owner_elem.text.strip():
                owner_username = owner_elem.text.strip().split('\n')[0]  # Get first line (username)
                break

        # Extract stats from page
        stats = await self.extract_stats(page)

        # Extract tags from page
        tags = await self.extract_tags(page)

        # Extract metadata
        metadata = await self.extract_metadata(page)

        # Create minimal project with required fields
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # Generate owner ID from username
        owner_id = hash(owner_username) % (10 ** 8)

        return Project(
            id=project_id,
            title=title,
            description=description,
            url=current_url.split('?')[0],  # Clean URL without query params
            published_on=metadata.get("published_on", now),
            created_on=metadata.get("created_on", now),
            modified_on=now,
            stats=stats,
            tags=tags,
            covers={},
            owner_id=owner_id,
            owner_username=owner_username
        )

    async def extract_from_json(self, data: Dict[str, Any]) -> Project:
        """Extract project data from JSON API response.

        Args:
            data: JSON dictionary from Behance API

        Returns:
            Project: Extracted project model
        """
        from datetime import datetime, timezone

        # Parse timestamps - caller ensures strings are provided
        published_on = datetime.fromisoformat(data["published_on"].replace("Z", "+00:00"))
        created_on = datetime.fromisoformat(data["created_on"].replace("Z", "+00:00"))
        modified_on = datetime.fromisoformat(data["modified_on"].replace("Z", "+00:00"))

        # Extract stats
        stats_data = data.get("stats", {})
        stats = ProjectStats(
            views=stats_data.get("views", 0),
            appreciations=stats_data.get("appreciations", 0),
            comments=stats_data.get("comments", 0)
        )

        # Extract covers
        covers = data.get("covers", {})

        # Extract owner info - caller ensures owner_id is present
        owner_id = data["owner_id"]
        owner_username = data.get("owner_username", "unknown")

        return Project(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            url=data["url"],
            published_on=published_on,
            created_on=created_on,
            modified_on=modified_on,
            stats=stats,
            tags=data.get("tags", []),
            covers=covers,
            owner_id=owner_id,
            owner_username=owner_username
        )

    async def extract_metadata(self, page: Page) -> Dict[str, Any]:
        """Extract project metadata from page.

        Args:
            page: Playwright page object

        Returns:
            Dict containing metadata fields
        """
        from datetime import datetime, timezone

        # Try to find metadata elements
        meta_elem = await page.query_selector(".project-metadata")

        # Return metadata with timestamp fields
        now = datetime.now(timezone.utc)
        return {
            "published_on": now,
            "created_on": now,
            "modified_on": now
        }

    async def extract_tags(self, page: Page) -> List[str]:
        """Extract project tags from HTML.

        Args:
            page: Playwright page object

        Returns:
            List of tag strings
        """
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all tag elements
        tag_elements = soup.select(".tag")

        tags = []
        for tag_elem in tag_elements:
            tag_text = tag_elem.text.strip()
            if tag_text:
                tags.append(tag_text)

        return tags

    async def extract_stats(self, page: Page) -> ProjectStats:
        """Extract project statistics from HTML.

        Args:
            page: Playwright page object

        Returns:
            ProjectStats: Extracted statistics
        """
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        import re

        # Extract stats from discovered selector
        stats_elem = soup.select_one("div[class*='stats']")

        views = 0
        appreciations = 0
        comments = 0

        if stats_elem:
            stats_text = stats_elem.text
            # Try to extract numbers from stats text
            # Example: "283\n283 appreciations for Krustyworld✨\n1.7K\n1,694 ..."
            numbers = re.findall(r'[\d,]+\.?\d*[KMB]?', stats_text.replace('\n', ' '))

            # Try to identify which stat is which based on keywords
            if 'appreciation' in stats_text.lower():
                # Find number before "appreciation"
                appr_match = re.search(r'([\d,]+)\s*appreciation', stats_text.lower())
                if appr_match:
                    appreciations = int(appr_match.group(1).replace(',', ''))

            if 'view' in stats_text.lower():
                view_match = re.search(r'([\d,]+\.?\d*[KMB]?)\s*view', stats_text.lower())
                if view_match:
                    views = self._parse_number(view_match.group(1))

            if 'comment' in stats_text.lower():
                comment_match = re.search(r'([\d,]+)\s*comment', stats_text.lower())
                if comment_match:
                    comments = int(comment_match.group(1).replace(',', ''))

        # Fallback: Try individual selectors
        if views == 0:
            views_elem = soup.select_one(".views, .stats-views, [class*='view']")
            if views_elem:
                text = views_elem.text.strip()
                numbers = re.findall(r'[\d,]+', text)
                views = int(numbers[0].replace(',', '')) if numbers else 0

        if appreciations == 0:
            appr_elem = soup.select_one(".appreciations, .stats-appreciations, [class*='appreciation']")
            if appr_elem:
                text = appr_elem.text.strip()
                numbers = re.findall(r'[\d,]+', text)
                appreciations = int(numbers[0].replace(',', '')) if numbers else 0

        if comments == 0:
            comment_elem = soup.select_one(".comments, .stats-comments, [class*='comment']")
            if comment_elem:
                text = comment_elem.text.strip()
                numbers = re.findall(r'[\d,]+', text)
                comments = int(numbers[0].replace(',', '')) if numbers else 0

        return ProjectStats(
            views=views,
            appreciations=appreciations,
            comments=comments
        )

    def _parse_number(self, num_str: str) -> int:
        """Parse number string with K/M/B suffixes.

        Args:
            num_str: Number string like "1.7K" or "2.3M"

        Returns:
            Integer value
        """
        num_str = num_str.replace(',', '').strip()

        multipliers = {
            'K': 1000,
            'M': 1000000,
            'B': 1000000000
        }

        for suffix, multiplier in multipliers.items():
            if suffix in num_str.upper():
                try:
                    value = float(num_str.upper().replace(suffix, ''))
                    return int(value * multiplier)
                except:
                    return 0

        try:
            return int(float(num_str))
        except:
            return 0

    async def extract_covers(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract project cover images from data.

        Args:
            data: Dictionary containing project data

        Returns:
            Dict mapping cover size names to URLs
        """
        covers = data.get("covers", {})
        return covers
