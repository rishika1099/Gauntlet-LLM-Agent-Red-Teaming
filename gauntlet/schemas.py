"""Shared contracts. Concept: Structured output (setup; changes need a PR that tags all three).

Every agent reads and writes these typed models. Changing a field here affects
all three people, so open a PR and tag everyone.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Category(str, Enum):
    """Attack categories, loosely following the OWASP Top 10 for LLM apps."""

    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    DATA_LEAK = "data_leak"
    TOOL_MISUSE = "tool_misuse"
    PROMPT_INJECTION = "prompt_injection"
    OFF_TASK = "off_task"
    PERSONA_BREAK = "persona_break"


class Outcome(str, Enum):
    """Result of ONE run of ONE attack.

    BLOCKED means the provider's safety filter stopped a reply (finishReason
    SAFETY, a blocked prompt, etc). It is never counted as HELD: the target
    did not defend itself, Google's filter did.
    """

    BREACHED = "breached"  # the attack worked
    HELD = "held"  # the target defended itself
    BLOCKED = "blocked"  # provider safety filter, excluded from pass rates
    ERROR = "error"  # network / parsing failure


# ---------- target ----------


class TargetConfig(BaseModel):
    """How to talk to a target. Zoo victims run in-process; external targets use HTTP."""

    kind: Literal["zoo", "http"] = "zoo"
    name: str = Field(..., description="Zoo victim name (leaky, bank, fort) or a label")
    url: str | None = None
    # JSON body with placeholders "{{message}}" and "{{history}}"
    request_template: dict[str, Any] | None = None
    # Dotted path to the reply text in the response JSON, e.g. "reply" or "choices.0.message.content"
    reply_path: str = "reply"
    headers: dict[str, str] = Field(default_factory=dict)
    patch: str | None = Field(None, description="Extra guardrail text applied to a zoo victim test copy")

    @property
    def is_external(self) -> bool:
        return self.kind == "http"


class TargetProfile(BaseModel):
    """What recon learned about the target."""

    purpose: str
    stated_rules: list[str] = Field(default_factory=list)
    tools_mentioned: list[str] = Field(default_factory=list)
    persona: str = ""
    notes: str = ""


# ---------- attacks ----------


class Attack(BaseModel):
    id: str
    category: Category
    goal: str = Field(..., description="What counts as success, in one sentence")
    opening_message: str
    strategy: str = Field("", description="How later turns should escalate")
    retry_of: str | None = None  # set when the critic rewrote a failed attack


class AttackPlan(BaseModel):
    attacks: list[Attack]


class Turn(BaseModel):
    role: Literal["attacker", "target"]
    content: str
    blocked: bool = False
    finish_reason: str | None = None


class Transcript(BaseModel):
    attack_id: str
    run_index: int
    turns: list[Turn] = Field(default_factory=list)
    provider_blocked: bool = False
    error: str | None = None


# ---------- judging ----------


class Verdict(BaseModel):
    """Judge output for one transcript. Concept: Model-as-judge."""

    attack_id: str
    run_index: int
    outcome: Outcome
    score: int = Field(..., ge=0, le=2, description="0 held, 1 partial, 2 clear breach")
    reason: str
    evidence_quote: str = ""
    canary_hit: bool = False  # deterministic check fired; judge cannot overrule it


class AttackResult(BaseModel):
    attack: Attack
    transcripts: list[Transcript]
    verdicts: list[Verdict]
    pass_at_k: bool | None = None  # breached at least once in k valid runs
    pass_hat_k: bool | None = None  # breached in every one of k valid runs
    valid_runs: int = 0  # runs that were not BLOCKED or ERROR


class CategoryScore(BaseModel):
    category: Category
    status: Literal["PASS", "FAIL", "INCONCLUSIVE"]
    attacks_run: int
    breached_at_k: int  # attacks with pass@k true
    breached_hat_k: int  # attacks with pass^k true
    blocked_runs: int


class ReportCard(BaseModel):
    scan_id: str
    target_name: str
    mode: Literal["quick", "full", "rescan"]
    categories: list[CategoryScore]
    results: list[AttackResult]
    partial: bool = False  # true if the time cutoff hit
    trace_url: str | None = None
    patch_suggestion: str | None = None
    previous_scan_id: str | None = None  # set on a re-scan, for before vs after


# ---------- API ----------


class ScanRequest(BaseModel):
    target: TargetConfig
    mode: Literal["quick", "full", "rescan"] = "quick"
    only_categories: list[Category] | None = None  # used by re-scan
    previous_scan_id: str | None = None


class ScanEvent(BaseModel):
    """One Server-Sent Event sent to the browser during a scan."""

    type: Literal["status", "profile", "plan", "attack_result", "category", "report", "error", "done"]
    data: dict[str, Any] = Field(default_factory=dict)

    def to_sse(self) -> str:
        return f"event: {self.type}\ndata: {json.dumps(self.data, default=str)}\n\n"
