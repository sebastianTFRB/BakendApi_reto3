from typing import Optional

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, EmailStr

from core.security import get_current_user, resolve_role
from schemas.token import Token
from schemas.user import UserCreate, UserRead
from services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=UserRead, status_code=201)
def register_user(user_in: UserCreate):
    service = AuthService()
    return service.register_user(user_in)


@router.post("/login", response_model=Token)
def login(login: LoginRequest = Body(...)):
    service = AuthService()
    user = service.authenticate_user(login.email, login.password)
    token = service.create_login_token(user)
    role = resolve_role(user)
    return Token(
        access_token=token,
        user_id=user["id"],
        role=role,
        agency_id=user.get("agency_id"),
    )

@router.get("/me", response_model=UserRead)
def read_me(current_user=Depends(get_current_user)):
    return current_user
