from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class PropertyRepository(BaseRepository):
    def list(self, agency_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Simple list helper used by scoring routines.
        """
        query = self.supabase.table("properties").select("*").order("created_at", desc=True)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        resp = query.execute()
        return resp.data or []

    def get(self, property_id: int, agency_id: Optional[int]) -> Optional[Dict[str, Any]]:
        query = self.supabase.table("properties").select("*").eq("id", property_id)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        resp = query.execute()
        return resp.data[0] if resp.data else None

    def list_filtered(
        self,
        agency_id: Optional[int] = None,
        location: Optional[str] = None,
        property_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[int] = None,
        parking: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        query = self.supabase.table("properties").select("*").order("created_at", desc=True)
        if agency_id is not None:
            query = query.eq("agency_id", agency_id)
        if location:
            query = query.ilike("location", f"%{location}%")
        if property_type:
            query = query.eq("property_type", property_type)
        if min_price is not None:
            query = query.gte("price", min_price)
        if max_price is not None:
            query = query.lte("price", max_price)
        if bedrooms:
            query = query.gte("bedrooms", bedrooms)
        if bathrooms:
            query = query.gte("bathrooms", bathrooms)
        if parking is not None:
            query = query.eq("parking", parking)
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
