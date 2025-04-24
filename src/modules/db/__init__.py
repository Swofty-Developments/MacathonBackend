import os
import logging

# TODO: Implement a MongoDB connection here.

from .collections import CollectionRef
from .users import UserRef

__all__ = ["get_db", "UserRef", "CollectionRef"]

_log = logging.getLogger("uvicorn")


# TODO: Add type hint for the database connection return type.
def get_db(endpoint: str, token: str = None):
    token = token if token is not None else os.getenv("MONGODB_URI")
