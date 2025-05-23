# Handle passing user token after validating password hash, password resets,
# etc.

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user_models import PublicUserDto, UserDto
from modules.db import CollectionRef, UserRef
from web.auth.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/leaderboard",
    tags=["users", "leaderboard"],
)

# Returns a list with 'size' entries sorted in descending order of points out of all users in the database
@router.get("/")
async def get_leaderboard(size: int) -> list[PublicUserDto]:
    collection = await config.db.get_collection(CollectionRef.USERS)

    return [PublicUserDto.model_validate(data) for data in await collection.aggregate(
        [
            {"$sort": {UserRef.POINTS: -1, UserRef.NAME: 1}},
            {"$limit": int(size)},
        ]
    ).to_list()]

# Returns the rank (most points) of the user corresponding to 'user_id' compared with all other users
# Rank = (# people with more points) + 1
@router.get("/rank/{user_id}")
async def get_rank(user_id: str) -> int:
    collection = await config.db.get_collection(CollectionRef.USERS)

    user = await collection.find_one({UserRef.ID: user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",

        )
    points = user[UserRef.POINTS]

    entry = await collection.aggregate([{"$match": {UserRef.POINTS: {"$gt": points}}}, {"$count": "index"}]).to_list()

    if (len(entry) == 0):
        return 1
    return entry[0]['index'] + 1

# UNUSED: sets points of user, no longer referred to in code
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
