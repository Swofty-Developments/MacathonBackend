import asyncio
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import config
from modules.db import CollectionRef, UserRef
from models.user_models import UserDto

from modules.friendex import locations
from web.routers.location_routes import haversine


LOCATION_TTL = 30
TRACKING_TTL = 60 * 20

MAX_DISTANCE = 0.008 # 8 meters


class PlayersTracker():
    locations: dict[str, tuple[float, float, datetime]] = {}
    # First and second UUID is user A and B respectively, where A is the one who has selected B.
    currently_tracking: dict[str, tuple[str, datetime]] = defaultdict(dict)

    async def on_tick(self) -> None:
        # Give points and shit here
        await self.cleanup()
        
        for id_1, tracking in self.currently_tracking.items():
            id_2, _ = tracking

            if id_1 not in self.locations.keys():
                return
            elif id_2 not in self.locations.keys():
                return

            lat_1, long_1, _ = self.locations[id_1]
            lat_2, long_2, _ = self.locations[id_2]

            if id_1 == id_2:
                continue

            distance = haversine((lat_1, long_1), (lat_2, long_2))

            if distance <= MAX_DISTANCE:
                multiplier_1 = await self.classroom_multiplier(id_1)
                multiplier_2 = await self.classroom_multiplier(id_2)

                await self.give_points(id_1, multiplier_1)
                await self.give_points(id_2, multiplier_2)

    async def give_points(self, user_id: str, multiplier: float) -> None:
        user_collection = await config.db.get_collection(CollectionRef.USERS)
        user = UserDto.model_validate(await user_collection.find_one({UserRef.ID: user_id}))

        points = 1 * multiplier
        user.points += points

        await user_collection.update_one(
            {UserRef.ID: user.id},
            {"$set": user.model_dump()}
        )

        return {"message": f"Awarded {points} points to {user.id} with multiplier {multiplier}"}
        

    async def cleanup(self) -> None:
        user_collection = await config.db.get_collection(CollectionRef.USERS)

        ids_to_remove = []
        for id, location in self.locations.items():
            lat, long, ttl = location
            if datetime.now(timezone.utc) - ttl > timedelta(seconds=LOCATION_TTL):
                ids_to_remove.append(id)
        [self.locations.pop(id, None) for id in ids_to_remove]
        
        for id, player in self.currently_tracking.items():
            other_id, ttl = player
            if datetime.now(timezone.utc) - ttl > timedelta(seconds=TRACKING_TTL):
                user = UserDto.model_validate(await user_collection.find_one({UserRef.ID: id}))
                user.selected_friend = None
                await user_collection.update_one(
                    {UserRef.ID: user.id},
                    {"$set": user.model_dump()},
                )

                ids_to_remove.append(id)
        [self.currently_tracking.pop(id, None) for id in ids_to_remove]
    
    async def start_loop(self) -> None:
        while True:
            await self.on_tick()
            await asyncio.sleep(5) # Adjust frequency as needed.

    async def populate(self) -> None:
        user_collection = await config.db.get_collection(CollectionRef.USERS)
        
        users = [UserDto.model_validate(user) for user in await user_collection.find({UserRef.SELECTED_FRIEND: {"$ne": None}}).to_list(length=None)]
        for user in users:
            self.add_tracking(user.id, user.selected_friend)

    def update_location(self, id: str, lat: float, long: float) -> None:
        self.locations[id] = (lat, long, datetime.now(timezone.utc))
    
    def remove_location(self, id: str) -> None:
        self.locations.pop(id, None)
    
    def add_tracking(self, id_1: str, id_2: str) -> None:
        # Have ttl logic for tracking whilst rewarding points
        self.currently_tracking[id_1] = (id_2, datetime.now(timezone.utc))
        ...

    def remove_tracking(self, id_1: str) -> None:
        self.currently_tracking.pop(id_1)
    
    async def classroom_multiplier(self, user_id: str) -> int:
        user_location_collection = self.locations.get(user_id)
        lat, long, _ = user_location_collection

        user_coords = (lat, long)
        for location in locations.CLASSROOM_LOCATIONS:
            distance = haversine(user_coords, location["coords"])
            if distance <= location["radius"]/1000:
                return 2
    
        return 1