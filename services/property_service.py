from typing import Optional, List

from fastapi import HTTPException, status, UploadFile

from core.domain import UserRole
from core.security import resolve_role
from db.supabase_client import get_supabase_client
from repositories.property_repository import PropertyRepository
from schemas.property import PropertyCreate, PropertyUpdate
from core.config import settings
from utils.media import generate_object_path, validate_media
from services.social_publisher import SocialPublisher


class PropertyService:
    def __init__(self):
        supabase = get_supabase_client()
        self.property_repo = PropertyRepository(supabase)
        self.supabase = supabase
        self.bucket = settings.supabase_bucket
        self.publisher = SocialPublisher()

    def _is_superadmin(self, current_user) -> bool:
        return resolve_role(current_user) == UserRole.superadmin.value

    def _resolve_agency(self, requested_agency_id: Optional[int], current_user) -> int:
        if self._is_superadmin(current_user) and requested_agency_id:
            return requested_agency_id
        agency_id = requested_agency_id or current_user.get("agency_id")
        if not agency_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency is required")
        return agency_id

    def _agency_scope(self, current_user):
        return None if self._is_superadmin(current_user) else current_user.get("agency_id")

    def _ensure_agency_role(self, current_user):
        role = resolve_role(current_user)
        if role not in {UserRole.agency_admin.value, UserRole.superadmin.value}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo agencias pueden gestionar propiedades")

    def _upload_photos(self, agency_id: int, photos: List[UploadFile]) -> List[str]:
        if not photos:
            return []
        validate_media(photos, [])
        urls: List[str] = []
        storage = self.supabase.storage.from_(self.bucket)
        for upload in photos:
            object_path = generate_object_path(agency_id, upload.filename or "photo")
            file_bytes = upload.file.read()
            upload.file.seek(0)
            res = storage.upload(object_path, file_bytes, {"content-type": upload.content_type or "application/octet-stream"})
            if res is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo subir la imagen")
            public_url_resp = storage.get_public_url(object_path)
            url = public_url_resp.get("publicUrl") if isinstance(public_url_resp, dict) else str(public_url_resp)
            if not url:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo obtener URL de imagen")
            urls.append(url)
        return urls

    def create_property(self, property_in: PropertyCreate, current_user) -> dict:
        self._ensure_agency_role(current_user)
        agency_id = self._resolve_agency(property_in.agency_id, current_user)
        payload = {
            "agency_id": agency_id,
            "title": property_in.title,
            "description": property_in.description,
            "price": property_in.price,
            "area": property_in.area,
            "location": property_in.location,
            "property_type": property_in.property_type,
            "bedrooms": property_in.bedrooms,
            "bathrooms": property_in.bathrooms,
            "parking": property_in.parking,
            "status": property_in.status,
            "photos": property_in.photos or [],
        }
        created = self.property_repo.create(payload)
        self.publisher.publish_property(created)
        return created

    def create_property_with_media(
        self,
        *,
        title: str,
        price: float,
        description: Optional[str],
        area: Optional[str],
        location: Optional[str],
        property_type: Optional[str],
        bedrooms: Optional[int],
        bathrooms: Optional[int],
        parking: Optional[bool],
        status: str,
        photos: List[UploadFile],
        current_user,
        agency_id: Optional[int] = None,
    ) -> dict:
        self._ensure_agency_role(current_user)
        resolved_agency = self._resolve_agency(agency_id, current_user)
        photo_urls = self._upload_photos(resolved_agency, photos or [])
        property_in = PropertyCreate(
            title=title,
            price=price,
            description=description,
            area=area,
            location=location,
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            parking=parking,
            status=status or "available",
            agency_id=resolved_agency,
            photos=photo_urls,
        )
        return self.create_property(property_in, current_user)

    def list_properties(
        self,
        current_user,
        *,
        location: str = "",
        property_type: str = "",
        min_price: float = 0,
        max_price: float = 0,
        bedrooms: int = 0,
        bathrooms: int = 0,
        parking: Optional[bool] = None,
    ):
        return self.property_repo.list_filtered(
            agency_id=self._agency_scope(current_user),
            location=location or None,
            property_type=property_type or None,
            min_price=min_price or None,
            max_price=max_price or None,
            bedrooms=bedrooms or None,
            bathrooms=bathrooms or None,
            parking=parking,
        )

    def get_property(self, property_id: int, current_user):
        prop = self.property_repo.get(property_id, self._agency_scope(current_user))
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        return prop

    def update_property(self, property_id: int, property_in: PropertyUpdate, current_user):
        self._ensure_agency_role(current_user)
        prop = self.property_repo.get(property_id, self._agency_scope(current_user))
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        updates = property_in.dict(exclude_unset=True)
        return self.property_repo.update(property_id, updates)

    def delete_property(self, property_id: int, current_user):
        self._ensure_agency_role(current_user)
        prop = self.property_repo.get(property_id, self._agency_scope(current_user))
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        self.property_repo.delete(property_id)
