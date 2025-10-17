#!/usr/bin/env python3
"""Cron job script for autonomous Behance and Pinterest scraping.

This script runs both scrapers and can be scheduled via cron for automated execution.

Example crontab entries:
    # Run daily at 2 AM
    0 2 * * * cd /Users/gaganarora/Desktop/gagan_projects/behance && python3 cron_scraper.py >> logs/cron.log 2>&1

    # Run every 6 hours
    0 */6 * * * cd /Users/gaganarora/Desktop/gagan_projects/behance && python3 cron_scraper.py >> logs/cron.log 2>&1
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Behance imports
from src.browser.manager import BrowserManager, BrowserConfig
from src.extractors.search import SearchExtractor
from src.extractors.project import ProjectExtractor
from src.extractors.image import ImageExtractor
from src.storage.mongo_client import MongoClient, MongoConfig
from src.storage.image_pipeline import ImagePipeline
from src.storage.project_repository import ProjectRepository
from src.storage.image_repository import ImageRepository

# Pinterest imports
from src.extractors.pinterest import (
    PinterestProfileExtractor,
    PinterestBoardExtractor,
    PinterestPinExtractor
)
from src.auth.pinterest_auth import PinterestAuthenticator


class CronScraper:
    """Autonomous scraper for Behance and Pinterest."""

    def __init__(self):
        """Initialize scraper with configuration."""
        self.config = {
            'behance': {
                'urls': [
                    'https://www.behance.net/search/projects?search=magenta',
                    'https://www.behance.net/search/projects?search=branding',
                ],
                'mongodb_url': 'mongodb://localhost:27017',
                'database': 'behance_crawler',
                'output_dir': './behance_images',
                'max_projects': 5,
            },
            'pinterest': {
                'username': 'sangichandresh',
                'mongodb_url': 'mongodb://localhost:27017',
                'database': 'pinterest_crawler',
                'output_dir': './pinterest_images',
                'cookies_path': './pinterest_cookies.json',
                'email': 'gagan@getfoolish.com',
                'password': 'vandanchopra@114',
                'max_pins': 10000,
            }
        }

    def log(self, message: str):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")

    async def scrape_behance(self) -> dict:
        """Scrape Behance projects."""
        self.log("🎨 Starting Behance scraping...")

        config = self.config['behance']

        # Initialize components
        mongo_config = MongoConfig(url=config['mongodb_url'], database=config['database'])
        mongo_client = MongoClient(mongo_config)
        await mongo_client.connect()
        self.log(f"✅ Connected to MongoDB: {config['database']}")

        browser_config = BrowserConfig(
            headless=True,
            stealth_mode=True,
            viewport_width=1920,
            viewport_height=1080
        )
        browser_manager = BrowserManager(browser_config)
        await browser_manager.launch()
        self.log("✅ Browser launched")

        image_pipeline = ImagePipeline(output_dir=config['output_dir'])
        search_extractor = SearchExtractor()
        project_extractor = ProjectExtractor()
        image_extractor = ImageExtractor()
        project_repo = ProjectRepository(mongo_client)
        image_repo = ImageRepository(mongo_client)

        stats = {
            'projects_scraped': 0,
            'images_downloaded': 0,
            'errors': 0
        }

        try:
            context = await browser_manager.create_context()
            page = await context.new_page()

            for search_url in config['urls']:
                self.log(f"🔍 Scraping: {search_url}")

                try:
                    # Extract project links from search
                    # Extract the query from URL
                    import re
                    query_match = re.search(r'search=([^&]+)', search_url)
                    query = query_match.group(1) if query_match else 'design'

                    project_links = await search_extractor.search_projects(page, query, scroll=True)
                    project_links = project_links[:config['max_projects']]
                    self.log(f"  ✅ Found {len(project_links)} project links")

                    # Scrape each project
                    for i, project_url in enumerate(project_links, 1):
                        try:
                            self.log(f"  📦 [{i}/{len(project_links)}] Scraping: {project_url}")

                            await page.goto(project_url, wait_until='domcontentloaded', timeout=30000)
                            await page.wait_for_timeout(3000)

                            # Extract project data
                            project = await project_extractor.extract_from_page(page)
                            self.log(f"    📝 Project: {project.title}")

                            # Save project to database
                            await project_repo.upsert(project)

                            # Extract images
                            images = await image_extractor.extract_from_page(page, project.id)
                            self.log(f"    ✅ Found {len(images)} images")

                            if images:
                                # Save image metadata
                                await image_repo.save_many(images)

                                # Download images
                                # Create project-specific directory with readable name
                                clean_title = "".join(c for c in project.title if c.isalnum() or c in (' ', '-', '_')).strip()
                                clean_owner = "".join(c for c in project.owner_username if c.isalnum() or c in (' ', '-', '_')).strip()
                                folder_name = f"{clean_owner} - {clean_title}"
                                project_dir = Path(config['output_dir']) / folder_name

                                image_pipeline.output_dir = str(project_dir)
                                image_urls = [str(img.url) for img in images]

                                results = await image_pipeline.download_many(image_urls)
                                success_count = sum(1 for r in results if r.success)

                                self.log(f"    ✅ Downloaded {success_count}/{len(images)} images")

                                stats['projects_scraped'] += 1
                                stats['images_downloaded'] += success_count

                        except Exception as e:
                            self.log(f"    ❌ Error scraping project: {e}")
                            stats['errors'] += 1
                            continue

                except Exception as e:
                    self.log(f"❌ Error scraping search URL: {e}")
                    stats['errors'] += 1
                    continue

            await page.close()
            await context.close()

        finally:
            await browser_manager.close()
            await mongo_client.disconnect()

        self.log(f"✅ Behance scraping complete: {stats}")
        return stats

    async def scrape_pinterest(self) -> dict:
        """Scrape Pinterest boards."""
        self.log("📌 Starting Pinterest scraping...")

        config = self.config['pinterest']

        # Initialize components
        mongo_config = MongoConfig(url=config['mongodb_url'], database=config['database'])
        mongo_client = MongoClient(mongo_config)
        await mongo_client.connect()
        self.log(f"✅ Connected to MongoDB: {config['database']}")

        browser_config = BrowserConfig(
            headless=True,
            stealth_mode=True,
            viewport_width=1920,
            viewport_height=1080
        )
        browser_manager = BrowserManager(browser_config)
        await browser_manager.launch()
        self.log("✅ Browser launched")

        image_pipeline = ImagePipeline(output_dir=config['output_dir'])
        profile_extractor = PinterestProfileExtractor()
        board_extractor = PinterestBoardExtractor()
        pin_extractor = PinterestPinExtractor()
        authenticator = PinterestAuthenticator()

        stats = {
            'boards_scraped': 0,
            'pins_scraped': 0,
            'images_downloaded': 0,
            'errors': 0
        }

        try:
            context = await browser_manager.create_context()
            page = await context.new_page()

            # Authenticate
            logged_in = False
            if Path(config['cookies_path']).exists():
                logged_in = await authenticator.login_with_cookies(context, config['cookies_path'])
                self.log(f"  {'✅' if logged_in else '❌'} Cookie authentication")

            if not logged_in and config.get('email') and config.get('password'):
                logged_in = await authenticator.login_with_google(
                    page, config['email'], config['password']
                )
                if logged_in and config.get('cookies_path'):
                    await authenticator.save_cookies(context, config['cookies_path'])
                self.log(f"  {'✅' if logged_in else '❌'} Google authentication")

            if not logged_in:
                self.log("⚠️  Not logged in - content may be limited")

            # Navigate to profile
            profile_url = f"https://www.pinterest.com/{config['username']}/"
            await page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)

            # Click Saved tab
            try:
                saved_tab = await page.wait_for_selector('button:has-text("Saved"), a:has-text("Saved")', timeout=5000)
                await saved_tab.click()
                await page.wait_for_timeout(3000)
                self.log("  ✅ Opened Saved tab")
            except:
                self.log("  ⚠️  Could not click Saved tab")

            # Extract boards
            boards = await board_extractor.extract_boards(page, config['username'])
            self.log(f"  ✅ Found {len(boards)} boards")

            # Save boards to database
            db = mongo_client.database
            if boards:
                for board in boards:
                    await db.pinterest_boards.update_one(
                        {'id': board.id, 'owner_username': board.owner_username},
                        {'$set': board.model_dump()},
                        upsert=True
                    )

            # Scrape each board
            for i, board in enumerate(boards, 1):
                try:
                    self.log(f"  📦 [{i}/{len(boards)}] Scraping board: {board.name}")

                    await page.goto(board.url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(3000)

                    # Extract pins
                    pins = await pin_extractor.extract_pins_from_board(
                        page, board.url, max_pins=config['max_pins']
                    )
                    self.log(f"    ✅ Found {len(pins)} pins")

                    if pins:
                        # Save pins to database
                        for pin in pins:
                            await db.pinterest_pins.update_one(
                                {'id': pin.id},
                                {'$set': pin.model_dump()},
                                upsert=True
                            )

                        # Download images
                        clean_board_name = "".join(c for c in board.name if c.isalnum() or c in (' ', '-', '_')).strip()
                        board_dir = Path(config['output_dir']) / config['username'] / clean_board_name
                        image_pipeline.output_dir = str(board_dir)

                        image_urls = [str(pin.image_url) for pin in pins if pin.image_url]
                        results = await image_pipeline.download_many(image_urls)
                        success_count = sum(1 for r in results if r.success)

                        self.log(f"    ✅ Downloaded {success_count}/{len(image_urls)} images")

                        stats['pins_scraped'] += len(pins)
                        stats['images_downloaded'] += success_count

                    stats['boards_scraped'] += 1

                except Exception as e:
                    self.log(f"    ❌ Error scraping board: {e}")
                    stats['errors'] += 1
                    continue

            await page.close()
            await context.close()

        finally:
            await browser_manager.close()
            await mongo_client.disconnect()

        self.log(f"✅ Pinterest scraping complete: {stats}")
        return stats

    async def run(self):
        """Run both scrapers."""
        self.log("="*60)
        self.log("🚀 STARTING CRON SCRAPER")
        self.log("="*60)

        results = {}

        # Run Behance scraper
        try:
            results['behance'] = await self.scrape_behance()
        except Exception as e:
            self.log(f"❌ Behance scraper failed: {e}")
            results['behance'] = {'error': str(e)}

        # Run Pinterest scraper
        try:
            results['pinterest'] = await self.scrape_pinterest()
        except Exception as e:
            self.log(f"❌ Pinterest scraper failed: {e}")
            results['pinterest'] = {'error': str(e)}

        # Summary
        self.log("="*60)
        self.log("🎉 SCRAPING COMPLETE")
        self.log("="*60)
        self.log(f"Behance: {results.get('behance', {})}")
        self.log(f"Pinterest: {results.get('pinterest', {})}")
        self.log("="*60)

        return results


async def main():
    """Main entry point."""
    scraper = CronScraper()

    try:
        await scraper.run()
        sys.exit(0)
    except Exception as e:
        scraper.log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
