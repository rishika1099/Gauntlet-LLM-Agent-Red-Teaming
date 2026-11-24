"""Attack planner. Owner: A. Issues: "[A] Planner", "[A] Day-1 attacker check".

Concept: Dynamic instructions. Build the planner's instructions at run time
from the TargetProfile in the RunContext (Agent(instructions=<callable>)), so
every plan is tailored to the target.

Return `per_category` attacks for each requested category, as a list of
schemas.Attack with ids "<category>-<n>". Never plan real-world harmful content
(gauntlet.guardrails filters again afterwards).

Fake mode: return fixed attacks per category (no model call).
"""

from gauntlet.schemas import Attack, Category
from gauntlet.state import ScanState
from gauntlet.stubs import stub


@stub("[A] Planner")
async def plan_attacks(state: ScanState, categories: list[Category], per_category: int) -> list[Attack]:
    ...
