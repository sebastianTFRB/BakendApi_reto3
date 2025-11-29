from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PostBase(BaseModel):
    title: str
    description: Optional[str] = None


class PostUpdateMetadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class PostRead(PostBase):
    id: UUID
    photos: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    company_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
