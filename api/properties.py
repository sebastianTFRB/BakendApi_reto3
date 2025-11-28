from typing import List

from fastapi import APIRouter, Depends, status

from core.security import get_current_user
from schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from services.property_service import PropertyService

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("/", response_model=List[PropertyRead])
def list_properties(current_user=Depends(get_current_user)):
    service = PropertyService()
    return service.list_properties(current_user)


@router.post("/", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(property_in: PropertyCreate, current_user=Depends(get_current_user)):
    service = PropertyService()
    return service.create_property(property_in, current_user)


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: int, current_user=Depends(get_current_user)):
    service = PropertyService()
    return service.get_property(property_id, current_user)


@router.put("/{property_id}", response_model=PropertyRead)
def update_property(property_id: int, property_in: PropertyUpdate, current_user=Depends(get_current_user)):
    service = PropertyService()
    return service.update_property(property_id, property_in, current_user)


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: int, current_user=Depends(get_current_user)):
    service = PropertyService()
    service.delete_property(property_id, current_user)
    return None
