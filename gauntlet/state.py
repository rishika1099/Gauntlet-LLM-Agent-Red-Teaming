"""Scan state passed to every agent. Concept: RunContext / State (setup).

Pass it as `context=state` to Runner.run; tools receive it as
`ctx: RunContextWrapper[ScanState]` (same pattern as Ghost Trials' RunState).

One ScanState lives for exactly one scan, inside one SSE request. It is never
shared across requests and never stored between requests: Cloud Run may route
the next request elsewhere, and CPU stops once the response ends.
The only cross-request memory is SCAN_HISTORY (small, in-process, for the
re-scan before/after view), which works because the demo runs with
min-instances = max-instances = 1.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from gauntlet.schemas import Attack, AttackResult, ReportCard, ScanEvent, TargetConfig, TargetProfile


@dataclass
class ScanState:
    target: TargetConfig
    mode: Literal["quick", "full", "rescan"]
    scan_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: float = field(default_factory=time.monotonic)
    deadline_s: float | None = None  # set for quick scans

    profile: TargetProfile | None = None
    attacks: list[Attack] = field(default_factory=list)
    results: list[AttackResult] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    llm_calls: int = 0

    events: asyncio.Queue[ScanEvent] = field(default_factory=asyncio.Queue)

    # ---- helpers every agent uses ----
    def emit(self, type_: str, **data) -> None:
        self.events.put_nowait(ScanEvent(type=type_, data=data))

    def add_usage(self, usage: dict[str, int]) -> None:
        self.llm_calls += 1
        self.tokens_in += usage.get("input", 0)
        self.tokens_out += usage.get("output", 0)

    def time_left(self) -> float | None:
        if self.deadline_s is None:
            return None
        return self.deadline_s - (time.monotonic() - self.started_at)

    def out_of_time(self) -> bool:
        left = self.time_left()
        return left is not None and left <= 0


# Last few reports, so a re-scan can show before vs after. Requires 1 instance.
SCAN_HISTORY: dict[str, ReportCard] = {}
MAX_HISTORY = 50


def remember(report: ReportCard) -> None:
    SCAN_HISTORY[report.scan_id] = report
    while len(SCAN_HISTORY) > MAX_HISTORY:
        SCAN_HISTORY.pop(next(iter(SCAN_HISTORY)))
