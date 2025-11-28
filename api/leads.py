from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.security import get_current_user
from db.session import get_db
from schemas.interaction import LeadInteractionCreate, LeadInteractionRead
from schemas.lead import LeadCreate, LeadRead, LeadUpdate
from services.lead_service import LeadService

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/", response_model=list[LeadRead])
def list_leads(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = LeadService(db)
    return service.list_leads(current_user)


@router.post("/", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(lead_in: LeadCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = LeadService(db)
    return service.create_lead(lead_in, current_user)


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = LeadService(db)
    return service.get_lead(lead_id, current_user)


@router.put("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: int, lead_in: LeadUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = LeadService(db)
    return service.update_lead(lead_id, lead_in, current_user)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = LeadService(db)
    service.delete_lead(lead_id, current_user)
    return None


@router.post("/{lead_id}/interactions", response_model=LeadInteractionRead, status_code=status.HTTP_201_CREATED)
def add_interaction(lead_id: int, interaction_in: LeadInteractionCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = LeadService(db)
    return service.add_interaction(lead_id, interaction_in, current_user)
