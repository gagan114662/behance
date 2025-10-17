"""Browser automation module with stealth and fingerprinting."""

from src.browser.manager import BrowserManager, BrowserConfig
from src.browser.stealth import StealthPlugin, FingerprintGenerator
from src.browser.behavior import HumanBehavior, MouseMovement, ScrollPattern

__all__ = [
    "BrowserManager",
    "BrowserConfig",
    "StealthPlugin",
    "FingerprintGenerator",
    "HumanBehavior",
    "MouseMovement",
    "ScrollPattern",
]
