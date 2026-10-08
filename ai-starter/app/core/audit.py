from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import get_settings


def write_audit_event(
    *, endpoint: str, model: Optional[str], status_code: int, headers: Any, attempt: int
) -> None:
    """Log operational metadata only; prompts, API key and generated data stay out."""

    settings = get_settings()
    settings.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "at": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "model": model,
        "status_code": status_code,
        "attempt": attempt,
        "request_id": headers.get("x-request-id") or headers.get("request-id"),
        "cost_usd": headers.get("x-litellm-response-cost"),
    }
    with settings.audit_log_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
