from typing import List

from fastapi import APIRouter, Depends, status

from core.domain import UserRole
from core.security import require_roles
from schemas.agency import AgencyCreate, AgencyRead
from services.agency_service import AgencyService

router = APIRouter(prefix="/api/agencies", tags=["agencies"])


@router.get("/", response_model=List[AgencyRead])
def list_agencies(current_user=Depends(require_roles(UserRole.agency_admin, UserRole.superadmin))):
    service = AgencyService()
    return service.list_agencies()


@router.post("/", response_model=AgencyRead, status_code=status.HTTP_201_CREATED)
def create_agency(
    agency_in: AgencyCreate, current_user=Depends(require_roles(UserRole.agency_admin, UserRole.superadmin))
):
    service = AgencyService()
    return service.create_agency(agency_in)


@router.get("/{agency_id}", response_model=AgencyRead)
def get_agency(agency_id: int, current_user=Depends(require_roles(UserRole.agency_admin, UserRole.superadmin))):
    service = AgencyService()
    return service.get_agency(agency_id)
