# Handle passing user token after validating password hash, password resets,
# etc.

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

import config
from models.user_models import PublicUserDto, UserDto
from modules.db import CollectionRef, UserRef
from web.auth.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/leaderboard",
    tags=["users", "leaderboard"],
)


class LeaderboardUserDto(BaseModel):
    _id: str
    name: str
    points: int


@router.get("/")
async def get_leaderboard(size: int) -> list[PublicUserDto]:
    collection = await config.db.get_collection(CollectionRef.USERS)

    return await collection.aggregate(
        [
            {"$sort": {UserRef.POINTS: -1, UserRef.NAME: 1}},
            {"$limit": int(size)},
        ]
    ).to_list()


@router.get("/rank/{user_id}")
async def get_rank(user_id: str) -> int:
    collection = await config.db.get_collection(CollectionRef.USERS)

    user = await collection.find_one({UserRef.ID: user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    points = user[UserRef.POINTS]

    entry = await collection.aggregate([{"$match": {UserRef.POINTS: {"$gt": points}}}, {"$count": "index"}]).to_list()

    if (len(entry) == 0):
        return 1
    return entry[0]['index'] + 1


async def set_points(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    points: int
) -> dict:
    collection = await config.db.get_collection(CollectionRef.USERS)

    await collection.update_one(
        {UserRef.ID: user.id},
        {"$set": {UserRef.POINTS: points}}
    )

    return {"message": "Set points successfully"}
