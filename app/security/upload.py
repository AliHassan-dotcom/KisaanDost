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


# Match only simple filenames; reject any directory separators or control chars.
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def sanitize_filename(name: str) -> str:
    """Return a safe, random filename with the original extension preserved."""
    name = Path(name).name  # strip any path components
    if not name or not _SAFE_NAME_RE.match(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )
    suffix = Path(name).suffix.lower()
    if suffix not in settings.upload_allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file extension.",
        )
    return f"{uuid.uuid4().hex}{suffix}"


def _content_type_matches(file: UploadFile) -> bool:
    content_type = (file.content_type or "").lower()
    return content_type in settings.upload_allowed_types


def validate_upload(file: UploadFile) -> Tuple[Path, str]:
    """Validate an uploaded image and return a safe target path + original name."""
    if file.filename is None or file.content_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing upload metadata.",
        )

    if not _content_type_matches(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only JPEG and PNG images are allowed.",
        )

    original_name = file.filename
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
