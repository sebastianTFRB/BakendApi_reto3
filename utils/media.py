import imghdr
import os
from typing import Iterable, Tuple
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

IMAGE_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
VIDEO_MAX_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_IMAGE_TYPES = {"jpeg", "png", "gif", "webp"}
ALLOWED_VIDEO_TYPES = {"mp4", "mov", "mkv", "avi", "webm"}


def _validate_file_size(upload: UploadFile, max_bytes: int):
    content = upload.file.read()
    size = len(content)
    if size > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File {upload.filename} exceeds size limit")
    upload.file.seek(0)
    return size


def _validate_image_type(upload: UploadFile):
    content = upload.file.read(512)
    upload.file.seek(0)
    kind = imghdr.what(None, content)
    if kind not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported image type for {upload.filename}")


def _validate_video_type(upload: UploadFile):
    ext = os.path.splitext(upload.filename or "")[1].lower().replace(".", "")
    if ext not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported video type for {upload.filename}")


def validate_media(images: Iterable[UploadFile], videos: Iterable[UploadFile]):
    for img in images:
        _validate_file_size(img, IMAGE_MAX_BYTES)
        _validate_image_type(img)
    for vid in videos:
        _validate_file_size(vid, VIDEO_MAX_BYTES)
        _validate_video_type(vid)


def generate_object_path(company_id: int, filename: str) -> str:
    ext = os.path.splitext(filename)[1]
    return f"{company_id}/{uuid4().hex}{ext}"
