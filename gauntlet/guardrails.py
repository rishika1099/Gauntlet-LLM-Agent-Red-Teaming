"""Guardrails on Gauntlet itself. Owner: C. Issue: "[C] Guardrails".

Concept: Guardrails.
- check_target: zoo victims (VICTIM_NAMES) are always allowed. External targets
  must be https AND start with a prefix in config.TARGET_ALLOWLIST, else raise
  GuardrailError with a message that says it is not on the allowlist.
- filter_attacks: drop any attack asking for real-world harmful content
  (weapons, malware, self-harm, drugs...), then cap at config.HARD_ATTACK_CAP.
  Return (kept attacks, notes about anything dropped).
"""

from gauntlet.schemas import Attack, TargetConfig
from gauntlet.stubs import stub


class GuardrailError(ValueError):
    pass


@stub("[C] Guardrails")
def check_target(target: TargetConfig) -> None:
    ...


@stub("[C] Guardrails")
def filter_attacks(attacks: list[Attack]) -> tuple[list[Attack], list[str]]:
    ...
