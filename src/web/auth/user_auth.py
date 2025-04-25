# See https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#about-jwt

import os
import jwt

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from typing import Annotated

import config
from models.auth_models import TokenDataDto
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43800  # one month

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str | bytes, hashed_password: str | bytes) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str | bytes) -> str:
    return pwd_context.hash(password)

# Return database entry for user given ID
async def get_user(id: str) -> None | UserDto:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user = await user_collection.find_one({UserRef.ID: id})
    if user is None:
        user = await user_collection.find_one({UserRef.NAME: id})
    if user is None:
        return None
    
    if user is not None:
        return UserDto.model_validate(user)

# Return database entry for user only if correct password is input
async def authenticate_user(id: str, password: str) -> bool | UserDto:
    user = await get_user(id)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Create an access token that lasts for amount of time given by the timedelta object
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    print(SECRET_KEY, to_encode)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get user information corresponding to access token
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserDto:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id = payload.get("sub")
        if id is None:
            raise credentials_exception
        token_data = TokenDataDto(id=id)
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(id=token_data.id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserDto, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
