# Handle passing user token after validating password hash, password resets,
# etc.

import logging

from fastapi import APIRouter, HTTPException, status

import config
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef


_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/user",
    tags=["users", "auth"],
)


@router.post("/user/{user_id}")
async def read_users_me(user_id: str) -> None | UserDto:
    collections = await config.db.get_collection(CollectionRef.USERS)

    user = UserDto.model_validate(await collections.find_one({UserRef.ID: user_id}))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user.model_dump()
