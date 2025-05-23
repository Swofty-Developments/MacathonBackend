# Handle passing user token after validating password hash, password resets,
# etc.

import logging
import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user_models import UserDto
from models.user_models import PublicUserDto
from modules.db import CollectionRef, UserRef
from web.auth.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    tags=["users", "location"],
)


class LocationUserDto(PublicUserDto):
    id: str
    latitude: float = -1
    longitude: float = -1
    is_occupied: bool = False

# Returns distance between 2 (latitude, longitude) pairs in km
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

# Returns dictionary of all recent locations of all active users
async def aggregate_locations() -> dict[tuple[float, float]]:
    # collection = await config.db.get_collection(CollectionRef.LOCATIONS)
    # locations = await collection.find({}).to_list()

    # location_table = {}
    # for location in locations:
    #     location_table[location[LocationRef.USER]] = (
    #         location[LocationRef.LATITUDE],
    #         location[LocationRef.LONGITUDE],
    #     )

    location_table = {}
    for user_id, (lat, long, _) in config.tracker.locations.items():
        location_table[user_id] = (lat, long)

    return location_table

# Upload the location of authenticated user in terms of latitude and longitude to the server
@router.post("/location/upload/")
async def upload_location(
    user: Annotated[UserDto, Depends(get_current_active_user)],
    latitude: float,
    longitude: float,
) -> dict:
    # collection = await config.db.get_collection(CollectionRef.LOCATIONS)

    # await collection.update_one(
    #     {LocationRef.USER: user.id},
    #     {"$set": { 
    #         LocationRef.USER: user.id,
    #         LocationRef.LATITUDE: latitude,
    #         LocationRef.LONGITUDE: longitude,
    #         LocationRef.CREATED: datetime.now(UTC)
    #     }},
    #     upsert=True
    # )

    config.tracker.update_location(user.id, latitude, longitude)

    return {"message": "Location uploaded"}

# Get all users within a 'radius' km distance to the most recent location of 'user_id'
@router.get("/location/radius-fetch/{user_id}")
async def fetch_radius(user_id: str, radius: float) -> list[LocationUserDto]:
    # location_collection = await config.db.get_collection(CollectionRef.LOCATIONS)
    # user = await location_collection.find_one({LocationRef.USER: user_id})
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="User location not found, please upload location first",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )

    if user_id not in config.tracker.locations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User location not found, please upload location first",
            headers={"WWW-Authenticate": "Bearer"},
        )

    lat, long, _ = config.tracker.locations.get(user_id)
    location_table = await aggregate_locations()

    valid_ids = []
    for table_id, table_coords in location_table.items():
        if user_id == table_id:
            continue
        distance = haversine((lat, long), table_coords)
        if distance <= radius:
            valid_ids.append(table_id)

    user_collection = await config.db.get_collection(CollectionRef.USERS)
    valid_users = [LocationUserDto.model_validate(data) async for data in user_collection.find({UserRef.ID: {"$in": valid_ids}})]

    for valid_user in valid_users:
        (lat, lon) = location_table[valid_user.id]
        valid_user.latitude = lat
        valid_user.longitude = lon
        valid_user.is_occupied = True if config.tracker.get_player_tracking(valid_user.id) else False

    return valid_users
