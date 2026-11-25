"""The agreement runner works offline. Tests use fake mode, where the judge answers HELD unless a canary hits."""

import json

from evals.judge_agreement import run


def _example(id_, outcome, score):
    return {
        "id": id_, "target_kind": "http", "target_name": "x", "category": "data_leak", "goal": "g",
        "turns": [{"role": "attacker", "content": "hi"}, {"role": "target", "content": "I cannot help with that."}],
        "label": {"outcome": outcome, "score": score, "reason": "r", "evidence_quote": ""},
    }


def test_load_examples_reads_sorted_json(tmp_path):
    (tmp_path / "b.json").write_text(json.dumps(_example("b", "held", 0)))
    (tmp_path / "a.json").write_text(json.dumps(_example("a", "held", 0)))
    assert [e["id"] for e in run.load_examples(tmp_path)] == ["a", "b"]


async def test_agreement_counts_matches_and_misses():
    examples = [_example("a", "held", 0), _example("b", "held", 0), _example("c", "breached", 2)]
    result = await run.evaluate(examples)
    assert result["total"] == 3 and result["agree"] == 2
    assert result["missed_breaches"] == 1 and result["false_breaches"] == 0
    assert result["by_category"] == {"data_leak": "2/3"}
    assert "Disagreements:" in run.report(result) and "c:" in run.report(result)


def test_main_reports_empty_folder(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "HERE", tmp_path)
    (tmp_path / "heldout").mkdir()
    assert run.main([]) == 1
    assert "No examples" in capsys.readouterr().out
