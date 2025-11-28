from typing import List, Optional

from sqlalchemy.orm import Session

from models.lead import Lead
from repositories.base import BaseRepository


class LeadRepository(BaseRepository):
    def get(self, lead_id: int, agency_id: Optional[int]) -> Optional[Lead]:
        query = self.db.query(Lead).filter(Lead.id == lead_id)
        if agency_id is not None:
            query = query.filter(Lead.agency_id == agency_id)
        return query.first()

    def list(self, agency_id: Optional[int]) -> List[Lead]:
        query = self.db.query(Lead)
        if agency_id is not None:
            query = query.filter(Lead.agency_id == agency_id)
        return query.order_by(Lead.created_at.desc()).all()

    def create(self, lead: Lead) -> Lead:
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def update(self, lead: Lead, **kwargs) -> Lead:
        for field, value in kwargs.items():
            setattr(lead, field, value)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def delete(self, lead: Lead) -> None:
        self.db.delete(lead)
        self.db.commit()
