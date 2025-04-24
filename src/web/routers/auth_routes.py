# Handle passing user token after validating password hash, password resets,
# etc.

import logging

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

import config
from models.auth_models import TokenDto
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.auth import require_api_key
from web.user_auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    get_user,
)

_log = logging.getLogger("uvicorn")
router = APIRouter(
    tags=["users", "auth"],
)


@router.post("/users/me")
async def read_users_me(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
) -> dict:
    return current_user.model_dump()


# Do not mistaken this for sending a password reset email.
@router.post("/users/account/reset-password")
async def reset_password(
    is_authorised: Annotated[OAuth2PasswordRequestForm, Depends(require_api_key)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user = await get_user(form_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    hashed_password = get_password_hash(form_data.password)
    await user_collection.update_one(
        {UserRef.ID: user.id},
        {"$set": {UserRef.HASHED_PASSWORD: hashed_password}},
    )

    return {"message": "Password reset"}


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenDto:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return TokenDto(access_token=access_token, token_type="bearer")


@router.delete("/")
async def delete_user(
    user: Annotated[UserDto, Depends(get_current_active_user)],
):
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    deleted = None
    if user.id:
        deleted = await user_collection.delete_one({UserRef.ID: user.id})
    elif user.email:
        deleted = await user_collection.delete_one({UserRef.ID: user.email})
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or Email was not specified",
        )

    if deleted.deleted_count > 0:
        _log.info(f"Deleted user {user.id}")
        return {"message": f"Deleted user {user.id}"}
    else:
        _log.info(f"User {user.id} could not be deleted because it does not exist")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {user.id} could not be deleted because it does not exist",
        )
