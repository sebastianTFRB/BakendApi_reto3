from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class PropertyRepository(BaseRepository):
    def get(self, property_id: int, agency_id: Optional[int]) -> Optional[Dict[str, Any]]:
        query = self.supabase.table("properties").select("*").eq("id", property_id)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        resp = query.execute()
        return resp.data[0] if resp.data else None

    def list(self, agency_id: Optional[int]) -> List[Dict[str, Any]]:
        query = self.supabase.table("properties").select("*").order("created_at", desc=True)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        resp = query.execute()
        return resp.data or []

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("properties").insert(payload).execute()
        return resp.data[0]

    def update(self, property_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("properties").update(payload).eq("id", property_id).execute()
        return resp.data[0]

    def delete(self, property_id: int) -> None:
        self.supabase.table("properties").delete().eq("id", property_id).execute()
