from typing import Any, Dict, List, Optional

from repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.supabase.table("users").insert(payload).execute()
        return resp.data[0]

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        resp = self.supabase.table("users").select("*").eq("email", email).execute()
        return resp.data[0] if resp.data else None

    def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        resp = self.supabase.table("users").select("*").eq("id", user_id).execute()
        return resp.data[0] if resp.data else None

    def list(self) -> List[Dict[str, Any]]:
        resp = self.supabase.table("users").select("*").execute()
        return resp.data or []
