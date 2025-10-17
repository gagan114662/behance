#!/usr/bin/env python3
"""Production Pinterest scraper with CLI interface."""

import asyncio
import argparse
from pathlib import Path
from typing import Set
import sys

from src.browser.manager import BrowserManager, BrowserConfig
from src.extractors.pinterest import (
    PinterestProfileExtractor,
    PinterestBoardExtractor,
    PinterestPinExtractor
)
from src.storage.mongo_client import MongoClient, MongoConfig
from src.storage.image_pipeline import ImagePipeline
from src.auth.pinterest_auth import PinterestAuthenticator


class PinterestScraper:
    """Main scraper orchestrator for Pinterest image extraction."""

    def __init__(
        self,
        mongodb_url: str = "mongodb://localhost:27017",
        database: str = "pinterest_crawler",
        headless: bool = True,
        output_dir: str = "./pinterest_images",
        email: str = None,
        password: str = None,
        cookies_path: str = None
    ):
        """Initialize scraper.

        Args:
            mongodb_url: MongoDB connection URL
            database: Database name
            headless: Run browser in headless mode
            output_dir: Directory to save downloaded images
            email: Pinterest email for authentication
            password: Pinterest password for authentication
            cookies_path: Path to saved cookies file
        """
        self.mongodb_url = mongodb_url
        self.database = database
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.email = email
        self.password = password
        self.cookies_path = cookies_path

        # Initialize components
        self.mongo_client = None
        self.browser_manager = None
        self.image_pipeline = None
        self.authenticator = PinterestAuthenticator()

        # Extractors
        self.profile_extractor = PinterestProfileExtractor()
        self.board_extractor = PinterestBoardExtractor()
        self.pin_extractor = PinterestPinExtractor()

        # Track processed URLs
        self.processed_boards: Set[str] = set()

    async def _extract_pins_from_current_page(self, page, username: str, max_pins: int = 100):
        """Extract pins from the current page (e.g., saved pins page)."""
        from src.models.pinterest import PinterestPin
        import re

        pins = []
        pin_elements = await page.query_selector_all('div[data-test-id="pin"]')

        for elem in pin_elements[:max_pins]:
            try:
                # Get pin link
                link_elem = await elem.query_selector('a[href*="/pin/"]')
                if not link_elem:
                    continue

                url = await link_elem.get_attribute('href')
                if url and not url.startswith('http'):
                    url = f"https://www.pinterest.com{url}"

                # Extract pin ID from URL
                pin_id_match = re.search(r'/pin/(\d+)', url)
                pin_id = pin_id_match.group(1) if pin_id_match else f"pin_{len(pins)}"

                # Get image
                img_elem = await elem.query_selector('img')
                image_url = await img_elem.get_attribute('src') if img_elem else None

                if not image_url:
                    continue

                # Get title/description
                title_elem = await elem.query_selector('h3, div[data-test-id="pin-title"]')
                title = await title_elem.text_content() if title_elem else None

                pin = PinterestPin(
                    id=pin_id,
                    title=title.strip() if title else None,
                    url=url,
                    image_url=image_url,
                    board_name="saved_pins",
                    owner_username=username
                )
                pins.append(pin)
            except Exception as e:
                print(f"    ⚠️  Error extracting pin: {e}")
                continue

        return pins

    async def setup(self):
        """Setup MongoDB and browser connections."""
        print("🔧 Setting up Pinterest scraper...")

        # Connect to MongoDB
        mongo_config = MongoConfig(url=self.mongodb_url, database=self.database)
        self.mongo_client = MongoClient(mongo_config)
        await self.mongo_client.connect()
        print(f"✅ Connected to MongoDB: {self.database}")

        # Initialize image pipeline
        self.image_pipeline = ImagePipeline(output_dir=str(self.output_dir))

        # Launch browser
        browser_config = BrowserConfig(
            headless=self.headless,
            stealth_mode=True,
            viewport_width=1920,
            viewport_height=1080
        )
        self.browser_manager = BrowserManager(browser_config)
        await self.browser_manager.launch()
        print("✅ Browser launched")

    async def cleanup(self):
        """Cleanup connections."""
        print("\n🧹 Cleaning up...")
        if self.browser_manager:
            await self.browser_manager.close()
        if self.mongo_client:
            await self.mongo_client.disconnect()
        print("✅ Cleanup complete")

    async def scrape_profile(self, username: str, max_boards: int = None, max_pins_per_board: int = 50, scroll_boards: int = 5, scrape_saved: bool = True) -> dict:
        """Scrape all boards and pins from a Pinterest profile.

        Args:
            username: Pinterest username
            max_boards: Maximum number of boards to scrape (None for all)
            max_pins_per_board: Maximum pins to scrape per board
            scrape_saved: If True, scrape saved pins instead of created boards

        Returns:
            Dictionary with scraping statistics
        """
        print(f"\n👤 Scraping Pinterest profile: {username}")

        context = await self.browser_manager.create_context()
        page = await context.new_page()

        stats = {
            'boards_scraped': 0,
            'pins_scraped': 0,
            'images_downloaded': 0,
            'boards': []
        }

        try:
            # Handle authentication
            logged_in = False

            # Try cookies first
            if self.cookies_path:
                logged_in = await self.authenticator.login_with_cookies(context, self.cookies_path)

            # If no cookies or cookies failed, try email/password
            if not logged_in and self.email and self.password:
                # Try Google login first (more common)
                logged_in = await self.authenticator.login_with_google(page, self.email, self.password)

                # If Google login failed, try direct Pinterest login
                if not logged_in:
                    print("  ℹ️  Google login failed, trying direct Pinterest login...")
                    logged_in = await self.authenticator.login(page, self.email, self.password)

                # Save cookies for future use
                if logged_in and self.cookies_path:
                    await self.authenticator.save_cookies(context, self.cookies_path)

            if not logged_in:
                print("⚠️  WARNING: Not logged in - Pinterest may limit content!")
                print("   Use --email and --password to login, or provide --cookies-path")

            # Navigate to profile to see boards
            profile_url = f"https://www.pinterest.com/{username}/"
            print(f"\n🌐 Navigating to profile: {profile_url}")

            try:
                await page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
            except Exception:
                # Try with just load event
                await page.goto(profile_url, wait_until='load', timeout=30000)
            await page.wait_for_timeout(5000)

            # Try to close any modals
            try:
                close_button = await page.query_selector('[aria-label="close"], button:has-text("×")')
                if close_button:
                    await close_button.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Extract profile data
            print("📊 Extracting profile data...")
            profile = await self.profile_extractor.extract_from_page(page)
            print(f"  ✅ Profile: {profile.display_name}")
            print(f"  📌 Followers: {profile.follower_count}")
            print(f"  👥 Following: {profile.following_count}")

            # Save profile to MongoDB
            db = self.mongo_client.database
            await db.pinterest_profiles.update_one(
                {'username': profile.username},
                {'$set': profile.model_dump()},
                upsert=True
            )
            print("  💾 Saved profile to database")

            # Click on Saved or Created tab
            if scrape_saved:
                print(f"\n📌 Clicking 'Saved' tab...")
                try:
                    # Try to click the Saved tab
                    saved_tab = await page.wait_for_selector('button:has-text("Saved"), a:has-text("Saved")', timeout=5000)
                    await saved_tab.click()
                    await page.wait_for_timeout(3000)
                    print("  ✅ Opened Saved tab")
                except Exception as e:
                    print(f"  ⚠️  Could not click Saved tab: {e}")
            else:
                print(f"\n📌 Clicking 'Created' tab...")
                try:
                    created_tab = await page.wait_for_selector('button:has-text("Created"), a:has-text("Created")', timeout=5000)
                    await created_tab.click()
                    await page.wait_for_timeout(3000)
                    print("  ✅ Opened Created tab")
                except Exception as e:
                    print(f"  ⚠️  Could not click Created tab: {e}")

            # Extract boards (now works for both Saved and Created)
            print(f"\n📋 Extracting boards...")
            boards = await self.board_extractor.extract_boards(page, username)

            # Limit boards if specified
            if max_boards:
                boards = boards[:max_boards]
                print(f"  ⚡ Processing first {max_boards} boards")

            # Save boards to MongoDB
            if boards:
                await db.pinterest_boards.insert_many([b.model_dump() for b in boards])
                print(f"  💾 Saved {len(boards)} boards to database")

            # Scrape each board
            for i, board in enumerate(boards, 1):
                if board.url in self.processed_boards:
                    print(f"\n  ⏭️  [{i}/{len(boards)}] Skipping board: {board.name} (already processed)")
                    continue

                print(f"\n📦 [{i}/{len(boards)}] Processing board: {board.name}")
                print(f"  🔗 URL: {board.url}")
                print(f"  📌 Pins: {board.pin_count}")

                try:
                    # Navigate to board page
                    try:
                        await page.goto(board.url, wait_until='domcontentloaded', timeout=30000)
                    except Exception:
                        await page.goto(board.url, wait_until='load', timeout=30000)
                    await page.wait_for_timeout(3000)

                    # Extract pins from board
                    pins = await self.pin_extractor.extract_pins_from_board(
                        page, board.url, max_pins=max_pins_per_board
                    )
                    print(f"  ✅ Found {len(pins)} pins")

                    if pins:
                        # Save pins to MongoDB
                        await db.pinterest_pins.insert_many([p.model_dump() for p in pins])
                        print(f"  💾 Saved {len(pins)} pins to database")

                        # Download images
                        print(f"  ⬇️  Downloading images...")
                        image_urls = [str(pin.image_url) for pin in pins if pin.image_url]

                        # Create board-specific directory using board name
                        # Clean board name for folder
                        clean_board_name = "".join(c for c in board.name if c.isalnum() or c in (' ', '-', '_')).strip()
                        board_dir = self.output_dir / username / clean_board_name
                        self.image_pipeline.output_dir = str(board_dir)

                        # Download images concurrently
                        results = await self.image_pipeline.download_many(image_urls)
                        success_count = sum(1 for r in results if r.success)
                        print(f"  ✅ Downloaded {success_count}/{len(image_urls)} images")

                        stats['pins_scraped'] += len(pins)
                        stats['images_downloaded'] += success_count

                    self.processed_boards.add(board.url)
                    stats['boards_scraped'] += 1
                    stats['boards'].append({
                        'name': board.name,
                        'pins': len(pins),
                        'images_downloaded': success_count if pins else 0
                    })

                    # Rate limiting between boards
                    if i < len(boards):
                        await asyncio.sleep(2)

                except Exception as e:
                    print(f"  ❌ Error scraping board: {e}")
                    continue

            return stats

        finally:
            await page.close()
            await context.close()


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape images from Pinterest profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all boards from a profile
  python scrape_pinterest_images.py --username sangichandresh

  # Scrape first 5 boards only
  python scrape_pinterest_images.py --username sangichandresh --max-boards 5

  # Scrape with custom pins per board limit
  python scrape_pinterest_images.py --username sangichandresh --max-pins 100

  # Run in visible browser mode (for debugging)
  python scrape_pinterest_images.py --username sangichandresh --no-headless

  # Custom output directory
  python scrape_pinterest_images.py --username sangichandresh --output ./my_pinterest_images
        """
    )

    parser.add_argument('--username', type=str, required=True, help='Pinterest username to scrape')
    parser.add_argument('--max-boards', type=int, help='Maximum boards to scrape (default: all)')
    parser.add_argument('--max-pins', type=int, default=50, help='Maximum pins per board (default: 50)')
    parser.add_argument('--output', type=str, default='./pinterest_images', help='Output directory for images')
    parser.add_argument('--mongodb', type=str, default='mongodb://localhost:27017', help='MongoDB URL')
    parser.add_argument('--database', type=str, default='pinterest_crawler', help='Database name')
    parser.add_argument('--no-headless', action='store_true', help='Run browser in visible mode')
    parser.add_argument('--email', type=str, help='Pinterest email for authentication')
    parser.add_argument('--password', type=str, help='Pinterest password for authentication')
    parser.add_argument('--cookies-path', type=str, default='./pinterest_cookies.json', help='Path to cookies file')

    args = parser.parse_args()

    # Initialize scraper
    scraper = PinterestScraper(
        mongodb_url=args.mongodb,
        database=args.database,
        headless=not args.no_headless,
        output_dir=args.output,
        email=args.email,
        password=args.password,
        cookies_path=args.cookies_path
    )

    try:
        # Setup
        await scraper.setup()

        # Scrape profile
        stats = await scraper.scrape_profile(
            username=args.username,
            max_boards=args.max_boards,
            max_pins_per_board=args.max_pins
        )

        # Summary
        print(f"\n{'='*60}")
        print(f"🎉 Scraping Complete!")
        print(f"{'='*60}")
        print(f"📊 Boards scraped: {stats['boards_scraped']}")
        print(f"📌 Pins scraped: {stats['pins_scraped']}")
        print(f"🖼️  Images downloaded: {stats['images_downloaded']}")
        print(f"💾 Images saved to: {args.output}/{args.username}/")
        print(f"🗄️  Data saved to MongoDB: {args.database}")
        print(f"\n📋 Board Summary:")
        for board in stats['boards']:
            print(f"  • {board['name']}: {board['pins']} pins, {board['images_downloaded']} images")
        print(f"{'='*60}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
