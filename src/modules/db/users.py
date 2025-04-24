from enum import StrEnum


class UserRef(StrEnum):
    ID = "_id"
    NAME = "name"
    HASHED_PASSWORD = "hashed_password"
    DISABLED = "disabled"
    POINTS = "points"
    QUESTIONS = "questions"
