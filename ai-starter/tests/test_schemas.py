import pytest
from pydantic import ValidationError

from app.schemas import TextRequest, VideoRequest


def test_text_request_turns_prompt_into_message() -> None:
    assert TextRequest(prompt="Xin chao").as_messages() == [{"role": "user", "content": "Xin chao"}]


def test_text_request_accepts_reasoning_controls() -> None:
    request = TextRequest(prompt="Kiem tra", reasoning_effort="low", thinking_enabled=False)
    assert request.reasoning_effort == "low"
    assert request.thinking_enabled is False


def test_text_request_requires_input() -> None:
    with pytest.raises(ValidationError):
        TextRequest()


def test_video_request_keeps_low_cost_default() -> None:
    assert VideoRequest(prompt="Mo ta").seconds == 4


def test_video_refuses_out_of_range_duration() -> None:
    with pytest.raises(ValidationError):
        VideoRequest(prompt="Mo ta", seconds=9)
