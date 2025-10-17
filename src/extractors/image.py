"""Image data extraction and download from Behance."""

from typing import Dict, Any, List
import httpx
import aiofiles
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import Page

from src.models.image import Image


class ImageExtractor:
    """Extract and download images from Behance projects."""

    def __init__(self):
        """Initialize image extractor."""
        pass

    async def extract_from_page(self, page: Page, project_id: int = 0) -> List[Image]:
        """Extract all images from Behance project page.

        Args:
            page: Playwright page object with project page loaded
            project_id: ID of the project these images belong to

        Returns:
            List of Image models
        """
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        images = []

        # Discovered selector: img[src*='behance.net']
        image_selectors = [
            "img[src*='behance.net']",      # CDN images
            "img[src*='mir-s3']",            # Mirror S3 images
            ".project-module img",           # Project module images
        ]

        seen_urls = set()  # Track unique URLs

        for selector in image_selectors:
            img_elements = soup.select(selector)

            for img_elem in img_elements:
                img_url = img_elem.get('src') or img_elem.get('data-src')

                if not img_url or img_url in seen_urls:
                    continue

                # Skip small images (likely thumbnails or UI elements)
                if any(size in img_url for size in ['_thumb', '_small', '/32x32/', '/64x64/', '/avatar']):
                    continue

                seen_urls.add(img_url)

                # Extract dimensions if available
                width = int(img_elem.get('width', 1920))
                height = int(img_elem.get('height', 1080))

                # Create Image model
                image = Image(
                    url=img_url,
                    width=width,
                    height=height,
                    size=0,  # Size unknown from HTML
                    format=self.extract_format(img_url),
                    project_id=project_id
                )
                images.append(image)

        return images

    async def extract_from_project(self, data: Dict[str, Any]) -> List[Image]:
        """Extract all images from project data.

        Args:
            data: Dictionary containing project data with modules

        Returns:
            List of Image models
        """
        modules = data.get("modules", [])
        images = []

        for module in modules:
            # Only process image modules
            if module.get("type") == "image":
                sizes = module.get("sizes", {})
                original_url = sizes.get("original")

                if original_url:
                    # Extract metadata if available
                    metadata = await self.extract_metadata(module)

                    # Extract format from URL
                    image_format = self.extract_format(original_url)

                    # Create Image model
                    image = Image(
                        url=original_url,
                        width=metadata.get("width", 1920),
                        height=metadata.get("height", 1080),
                        size=metadata.get("size", 0),
                        format=image_format,
                        project_id=data.get("id", 0)
                    )
                    images.append(image)

        return images

    async def extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract image metadata from data.

        Args:
            data: Dictionary containing image data

        Returns:
            Dict with width, height, size, etc.
        """
        metadata = {}

        # Extract dimensions
        if "width" in data:
            metadata["width"] = data["width"]
        else:
            metadata["width"] = 1920  # Default width

        if "height" in data:
            metadata["height"] = data["height"]
        else:
            metadata["height"] = 1080  # Default height

        # Extract file size
        if "size" in data:
            metadata["size"] = data["size"]
        else:
            metadata["size"] = 0  # Unknown size

        return metadata

    async def extract_url_variants(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract different image size variants from data.

        Args:
            data: Dictionary containing image size variants

        Returns:
            Dict mapping size names to URLs
        """
        sizes = data.get("sizes", {})
        return sizes

    async def download_image(self, url: str, output_path: str) -> str:
        """Download image from URL to local file.

        Args:
            url: Image URL to download
            output_path: Local file path to save image

        Returns:
            Path to downloaded file
        """
        # Create parent directory if it doesn't exist
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Download image using httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            # Write image data to file using aiofiles
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(response.content)

        return output_path

    def extract_format(self, url: str) -> str:
        """Extract image format from URL extension.

        Args:
            url: Image URL

        Returns:
            Format string (jpg, png, etc.)
        """
        # Get the file extension from URL
        url_lower = url.lower()

        # Check for common image formats
        if ".jpg" in url_lower or ".jpeg" in url_lower:
            return "jpg"
        elif ".png" in url_lower:
            return "png"
        elif ".gif" in url_lower:
            return "gif"
        elif ".webp" in url_lower:
            return "webp"
        elif ".svg" in url_lower:
            return "svg"
        else:
            # Default to jpg if no extension found
            return "jpg"

    def calculate_aspect_ratio(self, width: int, height: int) -> float:
        """Calculate aspect ratio from width and height.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Aspect ratio as float (width / height)
        """
        # Caller is responsible for ensuring height > 0
        return width / height
