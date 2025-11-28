from typing import List, Optional

from models.agency import Agency
from repositories.base import BaseRepository


class AgencyRepository(BaseRepository):
    def get(self, agency_id: int) -> Optional[Agency]:
        return self.db.query(Agency).filter(Agency.id == agency_id).first()

    def get_by_name(self, name: str) -> Optional[Agency]:
        return self.db.query(Agency).filter(Agency.name == name).first()

    def list(self) -> List[Agency]:
        return self.db.query(Agency).all()

    def create(self, agency: Agency) -> Agency:
        self.db.add(agency)
        self.db.commit()
        self.db.refresh(agency)
        return agency
