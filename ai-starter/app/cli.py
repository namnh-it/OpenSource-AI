from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from app.agents.runner import AgentRunner
from app.core.config import get_settings
from app.core.gateway import GatewayClient
from app.schemas import AgentRunRequest

REVIEW_MODES = ("review", "debug")
SENSITIVE_FILENAMES = {".env", ".env.local", "id_rsa", "credentials.json", "service-account.json"}


def read_review_file(path_value: str, max_chars: int) -> tuple[Path, str]:
    path = Path(path_value).resolve()
    if not path.is_file():
        raise ValueError(f"Not a readable file: {path}")
    if path.name.lower() in SENSITIVE_FILENAMES or path.suffix.lower() in {".pem", ".key", ".pfx"}:
        raise ValueError("Refusing to send a likely secret file to an AI model")
    content = path.read_text(encoding="utf-8")
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[TRUNCATED: send a smaller, focused file or diff.]"
    return path, content


def build_review_prompt(*, mode: str, path: Path, content: str, context: str) -> str:
    action = (
        "Find the most likely root cause from the failure evidence, then give the smallest safe repair plan."
        if mode == "debug"
        else (
            "Find only defects that can affect correctness, security, reliability, "
            "or the stated acceptance path."
        )
    )
    return f"""You are a bounded senior engineer helping a 2-hour hackathon team.
{action}

Rules:
- Review only the supplied file and context; do not invent APIs, files, tests, or observed behavior.
- Do not request, infer, or repeat credentials. Do not rewrite the whole file.
- Return at most 5 findings, ranked P0-P3. For each: evidence with line number, impact,
  and one focused verification command/test.
- End with the smallest patch plan. If evidence is insufficient, say exactly what is missing.

Mode: {mode}
File: {path.name}
Context / failing test output:
{context or "(none supplied)"}

Source:
```text
{content}
```"""


def doctor() -> int:
    settings = get_settings()
    print(
        json.dumps(
            {
                "gateway": settings.aitc_base_url,
                "api_key_configured": bool(settings.aitc_api_key),
                "dry_run": settings.ai_dry_run,
                "models": {
                    "text": settings.ai_text_model,
                    "image": settings.ai_image_model,
                    "video": settings.ai_video_model,
                    "tts": settings.ai_tts_model,
                    "stt": settings.ai_stt_model,
                    "embedding": settings.ai_embedding_model,
                },
                "artifact_dir": str(settings.artifact_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


async def text(prompt: str, model: Optional[str]) -> int:
    settings = get_settings()
    response = await GatewayClient().chat(
        {
            "model": model or settings.ai_text_model,
            "messages": [{"role": "user", "content": prompt}],
        }
    )
    print((response.get("choices") or [{}])[0].get("message", {}).get("content", ""))
    return 0


async def review(
    *, path_value: str, mode: str, context: str, model: Optional[str], effort: str, max_chars: int
) -> int:
    path, content = read_review_file(path_value, max_chars)
    settings = get_settings()
    response = await GatewayClient().chat(
        {
            "model": model or settings.ai_text_model,
            "messages": [
                {
                    "role": "user",
                    "content": build_review_prompt(mode=mode, path=path, content=content, context=context),
                }
            ],
            "reasoning_effort": effort,
            "max_completion_tokens": 4000,
        }
    )
    print((response.get("choices") or [{}])[0].get("message", {}).get("content", ""))
    return 0


async def agent(*, goal: str, context: str, steps: int, tool: list[str], model: Optional[str]) -> int:
    request = AgentRunRequest(
        goal=goal,
        context=context or None,
        max_steps=steps,
        allowed_tools=tool or ["create_checklist", "draft_text"],
        model=model,
    )
    result = await AgentRunner(GatewayClient()).run(request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Thuc Chien starter CLI")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Show safe runtime configuration")
    text_command = commands.add_parser("text", help="Send one text prompt")
    text_command.add_argument("prompt")
    text_command.add_argument("--model")
    review_command = commands.add_parser("review", help="Review or debug one focused source file")
    review_command.add_argument(
        "--file", required=True, help="Source file only; .env and key files are refused"
    )
    review_command.add_argument("--mode", choices=REVIEW_MODES, default="review")
    review_command.add_argument(
        "--context", default="", help="Focused failure output or acceptance criterion"
    )
    review_command.add_argument("--model", default="gpt-6-luna")
    review_command.add_argument("--effort", choices=("none", "low", "medium", "high"), default="low")
    review_command.add_argument("--max-chars", type=int, default=24_000)
    agent_command = commands.add_parser("agent", help="Run a bounded tool-using demo agent")
    agent_command.add_argument("goal")
    agent_command.add_argument("--context", default="")
    agent_command.add_argument("--steps", type=int, default=2)
    agent_command.add_argument(
        "--tool", action="append", choices=("create_checklist", "draft_text", "generate_image")
    )
    agent_command.add_argument("--model")
    args = parser.parse_args()

    if args.command == "doctor":
        return doctor()
    if args.command == "text":
        return asyncio.run(text(args.prompt, args.model))
    if args.command == "review":
        return asyncio.run(
            review(
                path_value=args.file,
                mode=args.mode,
                context=args.context,
                model=args.model,
                effort=args.effort,
                max_chars=args.max_chars,
            )
        )
    if args.command == "agent":
        return asyncio.run(
            agent(
                goal=args.goal, context=args.context, steps=args.steps, tool=args.tool or [], model=args.model
            )
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
