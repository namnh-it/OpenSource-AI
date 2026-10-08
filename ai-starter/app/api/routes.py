from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.agents.runner import AgentRunner
from app.core.artifacts import artifact_path, save_base64, save_bytes
from app.core.config import get_settings
from app.core.gateway import GatewayClient
from app.schemas import (
    AgentRunRequest,
    EmbeddingRequest,
    ImageRequest,
    ModerationRequest,
    SpeechRequest,
    TextRequest,
    VideoRequest,
)

router = APIRouter(prefix="/api/ai", tags=["AI Gateway"])


def client() -> GatewayClient:
    return GatewayClient()


@router.get("/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "gateway_url": settings.aitc_base_url,
        "key_configured": bool(settings.aitc_api_key),
        "dry_run": settings.ai_dry_run,
    }


@router.post("/text")
async def generate_text(request: TextRequest) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": request.model or get_settings().ai_text_model,
        "messages": request.as_messages(),
    }
    if request.temperature is not None:
        payload["temperature"] = request.temperature
    if request.max_completion_tokens is not None:
        payload["max_completion_tokens"] = request.max_completion_tokens
    if request.reasoning_effort:
        payload["reasoning_effort"] = request.reasoning_effort
    if request.thinking_enabled is False:
        # DeepSeek's SDK extra_body is serialized at the top level by this raw client.
        payload["thinking"] = {"type": "disabled"}
    if request.web_grounding:
        payload["tools"] = [{"googleSearch": {}}]
    response = await client().chat(payload)
    choice = (response.get("choices") or [{}])[0]
    return {
        "text": choice.get("message", {}).get("content", ""),
        "model": response.get("model", payload["model"]),
        "raw": response,
    }


@router.post("/agent/runs")
async def run_agent(request: AgentRunRequest) -> dict[str, Any]:
    """Run a short, auditable tool loop. Media generation must be explicitly allowed."""
    return await AgentRunner(client()).run(request)


@router.post("/images")
async def generate_image(request: ImageRequest) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": request.model or get_settings().ai_image_model,
        "prompt": request.prompt,
        "n": 1,
    }
    if request.aspect_ratio:
        # The OpenAI SDK merges extra_body into JSON; this raw client must send it directly.
        payload["aspect_ratio"] = request.aspect_ratio
    if request.size:
        payload["size"] = request.size
    if request.quality:
        payload["quality"] = request.quality
    response = await client().image(payload)
    image = (response.get("data") or [{}])[0]
    if image.get("b64_json"):
        filename, _ = save_base64(image["b64_json"], prefix="image", content_type="image/png")
        return {
            "artifact_url": f"/artifacts/{filename}",
            "revised_prompt": image.get("revised_prompt"),
            "model": payload["model"],
        }
    if image.get("url"):
        return {
            "source_url": image["url"],
            "revised_prompt": image.get("revised_prompt"),
            "model": payload["model"],
        }
    raise HTTPException(status_code=502, detail="Gateway image response has neither b64_json nor url")


@router.post("/videos")
async def create_video(request: VideoRequest) -> dict[str, Any]:
    settings = get_settings()
    if request.seconds > settings.ai_max_video_seconds:
        raise HTTPException(
            status_code=422, detail=f"seconds exceeds AI_MAX_VIDEO_SECONDS ({settings.ai_max_video_seconds})"
        )
    payload = {
        "model": request.model or settings.ai_video_model,
        "prompt": request.prompt,
        "seconds": request.seconds,
        "size": request.size,
    }
    return await client().video_create(payload)


@router.get("/videos/{video_id}")
async def get_video_status(video_id: str) -> dict[str, Any]:
    return await client().video_status(video_id)


@router.post("/videos/{video_id}/download")
async def download_video(video_id: str) -> dict[str, str]:
    status = await client().video_status(video_id)
    if status.get("status") != "completed":
        raise HTTPException(
            status_code=409, detail={"message": "Video is not completed", "status": status.get("status")}
        )
    data, content_type = await client().video_content(video_id)
    filename, _ = save_bytes(data, prefix="video", content_type=content_type, extension=".mp4")
    return {"artifact_url": f"/artifacts/{filename}"}


@router.post("/audio/speech")
async def create_speech(request: SpeechRequest) -> dict[str, str]:
    payload = request.model_dump(exclude_none=True)
    payload["model"] = request.model or get_settings().ai_tts_model
    data, content_type = await client().speech(payload)
    filename, _ = save_bytes(data, prefix="speech", content_type=content_type, extension=".mp3")
    return {"artifact_url": f"/artifacts/{filename}"}


@router.post("/audio/transcriptions")
async def transcribe_audio(file: UploadFile = File(...), model: Optional[str] = None) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Empty audio file")
    selected_model = model or get_settings().ai_stt_model
    return await client().transcription(
        model=selected_model,
        filename=file.filename or "audio.bin",
        content=content,
        content_type=file.content_type,
    )


@router.post("/embeddings")
async def create_embeddings(request: EmbeddingRequest) -> dict[str, Any]:
    payload = request.model_dump(exclude_none=True)
    payload["model"] = request.model or get_settings().ai_embedding_model
    return await client().embeddings(payload)


@router.post("/moderations")
async def moderate(request: ModerationRequest) -> dict[str, Any]:
    return await client().moderation(request.model_dump())


@router.get("/artifacts/{filename}", include_in_schema=False)
async def get_artifact(filename: str) -> FileResponse:
    path: Path = artifact_path(filename)
    return FileResponse(path)
