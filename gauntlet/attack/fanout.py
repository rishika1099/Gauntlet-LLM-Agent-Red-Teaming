"""Parallel multi-turn attacks. Owner: A. Issues: "[A] Multi-turn attacker + fan-out", "[A] Live progress hooks".

Concept: Parallel fan-out. Run every attack k times at once (asyncio.gather).
Each run is a multi-turn conversation of up to config.MAX_TURNS: the attacker
agent writes the next message from the target's last reply; the target answers
through gauntlet.adapter.send.

Concept: Hooks. Use a RunHooks subclass to emit live progress events
(state.emit) for each attacker turn, so the browser sees attacks as they happen.

Rules:
- Use gauntlet.models.run_agent (semaphore, retries, block detection).
- A target Turn with blocked=True ends the run: set transcript.provider_blocked.
- Stop early if gauntlet.judge.canary.find_canary hits (leak proven).
- Stop starting new turns when state.out_of_time().
- An exception in one run sets transcript.error; it must not kill the others.

Returns {attack_id: [Transcript, ...k]}.
"""

from gauntlet.schemas import Attack, Transcript
from gauntlet.state import ScanState
from gauntlet.stubs import stub


@stub("[A] Multi-turn attacker + fan-out")
async def run_all(state: ScanState, attacks: list[Attack], k: int) -> dict[str, list[Transcript]]:
    ...
