from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.domain import UserRole
from core.config import settings
from db.supabase_client import get_supabase_client

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    from repositories.user_repository import UserRepository

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if hasattr(request.state, "user"):
        return request.state.user
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    supabase = get_supabase_client()
    user_repo = UserRepository(supabase)
    user = user_repo.get(int(user_id))
    if user is None or not user.get("is_active", False):
        raise credentials_exception
    if user.get("is_superuser"):
        user["role"] = UserRole.superadmin.value
    elif "role" not in user or not user.get("role"):
        user["role"] = UserRole.user.value
    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.get("is_active", False):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


def resolve_role(user: dict) -> str:
    if user.get("is_superuser"):
        return UserRole.superadmin.value

    role = user.get("role")
    if hasattr(role, "value"):
        role = role.value
    if role:
        return str(role)
    return UserRole.user.value


def require_roles(*roles):
    allowed = {r.value if hasattr(r, "value") else str(r) for r in roles}

    def dependency(current_user=Depends(get_current_user)):
        user_role = resolve_role(current_user)
        if user_role == UserRole.superadmin.value:
            return current_user
        if user_role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency
