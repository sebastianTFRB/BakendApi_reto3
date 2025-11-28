from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.property import Property
from repositories.property_repository import PropertyRepository
from schemas.property import PropertyCreate, PropertyUpdate


class PropertyService:
    def __init__(self, db: Session):
        self.db = db
        self.property_repo = PropertyRepository(db)

    def _resolve_agency(self, requested_agency_id: Optional[int], current_user) -> int:
        if getattr(current_user, "is_superuser", False) and requested_agency_id:
            return requested_agency_id
        agency_id = requested_agency_id or getattr(current_user, "agency_id", None)
        if not agency_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency is required")
        return agency_id

    def _agency_scope(self, current_user):
        return None if getattr(current_user, "is_superuser", False) else getattr(current_user, "agency_id", None)

    def create_property(self, property_in: PropertyCreate, current_user) -> Property:
        agency_id = self._resolve_agency(property_in.agency_id, current_user)
        property_obj = Property(
            agency_id=agency_id,
            title=property_in.title,
            description=property_in.description,
            price=property_in.price,
            area=property_in.area,
            location=property_in.location,
            bedrooms=property_in.bedrooms,
            bathrooms=property_in.bathrooms,
            status=property_in.status,
        )
        return self.property_repo.create(property_obj)

    def list_properties(self, current_user):
        return self.property_repo.list(self._agency_scope(current_user))

    def get_property(self, property_id: int, current_user):
        prop = self.property_repo.get(property_id, self._agency_scope(current_user))
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        return prop

    def update_property(self, property_id: int, property_in: PropertyUpdate, current_user):
        prop = self.property_repo.get(property_id, self._agency_scope(current_user))
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        updates = property_in.dict(exclude_unset=True)
        for field, value in updates.items():
            setattr(prop, field, value)
        self.db.commit()
        self.db.refresh(prop)
        return prop

    def delete_property(self, property_id: int, current_user):
        agency_id = getattr(current_user, "agency_id", None)
        prop = self.property_repo.get(property_id, agency_id)
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        self.property_repo.delete(prop)
