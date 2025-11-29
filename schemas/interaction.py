from datetime import datetime

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)
