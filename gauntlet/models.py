"""How every agent talks to a model. Setup (shared): use these, don't call LiteLLM or Runner directly.

- `model(name)`: a LitellmModel for Gemini on Vertex AI (same as Ghost Trials).
- `SETTINGS`: per-call timeout and LiteLLM retries (429s and 5xx back off and retry).
- `run_agent(...)`: Runner.run behind a global semaphore (MAX_PARALLEL_CALLS), so 36
  parallel conversations don't trigger a wall of 429s. It also turns a provider
  safety block into `AgentRun(blocked=True)`.

Why the block handling matters: when Gemini's safety filter blocks a reply, the
Agents SDK raises ModelRefusalError with the text "Response withheld by the
provider's content filter." That is Google's filter, not the target defending
itself, so it must be scored BLOCKED, never HELD (tests/test_models.py).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from agents import Agent, ModelRefusalError, ModelSettings, Runner, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

from gauntlet import config

# The SDK's own traces upload to OpenAI by default. We trace with Langfuse instead (gauntlet/tracing.py).
set_tracing_disabled(True)

CONTENT_FILTER_MARKER = "withheld by the provider's content filter"

SETTINGS = ModelSettings(extra_args={**config.VERTEX_ARGS, "timeout": config.MODEL_TIMEOUT_S, "num_retries": 3})
# OpenAI models (judge, patch writer) need no Vertex args.
OPENAI_SETTINGS = ModelSettings()

_semaphore: asyncio.Semaphore | None = None


def _sem() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(config.MAX_PARALLEL_CALLS)
    return _semaphore


def model(name: str) -> LitellmModel | str:
    """Gemini ids ('vertex_ai/...') go through LiteLLM; OpenAI ids are passed as plain strings."""
    if name.startswith("vertex_ai/") or "/" in name:
        # api_key is unused: Vertex AI uses gcloud / service account credentials.
        return LitellmModel(model=name, api_key="unused")
    return name


def settings_for(name: str) -> ModelSettings:
    return SETTINGS if "/" in name else OPENAI_SETTINGS


@dataclass
class AgentRun:
    output: Any = None  # final_output (a str, or the agent's output_type)
    blocked: bool = False  # provider safety filter fired
    refusal: str | None = None  # the model itself refused (counts as the target holding)
    input_tokens: int = 0
    output_tokens: int = 0


async def run_agent(agent: Agent[Any], input: str | list[Any], *, context: Any = None,
                    max_turns: int = 4, hooks: Any = None) -> AgentRun:
    async with _sem():
        try:
            result = await Runner.run(agent, input, context=context, max_turns=max_turns, hooks=hooks)
        except ModelRefusalError as exc:
            if CONTENT_FILTER_MARKER in (exc.refusal or ""):
                return AgentRun(blocked=True)
            return AgentRun(refusal=exc.refusal)
    usage = result.context_wrapper.usage
    return AgentRun(output=result.final_output, input_tokens=usage.input_tokens, output_tokens=usage.output_tokens)


async def fake_delay() -> None:
    """Call at the top of a fake-mode branch, so a long fake scan can test Cloud Run streaming."""
    if config.FAKE_LLM_DELAY_S > 0:
        async with _sem():
            await asyncio.sleep(config.FAKE_LLM_DELAY_S)
