from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class LeadRepository(BaseRepository):
    def get(self, lead_id: int, agency_id: Optional[int], user_id: Optional[int]) -> Optional[Dict[str, Any]]:
        query = self.supabase.table("leads").select("*").eq("id", lead_id)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        resp = query.execute()
        return resp.data[0] if resp.data else None

    def list(self, agency_id: Optional[int], user_id: Optional[int]) -> List[Dict[str, Any]]:
        query = self.supabase.table("leads").select("*").order("created_at", desc=True)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        resp = query.execute()
        return resp.data or []

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("leads").insert(payload).execute()
        return resp.data[0]

    def update(self, lead_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("leads").update(payload).eq("id", lead_id).execute()
        return resp.data[0]

    def delete(self, lead_id: int) -> None:
        self.supabase.table("leads").delete().eq("id", lead_id).execute()
