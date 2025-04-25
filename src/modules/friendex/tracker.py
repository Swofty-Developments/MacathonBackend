import asyncio
from datetime import datetime


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
