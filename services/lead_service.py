from typing import Optional

from fastapi import HTTPException, status

from core.domain import UserRole
from core.security import resolve_role
from db.supabase_client import get_supabase_client
from repositories.interaction_repository import LeadInteractionRepository
from repositories.lead_repository import LeadRepository
from repositories.post_repository import PostRepository
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
        self.post_repo = PostRepository(supabase)

    def _is_superadmin(self, current_user) -> bool:
        return resolve_role(current_user) == UserRole.superadmin.value

    def _scope(self, current_user):
        if self._is_superadmin(current_user):
            return {"agency_id": None, "user_id": None}
        agency_id = current_user.get("agency_id")
        if agency_id:
            return {"agency_id": agency_id, "user_id": None}
        return {"agency_id": None, "user_id": current_user.get("id")}

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
        if not lead_in.post_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="post_id is required")

        post = self.post_repo.get(lead_in.post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        agency_id = post.get("company_id") or post.get("agency_id")
        if not agency_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post missing agency/company")

        lead_payload = {
            "agency_id": agency_id,
            "user_id": current_user.get("id"),
            "full_name": lead_in.full_name,
            "email": lead_in.email,
            "phone": lead_in.phone,
            "preferred_area": lead_in.preferred_area,
            "budget": lead_in.budget,
            "urgency": getattr(lead_in.urgency, "value", lead_in.urgency),
            "notes": lead_in.notes,
            "status": "new",
            "post_id": lead_in.post_id,
        }
        self._recalculate(lead_payload)
        return self.lead_repo.create(lead_payload)

    def update_lead(self, lead_id: int, lead_in: LeadUpdate, current_user) -> dict:
        scope = self._scope(current_user)
        lead = self.lead_repo.get(lead_id, scope["agency_id"], scope["user_id"])
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        updates = lead_in.dict(exclude_unset=True)
        if "urgency" in updates and hasattr(updates["urgency"], "value"):
            updates["urgency"] = updates["urgency"].value
        if "post_id" in updates and updates["post_id"]:
            post = self.post_repo.get(updates["post_id"])
            if not post:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
            updates["agency_id"] = post.get("company_id") or post.get("agency_id")
        merged = {**lead, **updates}
        if any(field in updates for field in ["preferred_area", "budget", "urgency"]):
            self._recalculate(merged)
        updates.update({"intent_score": merged.get("intent_score"), "category": merged.get("category")})
        return self.lead_repo.update(lead_id, updates)

    def list_leads(self, current_user):
        scope = self._scope(current_user)
        return self.lead_repo.list(scope["agency_id"], scope["user_id"])

    def get_lead(self, lead_id: int, current_user):
        scope = self._scope(current_user)
        lead = self.lead_repo.get(lead_id, scope["agency_id"], scope["user_id"])
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        lead["interactions"] = self.interaction_repo.list_by_lead(lead_id)
        return lead

    def delete_lead(self, lead_id: int, current_user):
        scope = self._scope(current_user)
        lead = self.lead_repo.get(lead_id, scope["agency_id"], scope["user_id"])
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
