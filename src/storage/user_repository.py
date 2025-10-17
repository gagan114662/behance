"""Repository for User data persistence."""

from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection

from src.storage.mongo_client import MongoClient
from src.models.user import User


class UserRepository:
    """Repository for managing User documents in MongoDB."""

    def __init__(self, mongodb_client: MongoClient) -> None:
        """Initialize user repository.

        Args:
            mongodb_client: MongoDB client instance
        """
        self._client = mongodb_client
        self.collection: Optional[AsyncIOMotorCollection] = None

    def _get_collection(self) -> AsyncIOMotorCollection:
        """Get users collection reference (lazy initialization).

        Returns:
            AsyncIOMotorCollection: Users collection
        """
        if self.collection is None:
            # Check if client is our MongoClient wrapper or raw Motor client
            if hasattr(self._client, 'database_name'):
                # Our MongoClient wrapper
                self.collection = self._client.get_collection("users")
            else:
                # Direct Motor client - assume test_behance_crawler database
                self.collection = self._client["test_behance_crawler"]["users"]
        return self.collection

    async def save(self, user: User) -> User:
        """Save a new user to the database.

        Args:
            user: User instance to save

        Returns:
            User: The saved user
        """
        collection = self._get_collection()
        user_dict = user.model_dump()
        # Convert HttpUrl to string for MongoDB storage
        user_dict["url"] = str(user_dict["url"])
        await collection.insert_one(user_dict)
        return user

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username.

        Args:
            username: Username to search for

        Returns:
            Optional[User]: Found user or None
        """
        collection = self._get_collection()
        doc = await collection.find_one({"username": username})
        if doc:
            return User(**doc)
        return None

    async def update_stats(self, user_id: int, stats: Dict[str, Any]) -> None:
        """Update user statistics.

        Args:
            user_id: User ID to update
            stats: Dictionary containing stats to update
        """
        collection = self._get_collection()
        await collection.update_one(
            {"id": user_id},
            {"$set": {"stats": stats}}
        )
