"""Setup tests: these pass from day 1 and must keep passing."""

import json

import litellm
import pytest
from agents import Agent
from fastapi.testclient import TestClient
from litellm import ModelResponse
from litellm.types.utils import Choices, Message, Usage

from app import app
from gauntlet import models
from gauntlet.schemas import ScanEvent
from gauntlet.stubs import NotBuiltYet, is_built, stub

client = TestClient(app)


def sse_events(body: dict) -> list[tuple[str, dict]]:
    with client.stream("POST", "/api/scan", json=body) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())
    out = []
    for chunk in text.split("\n\n"):
        if chunk.strip() and not chunk.startswith(":"):
            lines = dict(line.split(": ", 1) for line in chunk.splitlines())
            out.append((lines["event"], json.loads(lines["data"])))
    return out


def test_health():
    body = client.get("/health").json()
    assert body["ok"] and body["fake_llm"] and body["victims"] == ["leaky", "bank", "fort"]


def test_sse_format():
    assert ScanEvent(type="status", data={"message": "hi"}).to_sse() == 'event: status\ndata: {"message": "hi"}\n\n'


def test_scan_always_ends_with_report_and_done():
    events = sse_events({"target": {"kind": "zoo", "name": "leaky"}, "mode": "quick"})
    types = [t for t, _ in events]
    assert types[0] == "status" and types[-2:] == ["report", "done"] or "error" in types


async def test_stub_raises_and_is_detected():
    @stub("[X] Example")
    async def f():
        return 1

    assert not is_built(f)
    with pytest.raises(NotBuiltYet, match="Example"):
        await f()


def _fake_litellm(monkeypatch, finish_reason, content):
    async def fake(*args, **kwargs):
        r = ModelResponse(id="x", model="vertex_ai/test", choices=[
            Choices(finish_reason=finish_reason, index=0, message=Message(role="assistant", content=content))])
        r.usage = Usage(prompt_tokens=7, completion_tokens=3, total_tokens=10)
        return r

    monkeypatch.setattr(litellm, "acompletion", fake)


async def test_run_agent_normal_reply(monkeypatch):
    _fake_litellm(monkeypatch, "stop", "hello")
    run = await models.run_agent(Agent(name="t", instructions="x", model=models.model("vertex_ai/test")), "hi")
    assert run.output == "hello" and not run.blocked and run.input_tokens == 7


async def test_gemini_safety_block_is_blocked_not_a_refusal(monkeypatch):
    """Gemini's safety filter -> LiteLLM finish_reason content_filter -> AgentRun(blocked=True)."""
    _fake_litellm(monkeypatch, "content_filter", None)
    run = await models.run_agent(Agent(name="t", instructions="x", model=models.model("vertex_ai/test")), "hi")
    assert run.blocked and run.output is None and run.refusal is None


def test_openai_ids_are_plain_strings():
    assert models.model("gpt-6.1-sol") == "gpt-6.1-sol"
    assert models.model("vertex_ai/gemini-3.5-flash-lite").model == "vertex_ai/gemini-3.5-flash-lite"


def test_selftest_stream_short():
    with client.stream("GET", "/api/selftest/stream?seconds=5") as resp:
        text = "".join(resp.iter_text())
    assert "event: status" in text and "event: done" in text
