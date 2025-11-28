from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.security import get_current_user
from db.session import get_db
from schemas.agency import AgencyCreate, AgencyRead
from services.agency_service import AgencyService

router = APIRouter(prefix="/api/agencies", tags=["agencies"])


@router.get("/", response_model=list[AgencyRead])
def list_agencies(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = AgencyService(db)
    return service.list_agencies()


@router.post("/", response_model=AgencyRead, status_code=status.HTTP_201_CREATED)
def create_agency(agency_in: AgencyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = AgencyService(db)
    return service.create_agency(agency_in)


@router.get("/{agency_id}", response_model=AgencyRead)
def get_agency(agency_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = AgencyService(db)
    return service.get_agency(agency_id)
