from pydantic import BaseModel

class TokenDto(BaseModel):
    access_token: str
    token_type: str

class TokenDataDto(BaseModel):
    id: str | None = None
