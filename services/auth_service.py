from fastapi import HTTPException, status

from core.domain import UserRole
from core.security import create_access_token, get_password_hash, verify_password
from core.security import resolve_role
from db.supabase_client import get_supabase_client
from repositories.agency_repository import AgencyRepository
from repositories.user_repository import UserRepository
from schemas.user import UserCreate


class AuthService:
    def __init__(self):
        supabase = get_supabase_client()
        self.user_repo = UserRepository(supabase)
        self.agency_repo = AgencyRepository(supabase)

    def register_user(self, user_in: UserCreate) -> dict:
        existing = self.user_repo.get_by_email(user_in.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        hashed = get_password_hash(user_in.password)
        payload = {
            "email": user_in.email,
            "full_name": user_in.full_name,
            "phone": user_in.phone,
            "hashed_password": hashed,
            "agency_id": None,
            "is_active": True,
            "is_superuser": False,
            "role": UserRole.user.value,
        }
        return self.user_repo.create(payload)

    def authenticate_user(self, email: str, password: str) -> dict:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.get("hashed_password", "")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        return user

    def create_login_token(self, user: dict) -> str:
        role = resolve_role(user)
        return create_access_token(
            {
                "sub": str(user["id"]),
                "email": user["email"],
                "role": role,
                "agency_id": user.get("agency_id"),
            }
        )
