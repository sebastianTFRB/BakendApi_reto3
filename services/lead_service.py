from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.lead import Lead
from repositories.interaction_repository import LeadInteractionRepository
from repositories.lead_repository import LeadRepository
from repositories.property_repository import PropertyRepository
from schemas.interaction import LeadInteractionCreate
from schemas.lead import LeadCreate, LeadUpdate
from utils.scoring import calculate_intent_score


class LeadService:
    def __init__(self, db: Session):
        self.db = db
        self.lead_repo = LeadRepository(db)
        self.property_repo = PropertyRepository(db)
        self.interaction_repo = LeadInteractionRepository(db)

    def _resolve_agency(self, current_user, requested_agency_id: Optional[int]) -> Optional[int]:
        if getattr(current_user, "is_superuser", False) and requested_agency_id:
            return requested_agency_id
        return requested_agency_id or getattr(current_user, "agency_id", None)

    def _agency_scope(self, current_user) -> Optional[int]:
        return None if getattr(current_user, "is_superuser", False) else getattr(current_user, "agency_id", None)

    def _recalculate(self, lead: Lead):
        properties = self.property_repo.list(lead.agency_id)
        score, category = calculate_intent_score(
            lead.preferred_area,
            float(lead.budget) if lead.budget else None,
            lead.urgency,
            properties,
        )
        lead.intent_score = score
        lead.category = category

    def create_lead(self, lead_in: LeadCreate, current_user) -> Lead:
        agency_id = self._resolve_agency(current_user, lead_in.agency_id)
        if not agency_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency is required for lead")

        lead = Lead(
            agency_id=agency_id,
            full_name=lead_in.full_name,
            email=lead_in.email,
            phone=lead_in.phone,
            preferred_area=lead_in.preferred_area,
            budget=lead_in.budget,
            urgency=lead_in.urgency,
            notes=lead_in.notes,
        )
        self._recalculate(lead)
        return self.lead_repo.create(lead)

    def update_lead(self, lead_id: int, lead_in: LeadUpdate, current_user) -> Lead:
        lead = self.lead_repo.get(lead_id, self._agency_scope(current_user))
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        updatable_fields = lead_in.dict(exclude_unset=True)
        for field, value in updatable_fields.items():
            setattr(lead, field, value)

        if any(field in updatable_fields for field in ["preferred_area", "budget", "urgency"]):
            self._recalculate(lead)

        self.db.commit()
        self.db.refresh(lead)
        return lead

    def list_leads(self, current_user):
        return self.lead_repo.list(self._agency_scope(current_user))

    def get_lead(self, lead_id: int, current_user):
        lead = self.lead_repo.get(lead_id, self._agency_scope(current_user))
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        return lead

    def delete_lead(self, lead_id: int, current_user):
        lead = self.lead_repo.get(lead_id, self._agency_scope(current_user))
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        self.lead_repo.delete(lead)

    def add_interaction(self, lead_id: int, interaction_in: LeadInteractionCreate, current_user):
        lead = self.get_lead(lead_id, current_user)
        from models.interaction import LeadInteraction

        interaction = LeadInteraction(
            lead_id=lead.id,
            channel=interaction_in.channel,
            direction=interaction_in.direction,
            message=interaction_in.message,
        )
        return self.interaction_repo.create(interaction)
