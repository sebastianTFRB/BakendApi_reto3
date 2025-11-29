from typing import Optional

from pydantic import BaseModel

from core.domain import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole
    agency_id: Optional[int] = None
