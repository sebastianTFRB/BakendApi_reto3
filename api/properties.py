from typing import List

from fastapi import APIRouter, Depends, status, UploadFile, File, Form

from core.security import get_current_user
from schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from services.property_service import PropertyService

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("", response_model=List[PropertyRead])
def list_properties(
    location: str = "",
    property_type: str = "",
    min_price: float = 0,
    max_price: float = 0,
    bedrooms: int = 0,
    bathrooms: int = 0,
    parking: bool | None = None,
    current_user=Depends(get_current_user),
):
    service = PropertyService()
    return service.list_properties(
        current_user,
        location=location,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        parking=parking,
    )


@router.post("", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(property_in: PropertyCreate, current_user=Depends(get_current_user)):
    service = PropertyService()
    return service.create_property(property_in, current_user)

@router.post("/with-media", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property_with_media(
    title: str = Form(...),
    price: float = Form(...),
    description: str | None = Form(None),
    area: str | None = Form(None),
    location: str | None = Form(None),
    property_type: str | None = Form(None),
    bedrooms: int | None = Form(None),
    bathrooms: int | None = Form(None),
    parking: bool | None = Form(None),
    status: str = Form("available"),
    photos: list[UploadFile] = File(None),
    agency_id: int | None = Form(None),
    current_user=Depends(get_current_user),
):
    service = PropertyService()
    return service.create_property_with_media(
        title=title,
        price=price,
        description=description,
        area=area,
        location=location,
        property_type=property_type,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        parking=parking,
        status=status,
        photos=photos or [],
        agency_id=agency_id,
        current_user=current_user,
    )


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
