from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from core.domain import LeadCategory, LeadUrgency
from schemas.interaction import LeadInteractionRead


class LeadBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    preferred_area: Optional[str] = None
    budget: Optional[float] = None
    urgency: LeadUrgency = LeadUrgency.medium
    notes: Optional[str] = None
    post_id: Optional[str] = None
    agency_id: Optional[int] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    preferred_area: Optional[str] = None
    budget: Optional[float] = None
    urgency: Optional[LeadUrgency] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    category: Optional[LeadCategory] = None
    post_id: Optional[str] = None


class LeadRead(LeadBase):
    id: int
    agency_id: Optional[int] = None
    user_id: Optional[int] = None
    intent_score: float
    category: LeadCategory
    status: str
    preferences: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    interactions: List[LeadInteractionRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
