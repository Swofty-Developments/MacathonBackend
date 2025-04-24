# Chuck in anything related to the user model here.
# e.g. The user itself, maybe user settings (if separated) etc.

from typing import Optional

from pydantic import BaseModel

from .generic import DBRecord
from models.question_models import QuestionDto


class PublicUserDto(BaseModel):
    id: Optional[str] = None
    name: str
    points: int
    disabled: bool = False
    questions: list[QuestionDto] = None


class UserDto(PublicUserDto, DBRecord):
    hashed_password: Optional[str] = None
