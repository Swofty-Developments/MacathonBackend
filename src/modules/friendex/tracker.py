import asyncio
from datetime import datetime
from fastapi import HTTPException, status
import config
from modules.db import CollectionRef, LocationRef
from web.routers.location_routes import haversine
import modules.friendex.locations as classrooms


class PlayersTracker():
    locations: dict[str, tuple[float, float]] = {}
    # First and second UUID is user A and B respectively, where A is the one who has selected B.
    currently_tracking: dict[str, str, datetime] = {}

    async def on_tick(self) -> None:
        # Give points and shit here
        # print("wee")
        ...
    
    async def start_loop(self) -> None:
        while True:
            await self.on_tick()
            await asyncio.sleep(1) # Adjust frequency as needed.

    async def add_location(id: str, lat: float, long: float) -> None:
        ...
    
    async def remove_location(id: str) -> None:
        ...
    
    async def add_tracking(id_1: str, id_2: str) -> None:
        # Have ttl logic for tracking whilst rewarding points
        ...
    
    async def classroom_multiplier(
        user_id: str
    ) -> float:
        user_location_collection = await config.db.get_collection(CollectionRef.LOCATIONS)
        user = await user_location_collection.find_one({LocationRef.USER: user_id})

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User location not found, please upload location first",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_coords = (user[LocationRef.LATITUDE], user[LocationRef.LONGITUDE])
        for location in classrooms.CLASSROOM_LOCATIONS:
            distance = haversine(user_coords, location["coords"])
            if distance <= location["radius"]/1000:
                return 1.5
    
        return 1.0
