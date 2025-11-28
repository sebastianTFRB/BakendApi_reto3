from typing import List

from models.interaction import LeadInteraction
from repositories.base import BaseRepository


class LeadInteractionRepository(BaseRepository):
    def create(self, interaction: LeadInteraction) -> LeadInteraction:
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def list_by_lead(self, lead_id: int) -> List[LeadInteraction]:
        return self.db.query(LeadInteraction).filter(LeadInteraction.lead_id == lead_id).order_by(LeadInteraction.created_at.desc()).all()
