from __future__ import annotations

import asyncio
from typing import Any, Optional, Tuple

import httpx
from fastapi import HTTPException

from app.core.audit import write_audit_event
from app.core.config import Settings, get_settings


class GatewayClient:
    """Small resilient client for the OpenAI-compatible AI Thuc Chien Gateway."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def _assert_ready(self) -> None:
        if self.settings.ai_dry_run:
            raise HTTPException(
                status_code=503, detail="AI_DRY_RUN=true: outbound Gateway calls are disabled"
            )
        if not self.settings.aitc_api_key:
            raise HTTPException(
                status_code=503, detail="Missing AITC_API_KEY. Add it to .env before calling Gateway."
            )

    async def request(
        self,
        method: str,
        path: str,
        *,
        model: Optional[str] = None,
        json: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        self._assert_ready()
        headers = {"Authorization": f"Bearer {self.settings.aitc_api_key}"}
        timeout = httpx.Timeout(self.settings.ai_timeout_seconds, connect=15)
        retryable_codes = {429, 500, 502, 503, 504}
        last_error: Optional[Exception] = None

        async with httpx.AsyncClient(base_url=self.settings.aitc_base_url, timeout=timeout) as client:
            for attempt in range(self.settings.ai_max_retries + 1):
                try:
                    response = await client.request(method, path, headers=headers, json=json, files=files)
                    write_audit_event(
                        endpoint=path,
                        model=model,
                        status_code=response.status_code,
                        headers=response.headers,
                        attempt=attempt + 1,
                    )
                    if response.status_code not in retryable_codes or attempt == self.settings.ai_max_retries:
                        self._raise_for_gateway_error(response)
                        return response
                    await asyncio.sleep(min(2**attempt, 4))
                except httpx.RequestError as exc:
                    last_error = exc
                    if attempt == self.settings.ai_max_retries:
                        break
                    await asyncio.sleep(min(2**attempt, 4))

        raise HTTPException(status_code=502, detail=f"Could not reach AI Gateway: {last_error}")

    @staticmethod
    def _raise_for_gateway_error(response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            body = response.json()
            detail = body.get("error", body)
        except ValueError:
            detail = response.text[:500] or "Unknown Gateway error"
        raise HTTPException(status_code=response.status_code, detail={"gateway": detail})

    async def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.request("POST", "/chat/completions", model=payload.get("model"), json=payload)
        return response.json()

    async def image(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.request("POST", "/images/generations", model=payload.get("model"), json=payload)
        return response.json()

    async def video_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.request("POST", "/v1/videos", model=payload.get("model"), json=payload)
        return response.json()

    async def video_status(self, video_id: str) -> dict[str, Any]:
        response = await self.request("GET", f"/v1/videos/{video_id}")
        return response.json()

    async def video_content(self, video_id: str) -> Tuple[bytes, Optional[str]]:
        response = await self.request("GET", f"/v1/videos/{video_id}/content")
        return response.content, response.headers.get("content-type")

    async def speech(self, payload: dict[str, Any]) -> Tuple[bytes, Optional[str]]:
        response = await self.request("POST", "/audio/speech", model=payload.get("model"), json=payload)
        return response.content, response.headers.get("content-type")

    async def transcription(
        self, *, model: str, filename: str, content: bytes, content_type: Optional[str]
    ) -> dict[str, Any]:
        files = {
            "model": (None, model),
            "file": (filename, content, content_type or "application/octet-stream"),
        }
        response = await self.request("POST", "/audio/transcriptions", model=model, files=files)
        return response.json()

    async def embeddings(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.request("POST", "/embeddings", model=payload.get("model"), json=payload)
        return response.json()

    async def moderation(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.request("POST", "/moderations", model=payload.get("model"), json=payload)
        return response.json()
