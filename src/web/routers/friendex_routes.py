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

    entry = await users_collection.find_one(query, projection)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return entry


@router.get("/friends/{user_id}")
async def get_friends(user_id: str) -> list:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    user = UserDto.model_validate(await users_collection.find_one({UserRef.ID: user_id}))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    friends = user.friends

    return await users_collection.find({UserRef.ID: {"$in": friends}}).to_list()

@router.post("/select/{user_id}")
async def select_user(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    user_id: str
) -> dict:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    other_user = UserDto.model_validate(await users_collection.find_one({UserRef.ID: user_id}))
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    elif other_user.id in user.friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already in friends list",
        )
    elif other_user.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot catch yourself",
        )
    elif other_user.id in user.selected_friend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already selected",
        )
    elif user.id in other_user.selected_friend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already selected by the other user",
        )
    
    user.selected_friend = other_user.id
    await users_collection.update_one(
        {UserRef.ID: user.id},
        {"$set": user.model_dump()},
    )

    return {}

@router.post('/addfriend')
async def add_friend(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    friend_id: str
) -> dict:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    entry = await users_collection.find_one({UserRef.ID: user.id})
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    friends = entry["friends"]

    if friend_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot friend yourself",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if friend_id in friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already in friends list",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not await users_collection.find_one({UserRef.ID: friend_id}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid friend ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    friends.append(friend_id)

    await users_collection.update_one(
        {UserRef.ID: user.id},
        {"$set": {UserRef.FRIENDS: friends}},
    )

    return { 'message': 'Added friend successfully' }