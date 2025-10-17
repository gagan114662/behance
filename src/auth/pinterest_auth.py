"""Pinterest authentication module."""

import asyncio
from typing import Optional
from playwright.async_api import Page, BrowserContext


class PinterestAuthenticator:
    """Handle Pinterest authentication."""

    async def login_with_google(
        self,
        page: Page,
        email: str,
        password: str,
        timeout: int = 60000
    ) -> bool:
        """Login to Pinterest using Google OAuth.

        Args:
            page: Playwright page object
            email: Google email
            password: Google password
            timeout: Login timeout in milliseconds

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            print("🔐 Logging into Pinterest with Google...")

            # Navigate to Pinterest login page
            await page.goto('https://www.pinterest.com/login/', wait_until='domcontentloaded', timeout=timeout)
            await page.wait_for_timeout(3000)

            # Click "Continue with Google" button
            print("  🔘 Clicking 'Continue with Google'...")

            # Try multiple selectors for the Google button
            google_button = None
            google_selectors = [
                'div[data-test-id="google-connect-button"]',
                'button[data-provider="google"]',
                'button:has-text("Continue with Google")',
                '[aria-label*="Google"]'
            ]

            for selector in google_selectors:
                try:
                    google_button = await page.wait_for_selector(selector, timeout=5000)
                    if google_button:
                        print(f"  ✓ Found Google button with selector: {selector}")
                        break
                except:
                    continue

            if not google_button:
                print("  ❌ Could not find Google login button")
                return False

            # Click the Google button and check if it opens a popup or navigates
            await google_button.click()
            await page.wait_for_timeout(3000)

            # Check if we're on Google OAuth page (same page navigation)
            current_url = page.url
            if 'accounts.google.com' in current_url:
                print(f"  📍 Navigated to Google OAuth (same page)")
                # Use the main page for Google login
                google_page = page
            else:
                # Check if a popup was opened
                popup_pages = page.context.pages
                if len(popup_pages) > 1:
                    google_page = popup_pages[-1]
                    print(f"  📱 Popup opened: {google_page.url}")
                    await google_page.wait_for_load_state('domcontentloaded')
                else:
                    print("  ❌ Neither popup nor redirect detected")
                    return False

            # Handle Google login
            print("  📧 Entering Google credentials...")

            # Wait for and fill email
            try:
                email_input = await google_page.wait_for_selector('input[type="email"]', timeout=15000)
                await email_input.fill(email)
                await google_page.wait_for_timeout(1000)
                print("  ✓ Email entered")
            except Exception as e:
                print(f"  ❌ Email input error: {e}")
                return False

            # Click Next - try multiple selectors
            next_clicked = False
            next_selectors = [
                '#identifierNext button',
                'button:has-text("Next")',
                'button[type="button"]:has-text("Next")',
                '[id="identifierNext"]'
            ]

            for selector in next_selectors:
                try:
                    next_button = await google_page.wait_for_selector(selector, timeout=3000, state='visible')
                    await next_button.click()
                    print(f"  ✓ Clicked Next with selector: {selector}")
                    next_clicked = True
                    break
                except:
                    continue

            if not next_clicked:
                # Try pressing Enter as fallback
                print("  ⚠️  Next button not found, trying Enter key")
                await email_input.press('Enter')

            await google_page.wait_for_timeout(3000)

            # Wait for and fill password
            try:
                password_input = await google_page.wait_for_selector('input[type="password"]', timeout=15000)
                await password_input.fill(password)
                await google_page.wait_for_timeout(1000)
                print("  ✓ Password entered")
            except Exception as e:
                print(f"  ❌ Password input error: {e}")
                return False

            # Click Next/Sign in
            signin_clicked = False
            signin_selectors = [
                '#passwordNext button',
                'button:has-text("Next")',
                'button[type="button"]:has-text("Next")',
                '[id="passwordNext"]'
            ]

            for selector in signin_selectors:
                try:
                    sign_in_button = await google_page.wait_for_selector(selector, timeout=3000, state='visible')
                    await sign_in_button.click()
                    print(f"  ✓ Clicked sign in with selector: {selector}")
                    signin_clicked = True
                    break
                except:
                    continue

            if not signin_clicked:
                # Try pressing Enter as fallback
                print("  ⚠️  Sign in button not found, trying Enter key")
                await password_input.press('Enter')

            # Wait for redirect back to Pinterest
            print("  ⏳ Waiting for authentication to complete...")
            await page.wait_for_timeout(10000)

            # Close popup if it was a popup
            if google_page != page and not google_page.is_closed():
                await google_page.close()

            # Check if login was successful on main page
            await page.wait_for_timeout(2000)
            current_url = page.url

            print(f"  📍 Current URL: {current_url}")

            # Check for login success indicators
            if 'pinterest.com' in current_url and 'login' not in current_url.lower():
                print("  ✅ Google login successful!")
                return True

            # Check if we can find logged-in indicators
            try:
                # Look for user avatar or profile indicator
                logged_in_indicators = [
                    '[data-test-id="header-profile"]',
                    '[aria-label*="Profile"]',
                    'div[data-test-id="user-menu"]'
                ]

                for indicator in logged_in_indicators:
                    element = await page.query_selector(indicator)
                    if element:
                        print(f"  ✅ Found logged-in indicator: {indicator}")
                        return True
            except:
                pass

            # If still on Pinterest (even if URL unclear), consider it success
            if 'pinterest.com' in current_url:
                print("  ✅ Login appears successful (on Pinterest)")
                return True

            print("  ❌ Login verification failed")
            return False

        except Exception as e:
            print(f"  ❌ Google login error: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def login(
        self,
        page: Page,
        email: str,
        password: str,
        timeout: int = 30000
    ) -> bool:
        """Login to Pinterest.

        Args:
            page: Playwright page object
            email: Pinterest email
            password: Pinterest password
            timeout: Login timeout in milliseconds

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            print("🔐 Logging into Pinterest...")

            # Navigate to login page
            await page.goto('https://www.pinterest.com/login/', wait_until='domcontentloaded', timeout=timeout)
            await page.wait_for_timeout(2000)

            # Fill email
            email_input = await page.wait_for_selector('input[id="email"]', timeout=10000)
            await email_input.fill(email)
            await page.wait_for_timeout(500)

            # Fill password
            password_input = await page.wait_for_selector('input[id="password"]', timeout=10000)
            await password_input.fill(password)
            await page.wait_for_timeout(500)

            # Click login button
            login_button = await page.wait_for_selector('button[type="submit"]', timeout=10000)
            await login_button.click()

            # Wait for navigation after login
            print("  ⏳ Waiting for login to complete...")
            await page.wait_for_timeout(5000)

            # Check if login was successful
            # If we're redirected away from login page, login was likely successful
            current_url = page.url

            if 'login' not in current_url.lower():
                print("  ✅ Login successful!")
                return True
            else:
                # Check for error messages
                error = await page.query_selector('div[data-test-id="error-message"], div:has-text("incorrect")')
                if error:
                    error_text = await error.text_content()
                    print(f"  ❌ Login failed: {error_text}")
                else:
                    print("  ❌ Login failed: Still on login page")
                return False

        except Exception as e:
            print(f"  ❌ Login error: {e}")
            return False

    async def login_with_cookies(
        self,
        context: BrowserContext,
        cookies_path: str
    ) -> bool:
        """Login using saved cookies.

        Args:
            context: Playwright browser context
            cookies_path: Path to cookies file

        Returns:
            bool: True if successful
        """
        try:
            import json
            from pathlib import Path

            cookies_file = Path(cookies_path)
            if not cookies_file.exists():
                print(f"❌ Cookies file not found: {cookies_path}")
                return False

            with open(cookies_file, 'r') as f:
                cookies = json.load(f)

            await context.add_cookies(cookies)
            print("✅ Loaded cookies successfully")
            return True

        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            return False

    async def save_cookies(
        self,
        context: BrowserContext,
        cookies_path: str
    ) -> bool:
        """Save current session cookies.

        Args:
            context: Playwright browser context
            cookies_path: Path to save cookies

        Returns:
            bool: True if successful
        """
        try:
            import json
            from pathlib import Path

            cookies = await context.cookies()

            cookies_file = Path(cookies_path)
            cookies_file.parent.mkdir(parents=True, exist_ok=True)

            with open(cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)

            print(f"✅ Saved cookies to: {cookies_path}")
            return True

        except Exception as e:
            print(f"❌ Error saving cookies: {e}")
            return False
