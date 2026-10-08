from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings. Secrets are loaded only from environment/.env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    aitc_api_key: str = Field(default="", repr=False)
    aitc_base_url: str = "https://api.thucchien.ai"

    ai_text_model: str = "gpt-6-luna"
    ai_image_model: str = "nano-banana-2-lite"
    ai_video_model: str = "veo-3.1-lite-generate-001"
    ai_tts_model: str = "gemini-2.5-flash-preview-tts"
    ai_stt_model: str = "gemini-3.5-transcribe-preview"
    ai_embedding_model: str = "text-multilingual-embedding-002"

    ai_timeout_seconds: float = 90
    ai_max_retries: int = 2
    ai_max_video_seconds: int = 8
    ai_dry_run: bool = False
    ai_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @field_validator("aitc_base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def artifact_dir(self) -> Path:
        return PROJECT_ROOT / "runtime" / "artifacts"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ai_cors_origins.split(",") if origin.strip()]

    @property
    def audit_log_path(self) -> Path:
        return PROJECT_ROOT / "runtime" / "audit.jsonl"


@lru_cache
def get_settings() -> Settings:
    return Settings()
