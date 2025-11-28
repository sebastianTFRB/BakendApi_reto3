from typing import Optional

from fastapi import HTTPException, status

from db.supabase_client import get_supabase_client
from repositories.interaction_repository import LeadInteractionRepository
from repositories.lead_repository import LeadRepository
from repositories.property_repository import PropertyRepository
from schemas.interaction import LeadInteractionCreate
from schemas.lead import LeadCreate, LeadUpdate
from utils.scoring import calculate_intent_score


class LeadService:
    def __init__(self):
        supabase = get_supabase_client()
        self.lead_repo = LeadRepository(supabase)
        self.property_repo = PropertyRepository(supabase)
        self.interaction_repo = LeadInteractionRepository(supabase)

    def _resolve_agency(self, current_user, requested_agency_id: Optional[int]) -> Optional[int]:
        if current_user.get("is_superuser") and requested_agency_id:
            return requested_agency_id
        return requested_agency_id or current_user.get("agency_id")

    def _agency_scope(self, current_user) -> Optional[int]:
        return None if current_user.get("is_superuser") else current_user.get("agency_id")

    def _recalculate(self, lead_dict: dict):
        properties = self.property_repo.list(lead_dict.get("agency_id"))
        urgency_val = lead_dict.get("urgency")
        if hasattr(urgency_val, "value"):
            urgency_val = urgency_val.value
        score, category = calculate_intent_score(
            lead_dict.get("preferred_area"),
            float(lead_dict.get("budget")) if lead_dict.get("budget") else None,
            urgency_val,
            properties,
        )
        lead_dict["intent_score"] = score
        lead_dict["category"] = getattr(category, "value", category)

    def create_lead(self, lead_in: LeadCreate, current_user) -> dict:
        agency_id = self._resolve_agency(current_user, lead_in.agency_id)
        if not agency_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency is required for lead")

        lead_payload = {
            "agency_id": agency_id,
            "full_name": lead_in.full_name,
            "email": lead_in.email,
            "phone": lead_in.phone,
            "preferred_area": lead_in.preferred_area,
            "budget": lead_in.budget,
            "urgency": getattr(lead_in.urgency, "value", lead_in.urgency),
            "notes": lead_in.notes,
            "status": "new",
        }
        self._recalculate(lead_payload)
        return self.lead_repo.create(lead_payload)

    def update_lead(self, lead_id: int, lead_in: LeadUpdate, current_user) -> dict:
        lead = self.lead_repo.get(lead_id, self._agency_scope(current_user))
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        updates = lead_in.dict(exclude_unset=True)
        if "urgency" in updates and hasattr(updates["urgency"], "value"):
            updates["urgency"] = updates["urgency"].value
        merged = {**lead, **updates}
        if any(field in updates for field in ["preferred_area", "budget", "urgency"]):
            self._recalculate(merged)
        updates.update({"intent_score": merged.get("intent_score"), "category": merged.get("category")})
        return self.lead_repo.update(lead_id, updates)

    def list_leads(self, current_user):
        return self.lead_repo.list(self._agency_scope(current_user))

    def get_lead(self, lead_id: int, current_user):
        lead = self.lead_repo.get(lead_id, self._agency_scope(current_user))
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        lead["interactions"] = self.interaction_repo.list_by_lead(lead_id)
        return lead

    def delete_lead(self, lead_id: int, current_user):
        lead = self.lead_repo.get(lead_id, self._agency_scope(current_user))
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        self.lead_repo.delete(lead_id)

    def add_interaction(self, lead_id: int, interaction_in: LeadInteractionCreate, current_user):
        lead = self.get_lead(lead_id, current_user)
        payload = {
            "lead_id": lead_id,
            "channel": interaction_in.channel,
            "direction": interaction_in.direction,
            "message": interaction_in.message,
        }
        return self.interaction_repo.create(payload)
