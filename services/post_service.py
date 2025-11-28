from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from core.config import settings
from db.supabase_client import get_supabase_client
from repositories.post_repository import PostRepository
from utils.media import generate_object_path, validate_media


class PostService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.repo = PostRepository(self.supabase)
        self.bucket = settings.supabase_bucket

    def _upload_files(self, company_id: int, files: List[UploadFile]) -> List[str]:
        urls: List[str] = []
        storage = self.supabase.storage.from_(self.bucket)
        for upload in files:
            object_path = generate_object_path(company_id, upload.filename or "file")
            file_bytes = upload.file.read()
            upload.file.seek(0)
            res = storage.upload(object_path, file_bytes, {"content-type": upload.content_type or "application/octet-stream"})
            if res is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload media")
            public_url_resp = storage.get_public_url(object_path)
            if isinstance(public_url_resp, dict):
                url = public_url_resp.get("publicUrl") or public_url_resp.get("public_url")
            else:
                url = str(public_url_resp)
            if not url:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to obtain media URL")
            urls.append(url)
        return urls

    def _authorize(self, post: Dict[str, Any], company_id: int):
        if post.get("company_id") != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to modify this post")

    def create_post(self, title: str, description: Optional[str], photos: List[UploadFile], videos: List[UploadFile], company_id: int) -> Dict[str, Any]:
        if not company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company is required to create posts")
        validate_media(photos, videos)
        photo_urls = self._upload_files(company_id, photos)
        video_urls = self._upload_files(company_id, videos) if videos else []
        payload = {
            "title": title,
            "description": description,
            "photos": photo_urls,
            "videos": video_urls,
            "company_id": company_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        return self.repo.create(payload)

    def get_post(self, post_id: Union[str, UUID]) -> Dict[str, Any]:
        post = self.repo.get(post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        return post

    def list_posts(self, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        return self.repo.list(offset, limit)

    def update_post(self, post_id: Union[str, UUID], metadata: Dict[str, Optional[str]], photos: List[UploadFile], videos: List[UploadFile], company_id: int) -> Dict[str, Any]:
        if not company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company is required to update posts")
        existing = self.get_post(post_id)
        self._authorize(existing, company_id)
        validate_media(photos, videos)
        updates: Dict[str, any] = {}
        if metadata.get("title") is not None:
            updates["title"] = metadata["title"]
        if metadata.get("description") is not None:
            updates["description"] = metadata["description"]
        photo_urls: List[str] = existing.get("photos", [])
        video_urls: List[str] = existing.get("videos", [])
        if photos:
            photo_urls += self._upload_files(company_id, photos)
            updates["photos"] = photo_urls
        if videos:
            video_urls += self._upload_files(company_id, videos)
            updates["videos"] = video_urls
        updates["updated_at"] = datetime.utcnow().isoformat()
        return self.repo.update(post_id, updates)

    def delete_post(self, post_id: Union[str, UUID], company_id: int) -> None:
        if not company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company is required to delete posts")
        existing = self.get_post(post_id)
        self._authorize(existing, company_id)
        self.repo.delete(post_id)
