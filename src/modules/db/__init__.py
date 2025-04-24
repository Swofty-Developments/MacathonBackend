import os
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

# TODO: Implement a MongoDB connection here.

from .collections import CollectionRef
from .users import UserRef

__all__ = ["get_db", "UserRef", "CollectionRef"]

_log = logging.getLogger("uvicorn")

class MongoClient:
    def __init__(self, uri):
        self.db = AsyncIOMotorClient(uri).database

    async def insert(self, collection, document):
        return await self.db[collection].insert_one(document)
    
    async def find(self, collection, query):
        return await self.db[collection].find_one(query)



# TODO: Add type hint for the database connection return type.
def get_db(uri: str = None):
    uri = uri if uri is not None else os.getenv("MONGODB_URI")
    return MongoClient(uri)
