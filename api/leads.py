from typing import List

from fastapi import APIRouter, Depends, status

from core.security import get_current_user
from schemas.interaction import LeadInteractionCreate, LeadInteractionRead
from schemas.lead import LeadCreate, LeadRead, LeadUpdate
from services.lead_service import LeadService

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/", response_model=List[LeadRead])
def list_leads(current_user=Depends(get_current_user)):
    service = LeadService()
    return service.list_leads(current_user)


@router.post("/", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(lead_in: LeadCreate, current_user=Depends(get_current_user)):
    service = LeadService()
    return service.create_lead(lead_in, current_user)


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, current_user=Depends(get_current_user)):
    service = LeadService()
    return service.get_lead(lead_id, current_user)


@router.put("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: int, lead_in: LeadUpdate, current_user=Depends(get_current_user)):
    service = LeadService()
    return service.update_lead(lead_id, lead_in, current_user)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, current_user=Depends(get_current_user)):
    service = LeadService()
    service.delete_lead(lead_id, current_user)
    return None


@router.post("/{lead_id}/interactions", response_model=LeadInteractionRead, status_code=status.HTTP_201_CREATED)
def add_interaction(lead_id: int, interaction_in: LeadInteractionCreate, current_user=Depends(get_current_user)):
    service = LeadService()
    return service.add_interaction(lead_id, interaction_in, current_user)
