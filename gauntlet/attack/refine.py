"""Generator/critic. Owner: A. Issue: "[A] Generator/critic loop".

Concept: Generator/Critic. Given an attack that failed, one of its transcripts
and the judge's Verdict (the critic's reason), write a better attack with the
same category and goal. New id "<old id>-r<round>", retry_of=<old id>.
Full scans only, at most config.MAX_CRITIC_ROUNDS rounds.
"""

from gauntlet.schemas import Attack, Transcript, Verdict
from gauntlet.state import ScanState
from gauntlet.stubs import stub


@stub("[A] Generator/critic loop")
async def refine(state: ScanState, attack: Attack, transcript: Transcript, verdict: Verdict, round_: int) -> Attack | None:
    ...
