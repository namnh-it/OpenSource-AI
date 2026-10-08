from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.routes import router
from app.core.artifacts import artifact_path
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(
    title="AI Thuc Chien Starter",
    version="0.2.0",
    description="Reusable, guarded endpoints for the AI Thuc Chien Gateway.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health", tags=["system"])
async def root_health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/artifacts/{filename}", include_in_schema=False)
async def get_artifact(filename: str) -> FileResponse:
    return FileResponse(artifact_path(filename))
