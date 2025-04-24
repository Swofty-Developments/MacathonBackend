# Handle passing user token after validating password hash, password resets,
# etc.

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.auth.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/friendex",
    tags=["users", "friendex"],
)


@router.get("/{user_id}")
async def get_entry(user_id: str) -> dict:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    query = {UserRef.ID: user_id}

    projection = {}

    return await users_collection.find_one(query, projection)


@router.get("/friends/{user_id}")
async def get_friends(user_id: str) -> dict:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    friends = await users_collection.find_one({UserRef.ID: user_id})["friends"]

    projection = {}

    return await users_collection.aggregate(
        [{"$match": {UserRef.ID: {"$in": friends}}}, {"$project": projection}]
    )

@router.post("/select/{user_id}")
async def select_user(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    user_id: str
) -> dict:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    other_user = await users_collection.find_one({UserRef.ID: user_id})
    if not other_user:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    elif user_id in user.friends:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already in friends list",
        )
    elif user_id == user.id:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot catch yourself",
        )
    
    user.selected_friend = user_id
    await users_collection.update_one(
        {UserRef.ID: user.id},
        {"$set": user.model_dump()},
    )

    return {}
