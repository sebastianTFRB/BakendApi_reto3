from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from core.domain import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    role: UserRole
    agency_id: Optional[int] = None
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)
