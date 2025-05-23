import json

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
    _StreamingResponse,
)


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        response: _StreamingResponse = await call_next(request)

        if request.url.path.startswith("/auth/login"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return response

        if response.status_code == 200:
            return JSONResponse(
                content={"status": "success", "data": payload},
                status_code=response.status_code,
            )
        else:
            return JSONResponse(
                content={"status": "failed", "data": payload},
                status_code=response.status_code,
            )
