"""Repository for Project data persistence."""

from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

from src.storage.mongo_client import MongoClient
from src.models.project import Project


class ProjectRepository:
    """Repository for managing Project documents in MongoDB."""

    def __init__(self, mongodb_client: MongoClient) -> None:
        """Initialize project repository.

        Args:
            mongodb_client: MongoDB client instance
        """
        self._client = mongodb_client
        self.collection: Optional[AsyncIOMotorCollection] = None

    def _get_collection(self) -> Optional[AsyncIOMotorCollection]:
        """Get projects collection reference (lazy initialization).

        Returns:
            AsyncIOMotorCollection: Projects collection
        """
        if self.collection is None:
            from motor.motor_asyncio import AsyncIOMotorClient
            # Check if client is our MongoClient wrapper or raw Motor client
            if isinstance(self._client, AsyncIOMotorClient):
                # Direct Motor client - assume test_behance_crawler database
                self.collection = self._client["test_behance_crawler"]["projects"]
            else:
                # Our MongoClient wrapper
                self.collection = self._client.get_collection("projects")
        return self.collection

    async def save(self, project: Project) -> Project:
        """Save a new project to the database.

        Args:
            project: Project instance to save

        Returns:
            Project: The saved project
        """
        collection = self._get_collection()
        project_dict = project.model_dump()
        # Convert HttpUrl to string for MongoDB storage
        project_dict["url"] = str(project_dict["url"])
        await collection.insert_one(project_dict)
        return project

    async def find_by_id(self, project_id: int) -> Optional[Project]:
        """Find a project by its ID.

        Args:
            project_id: Project ID to search for

        Returns:
            Optional[Project]: Found project or None
        """
        collection = self._get_collection()
        doc = await collection.find_one({"id": project_id})
        if doc:
            return Project(**doc)
        return None

    async def update(self, project: Project) -> None:
        """Update an existing project.

        Args:
            project: Project instance with updated data
        """
        collection = self._get_collection()
        project_dict = project.model_dump()
        # Convert HttpUrl to string for MongoDB storage
        project_dict["url"] = str(project_dict["url"])
        await collection.update_one(
            {"id": project.id},
            {"$set": project_dict}
        )

    async def delete(self, project_id: int) -> None:
        """Delete a project by ID.

        Args:
            project_id: Project ID to delete
        """
        collection = self._get_collection()
        await collection.delete_one({"id": project_id})

    async def find_by_owner(self, owner_id: int) -> List[Project]:
        """Find all projects by owner ID.

        Args:
            owner_id: Owner user ID

        Returns:
            List[Project]: List of projects owned by the user
        """
        collection = self._get_collection()
        cursor = collection.find({"owner_id": owner_id})
        docs = await cursor.to_list(length=None)
        return [Project(**doc) for doc in docs]

    async def count(self) -> int:
        """Count total number of projects.

        Returns:
            int: Total project count
        """
        collection = self._get_collection()
        return await collection.count_documents({})

    async def upsert(self, project: Project) -> None:
        """Insert or update a project (upsert operation).

        Args:
            project: Project instance to upsert
        """
        collection = self._get_collection()
        project_dict = project.model_dump()
        # Convert HttpUrl to string for MongoDB storage
        project_dict["url"] = str(project_dict["url"])
        await collection.update_one(
            {"id": project.id},
            {"$set": project_dict},
            upsert=True
        )
