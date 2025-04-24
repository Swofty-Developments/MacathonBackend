# Chuck in anything related to the user model here.
# e.g. The user itself, maybe user settings (if separated) etc.

from typing import Optional

from .generic import DBRecord
from models.question_models import QuestionDto


class UserDto(DBRecord):
    id: Optional[str] = None
    name: str
    hashed_password: Optional[str] = None
    disabled: bool = False
    questions: list[QuestionDto] = None
