from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class TextRequest(BaseModel):
    prompt: Optional[str] = Field(default=None, min_length=1)
    messages: Optional[List[Message]] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_completion_tokens: Optional[int] = Field(default=None, ge=1, le=32_000)
    reasoning_effort: Optional[Literal["none", "low", "medium", "high", "xhigh", "max"]] = None
    thinking_enabled: Optional[bool] = None
    web_grounding: bool = False

    @model_validator(mode="after")
    def validate_input(self) -> TextRequest:
        if not self.messages and not self.prompt:
            raise ValueError("Provide prompt or messages")
        return self

    def as_messages(self) -> list[dict[str, str]]:
        if self.messages:
            return [message.model_dump() for message in self.messages]
        return [{"role": "user", "content": self.prompt or ""}]


class ImageRequest(BaseModel):
    prompt: str = Field(min_length=1)
    model: Optional[str] = None
    aspect_ratio: Optional[Literal["1:1", "3:4", "4:3", "16:9", "9:16"]] = None
    size: Optional[Literal["1024x1024", "1536x1024", "1024x1536"]] = None
    quality: Optional[Literal["low", "medium", "high"]] = None


class VideoRequest(BaseModel):
    prompt: str = Field(min_length=1)
    model: Optional[str] = None
    seconds: int = Field(default=4, ge=4, le=8)
    size: Literal["1280x720", "1920x1080"] = "1280x720"


class SpeechRequest(BaseModel):
    input: str = Field(min_length=1, max_length=10_000)
    voice: str = "Charon"
    model: Optional[str] = None


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: Optional[str] = None


class ModerationRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "omni-moderation-latest"


AgentToolName = Literal["create_checklist", "draft_text", "generate_image"]


class AgentRunRequest(BaseModel):
    """Bounded request for a small tool-using agent run."""

    goal: str = Field(min_length=3, max_length=4_000)
    context: Optional[str] = Field(default=None, max_length=12_000)
    model: Optional[str] = None
    allowed_tools: List[AgentToolName] = Field(default_factory=lambda: ["create_checklist", "draft_text"])
    max_steps: int = Field(default=2, ge=1, le=4)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_completion_tokens: int = Field(default=1_200, ge=64, le=4_000)
