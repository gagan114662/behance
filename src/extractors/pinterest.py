"""Pinterest extractors for profiles, boards, and pins."""

import re
from typing import List, Optional
from playwright.async_api import Page
from src.models.pinterest import PinterestProfile, PinterestBoard, PinterestPin


class PinterestProfileExtractor:
    """Extract profile information from Pinterest."""

    async def extract_from_page(self, page: Page) -> PinterestProfile:
        """Extract profile data from a Pinterest profile page.

        Args:
            page: Playwright page object

        Returns:
            PinterestProfile: Extracted profile data
        """
        # Get username from URL
        url = page.url
        username_match = re.search(r'pinterest\.com/([^/]+)', url)
        username = username_match.group(1) if username_match else "unknown"

        # Extract display name
        display_name_elem = await page.query_selector('h1[data-test-id="profile-name"]')
        if not display_name_elem:
            display_name_elem = await page.query_selector('div[data-test-id="user-name"]')
        display_name = await display_name_elem.text_content() if display_name_elem else username

        # Extract bio
        bio_elem = await page.query_selector('div[data-test-id="about"]')
        bio = await bio_elem.text_content() if bio_elem else None

        # Extract profile image
        profile_img = await page.query_selector('img[alt*="avatar"], div[data-test-id="user-avatar"] img')
        profile_image = await profile_img.get_attribute('src') if profile_img else None

        # Extract stats (followers, following, boards)
        follower_count = 0
        following_count = 0
        board_count = 0
        pin_count = 0

        # Try to get follower count
        follower_elem = await page.query_selector('div[data-test-id="follower-count"]')
        if follower_elem:
            follower_text = await follower_elem.text_content()
            follower_count = self._parse_count(follower_text)

        # Try to get following count
        following_elem = await page.query_selector('div[data-test-id="following-count"]')
        if following_elem:
            following_text = await following_elem.text_content()
            following_count = self._parse_count(following_text)

        return PinterestProfile(
            username=username,
            display_name=display_name.strip() if display_name else username,
            bio=bio.strip() if bio else None,
            profile_image=profile_image,
            follower_count=follower_count,
            following_count=following_count,
            board_count=board_count,
            pin_count=pin_count
        )

    def _parse_count(self, text: str) -> int:
        """Parse count from text like '1.2k' or '5m'."""
        if not text:
            return 0

        text = text.strip().lower()
        multiplier = 1

        if 'k' in text:
            multiplier = 1000
            text = text.replace('k', '')
        elif 'm' in text:
            multiplier = 1000000
            text = text.replace('m', '')

        try:
            return int(float(text) * multiplier)
        except (ValueError, TypeError):
            return 0


