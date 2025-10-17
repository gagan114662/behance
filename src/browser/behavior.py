"""Human behavior simulation for browser automation."""

import asyncio
import random
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from playwright.async_api import Page


class MouseMovement(BaseModel):
    """Model for mouse movement coordinates and timing."""

    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    duration_ms: int = Field(..., description="Movement duration in milliseconds")

    @field_validator("x")
    @classmethod
    def validate_x(cls, v: int) -> int:
        """Validate x coordinate is non-negative."""
        if v < 0:
            raise ValueError("x coordinate must be non-negative")
        return v

    @field_validator("y")
    @classmethod
    def validate_y(cls, v: int) -> int:
        """Validate y coordinate is non-negative."""
        if v < 0:
            raise ValueError("y coordinate must be non-negative")
        return v

    @field_validator("duration_ms")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Validate duration is positive."""
        if v <= 0:
            raise ValueError("duration_ms must be positive")
        return v


class ScrollPattern(BaseModel):
    """Model for scroll pattern with positions and optional delays."""

    scroll_positions: list[int] = Field(..., description="List of scroll positions in pixels")
    delays_seconds: Optional[list[float]] = Field(None, description="Optional delays between scrolls")

    @field_validator("delays_seconds")
    @classmethod
    def validate_delays_length(cls, v: Optional[list[float]], info) -> Optional[list[float]]:
        """Validate delays list matches positions length if provided."""
        # No validation needed - caller is responsible for providing matching lengths
        return v


class HumanBehavior:
    """Simulator for human-like browser behavior."""

    def __init__(
        self,
        typing_delay_min: float = 0.05,
        typing_delay_max: float = 0.15,
    ) -> None:
        """Initialize human behavior simulator.

        Args:
            typing_delay_min: Minimum delay between keystrokes in seconds
            typing_delay_max: Maximum delay between keystrokes in seconds
        """
        self.typing_delay_min = typing_delay_min
        self.typing_delay_max = typing_delay_max

    async def random_delay(self, min_seconds: float, max_seconds: float) -> float:
        """Generate and execute a random delay.

        Args:
            min_seconds: Minimum delay duration
            max_seconds: Maximum delay duration

        Returns:
            The actual delay duration used
        """
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
        return delay

    async def type_like_human(self, page: Page, selector: str, text: str) -> None:
        """Type text with human-like delays between keystrokes.

        Args:
            page: Playwright page instance
            selector: CSS selector for input element
            text: Text to type
        """
        # Calculate random delay within configured range
        delay_ms = random.uniform(self.typing_delay_min, self.typing_delay_max) * 1000

        # Use Playwright's type method with delay
        await page.type(selector, text, delay=delay_ms)

    async def generate_mouse_movements(self, count: int) -> list[MouseMovement]:
        """Generate random mouse movements.

        Args:
            count: Number of movements to generate

        Returns:
            List of mouse movements
        """
        movements = []

        for _ in range(count):
            movement = MouseMovement(
                x=random.randint(0, 1920),
                y=random.randint(0, 1080),
                duration_ms=random.randint(100, 500),
            )
            movements.append(movement)

        return movements

    async def generate_scroll_pattern(self, page_height: int) -> ScrollPattern:
        """Generate a realistic scroll pattern for a page.

        Args:
            page_height: Total height of the page in pixels

        Returns:
            ScrollPattern with positions and delays
        """
        # Generate 5-10 scroll positions
        num_scrolls = random.randint(5, 10)
        positions = []

        current_pos = 0
        for _ in range(num_scrolls):
            # Scroll by 200-500 pixels each time
            scroll_amount = random.randint(200, 500)
            current_pos = min(current_pos + scroll_amount, page_height)
            positions.append(current_pos)

        # Generate delays between 0.5 and 2 seconds
        delays = [random.uniform(0.5, 2.0) for _ in range(len(positions))]

        return ScrollPattern(scroll_positions=positions, delays_seconds=delays)

    async def reading_delay(self, content_length: int) -> float:
        """Calculate reading delay based on content length.

        Args:
            content_length: Length of content in characters

        Returns:
            Delay duration in seconds
        """
        # Assume reading speed of ~250 words per minute
        # Average word is ~5 characters
        words = content_length / 5
        minutes = words / 250

        # Convert to seconds and add some randomness
        base_delay = minutes * 60
        delay = base_delay * random.uniform(0.8, 1.2)

        # Cap at reasonable maximum
        return min(delay, 60.0)

    async def scroll_randomly(self, page: Page, scroll_count: int) -> None:
        """Execute random scrolls on the page.

        Args:
            page: Playwright page instance
            scroll_count: Number of scroll actions to perform
        """
        for _ in range(scroll_count):
            # Random scroll amount between 100 and 500 pixels
            scroll_amount = random.randint(100, 500)

            # Execute scroll
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")

            # Random delay between scrolls
            await asyncio.sleep(random.uniform(0.3, 1.0))
