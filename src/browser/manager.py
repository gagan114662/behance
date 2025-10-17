"""Browser manager for Playwright automation with stealth support."""

from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
from playwright.async_api import Browser, BrowserContext, async_playwright


class BrowserConfig(BaseModel):
    """Browser configuration model."""

    headless: bool = Field(default=True, description="Run browser in headless mode")
    user_data_dir: Optional[str] = Field(None, description="User data directory path")
    viewport_width: int = Field(default=1920, description="Viewport width in pixels")
    viewport_height: int = Field(default=1080, description="Viewport height in pixels")
    stealth_mode: bool = Field(default=False, description="Enable stealth evasions")

    @field_validator("viewport_width")
    @classmethod
    def validate_viewport_width(cls, v: int) -> int:
        """Validate viewport width is positive."""
        if v <= 0:
            raise ValueError("viewport_width must be positive")
        return v

    @field_validator("viewport_height")
    @classmethod
    def validate_viewport_height(cls, v: int) -> int:
        """Validate viewport height is positive."""
        if v <= 0:
            raise ValueError("viewport_height must be positive")
        return v


class BrowserManager:
    """Manages browser lifecycle and context creation."""

    def __init__(self, config: BrowserConfig) -> None:
        """Initialize browser manager with configuration.

        Args:
            config: Browser configuration settings
        """
        self.config = config
        self.browser: Optional[Browser] = None
        self.contexts: list[BrowserContext] = []
        self._playwright = None

    async def launch(self) -> None:
        """Launch browser instance with configured settings."""
        self._playwright = await async_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]

        if self.config.stealth_mode:
            launch_args.extend([
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ])

        launch_options: dict[str, Any] = {
            "headless": self.config.headless,
            "args": launch_args,
        }

        if self.config.user_data_dir:
            launch_options["user_data_dir"] = self.config.user_data_dir

        self.browser = await self._playwright.chromium.launch(**launch_options)

    async def create_context(self) -> BrowserContext:
        """Create a new browser context.

        Returns:
            New browser context
        """
        # Caller is responsible for calling launch() first
        context_options: dict[str, Any] = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
        }

        context = await self.browser.new_context(**context_options)

        # Track context
        self.contexts.append(context)

        return context

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        self.contexts.clear()
