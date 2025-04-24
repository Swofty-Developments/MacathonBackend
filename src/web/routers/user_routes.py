import os
import logging
import random
import string
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.auth import require_api_key
from web.user_auth import get_password_hash

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/by-uuid/{user_id}")
async def get_user_by_uuid(user_id: str) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user = await user_collection.find_one({UserRef.ID: user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    else:
        return user


# NOTE: A follow-up POST users/account/reset-password must be sent.
@router.post("/")
async def register_user(user: UserDto) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user.email = user.email.lower()
    # TODO: Handle UUID collisions if you want to go to that extra mile for this hackathon.
    user.id = str(uuid.uuid4())

    if await user_collection.find_one({UserRef.EMAIL: user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with the same email already exists",
        )

    random_password = "".join(random.choices(string.ascii_letters, k=32))
    user.hashed_password = get_password_hash(random_password)

    await user_collection.insert_one(user.model_dump())

    _log.info(f"User {user.id} created")

    return {"message": "User created", "user": user}
