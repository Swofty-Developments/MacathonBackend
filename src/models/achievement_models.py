from typing import Optional

from pydantic import BaseModel

class AchievementDto(BaseModel):
    title: str
    description: str
    reward: int