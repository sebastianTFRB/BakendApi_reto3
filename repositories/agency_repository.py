from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class AgencyRepository(BaseRepository):
    def get(self, agency_id: int) -> Optional[Dict[str, Any]]:
        resp = self.supabase.table("agencies").select("*").eq("id", agency_id).execute()
        return resp.data[0] if resp.data else None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        resp = self.supabase.table("agencies").select("*").eq("name", name).execute()
        return resp.data[0] if resp.data else None

    def list(self) -> List[Dict[str, Any]]:
        resp = self.supabase.table("agencies").select("*").execute()
        return resp.data or []

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("agencies").insert(payload).execute()
        return resp.data[0]
