# Handle passing user token after validating password hash, password resets,
# etc.

import logging

from fastapi import APIRouter

import config
from modules.db import CollectionRef, UserRef

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/friendex",
    tags=["users", "friendex"],
)


@router.get("/{user_id}")
async def get_entry(user_id: str) -> dict:
    collection = await config.db.get_collection(CollectionRef.USERS)

    query = {UserRef.ID: user_id}

    projection = {}

    return await collection.find_one(query, projection)


@router.get("/friends/{user_id}")
async def get_friends(user_id: str) -> dict:
    collection = await config.db.get_collection(CollectionRef.USERS)

    friends = await collection.find_one({UserRef.ID: user_id})["friends"]

    return await collection.aggregate(
        [{"$match": {UserRef.ID: {"$in": friends}}}, {"$project": {}}]
    )
