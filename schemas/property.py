from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PropertyBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    area: Optional[str] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    status: str = "available"
    agency_id: Optional[int] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    area: Optional[str] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    status: Optional[str] = None


class PropertyRead(PropertyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
