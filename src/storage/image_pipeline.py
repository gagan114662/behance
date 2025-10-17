"""Image download and processing pipeline."""

import asyncio
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse
import hashlib

import httpx
import aiofiles
from pydantic import BaseModel, Field


class ImageDownloadResult(BaseModel):
    """Result of an image download operation."""

    success: bool = Field(..., description="Whether download succeeded")
    url: str = Field(..., description="Image URL that was downloaded")
    local_path: Optional[str] = Field(None, description="Local file path if successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ImagePipeline:
    """Pipeline for downloading and processing images."""

    def __init__(self, output_dir: str) -> None:
        """Initialize image pipeline.

        Args:
            output_dir: Directory to save downloaded images
        """
        self.output_dir = output_dir

    async def download_image(self, url: str) -> ImageDownloadResult:
        """Download a single image from URL.

        Args:
            url: Image URL to download

        Returns:
            ImageDownloadResult: Download result with success status
        """
        try:
            # Ensure output directory exists
            await self.ensure_output_dir()

            # Generate filename from URL
            filename = self.generate_filename(url)
            local_path = str(Path(self.output_dir) / filename)

            # Download image using httpx
            client = httpx.AsyncClient()
            try:
                response = await client.get(url)
                response.raise_for_status()

                # Save image to file using aiofiles
                file_handle = await aiofiles.open(local_path, 'wb')
                try:
                    await file_handle.write(response.content)
                finally:
                    await file_handle.close()
            finally:
                await client.aclose()

            return ImageDownloadResult(
                success=True,
                url=url,
                local_path=local_path
            )

        except Exception as e:
            return ImageDownloadResult(
                success=False,
                url=url,
                local_path=None,
                error_message=str(e)
            )

    async def download_many(self, urls: List[str]) -> List[ImageDownloadResult]:
        """Download multiple images concurrently.

        Args:
            urls: List of image URLs to download

        Returns:
            List[ImageDownloadResult]: List of download results
        """
        # Create download tasks for all URLs
        tasks = [self.download_image(url) for url in urls]

        # Execute all downloads concurrently using asyncio.gather
        results = await asyncio.gather(*tasks)

        return list(results)

    def generate_filename(self, url: str) -> str:
        """Generate a filename from URL.

        Creates a unique filename using URL hash and preserves file extension.

        Args:
            url: Image URL

        Returns:
            str: Generated filename
        """
        # Parse URL to get path
        parsed = urlparse(url)
        path = parsed.path

        # Extract file extension
        extension = Path(path).suffix
        if not extension:
            extension = ".jpg"  # Default extension

        # Generate unique filename using URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{url_hash}{extension}"

        return filename

    async def ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist.

        Creates parent directories as needed.
        """
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    def get_file_size(self, path: str) -> int:
        """Get size of a file in bytes.

        Args:
            path: File path

        Returns:
            int: File size in bytes
        """
        file_path = Path(path)
        stat_info = file_path.stat()
        return stat_info.st_size
