from fastapi import HTTPException, status

from db.supabase_client import get_supabase_client
from repositories.agency_repository import AgencyRepository
from schemas.agency import AgencyCreate


class AgencyService:
    def __init__(self):
        supabase = get_supabase_client()
        self.agency_repo = AgencyRepository(supabase)

    def create_agency(self, agency_in: AgencyCreate) -> dict:
        existing = self.agency_repo.get_by_name(agency_in.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency already exists")
        payload = {"name": agency_in.name, "domain": agency_in.domain}
        return self.agency_repo.create(payload)

    def list_agencies(self):
        return self.agency_repo.list()

    def get_agency(self, agency_id: int) -> dict:
        agency = self.agency_repo.get(agency_id)
        if not agency:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
        return agency
