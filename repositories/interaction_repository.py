from typing import Any, Dict, List

from repositories.base import BaseRepository


class LeadInteractionRepository(BaseRepository):
    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("lead_interactions").insert(payload).execute()
        return resp.data[0]

    def list_by_lead(self, lead_id: int) -> List[Dict[str, Any]]:
        resp = (
            self.supabase.table("lead_interactions")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
