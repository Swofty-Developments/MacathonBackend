# Handle passing user token after validating password hash, password resets,
# etc.

import logging
import math
from typing import Annotated

from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user_models import UserDto
from models.user_models import PublicUserDto
from modules.db import CollectionRef, LocationRef, UserRef
from web.auth.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    tags=["users", "location"],
)


class LocationUserDto(PublicUserDto):
    latitude: float
    longitude: float


def haversine(point1, point2) -> float:
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
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance
    distance = R * c

    return distance


async def aggregate_locations() -> dict[tuple[float, float]]:
    collection = await config.db.get_collection(CollectionRef.LOCATIONS)
    locations = await collection.find({}).to_list()

    location_table = {}
    for location in locations:
        location_table[location[LocationRef.USER]] = (
            location[LocationRef.LATITUDE],
            location[LocationRef.LONGITUDE],
        )

    return location_table


@router.post("/location/upload/")
async def upload_location(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    latitude: float,
    longitude: float,
) -> dict:
    collection = await config.db.get_collection(CollectionRef.LOCATIONS)

    await collection.update_one(
        {LocationRef.USER: user.id},
        {"$set": { 
            LocationRef.USER: user.id,
            LocationRef.LATITUDE: latitude,
            LocationRef.LONGITUDE: longitude,
            LocationRef.CREATED: datetime.now(UTC)
        }},
        upsert=True
    )

    config.tracker.update_location(user.id, latitude, longitude)

    return {"message": "Location uploaded"}


@router.get("/location/radius-fetch/{user_id}")
async def fetch_radius(user_id: str, radius: float) -> list[LocationUserDto]:
    location_collection = await config.db.get_collection(CollectionRef.LOCATIONS)
    user = await location_collection.find_one({LocationRef.USER: user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User location not found, please upload location first",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_coords = (user[LocationRef.LATITUDE], user[LocationRef.LONGITUDE])
    location_table = await aggregate_locations()

    valid_ids = []
    for table_id, table_coords in location_table.items():
        if user_id == table_id:
            continue
        distance = haversine(user_coords, table_coords)
        if distance <= radius:
            valid_ids.append(table_id)

    user_collection = await config.db.get_collection(CollectionRef.USERS)
    valid_users = await user_collection.find({UserRef.ID: {"$in": valid_ids}}).to_list()

    for valid_user in valid_users:
        valid_id = valid_user[UserRef.ID]
        (lat, lon) = location_table[valid_id]
        valid_user[LocationRef.LATITUDE] = lat
        valid_user[LocationRef.LONGITUDE] = lon

    return valid_users
