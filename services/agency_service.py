from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.agency import Agency
from repositories.agency_repository import AgencyRepository
from schemas.agency import AgencyCreate


class AgencyService:
    def __init__(self, db: Session):
        self.db = db
        self.agency_repo = AgencyRepository(db)

    def create_agency(self, agency_in: AgencyCreate) -> Agency:
        existing = self.agency_repo.get_by_name(agency_in.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency already exists")
        agency = Agency(name=agency_in.name, domain=agency_in.domain)
        return self.agency_repo.create(agency)

    def list_agencies(self):
        return self.agency_repo.list()

    def get_agency(self, agency_id: int) -> Agency:
        agency = self.agency_repo.get(agency_id)
        if not agency:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
        return agency
