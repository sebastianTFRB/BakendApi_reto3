from typing import Any, Dict, List, Optional

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

    def list_filtered(
        self,
        *,
        lead_ids: Optional[List[int]] = None,
        channel: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = self.supabase.table("lead_interactions").select("*").order("created_at", desc=True)
        if lead_ids is not None:
            if not lead_ids:
                return []
            query = query.in_("lead_id", lead_ids)
        if channel:
            query = query.eq("channel", channel)
        if from_date:
            query = query.gte("created_at", from_date)
        if to_date:
            query = query.lte("created_at", to_date)
        resp = query.execute()
        return resp.data or []
