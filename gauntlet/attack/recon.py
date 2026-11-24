"""Recon agent. Owner: A. Issue: "[A] Recon agent".

Talk to the target normally for ~5 turns (through gauntlet.adapter.send), then
turn the transcript into a TargetProfile with an Agent whose output_type is
TargetProfile. Record token usage in state.add_usage(...).

Fake mode (config.FAKE_LLM): skip the model, return a canned TargetProfile.
"""

from gauntlet.schemas import TargetProfile
from gauntlet.state import ScanState
from gauntlet.stubs import stub


@stub("[A] Recon agent")
async def run_recon(state: ScanState) -> TargetProfile:
    ...
