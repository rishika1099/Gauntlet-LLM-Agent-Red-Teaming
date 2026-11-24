"""Suggest a guardrail patch; the user approves it before it is applied. Owner: C. Issue: "[C] Patch + approval flow".

Concept: Human-in-the-loop approval. suggest_patch writes short security rules
(an Agent on config.PATCH_MODEL) from the breached verdicts in a ReportCard.
Nothing is applied until the user clicks Approve in the UI; only then does
the browser start a re-scan with target.patch set, mode "rescan", and
only_categories = the failed ones (keeps grader task 2 under 5 minutes).
Return "" if nothing breached. Fake mode: a fixed patch.
"""

from gauntlet.schemas import ReportCard
from gauntlet.stubs import stub


@stub("[C] Patch + approval flow")
async def suggest_patch(report: ReportCard) -> str:
    ...
