from typing import Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from core.domain import UserRole
from core.config import settings
from db.supabase_client import get_supabase_client
from repositories.user_repository import UserRepository


class TokenAuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        exclude_paths: Tuple[str, ...] = (
            "/api/auth",
            "/api/lead/analyze",
            "/api/analytics/summary",
            "/docs",
            "/openapi.json",
            "/health",
        ),
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(prefix) for prefix in self.exclude_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id = payload.get("sub")
        except JWTError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        if not user_id:
            return JSONResponse(status_code=401, content={"detail": "Invalid token payload"})

        supabase = get_supabase_client()
        user = UserRepository(supabase).get(int(user_id))
        if not user or not user.get("is_active", False):
            return JSONResponse(status_code=401, content={"detail": "User not found or inactive"})
        if user.get("is_superuser"):
            user["role"] = UserRole.superadmin.value
        elif "role" not in user or not user.get("role"):
            user["role"] = UserRole.user.value
        request.state.user = user

        return await call_next(request)
