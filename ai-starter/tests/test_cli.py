from pathlib import Path

import pytest

from app.cli import build_review_prompt, read_review_file


def test_review_prompt_is_focused() -> None:
    prompt = build_review_prompt(
        mode="review", path=Path("sample.py"), content="print('ok')", context="must not crash"
    )
    assert "at most 5 findings" in prompt
    assert "Do not rewrite the whole file" in prompt


def test_review_refuses_env_file(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("AITC_API_KEY=secret", encoding="utf-8")
    with pytest.raises(ValueError, match="secret file"):
        read_review_file(str(path), 1_000)
