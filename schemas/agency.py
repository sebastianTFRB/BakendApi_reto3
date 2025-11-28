from typing import Optional

from pydantic import BaseModel, ConfigDict


class AgencyBase(BaseModel):
    name: str
    domain: Optional[str] = None


class AgencyCreate(AgencyBase):
    pass


class AgencyRead(AgencyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
