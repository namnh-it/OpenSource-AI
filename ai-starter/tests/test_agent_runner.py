import asyncio

from app.agents.runner import AgentRunner
from app.schemas import AgentRunRequest


class FakeGateway:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.requests: list[dict] = []

    async def chat(self, payload: dict) -> dict:
        self.requests.append(payload)
        return self.responses.pop(0)


def test_agent_runs_tool_then_returns_final_answer() -> None:
    gateway = FakeGateway(
        [
            {
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "function": {
                                        "name": "create_checklist",
                                        "arguments": '{"items":["Chot happy path","Test demo"]}',
                                    },
                                }
                            ]
                        }
                    }
                ],
            },
            {"model": "test-model", "choices": [{"message": {"content": "Da co checklist demo."}}]},
        ]
    )

    result = asyncio.run(AgentRunner(gateway).run(AgentRunRequest(goal="Chuan bi demo", max_steps=2)))

    assert result["status"] == "completed"
    assert result["final_answer"] == "Da co checklist demo."
    assert result["trace"][0]["result"]["checklist"] == ["1. Chot happy path", "2. Test demo"]
    assert gateway.requests[1]["messages"][-1]["role"] == "tool"


def test_agent_rejects_a_tool_outside_the_allow_list() -> None:
    runner = AgentRunner(FakeGateway([]))
    request = AgentRunRequest(goal="Chuan bi demo", allowed_tools=["create_checklist"])

    result = asyncio.run(runner._execute_tool("generate_image", {"prompt": "x"}, request))

    assert result == {"ok": False, "error": "Tool 'generate_image' is not allowed for this run"}
