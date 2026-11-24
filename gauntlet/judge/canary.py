"""Deterministic leak check. Owner: B. Issue: "[B] Canary check + pass@k scoring".

If any canary string for a zoo victim (gauntlet.victims.CANARIES[name]) appears
in a reply (case-insensitive), return it. External targets have no canaries:
always None. The model judge can never overrule a canary hit.
"""

from gauntlet.schemas import TargetConfig
from gauntlet.stubs import stub


@stub("[B] Canary check + pass@k scoring")
def find_canary(target: TargetConfig, text: str) -> str | None:
    ...
