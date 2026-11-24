"""Runs one scan end to end and streams progress into state.events. Setup (shared).

guardrail -> recon -> plan -> filter -> fan-out -> judge -> [critic rounds] -> score -> report

On day 1 every step is a stub: the scan stops at the first unbuilt step and
says which issue it is waiting for. As each person merges their part, the scan
gets further. Don't change the step order or signatures without telling everyone.
"""

from __future__ import annotations

import asyncio

from gauntlet import config, guardrails
from gauntlet.attack import fanout, planner, recon, refine
from gauntlet.judge import scoring
from gauntlet.judge.judge import judge
from gauntlet.schemas import Attack, AttackResult, Category, Outcome, ReportCard, ScanRequest
from gauntlet.state import SCAN_HISTORY, ScanState, remember
from gauntlet.stubs import NotBuiltYet
from gauntlet.tracing import finish_scan_trace, observe


async def _judge_attack(state: ScanState, attack: Attack, transcripts) -> AttackResult:
    verdicts = await asyncio.gather(*(judge(state, attack, t) for t in transcripts))
    result = scoring.score_attack(attack, transcripts, list(verdicts))
    state.emit("attack_result", result=result.model_dump(mode="json"))
    return result


async def _pipeline(req: ScanRequest, state: ScanState, results: list[AttackResult]) -> None:
    guardrails.check_target(req.target)  # raises GuardrailError

    state.emit("status", message="Recon: talking to the target normally")
    profile = await recon.run_recon(state)
    state.emit("profile", profile=profile.model_dump(mode="json"))

    categories = req.only_categories or list(Category)
    per_cat = config.FULL_PER_CATEGORY if req.mode == "full" else config.QUICK_PER_CATEGORY
    state.emit("status", message=f"Planning {per_cat * len(categories)} attacks")
    attacks, notes = guardrails.filter_attacks(await planner.plan_attacks(state, categories, per_cat))
    for note in notes:
        state.emit("status", message=note)
    state.emit("plan", attacks=[a.model_dump(mode="json") for a in attacks])

    k = config.RUNS_PER_ATTACK
    state.emit("status", message=f"Running {len(attacks)} attacks x {k} runs in parallel")
    by_attack = await fanout.run_all(state, attacks, k)
    results += await asyncio.gather(*(_judge_attack(state, a, by_attack[a.id]) for a in attacks))

    if req.mode != "full":
        return  # quick scans and re-scans skip critic rounds to fit the 5-minute grader limit
    latest = list(results)  # each round only rewrites the attacks that failed in the round before
    for round_ in range(1, config.MAX_CRITIC_ROUNDS + 1):
        failed = [r for r in latest if r.pass_at_k is False]
        if not failed or state.out_of_time():
            break
        state.emit("status", message=f"Critic round {round_}: rewriting {len(failed)} failed attacks")
        rewritten = []
        for r in failed:
            held = next((v for v in r.verdicts if v.outcome == Outcome.HELD), r.verdicts[0])
            if new := await refine.refine(state, r.attack, r.transcripts[0], held, round_):
                rewritten.append(new)
        rewritten, _ = guardrails.filter_attacks(rewritten)
        new_runs = await fanout.run_all(state, rewritten, k)
        latest = list(await asyncio.gather(*(_judge_attack(state, a, new_runs[a.id]) for a in rewritten)))
        results += latest


@observe(name="scan")
async def run_scan(req: ScanRequest, state: ScanState) -> ReportCard:
    results: list[AttackResult] = []
    unbuilt: str | None = None
    try:
        await _pipeline(req, state, results)
    except NotBuiltYet as exc:
        unbuilt = exc.issue
        state.emit("status", message=f"Stopped: this step is not built yet ({exc.issue})")

    try:
        categories = scoring.score_categories(results) if results else []
    except NotBuiltYet as exc:
        categories, unbuilt = [], unbuilt or exc.issue
    for c in categories:
        state.emit("category", score=c.model_dump(mode="json"))

    report = ReportCard(
        scan_id=state.scan_id,
        target_name=req.target.name,
        mode=req.mode,
        categories=categories,
        results=results,
        partial=state.out_of_time() or unbuilt is not None,
        previous_scan_id=req.previous_scan_id if req.previous_scan_id in SCAN_HISTORY else None,
        trace_url=finish_scan_trace(is_zoo=req.target.kind == "zoo"),
    )
    remember(report)
    return report
