from typing import List, Optional

from models.property import Property
from repositories.base import BaseRepository


class PropertyRepository(BaseRepository):
    def get(self, property_id: int, agency_id: Optional[int]) -> Optional[Property]:
        query = self.db.query(Property).filter(Property.id == property_id)
        if agency_id is not None:
            query = query.filter(Property.agency_id == agency_id)
        return query.first()

    def list(self, agency_id: Optional[int]) -> List[Property]:
        query = self.db.query(Property)
        if agency_id is not None:
            query = query.filter(Property.agency_id == agency_id)
        return query.order_by(Property.created_at.desc()).all()

    def create(self, property_obj: Property) -> Property:
        self.db.add(property_obj)
        self.db.commit()
        self.db.refresh(property_obj)
        return property_obj

    def update(self, property_obj: Property, **kwargs) -> Property:
        for field, value in kwargs.items():
            setattr(property_obj, field, value)
        self.db.commit()
        self.db.refresh(property_obj)
        return property_obj

    def delete(self, property_obj: Property) -> None:
        self.db.delete(property_obj)
        self.db.commit()
