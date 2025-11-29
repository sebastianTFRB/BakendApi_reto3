from typing import Optional

from fastapi import HTTPException, status

from core.domain import UserRole
from core.security import resolve_role
from db.supabase_client import get_supabase_client
from repositories.property_repository import PropertyRepository
from schemas.property import PropertyCreate, PropertyUpdate


class PropertyService:
    def __init__(self):
        supabase = get_supabase_client()
        self.property_repo = PropertyRepository(supabase)

    def _is_superadmin(self, current_user) -> bool:
        return resolve_role(current_user) == UserRole.superadmin.value

    def _resolve_agency(self, requested_agency_id: Optional[int], current_user) -> int:
        if self._is_superadmin(current_user) and requested_agency_id:
            return requested_agency_id
        agency_id = requested_agency_id or current_user.get("agency_id")
        if not agency_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency is required")
        return agency_id

    def _agency_scope(self, current_user):
        return None if self._is_superadmin(current_user) else current_user.get("agency_id")

    def create_property(self, property_in: PropertyCreate, current_user) -> dict:
        agency_id = self._resolve_agency(property_in.agency_id, current_user)
        payload = {
            "agency_id": agency_id,
            "title": property_in.title,
            "description": property_in.description,
            "price": property_in.price,
            "area": property_in.area,
            "location": property_in.location,
            "bedrooms": property_in.bedrooms,
            "bathrooms": property_in.bathrooms,
            "status": property_in.status,
        }
        return self.property_repo.create(payload)

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
        return self.property_repo.update(property_id, updates)

    def delete_property(self, property_id: int, current_user):
        prop = self.property_repo.get(property_id, self._agency_scope(current_user))
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        self.property_repo.delete(property_id)
