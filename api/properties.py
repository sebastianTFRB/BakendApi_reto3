from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.security import get_current_user
from db.session import get_db
from schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from services.property_service import PropertyService

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("/", response_model=list[PropertyRead])
def list_properties(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = PropertyService(db)
    return service.list_properties(current_user)


@router.post("/", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(property_in: PropertyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = PropertyService(db)
    return service.create_property(property_in, current_user)


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = PropertyService(db)
    return service.get_property(property_id, current_user)


@router.put("/{property_id}", response_model=PropertyRead)
def update_property(property_id: int, property_in: PropertyUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = PropertyService(db)
    return service.update_property(property_id, property_in, current_user)


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service = PropertyService(db)
    service.delete_property(property_id, current_user)
    return None
