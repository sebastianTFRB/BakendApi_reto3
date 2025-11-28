from datetime import datetime

from pydantic import BaseModel


class LeadInteractionBase(BaseModel):
    channel: str = "whatsapp"
    direction: str = "inbound"
    message: str


class LeadInteractionCreate(LeadInteractionBase):
    pass


class LeadInteractionRead(LeadInteractionBase):
    id: int
    lead_id: int
    created_at: datetime

    class Config:
        orm_mode = True
