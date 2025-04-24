from enum import StrEnum


class LocationRef(StrEnum):
    ID = "_id"
    USER = "user_id"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    CREATED = "created_at"
