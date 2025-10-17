#!/usr/bin/env python3
"""Production Behance image scraper with CLI interface."""

import asyncio
import argparse
from pathlib import Path
from typing import List, Set
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.browser.manager import BrowserManager, BrowserConfig
from src.extractors.search import SearchExtractor
from src.extractors.project import ProjectExtractor
from src.extractors.image import ImageExtractor
from src.extractors.user import UserExtractor
from src.storage.mongo_client import MongoClient, MongoConfig
from src.storage.project_repository import ProjectRepository
from src.storage.image_repository import ImageRepository
from src.storage.user_repository import UserRepository
from src.storage.image_pipeline import ImagePipeline


class BehanceScraper:
    """Main scraper orchestrator for Behance image extraction."""

    def __init__(
        self,
        mongodb_url: str = "mongodb://localhost:27017",
        database: str = "behance_crawler",
        headless: bool = True,
        output_dir: str = "./behance_images"
    ):
        """Initialize scraper.

        Args:
            mongodb_url: MongoDB connection URL
            database: Database name
            headless: Run browser in headless mode
            output_dir: Directory to save downloaded images
        """
        self.mongodb_url = mongodb_url
        self.database = database
        self.headless = headless
        self.output_dir = Path(output_dir)

        # Initialize components (will be set in setup())
        self.mongo_client = None
        self.browser_manager = None
        self.project_repo = None
        self.image_repo = None
        self.user_repo = None
        self.image_pipeline = None

        # Extractors
        self.search_extractor = SearchExtractor()
        self.project_extractor = ProjectExtractor()
        self.image_extractor = ImageExtractor()
        self.user_extractor = UserExtractor()

        # Track processed URLs to avoid duplicates
        self.processed_projects: Set[str] = set()

    async def setup(self):
        """Setup MongoDB and browser connections."""
        print("🔧 Setting up scraper...")

        # Connect to MongoDB
        mongo_config = MongoConfig(url=self.mongodb_url, database=self.database)
        self.mongo_client = MongoClient(mongo_config)
        await self.mongo_client.connect()
        print(f"✅ Connected to MongoDB: {self.database}")

        # Initialize repositories
        self.project_repo = ProjectRepository(self.mongo_client)
        self.image_repo = ImageRepository(self.mongo_client)
        self.user_repo = UserRepository(self.mongo_client)

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

    async def scrape_search(self, query: str, max_projects: int = 10) -> int:
        """Scrape projects from search results.

        Args:
            query: Search query
            max_projects: Maximum number of projects to scrape

        Returns:
            Number of projects scraped
        """
        print(f"\n🔍 Searching for: '{query}'")

        context = await self.browser_manager.create_context()
        page = await context.new_page()

        try:
            # Search and get project links
            project_links = await self.search_extractor.search_projects(
                page, query, scroll=True
            )
            print(f"📋 Found {len(project_links)} project links")

            # Limit to max_projects
            project_links = project_links[:max_projects]

            # Scrape each project
            count = 0
            for i, project_url in enumerate(project_links, 1):
                if project_url in self.processed_projects:
                    print(f"⏭️  [{i}/{len(project_links)}] Skipping (already processed): {project_url}")
                    continue

                print(f"\n📦 [{i}/{len(project_links)}] Processing: {project_url}")

                try:
                    await self.scrape_project(page, project_url)
                    self.processed_projects.add(project_url)
                    count += 1

                    # Rate limiting: wait between projects
                    if i < len(project_links):
                        await asyncio.sleep(3)  # 3 second delay

                except Exception as e:
                    print(f"❌ Error scraping project: {e}")
                    continue

            print(f"\n✅ Scraped {count} new projects from search")
            return count

        finally:
            await page.close()
            await context.close()

    async def scrape_project(self, page, project_url: str):
        """Scrape a single project page.

        Args:
            page: Playwright page object
            project_url: URL of the project
        """
        # Navigate to project
        await page.goto(project_url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Extract project data
        project = await self.project_extractor.extract_from_page(page)
        print(f"  📝 Project: {project.title}")
        print(f"  👤 Owner: {project.owner_username}")

        # Save project to MongoDB
        await self.project_repo.upsert(project)
        print(f"  💾 Saved project to database")

        # Extract images
        images = await self.image_extractor.extract_from_page(page, project.id)
        print(f"  🖼️  Found {len(images)} images")

        if images:
            # Save image metadata to MongoDB
            await self.image_repo.save_many(images)
            print(f"  💾 Saved image metadata to database")

            # Download images
            print(f"  ⬇️  Downloading images...")
            image_urls = [str(img.url) for img in images]

            # Create project-specific directory
            project_dir = self.output_dir / str(project.id)
            self.image_pipeline.output_dir = str(project_dir)

            # Download images concurrently
            results = await self.image_pipeline.download_many(image_urls)
            success_count = sum(1 for r in results if r.success)
            print(f"  ✅ Downloaded {success_count}/{len(images)} images")

    async def scrape_user(self, username: str, max_projects: int = 10) -> int:
        """Scrape all projects from a user profile.

        Args:
            username: Behance username
            max_projects: Maximum number of projects to scrape

        Returns:
            Number of projects scraped
        """
        print(f"\n👤 Scraping user: {username}")

        context = await self.browser_manager.create_context()
        page = await context.new_page()

        try:
            # Navigate to profile
            profile_url = f"https://www.behance.net/{username}"
            await page.goto(profile_url, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Extract user data
            user = await self.user_extractor.extract_from_page(page)
            print(f"  📝 User: {user.display_name}")
            print(f"  📍 Location: {user.location or 'N/A'}")

            # Save user to MongoDB
            await self.user_repo.save(user)
            print(f"  💾 Saved user to database")

            # Get project links
            project_links = await self.search_extractor.get_user_projects(page, username)
            print(f"  📋 Found {len(project_links)} projects")

            # Limit to max_projects
            project_links = project_links[:max_projects]

            # Scrape each project
            count = 0
            for i, project_url in enumerate(project_links, 1):
                if project_url in self.processed_projects:
                    print(f"  ⏭️  [{i}/{len(project_links)}] Skipping (already processed)")
                    continue

                print(f"\n  📦 [{i}/{len(project_links)}] Processing project...")

                try:
                    await self.scrape_project(page, project_url)
                    self.processed_projects.add(project_url)
                    count += 1

                    # Rate limiting
                    if i < len(project_links):
                        await asyncio.sleep(3)

                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    continue

            print(f"\n✅ Scraped {count} new projects from user {username}")
            return count

        finally:
            await page.close()
            await context.close()

    async def scrape_trending(self, max_projects: int = 10) -> int:
        """Scrape trending/featured projects.

        Args:
            max_projects: Maximum number of projects to scrape

        Returns:
            Number of projects scraped
        """
        print(f"\n🔥 Scraping trending projects...")

        context = await self.browser_manager.create_context()
        page = await context.new_page()

        try:
            # Get trending project links
            project_links = await self.search_extractor.get_trending_projects(page, scroll=True)
            print(f"📋 Found {len(project_links)} trending projects")

            # Limit to max_projects
            project_links = project_links[:max_projects]

            # Scrape each project
            count = 0
            for i, project_url in enumerate(project_links, 1):
                if project_url in self.processed_projects:
                    print(f"⏭️  [{i}/{len(project_links)}] Skipping (already processed)")
                    continue

                print(f"\n📦 [{i}/{len(project_links)}] Processing project...")

                try:
                    await self.scrape_project(page, project_url)
                    self.processed_projects.add(project_url)
                    count += 1

                    # Rate limiting
                    if i < len(project_links):
                        await asyncio.sleep(3)

                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue

            print(f"\n✅ Scraped {count} new trending projects")
            return count

        finally:
            await page.close()
            await context.close()


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape images from Behance projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for projects and download images
  python scrape_behance_images.py --search "web design" --max 20

  # Scrape a specific user's projects
  python scrape_behance_images.py --user adobe --max 10

  # Scrape trending projects
  python scrape_behance_images.py --trending --max 15

  # Run in visible browser mode (for debugging)
  python scrape_behance_images.py --search "logo" --no-headless

  # Custom output directory
  python scrape_behance_images.py --search "illustration" --output ./my_images
        """
    )

    parser.add_argument('--search', type=str, help='Search query for projects')
    parser.add_argument('--user', type=str, help='Behance username to scrape')
    parser.add_argument('--trending', action='store_true', help='Scrape trending projects')
    parser.add_argument('--max', type=int, default=10, help='Maximum projects to scrape (default: 10)')
    parser.add_argument('--output', type=str, default='./behance_images', help='Output directory for images')
    parser.add_argument('--mongodb', type=str, default='mongodb://localhost:27017', help='MongoDB URL')
    parser.add_argument('--database', type=str, default='behance_crawler', help='Database name')
    parser.add_argument('--no-headless', action='store_true', help='Run browser in visible mode')

    args = parser.parse_args()

    # Validate arguments
    if not any([args.search, args.user, args.trending]):
        parser.error("Must specify one of: --search, --user, or --trending")

    # Initialize scraper
    scraper = BehanceScraper(
        mongodb_url=args.mongodb,
        database=args.database,
        headless=not args.no_headless,
        output_dir=args.output
    )

    try:
        # Setup
        await scraper.setup()

        # Execute scraping based on mode
        total_scraped = 0

        if args.search:
            total_scraped = await scraper.scrape_search(args.search, max_projects=args.max)

        elif args.user:
            total_scraped = await scraper.scrape_user(args.user, max_projects=args.max)

        elif args.trending:
            total_scraped = await scraper.scrape_trending(max_projects=args.max)

        # Summary
        print(f"\n{'='*60}")
        print(f"🎉 Scraping Complete!")
        print(f"{'='*60}")
        print(f"📊 Total projects scraped: {total_scraped}")
        print(f"💾 Images saved to: {args.output}")
        print(f"🗄️  Data saved to MongoDB: {args.database}")
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
