# Handle passing user token after validating password hash, password resets,
# etc.

import logging

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

import config
from modules.db import CollectionRef, UserRef

_log = logging.getLogger("uvicorn")
router = APIRouter(
    tags=["users", "auth"],
)

@router.get("/leaderboard")
async def get_leaderboard() -> dict:
    leaderboard_collection = await config.db.get_collection(CollectionRef.USERS)

    pipeline = [
        {
            '$sort': {
                'points': -1, 
                'name': 1
            }
        }, {
            '$limit': 100
        }
    ]

    return leaderboard_collection.aggregate(pipeline)

@router.get("/leaderboard/rank/{user_id}")
async def get_rank(user_id: str) -> int:
    user = await config.db.find_one({UserRef.ID: user_id})
    points = user.points
    agg = await config.db.aggregate([
        {
            '$match': {
                'points': {
                    '$lt': 10
                }
            }
        }, {
            '$count': 'index'
        }
    ])['index']

    return agg
