import asyncio
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

import config
from modules.db import CollectionRef, UserRef
from models.user_models import UserDto
from modules.friendex import locations
from web.routers.location_routes import haversine


LOCATION_TTL = 5
TRACKING_TTL = 60 * 20

MAX_DISTANCE = 0.008 # 8 meters

TICK_INTERVAL = 5 # seconds
POINTS_PER_TICK = 1

class TrackingDto(BaseModel):
    id_1: str
    id_2: str
    tracker_points_accumulated: float = 0.0
    tracking_points_accumulated: float = 0.0
    created_at: datetime


class PlayersTracker():
    locations: dict[str, tuple[int, int, datetime]] = {}
    # First and second UUID is user A and B respectively, where A is the one who has selected B.
    currently_tracking: list[TrackingDto] = []

    def get_player_tracking(self, id: str) -> TrackingDto:
        for tracking in self.currently_tracking:
            if tracking.id_1 == id or tracking.id_2 == id:
                return tracking
            
        return None

    async def on_tick(self) -> None:
        # Give points and shit here
        await self.cleanup()
        
        for tracking in self.currently_tracking:
            if tracking.id_1 not in self.locations.keys():
                return
            elif tracking.id_2 not in self.locations.keys():
                return

            lat_1, long_1, _ = self.locations[tracking.id_1]
            lat_2, long_2, _ = self.locations[tracking.id_2]

            if tracking.id_1 == tracking.id_2:
                continue

            distance = haversine((lat_1, long_1), (lat_2, long_2))

            if distance <= MAX_DISTANCE:
                multiplier_1 = self.classroom_multiplier(tracking.id_1)
                multiplier_2 = self.classroom_multiplier(tracking.id_2)

                await self.give_points(tracking.id_1, multiplier_1)
                await self.give_points(tracking.id_2, multiplier_2)

    async def give_points(self, user_id: str, multiplier: float) -> None:
        user_collection = await config.db.get_collection(CollectionRef.USERS)
        user = UserDto.model_validate(await user_collection.find_one({UserRef.ID: user_id}))

        points = POINTS_PER_TICK * multiplier

        user.points += points
        tracking = self.get_player_tracking(user_id)
        if tracking:
            if tracking.id_1 == user_id:
                tracking.tracker_points_accumulated += points
            elif tracking.id_2 == user_id:
                tracking.tracking_points_accumulated += points

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
        
        tracking_to_remove = []
        for tracking in self.currently_tracking:
            if datetime.now(timezone.utc) - tracking.created_at > timedelta(seconds=TRACKING_TTL):
                user = UserDto.model_validate(await user_collection.find_one({UserRef.ID: tracking.id_1}))
                user.selected_friend = None
                await user_collection.update_one(
                    {UserRef.ID: user.id},
                    {"$set": user.model_dump()},
                )

                tracking_to_remove.append(tracking)
        [self.currently_tracking.remove(tracking) for tracking in tracking_to_remove]
    
    async def start_loop(self) -> None:
        while True:
            await self.on_tick()
            await asyncio.sleep(TICK_INTERVAL) # Adjust frequency as needed.

    async def populate(self) -> None:
        user_collection = await config.db.get_collection(CollectionRef.USERS)
        
        users = [UserDto.model_validate(user) for user in await user_collection.find({UserRef.SELECTED_FRIEND: {"$ne": None}}).to_list(length=None)]
        for user in users:
            self.add_tracking(user.id, user.selected_friend)

    def get_selected_time(self, id: str) -> tuple[float, float]:
        tracking = self.get_player_tracking(id)
        if not tracking:
            return 0
        
        elapsed_time = (datetime.now(timezone.utc) - tracking.created_at).total_seconds()
        time_remaining = TRACKING_TTL - elapsed_time
        
        return time_remaining, elapsed_time
    
    def get_points_accumulated(self, id: str) -> float:
        time_remaining, elapsed_time = self.get_selected_time(id)
        if time_remaining <= 0:
            return 0
        
        tracking = self.get_player_tracking(id)
        if tracking.id_1 == id:
            return tracking.tracker_points_accumulated
        elif tracking.id_2 == id:
            return tracking.tracking_points_accumulated
        return self.currently_tracking[id][1]

    def update_location(self, id: str, lat: float, long: float) -> None:
        self.locations[id] = (lat, long, datetime.now(timezone.utc))
    
    def remove_location(self, id: str) -> None:
        self.locations.pop(id, None)
    
    def add_tracking(self, id_1: str, id_2: str) -> None:
        # Have ttl logic for tracking whilst rewarding points
        self.currently_tracking.append(TrackingDto(
            id_1=id_1,
            id_2=id_2,
            created_at=datetime.now(timezone.utc)
        ))
        ...

    async def remove_tracking(self, id: str) -> None:
        for tracking in self.currently_tracking:
            print(tracking.id_1, tracking.id_2, id)
            if tracking.id_1 == id or tracking.id_2 == id:
                user_collection = await config.db.get_collection(CollectionRef.USERS)

                user = UserDto.model_validate(await user_collection.find_one({UserRef.ID: tracking.id_1}))
                user.selected_friend = None
                await user_collection.update_one(
                    {UserRef.ID: user.id},
                    {"$set": user.model_dump()},
                )

                self.currently_tracking.remove(tracking)
                break
    
    def classroom_multiplier(self, user_id: str) -> int:
        user_location_collection = self.locations.get(user_id)
        lat, long, _ = user_location_collection

        user_coords = (lat, long)
        for location in locations.CLASSROOM_LOCATIONS:
            distance = haversine(user_coords, location["coords"])
            if distance <= location["radius"]/1000:
                return 2
    
        return 1