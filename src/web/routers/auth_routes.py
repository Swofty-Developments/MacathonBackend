# Handle passing user token after validating password hash, password resets,
# etc.

import logging
import uuid
import json

from datetime import timedelta
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

import config
from models.auth_models import TokenDto
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.user_auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)


_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/auth",
    tags=["users", "auth"],
)


@router.post("/me")
async def read_users_me(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
) -> dict:
    return current_user.model_dump()


@router.post("/register")
async def register_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    questions: Annotated[str, Form(...)],
) -> dict:
    parsed_questions = json.loads(questions)

    user_collection = await config.db.get_collection(CollectionRef.USERS)

    user = UserDto(
        id=str(uuid.uuid4()),
        # Probably should add sanity checks for the inputs.
        name=form_data.username,
        questions=parsed_questions,
    )

    if await user_collection.find_one({UserRef.NAME: user.name}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with the same name already exists",
        )

    user.hashed_password = get_password_hash(form_data.password)

    await user_collection.insert_one(user.model_dump())

    _log.info(f"User {user.id} created")

    return {"message": "User created", "user": user}


@router.post("/login")
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
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID was not specified",
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
