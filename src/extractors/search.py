"""Search results extraction from Behance."""

from typing import List
from bs4 import BeautifulSoup
from playwright.async_api import Page


class SearchExtractor:
    """Extract project links and data from Behance search results."""

    def __init__(self):
        """Initialize search extractor."""
        pass

    async def extract_project_links(self, page: Page) -> List[str]:
        """Extract all project links from search results page.

        Args:
            page: Playwright page object with search results loaded

        Returns:
            List of project URLs
        """
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        project_links = []
        seen_urls = set()

        # Discovered selector: a[href*='/gallery/']
        link_selectors = [
            "a[href*='/gallery/']",         # Most reliable
            "div[class*='ProjectCover'] a",  # Project card links
            ".project-link"                  # Legacy selector
        ]

        for selector in link_selectors:
            link_elements = soup.select(selector)

            for link_elem in link_elements:
                href = link_elem.get('href')

                if not href:
                    continue

                # Build full URL if relative
                if href.startswith('/'):
                    full_url = f"https://www.behance.net{href}"
                else:
                    full_url = href

                # Extract base URL without query params for deduplication
                base_url = full_url.split('?')[0]

                if base_url not in seen_urls and '/gallery/' in base_url:
                    seen_urls.add(base_url)
                    project_links.append(full_url)

        return project_links

    async def extract_user_links(self, page: Page) -> List[str]:
        """Extract all user profile links from search results page.

        Args:
            page: Playwright page object with search results loaded

        Returns:
            List of user profile URLs
        """
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        user_links = []
        seen_urls = set()

        # Extract user profile links (avoid gallery links)
        link_elements = soup.select("a[href^='/'][href]:not([href*='/gallery/'])")

        for link_elem in link_elements:
            href = link_elem.get('href')

            if not href or href in ['/', '/search', '/discover']:
                continue

            # Skip footer and nav links
            if any(skip in href for skip in ['/about', '/contact', '/terms', '/privacy', '/help']):
                continue

            # Build full URL
            full_url = f"https://www.behance.net{href}" if href.startswith('/') else href
            base_url = full_url.split('?')[0]

            # Simple username pattern: /username (no additional path)
            import re
            if re.match(r'^https://www\.behance\.net/[a-zA-Z0-9_-]+$', base_url):
                if base_url not in seen_urls:
                    seen_urls.add(base_url)
                    user_links.append(full_url)

        return user_links

    async def scroll_to_load_more(self, page: Page, scroll_count: int = 3) -> None:
        """Scroll down to trigger infinite scroll and load more results.

        Args:
            page: Playwright page object
            scroll_count: Number of times to scroll (default: 3)
        """
        for i in range(scroll_count):
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for content to load
            await page.wait_for_timeout(2000)

            # Check if "Load More" button exists and click it
            load_more_button = await page.query_selector("button:has-text('Load More')")
            if load_more_button:
                await load_more_button.click()
                await page.wait_for_timeout(2000)

    async def search_projects(self, page: Page, query: str, scroll: bool = True) -> List[str]:
        """Search for projects and extract all links.

        Args:
            page: Playwright page object
            query: Search query string
            scroll: Whether to scroll to load more results

        Returns:
            List of project URLs
        """
        # Navigate to search page
        search_url = f"https://www.behance.net/search/projects?search={query}"
        await page.goto(search_url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Scroll to load more results if requested
        if scroll:
            await self.scroll_to_load_more(page, scroll_count=3)

        # Extract project links
        return await self.extract_project_links(page)

    async def get_trending_projects(self, page: Page, scroll: bool = True) -> List[str]:
        """Get trending/featured project links.

        Args:
            page: Playwright page object
            scroll: Whether to scroll to load more results

        Returns:
            List of project URLs
        """
        # Try featured/discover pages
        urls_to_try = [
            "https://www.behance.net/featured",
            "https://www.behance.net/discover",
        ]

        for url in urls_to_try:
            try:
                await page.goto(url, wait_until="networkidle", timeout=10000)
                await page.wait_for_timeout(2000)

                if scroll:
                    await self.scroll_to_load_more(page, scroll_count=2)

                links = await self.extract_project_links(page)
                if links:
                    return links
            except:
                continue

        return []

    async def get_user_projects(self, page: Page, username: str) -> List[str]:
        """Get all project links from a user's profile.

        Args:
            page: Playwright page object
            username: Behance username

        Returns:
            List of project URLs
        """
        # Navigate to user profile
        profile_url = f"https://www.behance.net/{username}"
        await page.goto(profile_url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Scroll to load all projects
        await self.scroll_to_load_more(page, scroll_count=5)

        # Extract project links
        return await self.extract_project_links(page)
