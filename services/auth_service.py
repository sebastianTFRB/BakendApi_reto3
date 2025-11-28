from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import create_access_token, get_password_hash, verify_password
from models.user import User
from repositories.agency_repository import AgencyRepository
from repositories.user_repository import UserRepository
from schemas.user import UserCreate


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.agency_repo = AgencyRepository(db)

    def register_user(self, user_in: UserCreate) -> User:
        existing = self.user_repo.get_by_email(user_in.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        agency_id = user_in.agency_id
        if agency_id:
            agency = self.agency_repo.get(agency_id)
            if not agency:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
        hashed = get_password_hash(user_in.password)
        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed,
            agency_id=agency_id,
        )
        return self.user_repo.create(user)

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        return user

    def create_login_token(self, user: User) -> str:
        return create_access_token({"sub": str(user.id), "email": user.email})