class PinterestBoardExtractor:
    """Extract board information from Pinterest."""

    async def extract_boards(self, page: Page, username: str) -> List[PinterestBoard]:
        """Extract all boards from a profile page.

        Args:
            page: Playwright page object
            username: Pinterest username

        Returns:
            List of PinterestBoard objects
        """
        boards = []

        # Find all board elements FIRST (before scrolling)
        # Pinterest replaces boards with pins when you scroll
        board_elements = await page.query_selector_all('[data-test-id="board-card"]')

        # If we didn't find enough boards, try scrolling to load more
        if len(board_elements) < 5:
            await self._scroll_to_load(page, scrolls=2)
            board_elements = await page.query_selector_all('[data-test-id="board-card"]')

        print(f"  🔍 Processing {len(board_elements)} board elements...")
        for i, elem in enumerate(board_elements, 1):
            try:
                # Enable debug for first 3 boards
                debug = i <= 3
                board = await self._extract_board_from_element(elem, username, debug=debug)
                if board:
                    boards.append(board)
                    print(f"    ✓ Extracted board {i}: {board.name}")
                else:
                    print(f"    ⚠️  Board {i}: extraction returned None")
            except Exception as e:
                print(f"    ❌ Error extracting board {i}: {e}")
                import traceback
                traceback.print_exc()
                continue

        return boards

    async def _extract_board_from_element(self, elem, username: str, debug: bool = False) -> Optional[PinterestBoard]:
        """Extract board data from a board element."""
        # Get board link - try multiple selectors
        link_elem = await elem.query_selector('a[href*="/"][data-test-id="board-card-name"]')
        if not link_elem:
            link_elem = await elem.query_selector('a[data-test-id="board-name"]')
        if not link_elem:
            link_elem = await elem.query_selector('a[href*="/' + username + '/"]')
        if not link_elem:
            link_elem = await elem.query_selector('a[href]')

        if not link_elem:
            if debug:
                print("      ⚠️  No link element found")
            return None

        # Filter out non-board links
        try:
            href = await link_elem.get_attribute('href')
            if debug:
                print(f"      📎 href: {href}")
            if not href:
                if debug:
                    print("      ⚠️  No href")
                return None
            if username not in href:
                if debug:
                    print(f"      ⚠️  Username '{username}' not in href")
                return None
            if '_saved' in href or '_created' in href:
                if debug:
                    print("      ⚠️  href contains _saved or _created")
                return None
        except Exception as e:
            if debug:
                print(f"      ⚠️  Exception checking href: {e}")
            return None

        url = await link_elem.get_attribute('href')
        if url and not url.startswith('http'):
            url = f"https://www.pinterest.com{url}"

        # Extract board ID from URL
        board_id_match = re.search(r'/([^/]+)/?$', url)
        board_id = board_id_match.group(1) if board_id_match else "unknown"

        # Get board name
        name_elem = await elem.query_selector('div[data-test-id="board-card-name"]')
        if not name_elem:
            name_elem = await elem.query_selector('h3, h2')
        name = await name_elem.text_content() if name_elem else board_id

        # Get pin count
        pin_count = 0
        pin_count_elem = await elem.query_selector('div[data-test-id="board-card-pin-count"]')
        if pin_count_elem:
            pin_text = await pin_count_elem.text_content()
            pin_count = self._parse_pin_count(pin_text)

        # Get cover image
        img_elem = await elem.query_selector('img')
        image_url = await img_elem.get_attribute('src') if img_elem else None

        return PinterestBoard(
            id=board_id,
            name=name.strip() if name else board_id,
            url=url,
            pin_count=pin_count,
            image_url=image_url,
            owner_username=username,
            follower_count=0
        )

    def _parse_pin_count(self, text: str) -> int:
        """Parse pin count from text."""
        if not text:
            return 0

        # Extract numbers from text like "24 Pins" or "1.2k Pins"
        numbers = re.findall(r'[\d.]+', text)
        if numbers:
            num = float(numbers[0])
            if 'k' in text.lower():
                return int(num * 1000)
            return int(num)
        return 0

    async def _scroll_to_load(self, page: Page, scrolls: int = 3):
        """Scroll page to load more boards."""
        for _ in range(scrolls):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1000)


class PinterestPinExtractor:
    """Extract pin information from Pinterest."""

    async def extract_pins_from_board(self, page: Page, board_url: str, max_pins: int = 50) -> List[PinterestPin]:
        """Extract pins from a board.

        Args:
            page: Playwright page object (already navigated to board)
            board_url: URL of the board
            max_pins: Maximum number of pins to extract

        Returns:
            List of PinterestPin objects
        """
        # Page is already navigated, just wait a bit
        await page.wait_for_timeout(1000)

        # Get board info
        username_match = re.search(r'pinterest\.com/([^/]+)/', board_url)
        username = username_match.group(1) if username_match else "unknown"

        board_name_match = re.search(r'/([^/]+)/?$', board_url)
        board_name = board_name_match.group(1) if board_name_match else "unknown"

        pins = []

        # Scroll to load pins
        await self._scroll_to_load(page, scrolls=5)

        # Find all pin elements
        pin_elements = await page.query_selector_all('div[data-test-id="pin"]')

        for elem in pin_elements[:max_pins]:
            try:
                pin = await self._extract_pin_from_element(elem, username, board_name)
                if pin:
                    pins.append(pin)
            except Exception as e:
                print(f"Error extracting pin: {e}")
                continue

        return pins

    async def _extract_pin_from_element(self, elem, username: str, board_name: str) -> Optional[PinterestPin]:
        """Extract pin data from a pin element."""
        # Get pin link
        link_elem = await elem.query_selector('a[href*="/pin/"]')
        if not link_elem:
            return None

        url = await link_elem.get_attribute('href')
        if url and not url.startswith('http'):
            url = f"https://www.pinterest.com{url}"

        # Extract pin ID from URL
        pin_id_match = re.search(r'/pin/(\d+)', url)
        pin_id = pin_id_match.group(1) if pin_id_match else "unknown"

        # Get image
        img_elem = await elem.query_selector('img')
        image_url = await img_elem.get_attribute('src') if img_elem else None

        # Get title/description
        title_elem = await elem.query_selector('h3, div[data-test-id="pin-title"]')
        title = await title_elem.text_content() if title_elem else None

        return PinterestPin(
            id=pin_id,
            title=title.strip() if title else None,
            url=url,
            image_url=image_url or "",
            board_name=board_name,
            owner_username=username
        )

    async def _scroll_to_load(self, page: Page, scrolls: int = 5):
        """Scroll page to load more pins."""
        for _ in range(scrolls):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1500)
