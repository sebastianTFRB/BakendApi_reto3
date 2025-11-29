from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from core.domain import UserRole
from core.security import get_current_user, require_roles
from schemas.post import PostRead
from services.post_service import PostService

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("/", response_model=PostRead, status_code=status.HTTP_201_CREATED)
def create_post(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    photos: Optional[List[UploadFile]] = File(None),
    videos: Optional[List[UploadFile]] = File(None),
    current_user=Depends(require_roles(UserRole.agency_admin, UserRole.superadmin)),
):
    service = PostService()
    company_id = current_user.get("agency_id")
    return service.create_post(title, description, photos or [], videos or [], company_id)


@router.get("/{post_id}", response_model=PostRead)
def get_post(post_id: UUID, current_user=Depends(get_current_user)):
    service = PostService()
    return service.get_post(str(post_id))


@router.get("/", response_model=List[PostRead])
def list_posts(offset: int = 0, limit: int = 20, current_user=Depends(get_current_user)):
    service = PostService()
    return service.list_posts(offset, limit)


@router.put("/{post_id}", response_model=PostRead)
def update_post(
    post_id: UUID,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    photos: Optional[List[UploadFile]] = File(None),
    videos: Optional[List[UploadFile]] = File(None),
    current_user=Depends(require_roles(UserRole.agency_admin, UserRole.superadmin)),
):
    service = PostService()
    company_id = current_user.get("agency_id")
    metadata = {"title": title, "description": description}
    return service.update_post(str(post_id), metadata, photos or [], videos or [], company_id)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: UUID, current_user=Depends(require_roles(UserRole.agency_admin, UserRole.superadmin))):
    service = PostService()
    company_id = current_user.get("agency_id")
    service.delete_post(str(post_id), company_id)
    return None
