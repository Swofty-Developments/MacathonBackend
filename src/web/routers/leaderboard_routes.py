# Handle passing user token after validating password hash, password resets,
# etc.

import logging

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from typing import Optional
from pydantic import BaseModel

import config
from modules.db import CollectionRef, UserRef

_log = logging.getLogger("uvicorn")
router = APIRouter(
    tags=["users", "leaderboard"],
)

class LeaderboardUserDto(BaseModel):
    id: Optional[str] = None
    name: str
    points: int

@router.get("/leaderboard/{size}")
async def get_leaderboard(size : str) -> list[LeaderboardUserDto]:
    collection = await config.db.get_collection(CollectionRef.USERS)

    return collection.aggregate([
        {
            '$sort': {
                UserRef.POINTS: -1, 
                UserRef.NAME: 1
            }
        }, {
            '$limit': int(size)
        }, {
            '$project': {
                UserRef.NAME: 1,
                UserRef.POINTS: 1
            }
        }
    ])

@router.get("/leaderboard/rank/{user_id}")
async def get_rank(user_id: str) -> int:
    points = await config.db.find_one({UserRef.ID: user_id})[UserRef.POINTS]
    rank = await config.db.aggregate([
        {
            '$match': {
                UserRef.POINTS: {
                    '$lt': points
                }
            }
        }, {
            '$count': 'index'
        }
    ])['index'] + 1

    return rank