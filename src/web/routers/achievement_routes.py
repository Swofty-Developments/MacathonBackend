import logging

from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends

import config
from models.user_models import UserDto
from models.achievement_models import AchievementDto
from modules.db import CollectionRef, UserRef
from web.auth.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/user",
    tags=["users", "achievements"],
)

ACHIEVEMENTS = [
    {"title": "Not a loner I see", "description": "You aren't a loner anymore!", "points": 10, "min_friends": 1},
    {"title": "Got a lil something going ;)", "description": "You've made 5 friends, I see you go", "points": 25, "min_friends": 5},
    {"title": "Almost a soccer squad", "description": "Just say you're making your own team", "points": 35, "min_friends": 10},
    {"title": "Ok Mr Popular", "description": "Really collecting people now aren't we", "points": 10, "min_friends": 20},
]

@router.get("/{user_id}")
async def get_achievements(user_id: str) -> dict:
    collection = await config.db.get_collection(CollectionRef.USERS)
    user = await collection.find_one({UserRef.ID: user_id})

    if not user:
        return {"achievements": []}
    return {"achievements": user.get(UserRef.ACHIEVEMENTS, [])}

async def update_achievements(
    user_id: str
)-> dict:
    collection = await config.db.get_collection(CollectionRef.USERS)
    user = await collection.find_one({UserRef.ID: user_id})

    current_achievements = {ach['title'] for ach in user.get("achievements", [])}
    count = len(user.get("friends", []))
    points = user.get("points", 0)

    new_achievements = []
    for title, desc, points, min in ACHIEVEMENTS:
        if count>= min and title not in current_achievements:
            new_achievements.append({
                "title": title, 
                "description": desc, 
                "reward": points
            })

    if new_achievements:
        await collection.update_one(
            {UserRef.ID: user_id}, 
            {
                "$push": {"achievements": {"$each": new_achievements}},
                "$set": {"points": points + sum(ach["reward"] for ach in new_achievements)}
            }
        )

    return {"message": f"{len(new_achievements)} new achievement(s)" if new_achievements else "No new Achievements"}
