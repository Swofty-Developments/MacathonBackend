# Handle passing user token after validating password hash, password resets,
# etc.

import logging
import math
from typing import Annotated

from datetime import datetime, UTC
from fastapi import APIRouter, Depends

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
    locations = await collection.find({})

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
    
    query = { LocationRef.USER: user.id }

    doc = { 
        LocationRef.USER: user.id,
        LocationRef.LATITUDE: latitude,
        LocationRef.LONGITUDE: longitude,
        LocationRef.CREATED: datetime.now(UTC)
    }

    options = { 'upsert': True }

    await collection.replace_one(query, doc, options)
    return {"message": "Location uploaded"}


@router.get("/location/radiusFetch")
async def fetch_radius(user_id: str, radius: float) -> list[LocationUserDto]:
    collection = await config.db.get_collection(CollectionRef.LOCATIONS)
    user = await collection.find_one({LocationRef.USER: user_id})
    user_coords = (user[LocationRef.LATITUDE], user[LocationRef.LONGITUDE])
    location_table = await aggregate_locations()

    valid_ids = []
    for table_id, table_coords in location_table.items():
        if user_id == table_id:
            continue
        distance = haversine(user_coords, table_coords)
        if distance <= radius:
            valid_ids.append(table_id)

    projection = {}

    valid_users = await collection.aggregate(
        [{"$match": {UserRef.ID: {"$in": valid_ids}}}, {"$project": projection}]
    )

    for valid_user in valid_users:
        valid_id = valid_user[UserRef.ID]
        (lat, lon) = location_table[valid_id]
        valid_user[LocationRef.LATITUDE] = lat
        valid_user[LocationRef.LONGITUDE] = lon

    return valid_users
