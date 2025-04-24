from .generic import DBRecord
from typing import Optional


class FriendexDto(DBRecord):
    id: Optional[str] = None
    owner: str
    friends: list[str]
