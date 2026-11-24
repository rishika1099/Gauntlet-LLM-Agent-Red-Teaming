"""Lane A acceptance tests. They switch on as A removes each @stub. Add more as you build."""

from gauntlet import adapter
from gauntlet.attack import fanout, planner
from gauntlet.schemas import Attack, Category, TargetConfig, Turn
from gauntlet.state import ScanState
from tests.conftest import needs


def _state():
    return ScanState(target=TargetConfig(kind="zoo", name="leaky"), mode="quick")


@needs(planner.plan_attacks)
async def test_planner_returns_per_category_attacks():
    cats = [Category.DATA_LEAK, Category.OFF_TASK]
    attacks = await planner.plan_attacks(_state(), cats, 2)
    assert len(attacks) == 4 and {a.category for a in attacks} == set(cats)
    assert len({a.id for a in attacks}) == 4


@needs(fanout.run_all)
async def test_blocked_reply_ends_the_run(monkeypatch):
    async def blocked(target, history, message):
        return Turn(role="target", content="", blocked=True, finish_reason="content_filter")

    monkeypatch.setattr(adapter, "send", blocked)
    attack = Attack(id="a1", category=Category.DATA_LEAK, goal="g", opening_message="hi")
    (t,) = (await fanout.run_all(_state(), [attack], 1))["a1"]
    assert t.provider_blocked and len(t.turns) == 2


@needs(fanout.run_all)
async def test_one_failing_run_does_not_kill_the_others(monkeypatch):
    calls = {"n": 0}

    async def flaky(target, history, message):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return Turn(role="target", content="no")

    monkeypatch.setattr(adapter, "send", flaky)
    attack = Attack(id="a1", category=Category.DATA_LEAK, goal="g", opening_message="hi")
    runs = (await fanout.run_all(_state(), [attack], 3))["a1"]
    assert len(runs) == 3 and sum(1 for r in runs if r.error) == 1
