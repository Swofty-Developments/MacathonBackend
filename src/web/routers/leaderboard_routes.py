# Handle passing user token after validating password hash, password resets,
# etc.

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import config
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.auth.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/leaderboard",
    tags=["users", "leaderboard"],
)


class LeaderboardUserDto(BaseModel):
    id: Optional[str] = None
    name: str
    points: int


@router.get("/{size}")
async def get_leaderboard(size: int) -> list[LeaderboardUserDto]:
    collection = await config.db.get_collection(CollectionRef.USERS)

    return await collection.aggregate(
        [
            {"$sort": {UserRef.POINTS: -1, UserRef.NAME: 1}},
            {"$limit": int(size)},
            {"$project": {UserRef.NAME: 1, UserRef.POINTS: 1}},
        ]
    )


@router.get("/rank/{user_id}")
async def get_rank(user_id: str) -> int:
    collection = await config.db.get_collection(CollectionRef.USERS)

    points = await collection.find_one({UserRef.ID: user_id})[UserRef.POINTS]
    rank = (
        await collection.aggregate(
            [{"$match": {UserRef.POINTS: {"$lt": points}}}, {"$count": "index"}]
        )["index"]
        + 1
    )

    return await rank


async def set_points(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    points: int
) -> dict:
    collection = await config.db.get_collection(CollectionRef.USERS)

    query = { UserRef.ID: user.id }

    update = {"$set": {UserRef.POINTS: points}}

    await collection.update_one(query, update)

    return {"message": "Set points successfully"}
