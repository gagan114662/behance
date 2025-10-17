"""Repository for Image data persistence."""

from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

from src.storage.mongo_client import MongoClient
from src.models.image import Image


class ImageRepository:
    """Repository for managing Image documents in MongoDB."""

    def __init__(self, mongodb_client: MongoClient) -> None:
        """Initialize image repository.

        Args:
            mongodb_client: MongoDB client instance
        """
        self._client = mongodb_client
        self.collection: Optional[AsyncIOMotorCollection] = None

    def _get_collection(self) -> Optional[AsyncIOMotorCollection]:
        """Get images collection reference (lazy initialization).

        Returns:
            AsyncIOMotorCollection: Images collection
        """
        if self.collection is None:
            from motor.motor_asyncio import AsyncIOMotorClient
            # Check if client is our MongoClient wrapper or raw Motor client
            if isinstance(self._client, AsyncIOMotorClient):
                # Direct Motor client - assume test_behance_crawler database
                self.collection = self._client["test_behance_crawler"]["images"]
            else:
                # Our MongoClient wrapper
                self.collection = self._client.get_collection("images")
        return self.collection

    async def save(self, image: Image) -> Image:
        """Save a new image to the database.

        Args:
            image: Image instance to save

        Returns:
            Image: The saved image
        """
        collection = self._get_collection()
        image_dict = image.model_dump()
        # Convert HttpUrl to string for MongoDB storage
        image_dict["url"] = str(image_dict["url"])
        await collection.insert_one(image_dict)
        return image

    async def find_by_project(self, project_id: int) -> List[Image]:
        """Find all images for a project.

        Args:
            project_id: Project ID to search for

        Returns:
            List[Image]: List of images for the project
        """
        collection = self._get_collection()
        cursor = collection.find({"project_id": project_id})
        docs = await cursor.to_list(length=None)
        return [Image(**doc) for doc in docs]

    async def save_many(self, images: List[Image]) -> None:
        """Bulk save multiple images.

        Args:
            images: List of Image instances to save
        """
        # Caller is responsible for providing non-empty list
        collection = self._get_collection()
        image_dicts = []
        for image in images:
            image_dict = image.model_dump()
            # Convert HttpUrl to string for MongoDB storage
            image_dict["url"] = str(image_dict["url"])
            image_dicts.append(image_dict)

        await collection.insert_many(image_dicts)
