from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import HTTPException, status
from supabase import Client


class PostRepository:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = self.supabase.table("posts")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.table.insert(payload).execute()
        if response.error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error.message)
        return response.data[0]

    def get(self, post_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        response = self.table.select("*").eq("id", str(post_id)).execute()
        if response.error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error.message)
        return response.data[0] if response.data else None

    def list(self, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        response = self.table.select("*").range(offset, offset + limit - 1).order("created_at", desc=True).execute()
        if response.error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error.message)
        return response.data

    def update(self, post_id: Union[str, UUID], payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.table.update(payload).eq("id", str(post_id)).execute()
        if response.error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error.message)
        return response.data[0]

    def delete(self, post_id: Union[str, UUID]) -> None:
        response = self.table.delete().eq("id", str(post_id)).execute()
        if response.error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error.message)
        return None
