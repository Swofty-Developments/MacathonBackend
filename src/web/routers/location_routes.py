# Handle passing user token after validating password hash, password resets,
# etc.

import logging
import math

from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from typing import Optional
from pydantic import BaseModel

import config
from modules.db import CollectionRef, LocationRef

_log = logging.getLogger("uvicorn")
router = APIRouter(
    tags=["users", "location"],
)

@router.post("/location/upload/")
async def upload_location(user_id: int, latitude: float, longitude: float) -> dict:
    collection = await config.db.get_collection(CollectionRef.LOCATIONS)
    await collection.insert_one({ 
        LocationRef.USER: user_id,
        LocationRef.LATITUDE: latitude,
        LocationRef.LONGITUDE: longitude,
        LocationRef.CREATED: datetime.now(UTC)
    })
    return {"message": "Location uploaded"}

# def distance(origin, destination):
#     (lat1, lon1) = origin
#     (lat2, lon2) = destination
#     radius = 6371  # km

#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
#          math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
#          math.sin(dlon / 2) * math.sin(dlon / 2))
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     d = radius * c

#     return d

# async def aggregate_locations():
#     collection = await config.db.get_collection(CollectionRef.LOCATIONS)
#     locations = await collection.find({})

#     location_table = {}
#     for doc in locations:
#         doc

# @router.get("/location/radiusFetch")
# async def fetch_radius(user_id: int, radius: float):
