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
from modules.db import CollectionRef, LocationRef, UserRef

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

def haversine(point1, point2):
    (lat1, lon1) = point1
    (lat2, lon2) = point2
    # Returns the distance in km between two places with given latitudes and
    # longitudes. Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance
    distance = R * c

    return distance

async def aggregate_locations() -> dict[tuple[float, float]]:
    collection = await config.db.get_collection(CollectionRef.LOCATIONS)
    locations = await collection.find({})

    location_table = {}
    for doc in locations:
        location_table[doc[LocationRef.USER]] = (doc[LocationRef.LATITUDE], doc[LocationRef.LONGITUDE])
    
    return location_table

@router.get("/location/radiusFetch")
async def fetch_radius(user_id: int, radius: float):
    collection = await config.db.get_collection(CollectionRef.LOCATIONS)
    user = await collection.find_one({ LocationRef.USER: user_id })
    user_coords = (user[LocationRef.LATITUDE], user[LocationRef.LONGITUDE])
    location_table = await aggregate_locations()

    valid_user_ids = []
    for table_id, table_coords in location_table.items():
        if user_id == table_id:
            continue
        distance = haversine(user_coords, table_coords)
        if (distance <= radius):
            valid_user_ids.append(table_id)
    
    projection = {}

    return await collection.aggregate(
        [{"$match": {UserRef.ID: {"$in": valid_user_ids}}}, {"$project": projection}]
    )