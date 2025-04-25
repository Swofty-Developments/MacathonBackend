import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status, UploadFile
from bson.binary import Binary
from io import BytesIO
import base64

from fastapi.responses import StreamingResponse

import config
from models.user_models import UserDto
from modules.db import CollectionRef, PictureRef
from web.auth.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/picture",
    tags=["users", "picture"],
)

@router.get("/get_picture/{user_id}")
async def get_picture(user_id: str):
    picture_collection = await config.db.get_collection(CollectionRef.PICTURES)
    user = await picture_collection.find_one({ PictureRef.USER: user_id })
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image found for this user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # picture_bytes : bytes = base64.b64encode(user[PictureRef.PICTURE]).decode('utf-8')
    # return {"image": f"data:image/png;base64,{picture_bytes}"}
    
    return { "image": user[PictureRef.PICTURE] }


@router.post("/set_picture")
async def set_picture(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    picture: str
) -> dict:
    picture_collection = await config.db.get_collection(CollectionRef.PICTURES)
    query = { PictureRef.USER: user.id }
    update = { "$set": { PictureRef.PICTURE: picture } }

    await picture_collection.update_one(query, update, upsert=True)

    return { "message": "Uploaded picture successfully!"}