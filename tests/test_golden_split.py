"""The 6 golden examples (judge prompt) and the 30 held-out transcripts (agreement eval) must never overlap."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "evals" / "judge_agreement"


def load(folder: str) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((ROOT / folder).glob("*.json"))]


def test_no_overlap():
    key = lambda ex: json.dumps(ex["turns"], sort_keys=True)  # noqa: E731
    assert not ({key(e) for e in load("golden")} & {key(e) for e in load("heldout")})


def test_at_most_six_golden():
    assert len(load("golden")) <= 6
