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

@router.get("/leaderboard/{limit}")
async def get_leaderboard(limit : str) -> list[dict]:
    collection = await config.db.get_collection(CollectionRef.USERS)

    return collection.aggregate([
        {
            '$sort': {
                'points': -1, 
                'name': 1
            }
        }, {
            '$limit': int(limit)
        }, {
            '$project': {
                'name': 1,
                'points': 1
            }
        }
    ])

@router.get("/leaderboard/rank/{user_id}")
async def get_rank(user_id: str) -> int:
    points = await config.db.find_one({UserRef.ID: user_id})[points]
    rank = await config.db.aggregate([
        {
            '$match': {
                'points': {
                    '$lt': points
                }
            }
        }, {
            '$count': 'index'
        }
    ])['index'] + 1

    return rank