from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from core.security import get_current_user
from schemas.token import Token
from schemas.user import UserCreate, UserRead
from services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register_user(user_in: UserCreate):
    service = AuthService()
    user = service.register_user(user_in)
    token = service.create_login_token(user)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    service = AuthService()
    user = service.authenticate_user(form_data.username, form_data.password)
    token = service.create_login_token(user)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def read_me(current_user=Depends(get_current_user)):
    return current_user
