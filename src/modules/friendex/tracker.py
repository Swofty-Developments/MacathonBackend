import asyncio
from datetime import datetime, timezone
from collections import defaultdict


class PlayersTracker():
    locations: dict[str, tuple[float, float, datetime]] = {}
    # First and second UUID is user A and B respectively, where A is the one who has selected B.
    currently_tracking: dict[str, dict[str, datetime]] = defaultdict(dict)

    async def on_tick(self) -> None:
        # Give points and shit here
        # print(self.locations)
        ...
    
    async def start_loop(self) -> None:
        while True:
            await self.on_tick()
            await asyncio.sleep(1) # Adjust frequency as needed.

    def update_location(self, id: str, lat: float, long: float) -> None:
        self.locations[id] = (lat, long, datetime.now(timezone.utc))
    
    def remove_location(self, id: str) -> None:
        self.locations.pop(id, None)
    
    def add_tracking(self, id_1: str, id_2: str) -> None:
        # Have ttl logic for tracking whilst rewarding points
        self.currently_tracking[id_1][id_2] = datetime.now(timezone.utc)
    
    def remove_tracking(self, id_1: str, id_2: str = None) -> None:
        if id_2 is None:
            self.currently_tracking.pop(id_1)
        else:
            self.currently_tracking[id_1].pop(id_2, None)
