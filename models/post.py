from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class Post(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    photos: List[str]
    videos: List[str]
    company_id: int
    created_at: datetime
    updated_at: datetime
