"""Production external data source repository for MongoDB."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient


class ProdExternalDataSource:
    """External data source that connects to MongoDB."""

    def __init__(self, mongodb_uri: str) -> None:
        """Initialize the production data source.

        Args:
            mongodb_uri: MongoDB connection URI.
        """
        self._client: AsyncIOMotorClient[dict[str, Any]] = AsyncIOMotorClient(
            mongodb_uri
        )

    async def get_sample_documents(
        self, db_name: str, table_name: str, sample_size: int
    ) -> list[dict[str, Any]]:
        """Get sample documents from MongoDB using $sample aggregation.

        Args:
            db_name: The database name.
            table_name: The collection name.
            sample_size: Number of documents to sample.

        Returns:
            A list of sampled documents.
        """
        db = self._client[db_name]
        collection = db[table_name]

        # Use $sample aggregation for random sampling
        pipeline = [{"$sample": {"size": sample_size}}]
        cursor = collection.aggregate(pipeline)

        documents: list[dict[str, Any]] = []
        async for doc in cursor:
            # Convert ObjectId to string for JSON compatibility
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            documents.append(doc)

        return documents

    async def list_tables(self, db_name: str) -> list[str]:
        """List all collections in a MongoDB database.

        Args:
            db_name: The database name.

        Returns:
            A list of collection names.
        """
        db = self._client[db_name]
        collections = await db.list_collection_names()
        return sorted(collections)

    async def close(self) -> None:
        """Close the MongoDB connection."""
        self._client.close()
