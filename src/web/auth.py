from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from config import INTERFACE_API_KEY


api_key_header = APIKeyHeader(name="Authorization")


def require_api_key(api_key_header: str = Security(api_key_header)) -> bool:
    if api_key_header != INTERFACE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return True
