from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from mytask.common.settings import get_settings


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for specific paths if needed
        print(request.url.path)
        return await call_next(request)
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get auth token from settings
        settings = get_settings()
        auth_token = settings.auth_token
        
        # Extract bearer token from header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing"}
            )
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication scheme"}
                )
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid Authorization header format"}
            )
        
        # Validate token
        if token != auth_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
            )
        
        # Token is valid, continue with the request
        return await call_next(request)
