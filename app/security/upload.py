"""Safe file upload validation and storage helpers.

Protects against path traversal, oversized files, and unexpected content types.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, UploadFile, status

from app.config import settings


# Match valid image extensions
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def sanitize_filename(name: str) -> str:
    """Return a safe, random filename with the original extension preserved."""
    raw_name = Path(name).name.strip()  # strip any path components
    suffix = Path(raw_name).suffix.lower() if raw_name else ""
    if not suffix or suffix not in settings.upload_allowed_extensions:
        suffix = ".jpg"
    return f"{uuid.uuid4().hex}{suffix}"


def _content_type_matches(file: UploadFile) -> bool:
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if not content_type:
        return True
    if content_type in settings.upload_allowed_types:
        return True
    if content_type.startswith("image/"):
        return True
    if content_type == "application/octet-stream":
        return True
    return False


def validate_upload(file: UploadFile) -> Tuple[Path, str]:
    """Validate an uploaded image and return a safe target path + original name."""
    original_name = file.filename or "leaf_scan.jpg"

    if not _content_type_matches(file):
        # Fallback to extension check
        suffix = Path(original_name).suffix.lower()
        if suffix not in settings.upload_allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Only JPEG, PNG, and WebP images are allowed.",
            )

    safe_name = sanitize_filename(original_name)
    target_path = settings.uploads_dir() / safe_name

    # Resolve the target to catch path traversal attempts (e.g., ../../etc/passwd).
    try:
        resolved = target_path.resolve()
        resolved.relative_to(settings.uploads_dir().resolve())
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload path.",
        ) from exc

    return resolved, original_name


def save_upload(file: UploadFile, max_bytes: int = settings.upload_max_bytes) -> Tuple[Path, str]:
    """Validate, save, and return the stored file path + original filename."""
    target_path, original_name = validate_upload(file)

    # Stream to disk while enforcing size limit.
    size = 0
    try:
        with open(target_path, "wb") as fh:
            while True:
                chunk = file.file.read(8192)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size is {settings.upload_max_bytes} bytes.",
                    )
                fh.write(chunk)
    finally:
        file.file.close()

    return target_path, original_name
