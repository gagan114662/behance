"""MongoDB client wrapper with async support."""

from typing import Optional
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection


class MongoConfig(BaseModel):
    """MongoDB connection configuration."""

    url: str = Field(..., description="MongoDB connection URL")
    database: str = Field(..., description="Database name")


class MongoClient:
    """Async MongoDB client wrapper using Motor."""

    def __init__(self, config: MongoConfig) -> None:
        """Initialize MongoDB client with configuration.

        Args:
            config: MongoDB connection configuration
        """
        self.config = config
        self.database_name = config.database
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Connect to MongoDB database.

        Creates async Motor client and initializes database connection.
        """
        # Import here to allow for easier mocking in tests
        import motor.motor_asyncio
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.config.url)
        self.database = self.client[self.database_name]

    async def disconnect(self) -> None:
        """Disconnect from MongoDB database.

        Closes the Motor client connection.
        """
        if self.client:
            self.client.close()

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Get reference to a MongoDB collection.

        Args:
            name: Collection name

        Returns:
            AsyncIOMotorCollection: Collection reference
        """
        # Caller is responsible for calling connect() first
        return self.database[name]
