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

    def list_filtered(
        self,
        *,
        agency_id: Optional[int] = None,
        user_id: Optional[int] = None,
        lead_ids: Optional[List[int]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = self.supabase.table("leads").select("*").order("created_at", desc=True)
        if lead_ids is not None:
            if not lead_ids:
                return []
            query = query.in_("id", lead_ids)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        if from_date:
            query = query.gte("created_at", from_date)
        if to_date:
            query = query.lte("created_at", to_date)
        resp = query.execute()
        return resp.data or []

    def find_by_phone(self, phone: str, agency_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        query = self.supabase.table("leads").select("*").eq("phone", phone)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        resp = query.limit(1).execute()
        return resp.data[0] if resp.data else None

    def find_by_email(self, email: str, agency_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        query = self.supabase.table("leads").select("*").eq("email", email)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        resp = query.limit(1).execute()
        return resp.data[0] if resp.data else None

    def find_by_user(self, user_id: int, agency_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        query = self.supabase.table("leads").select("*").eq("user_id", user_id)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        resp = query.limit(1).execute()
        return resp.data[0] if resp.data else None

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("leads").insert(payload).execute()
        return resp.data[0]

    def update(self, lead_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("leads").update(payload).eq("id", lead_id).execute()
        return resp.data[0]

    def delete(self, lead_id: int) -> None:
        self.supabase.table("leads").delete().eq("id", lead_id).execute()
