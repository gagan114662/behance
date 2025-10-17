"""Stealth plugin for browser automation anti-detection."""

import hashlib
import random
from typing import Optional
from playwright.async_api import Page


class StealthPlugin:
    """Plugin for applying stealth evasions to browser pages."""

    def __init__(self) -> None:
        """Initialize stealth plugin."""
        self.enabled = True
        self.evasions = {
            "webdriver": True,
            "chrome_runtime": True,
            "permissions": True,
            "plugins": True,
        }

    async def apply_evasions(self, page: Page) -> None:
        """Apply all stealth evasions to remove webdriver traces.

        Args:
            page: Playwright page instance
        """
        # Remove webdriver property
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Override navigator properties
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        # Override chrome detection
        await page.add_init_script("""
            window.chrome = {
                runtime: {}
            };
        """)

    async def apply_chrome_runtime(self, page: Page) -> None:
        """Apply chrome runtime evasion.

        Args:
            page: Playwright page instance
        """
        await page.add_init_script("""
            if (!window.chrome) {
                window.chrome = {};
            }
            window.chrome.runtime = {
                connect: function() {},
                sendMessage: function() {}
            };
        """)

    async def apply_permissions(self, page: Page) -> None:
        """Apply permissions API evasion.

        Args:
            page: Playwright page instance
        """
        await page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    async def override_webgl(
        self,
        page: Page,
        vendor: Optional[str] = None,
        renderer: Optional[str] = None,
    ) -> None:
        """Override WebGL vendor and renderer information.

        Args:
            page: Playwright page instance
            vendor: WebGL vendor string
            renderer: WebGL renderer string
        """
        vendor_str = vendor or "Intel Inc."
        renderer_str = renderer or "Intel Iris OpenGL Engine"

        script = f"""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return '{vendor_str}';
                }}
                if (parameter === 37446) {{
                    return '{renderer_str}';
                }}
                return getParameter.apply(this, arguments);
            }};
        """

        await page.add_init_script(script)


class FingerprintGenerator:
    """Generator for browser fingerprints to avoid detection."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize fingerprint generator.

        Args:
            seed: Optional seed for consistent fingerprint generation
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def generate_canvas_fingerprint(self) -> str:
        """Generate a random canvas fingerprint hash.

        Returns:
            Hexadecimal hash string
        """
        if self.seed is not None:
            # Use seed for consistent generation
            random.seed(self.seed)
            data = f"canvas_{self.seed}_{random.randint(1000, 9999)}"
        else:
            # Random generation
            data = f"canvas_{random.random()}_{random.randint(10000, 99999)}"

        return hashlib.sha256(data.encode()).hexdigest()

    def generate_webgl_fingerprint(self) -> str:
        """Generate a random WebGL fingerprint hash.

        Returns:
            Hexadecimal hash string
        """
        if self.seed is not None:
            # Use seed for consistent generation
            random.seed(self.seed + 1)  # Different seed offset for variety
            data = f"webgl_{self.seed}_{random.randint(1000, 9999)}"
        else:
            # Random generation
            data = f"webgl_{random.random()}_{random.randint(10000, 99999)}"

        return hashlib.sha256(data.encode()).hexdigest()

    def generate_audio_fingerprint(self) -> str:
        """Generate a random audio context fingerprint hash.

        Returns:
            Hexadecimal hash string
        """
        if self.seed is not None:
            # Use seed for consistent generation
            random.seed(self.seed + 2)  # Different seed offset for variety
            data = f"audio_{self.seed}_{random.randint(1000, 9999)}"
        else:
            # Random generation
            data = f"audio_{random.random()}_{random.randint(10000, 99999)}"

        return hashlib.sha256(data.encode()).hexdigest()

    def generate_complete_fingerprint(self) -> dict[str, str]:
        """Generate a complete browser fingerprint with all components.

        Returns:
            Dictionary with canvas, webgl, and audio fingerprints
        """
        return {
            "canvas": self.generate_canvas_fingerprint(),
            "webgl": self.generate_webgl_fingerprint(),
            "audio": self.generate_audio_fingerprint(),
        }
