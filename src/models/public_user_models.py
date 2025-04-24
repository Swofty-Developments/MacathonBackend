from .generic import DBRecord
from typing import Optional

class PublicUserDto(DBRecord):
    id: Optional[str] = None
    name: str
    points: int