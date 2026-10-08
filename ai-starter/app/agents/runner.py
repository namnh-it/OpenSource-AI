from __future__ import annotations

import json
from typing import Any

from app.core.artifacts import save_base64
from app.core.config import get_settings
from app.schemas import AgentRunRequest

AGENT_TOOL_DEFINITIONS: dict[str, dict[str, Any]] = {
    "create_checklist": {
        "type": "function",
        "function": {
            "name": "create_checklist",
            "description": "Turn a short list of concrete tasks into a numbered execution checklist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 12,
                        "description": "Concrete actions, not vague ideas.",
                    }
                },
                "required": ["items"],
                "additionalProperties": False,
            },
        },
    },
    "draft_text": {
        "type": "function",
        "function": {
            "name": "draft_text",
            "description": "Ask the text model for one concise draft, script, or structured answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instruction": {"type": "string", "description": "What the draft must achieve."},
                    "context": {"type": "string", "description": "Only the facts needed for the draft."},
                },
                "required": ["instruction"],
                "additionalProperties": False,
            },
        },
    },
    "generate_image": {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate one image asset only when it materially improves the demo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "aspect_ratio": {
                        "type": "string",
                        "enum": ["1:1", "3:4", "4:3", "16:9", "9:16"],
                    },
                },
                "required": ["prompt"],
                "additionalProperties": False,
            },
        },
    },
}


class AgentRunner:
    """A small ReAct-style loop with an explicit tool allow-list and a hard step limit."""

    def __init__(self, gateway: Any) -> None:
        self.gateway = gateway

    async def run(self, request: AgentRunRequest) -> dict[str, Any]:
        tools = [AGENT_TOOL_DEFINITIONS[name] for name in request.allowed_tools]
        settings = get_settings()
        model = request.model or settings.ai_text_model
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are a bounded product-delivery agent for a short hackathon. "
                    "Achieve the stated goal with the smallest useful sequence. "
                    "Use a tool only when it moves the result forward. Do not invent tool outputs, "
                    "credentials, files, URLs, or test results. When enough evidence is available, "
                    "respond with a concise final answer in Vietnamese."
                ),
            },
            {
                "role": "user",
                "content": f"Goal:\n{request.goal}\n\nContext:\n{request.context or '(none)'}",
            },
        ]
        trace: list[dict[str, Any]] = []

        for step in range(1, request.max_steps + 1):
            response = await self.gateway.chat(
                {
                    "model": model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": request.temperature,
                    "max_completion_tokens": request.max_completion_tokens,
                }
            )
            message = ((response.get("choices") or [{}])[0]).get("message") or {}
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                final_answer = message.get("content") or "Agent returned no final answer."
                return {
                    "goal": request.goal,
                    "status": "completed",
                    "final_answer": final_answer,
                    "model": response.get("model", model),
                    "steps_used": step,
                    "trace": trace,
                }

            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )
            for tool_call in tool_calls:
                tool_name = (tool_call.get("function") or {}).get("name", "")
                arguments = self._parse_arguments((tool_call.get("function") or {}).get("arguments", "{}"))
                result = await self._execute_tool(tool_name, arguments, request)
                trace.append({"step": step, "tool": tool_name, "result": result})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", f"step-{step}-{tool_name}"),
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        return {
            "goal": request.goal,
            "status": "max_steps_reached",
            "final_answer": (
                "Đã dừng theo giới hạn số bước. Hãy dùng trace để chốt kết quả "
                "hoặc chạy lại với mục tiêu hẹp hơn."
            ),
            "model": model,
            "steps_used": request.max_steps,
            "trace": trace,
        }

    @staticmethod
    def _parse_arguments(raw_arguments: str) -> dict[str, Any]:
        try:
            value = json.loads(raw_arguments or "{}")
        except json.JSONDecodeError:
            return {"_error": "Tool arguments are not valid JSON"}
        return value if isinstance(value, dict) else {"_error": "Tool arguments must be an object"}

    async def _execute_tool(
        self, tool_name: str, arguments: dict[str, Any], request: AgentRunRequest
    ) -> dict[str, Any]:
        if tool_name not in request.allowed_tools:
            return {"ok": False, "error": f"Tool '{tool_name}' is not allowed for this run"}
        if "_error" in arguments:
            return {"ok": False, "error": arguments["_error"]}
        if tool_name == "create_checklist":
            return self._create_checklist(arguments)
        if tool_name == "draft_text":
            return await self._draft_text(arguments, request)
        if tool_name == "generate_image":
            return await self._generate_image(arguments)
        return {"ok": False, "error": f"Unsupported tool '{tool_name}'"}

    @staticmethod
    def _create_checklist(arguments: dict[str, Any]) -> dict[str, Any]:
        items = arguments.get("items")
        if not isinstance(items, list) or not items:
            return {"ok": False, "error": "items must be a non-empty list"}
        normalized = [str(item).strip()[:240] for item in items if str(item).strip()][:12]
        if not normalized:
            return {"ok": False, "error": "items must contain text"}
        return {"ok": True, "checklist": [f"{index}. {item}" for index, item in enumerate(normalized, 1)]}

    async def _draft_text(self, arguments: dict[str, Any], request: AgentRunRequest) -> dict[str, Any]:
        instruction = str(arguments.get("instruction", "")).strip()
        if not instruction:
            return {"ok": False, "error": "instruction is required"}
        context = str(arguments.get("context", request.context or "")).strip()[:12_000]
        settings = get_settings()
        model = request.model or settings.ai_text_model
        response = await self.gateway.chat(
            {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Write a concise, factual Vietnamese draft. Do not invent evidence.",
                    },
                    {"role": "user", "content": f"Instruction:\n{instruction}\n\nContext:\n{context}"},
                ],
                "temperature": request.temperature,
                "max_completion_tokens": request.max_completion_tokens,
            }
        )
        text = ((response.get("choices") or [{}])[0].get("message") or {}).get("content", "")
        return {"ok": True, "text": text, "model": response.get("model", model)}

    async def _generate_image(self, arguments: dict[str, Any]) -> dict[str, Any]:
        prompt = str(arguments.get("prompt", "")).strip()
        if not prompt:
            return {"ok": False, "error": "prompt is required"}
        settings = get_settings()
        payload: dict[str, Any] = {"model": settings.ai_image_model, "prompt": prompt[:4_000], "n": 1}
        if arguments.get("aspect_ratio"):
            payload["aspect_ratio"] = arguments["aspect_ratio"]
        response = await self.gateway.image(payload)
        image = (response.get("data") or [{}])[0]
        if image.get("b64_json"):
            filename, _ = save_base64(image["b64_json"], prefix="agent-image", content_type="image/png")
            return {"ok": True, "artifact_url": f"/artifacts/{filename}", "model": payload["model"]}
        if image.get("url"):
            return {"ok": True, "source_url": image["url"], "model": payload["model"]}
        return {"ok": False, "error": "Gateway image response has neither b64_json nor url"}
