from typing import Optional

from pydantic import BaseModel


class AgencyBase(BaseModel):
    name: str
    domain: Optional[str] = None


class AgencyCreate(AgencyBase):
    pass


class AgencyRead(AgencyBase):
    id: int

    class Config:
        orm_mode = True
