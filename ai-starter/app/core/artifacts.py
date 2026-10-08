from __future__ import annotations

import base64
import mimetypes
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException

from app.core.config import get_settings


def save_bytes(
    data: bytes, *, prefix: str, content_type: Optional[str], extension: Optional[str] = None
) -> Tuple[str, Path]:
    settings = get_settings()
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    guessed_extension = extension or mimetypes.guess_extension((content_type or "").split(";")[0]) or ".bin"
    if guessed_extension == ".jpe":
        guessed_extension = ".jpg"
    filename = f"{prefix}_{uuid.uuid4().hex}{guessed_extension}"
    path = settings.artifact_dir / filename
    path.write_bytes(data)
    return filename, path


def save_base64(data: str, *, prefix: str, content_type: Optional[str] = None) -> Tuple[str, Path]:
    """Accept plain base64 or a data URL emitted by multimodal chat."""

    raw = data
    detected_type = content_type
    if data.startswith("data:"):
        header, raw = data.split(",", 1)
        detected_type = header.split(";", 1)[0].removeprefix("data:")
    try:
        decoded = base64.b64decode(raw, validate=True)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Gateway returned invalid base64 media") from exc
    return save_bytes(decoded, prefix=prefix, content_type=detected_type)


def artifact_path(filename: str) -> Path:
    """Avoid path traversal before passing a file to FastAPI."""

    candidate = (get_settings().artifact_dir / filename).resolve()
    root = get_settings().artifact_dir.resolve()
    if root not in candidate.parents or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return candidate
