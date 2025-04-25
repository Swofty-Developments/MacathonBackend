# Handle passing user token after validating password hash, password resets,
# etc.

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.auth.user_auth import get_current_active_user

from web.routers.achievement_routes import update_achievements

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/friendex",
    tags=["users", "friendex"],
)

# Returns database entry for ID corresponding to user
@router.get("/{user_id}")
async def get_entry(user_id: str) -> dict:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    query = {UserRef.ID: user_id}

    projection = {}

    entry = await users_collection.find_one(query, projection)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    
    return entry

# Returns the list of IDs of friends of a user given their own ID
@router.get("/friends/{user_id}")
async def get_friends(user_id: str) -> list:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    user = UserDto.model_validate(await users_collection.find_one({UserRef.ID: user_id}))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    friends = user.friends

    return await users_collection.find({UserRef.ID: {"$in": friends}}).to_list()

# Returns information about current tracking session of authenticated user
@router.get('/select/check')
async def check_selected(
    user: Annotated[UserDto, Depends(get_current_active_user)]
) -> dict:
    tracking = config.tracker.get_player_tracking(user.id)
    if not tracking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No selected friend",
        )
    
    remaining, elapsed = config.tracker.get_selected_time(user.id)

    is_initiator = tracking.id_2 == user.selected_friend
    return {
        "selectedFriend": tracking.id_2 if is_initiator else tracking.id_1,
        "isInitiator": True if is_initiator else False,
        "timeRemaining": remaining,
        "elapsedTime": elapsed,
        "questionsReady": True if remaining <= 5 else False,
        "pointsAccumulated": config.tracker.get_points_accumulated(user.id),
    }

# Returns list of IDs of players not in friends list
@router.get("/unmet-players/{user_id}")
async def get_unmet_players(user_id: str) -> list:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user = await user_collection.find_one({UserRef.ID: user_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    friend_ids = user.get("friends", [])
    excluded_ids = friend_ids + [user_id]
    
    unmet = await user_collection.find(
        {UserRef.ID: {"$nin": excluded_ids}}
    ).to_list()

    return unmet

# Allows selection of user for tracking (user_id is ID of user to track by authenticated user)
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
            detail=f"User with ID {user_id} not found",
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
    elif other_user.id == user.selected_friend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already selected",
        )
    elif user.id == other_user.selected_friend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already selected by the other user",
        )
    elif config.tracker.get_player_tracking(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already selected by another user",
        )
    
    await config.tracker.remove_tracking(user.id)
    user.selected_friend = other_user.id
    await users_collection.update_one(
        {UserRef.ID: user.id},
        {"$set": user.model_dump()},
    )

    config.tracker.add_tracking(user.id, other_user.id)

    return {}

# Deselects the current selected user of the authenticated user
@router.post("/deselect")
async def deselect_user(
    user: Annotated[UserDto, Depends(get_current_active_user)],
) -> dict:
    await config.tracker.remove_tracking(user.id)

    return { 'message': 'Deselected user' }

# Adds the given 'friend_id' to the friends list of the authenticated user
@router.post('/add-friend')
async def add_friend(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    friend_id: str
) -> dict:
    users_collection = await config.db.get_collection(CollectionRef.USERS)

    friend = UserDto.model_validate(await users_collection.find_one({UserRef.ID: friend_id}))
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {friend.id} not found",
        )

    if friend_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot friend yourself",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not await users_collection.find_one({UserRef.ID: friend_id}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid friend ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if friend_id not in user.friends:
        user.friends.append(friend_id)
        await users_collection.update_one(
            {UserRef.ID: user.id},
            {"$set": {UserRef.FRIENDS: user.friends}},
        )
        
    if user.id not in friend.friends:
        friend.friends.append(user.id)
        await users_collection.update_one(
            {UserRef.ID: friend.id},
            {"$set": {UserRef.FRIENDS: friend.friends}},
        )

    await update_achievements(user.id)

    return { 'message': 'Added friend successfully' }
