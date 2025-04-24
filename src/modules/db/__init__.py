import os
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

# TODO: Implement a MongoDB connection here.

from .collections import CollectionRef
from .users import UserRef

__all__ = ["UserRef", "CollectionRef"]

_log = logging.getLogger("uvicorn")


class MongoClient:
    def __init__(self, uri: str = None):
        uri = uri if uri is not None else os.getenv("MONGODB_URI")
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client.get_database(os.getenv("MONGODB_DATABASE"))

    async def get_collection(self, collection: str) -> AsyncIOMotorCollection:
        return self.db[collection]
